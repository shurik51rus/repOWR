"""
Счётчик репутации для протокола repOWR.
Анализирует данные из базы и рассчитывает репутацию пользователей.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

# Импортируем наши модули
from database import Database
import config


class ReputationCounter:
    """Класс для расчёта репутации пользователей"""
    
    def __init__(self):
        """Инициализация счётчика"""
        self.db = Database(config.DATABASE_PATH)
        self.db.connect()
        
        # Словарь для хранения репутации пользователей
        # Структура: {адрес: {данные репутации}}
        self.reputation_data = {}
    
    def calculate_reputation(self):
        """
        Основной метод расчёта репутации.
        Получает все рейтинги из БД и рассчитывает репутацию для каждого пользователя.
        """
        print("=" * 60)
        print("🧮 Расчёт репутации пользователей (протокол repOWR)")
        print("=" * 60)
        
        # Получаем все рейтинги из базы
        print("\n📥 Загрузка данных из базы...")
        all_ratings = self.db.get_all_ratings()
        
        if not all_ratings:
            print("⚠ Рейтинги не найдены в базе данных")
            return
        
        print(f"✓ Загружено {len(all_ratings)} рейтингов")
        
        # Группируем рейтинги по получателям (receiver)
        # Репутация считается для того, кому ставят оценки
        user_ratings = defaultdict(list)
        user_given_ratings = defaultdict(int)  # Счётчик выставленных оценок
        
        for rating in all_ratings:
            # Добавляем рейтинг в список получателя
            user_ratings[rating['receiver']].append(rating)
            
            # Считаем сколько оценок выставил отправитель
            user_given_ratings[rating['sender']] += 1
        
        print(f"✓ Обработано пользователей: {len(user_ratings)}")
        
        # Рассчитываем репутацию для каждого пользователя
        print("\n⚙️ Расчёт репутации...")
        
        for address, ratings in user_ratings.items():
            rep_data = self._calculate_user_reputation(address, ratings)
            
            # Добавляем количество выставленных оценок
            rep_data['ratings_given'] = user_given_ratings.get(address, 0)
            
            self.reputation_data[address] = rep_data
        
        print(f"✓ Рассчитано репутаций: {len(self.reputation_data)}")
    
    def _calculate_user_reputation(self, address: str, ratings: List[Dict]) -> Dict[str, Any]:
        """
        Рассчитываем репутацию для одного пользователя
        
        Args:
            address: адрес пользователя
            ratings: список его рейтингов
        
        Returns:
            Словарь с данными репутации
        """
        total_score = 0
        ratings_count = 0
        
        # Группируем по типам для статистики
        by_type = defaultdict(list)
        
        for rating in ratings:
            rating_value = rating.get('rating')
            rating_type = rating.get('type', 'general')
            
            # Накапливаем сумму
            total_score += rating_value
            ratings_count += 1
            
            # Статистика по типам
            by_type[rating_type].append(rating_value)
        
        # Вычисляем средний балл
        avg_rating = total_score / ratings_count if ratings_count > 0 else 0
        
        # Вычисляем итоговый балл (пока просто средний, можно усложнить)
        final_score = avg_rating
        
        # Формируем результат
        result = {
            'address': address,
            'final_score': round(final_score, 2),
            'avg_rating': round(avg_rating, 2),
            'total_ratings': ratings_count,
            'by_type': dict(by_type)
        }
        
        return result
    
    def normalize_address(self, address: str) -> str:
        """
        Нормализует адрес к единому формату для поиска
        
        Args:
            address: адрес в любом формате
        
        Returns:
            нормализованный адрес (raw формат 0:hex)
        """
        if not address:
            return ""
        
        address = address.strip()
        
        # Если уже в raw формате - возвращаем как есть
        if address.startswith("0:") or address.startswith("-1:"):
            return address
        
        # Если user-friendly формат (UQ/EQ), конвертируем в raw
        if address.startswith("UQ") or address.startswith("EQ"):
            try:
                # Простая конвертация через pytoniq если доступна
                try:
                    from pytoniq_core import Address
                    addr_obj = Address(address)
                    return f"{addr_obj.wc}:{addr_obj.hash_part.hex()}"
                except ImportError:
                    # Если нет pytoniq - ищем по частичному совпадению
                    pass
            except:
                pass
        
        return address
    
    def find_user_by_address(self, address: str) -> Optional[str]:
        """
        Находит пользователя в базе по адресу (поддерживает разные форматы)
        Улучшенная версия - декодирует UQ/EQ адреса в raw формат
        
        Args:
            address: адрес для поиска
        
        Returns:
            найденный адрес из базы или None
        """
        # Если репутация ещё не рассчитана, рассчитываем
        if not self.reputation_data:
            self.calculate_reputation()
        
        address = address.strip()
        
        # Пытаемся найти точное совпадение
        if address in self.reputation_data:
            return address
        
        # Для UQ/EQ адресов - декодируем base64 и получаем hex
        if address.startswith("UQ") or address.startswith("EQ"):
            try:
                import base64
                
                # Убираем префикс UQ/EQ
                b64_part = address[2:]
                
                # Заменяем URL-safe символы на стандартные base64
                b64_part = b64_part.replace('-', '+').replace('_', '/')
                
                # Добавляем паддинг если нужно
                padding = 4 - (len(b64_part) % 4)
                if padding != 4:
                    b64_part += '=' * padding
                
                # Декодируем
                decoded = base64.b64decode(b64_part)
                decoded_hex = decoded.hex()
                
                # Структура: tag(1) + hash(32) + crc(2) = 35 байт = 70 hex символов
                # НО: workchain встроен в tag, hash начинается со второго hex символа
                
                if len(decoded_hex) >= 66:
                    # Hash - это символы с 1 по 65 (32 байта)
                    hash_hex = decoded_hex[1:65]
                    
                    # Workchain обычно 0 для user-friendly адресов
                    # Можно извлечь из первого байта, но проще поискать по hash
                    
                    if config.DEBUG_MODE:
                        print(f"🔍 Конвертация: {address[:10]}... hash={hash_hex[:16]}...")
                    
                    # Ищем в базе по hash части (игнорируя workchain)
                    for db_address in self.reputation_data.keys():
                        if ":" in db_address:
                            db_hash = db_address.split(":", 1)[1]
                            if db_hash == hash_hex:
                                if config.DEBUG_MODE:
                                    print(f"✅ Найдено: {db_address}")
                                return db_address
            except Exception as e:
                if config.DEBUG_MODE:
                    print(f"⚠️ Ошибка декодирования адреса {address}: {e}")
        
        # Для raw адресов (0:hex или -1:hex)
        if ":" in address:
            # Ищем точное совпадение
            if address in self.reputation_data:
                return address
            
            # Извлекаем hex часть
            try:
                hex_part = address.split(":", 1)[1].lower()
                
                # Ищем по hex части
                for db_address in self.reputation_data.keys():
                    if db_address.lower().endswith(hex_part):
                        return db_address
            except:
                pass
        
        # Если ничего не нашли - пытаемся искать по частичному совпадению
        # (последние 16 символов для уверенности)
        search_key = address.lower()[-16:] if len(address) >= 16 else address.lower()
        
        for db_address in self.reputation_data.keys():
            if search_key in db_address.lower():
                return db_address
        
        return None
    
    def get_user_reputation(self, address: str) -> Optional[Dict[str, Any]]:
    
        """
        Получаем репутацию конкретного пользователя
        
        Args:
            address: адрес пользователя (в любом формате)
        
        Returns:
            Словарь с данными репутации или None если не найден
        """
        # Находим адрес в базе
        found_address = self.find_user_by_address(address)
        
        if not found_address:
            return None
        
        return self.reputation_data.get(found_address)
    
    def get_top_users(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Получаем топ пользователей по репутации
        
        Args:
            count: количество пользователей в топе
        
        Returns:
            Список пользователей, отсортированный по final_score
        """
        # Сортируем по final_score
        sorted_users = sorted(
            self.reputation_data.values(),
            key=lambda x: x['final_score'],
            reverse=True
        )
        
        return sorted_users[:count]
    
    def format_reputation_text(self, address: str) -> str:
        """
        Форматируем репутацию пользователя в текст для бота
        
        Args:
            address: адрес пользователя (в любом формате)
        
        Returns:
            Отформатированный текст с репутацией
        """
        # Находим адрес в базе
        found_address = self.find_user_by_address(address)
        
        if not found_address:
            return f"📊 РЕПУТАЦИЯ ПОЛЬЗОВАТЕЛЯ\n\nАдрес: {address[:10]}...{address[-6:]}\n\n⚠️ Репутация не найдена"
        
        rep = self.reputation_data.get(found_address)
        
        if not rep:
            return f"📊 РЕПУТАЦИЯ ПОЛЬЗОВАТЕЛЯ\n\nАдрес: {address[:10]}...{address[-6:]}\n\n⚠️ Репутация не найдена"
        
        # Получаем профиль пользователя (если есть) - ищем по raw адресу
        profile = self.db.get_profile_by_address(found_address)
        
        text = "📊 РЕПУТАЦИЯ ПОЛЬЗОВАТЕЛЯ\n\n"
        
        # Добавляем информацию из профиля
        if profile:
            # Основная информация
            text += f"👤 <b>{profile['nickname']}</b>\n"
            
            # Аватарка (если есть)
            if profile.get('avatar'):
                text += f"🖼 <a href=\"{profile['avatar']}\">Аватарка</a>\n"
            
            text += f"📝 {profile['bio']}\n\n"
            
            # Дополнительные поля профиля
            if profile.get('skills'):
                skills = ', '.join(profile['skills'])
                text += f"💼 Навыки: {skills}\n"
            
            if profile.get('languages'):
                langs = ', '.join(profile['languages'])
                text += f"🌍 Языки: {langs}\n"
            
            if profile.get('location'):
                text += f"📍 Местоположение: {profile['location']}\n"
            
            if profile.get('nationality'):
                text += f"🏴 Гражданство: {profile['nationality']}\n"
            
            if profile.get('birth_year'):
                text += f"📅 Год рождения: {profile['birth_year']}\n"
            
            # Социальные ссылки
            if profile.get('links'):
                links_text = []
                for platform, link in profile['links'].items():
                    if platform == 'telegram':
                        links_text.append(f"Telegram: {link}")
                    elif platform == 'github':
                        links_text.append(f"GitHub: {link}")
                    elif platform == 'website':
                        links_text.append(f"Сайт: {link}")
                    else:
                        links_text.append(f"{platform.capitalize()}: {link}")
                
                if links_text:
                    text += f"\n🔗 Ссылки:\n"
                    for link_str in links_text:
                        text += f"  • {link_str}\n"
            
            text += f"\n"
        else:
            # Показываем исходный адрес который ввёл пользователь
            text += f"Адрес: <code>{address[:10]}...{address[-6:]}</code>\n\n"
        
        # Основные метрики
        text += f"🎯 Итоговый балл: {rep['final_score']}\n"
        text += f"⭐️ Средняя оценка: {rep['avg_rating']}\n"
        text += f"📊 Отзывов получено: {rep['total_ratings']}\n"
        text += f"✍️ Отзывов оставлено: {rep['ratings_given']}\n"
        
        # Детали по типам (если есть)
        if rep.get('by_type'):
            text += f"\n📋 По типам:\n"
            for rtype, values in rep['by_type'].items():
                avg = sum(values) / len(values)
                type_name = rtype if rtype else "general"
                text += f"  • {type_name}: {len(values)} шт., средняя {avg:.1f}\n"
        
        return text
    
    def format_reviews_text(self, address: str, limit: int = 5) -> str:
        """
        Форматируем последние отзывы пользователя (полученные и отправленные)
        
        Args:
            address: адрес пользователя (в любом формате)
            limit: количество отзывов для показа (по умолчанию 5)
        
        Returns:
            Отформатированный текст с отзывами
        """
        # Находим адрес в базе
        found_address = self.find_user_by_address(address)
        
        if not found_address:
            return f"📋 ОТЗЫВЫ ПОЛЬЗОВАТЕЛЯ\n\nАдрес: {address[:10]}...{address[-6:]}\n\n⚠️ Пользователь не найден"
        
        # Получаем профиль (если есть)
        profile = self.db.get_profile_by_address(found_address)
        
        # Получаем последние отзывы
        received_ratings = self.db.get_recent_ratings(found_address, as_sender=False, limit=limit)
        given_ratings = self.db.get_recent_ratings(found_address, as_sender=True, limit=limit)
        
        text = "📋 ОТЗЫВЫ ПОЛЬЗОВАТЕЛЯ\n\n"
        
        # Показываем имя пользователя
        if profile:
            text += f"👤 <b>{profile['nickname']}</b>\n"
        else:
            text += f"Адрес: <code>{address[:10]}...{address[-6:]}</code>\n"
        
        text += "\n"
        
        # ========== ПОЛУЧЕННЫЕ ОТЗЫВЫ ==========
        text += f"📥 <b>Полученные отзывы</b> (последние {limit}):\n\n"
        
        if received_ratings:
            for i, rating in enumerate(received_ratings, 1):
                # Получаем профиль отправителя (если есть)
                sender_profile = self.db.get_profile_by_address(rating['sender'])
                sender_name = sender_profile['nickname'] if sender_profile else f"{rating['sender'][:8]}..."
                
                # Форматируем дату
                from datetime import datetime
                date_str = datetime.fromtimestamp(rating['timestamp']).strftime("%d.%m.%Y")
                
                text += f"{i}. ⭐️ <b>{rating['rating']}/5</b> от {sender_name}\n"
                text += f"   📅 {date_str}"
                
                if rating.get('type'):
                    text += f" • Тип: {rating['type']}"
                
                if rating.get('comment'):
                    comment = rating['comment']
                    # Ограничиваем длину комментария
                    if len(comment) > 100:
                        comment = comment[:100] + "..."
                    text += f"\n   💬 {comment}"
                
                if rating.get('link'):
                    text += f"\n   🔗 <a href=\"{rating['link']}\">Ссылка</a>"
                
                text += "\n\n"
        else:
            text += "   Отзывов пока нет\n\n"
        
        # ========== ОТПРАВЛЕННЫЕ ОТЗЫВЫ ==========
        text += f"📤 <b>Отправленные отзывы</b> (последние {limit}):\n\n"
        
        if given_ratings:
            for i, rating in enumerate(given_ratings, 1):
                # Получаем профиль получателя (если есть)
                receiver_profile = self.db.get_profile_by_address(rating['receiver'])
                receiver_name = receiver_profile['nickname'] if receiver_profile else f"{rating['receiver'][:8]}..."
                
                # Форматируем дату
                from datetime import datetime
                date_str = datetime.fromtimestamp(rating['timestamp']).strftime("%d.%m.%Y")
                
                text += f"{i}. ⭐️ <b>{rating['rating']}/5</b> для {receiver_name}\n"
                text += f"   📅 {date_str}"
                
                if rating.get('type'):
                    text += f" • Тип: {rating['type']}"
                
                if rating.get('comment'):
                    comment = rating['comment']
                    # Ограничиваем длину комментария
                    if len(comment) > 100:
                        comment = comment[:100] + "..."
                    text += f"\n   💬 {comment}"
                
                if rating.get('link'):
                    text += f"\n   🔗 <a href=\"{rating['link']}\">Ссылка</a>"
                
                text += "\n\n"
        else:
            text += "   Отзывов пока нет\n\n"
        
        return text
    
    def print_report(self):
        """Выводим отчёт о репутации в консоль"""
        print("\n" + "=" * 60)
        print(f"🏆 ТОП-{config.TOP_USERS_COUNT} ПОЛЬЗОВАТЕЛЕЙ ПО РЕПУТАЦИИ")
        print("=" * 60)
        
        top_users = self.get_top_users(config.TOP_USERS_COUNT)
        
        if not top_users:
            print("⚠ Пользователи не найдены")
            return
        
        for i, user in enumerate(top_users, 1):
            print(f"\n#{i}")
            
            # Пытаемся получить профиль
            profile = self.db.get_profile_by_address(user['address'])
            
            if profile:
                print(f"  👤 {profile['nickname']}")
                print(f"  📝 {profile['bio']}")
                print(f"  Адрес:         {user['address'][:10]}...{user['address'][-6:]}")
                
                # Дополнительная информация из профиля
                if profile.get('skills'):
                    skills = ', '.join(profile['skills'])
                    print(f"  💼 Навыки: {skills}")
                
                if profile.get('location'):
                    print(f"  📍 {profile['location']}")
            else:
                print(f"  Адрес:         {user['address'][:10]}...{user['address'][-6:]}")
            
            print(f"  Итоговый балл: {user['final_score']}")
            print(f"  Средняя оценка: {user['avg_rating']}")
            print(f"  Всего оценок:  {user['total_ratings']}")
            print(f"  Выставлено:    {user.get('ratings_given', 0)}")
            
            # Статистика по типам
            if user.get('by_type'):
                print("  По типам:")
                for rtype, values in user['by_type'].items():
                    avg = sum(values) / len(values)
                    print(f"    - {rtype}: {len(values)} шт., средняя {avg:.1f}")
        
        print("\n" + "=" * 60)
    
    def save_to_json(self, filepath: str = None):
        """
        Сохраняем отчёт в JSON файл
        
        Args:
            filepath: путь к файлу (если None, используется из config)
        """
        if filepath is None:
            filepath = config.OUTPUT_JSON_PATH
        
        # Формируем данные для экспорта
        export_data = {
            'generated_at': datetime.now().isoformat(),
            'protocol': 'repOWR',
            'total_users': len(self.reputation_data),
            'top_users': self.get_top_users(config.TOP_USERS_COUNT),
            'all_users': list(self.reputation_data.values())
        }
        
        # Сохраняем в файл
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Отчёт сохранён в файл: {filepath}")
    
    def run(self):
        """Запускаем счётчик репутации"""
        # Рассчитываем репутацию
        self.calculate_reputation()
        
        # Выводим отчёт в зависимости от настроек
        if config.OUTPUT_FORMAT in ['console', 'both']:
            self.print_report()
        
        if config.OUTPUT_FORMAT in ['json', 'both']:
            self.save_to_json()
        
        print("\n✅ Расчёт репутации завершён!")
    
    def close(self):
        """Закрываем соединение с базой данных"""
        self.db.close()


# Точка входа скрипта
if __name__ == "__main__":
    # Создаём счётчик
    counter = ReputationCounter()
    
    try:
        # Запускаем расчёт
        counter.run()
    except KeyboardInterrupt:
        print("\n\n⚠ Расчёт прерван пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        if config.DEBUG_MODE:
            import traceback
            traceback.print_exc()
    finally:
        # Закрываем соединение с БД
        counter.close()
        print("\n👋 Счётчик остановлен")