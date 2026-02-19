"""
Парсер транзакций TON блокчейна для протокола repOWR.
Получает транзакции Jetton-токена, валидирует их и сохраняет в базу данных.
"""

import requests
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Импортируем наши модули
from database import Database
from validator import RepOWRValidator
import config


class TonParser:
    """Класс для парсинга транзакций из TON блокчейна"""
    
    def __init__(self):
        """Инициализация парсера"""
        self.db = Database(config.DATABASE_PATH)
        self.validator = RepOWRValidator()  # ОБНОВЛЕНО: используем новый валидатор
        self.api_endpoint = config.TON_API_ENDPOINT
        self.api_key = config.TON_API_KEY
        self.jetton_master = config.JETTON_MASTER_ADDRESS
        
        # Подключаемся к базе данных
        self.db.connect()
        
        # Создаём таблицы если их ещё нет
        self.db.create_tables()
    
    def normalize_address(self, address: str) -> str:
        """
        Нормализует адрес к единому формату
        
        Args:
            address: адрес в любом формате
        
        Returns:
            нормализованный адрес
        """
        if not address:
            return ""
        
        address = address.strip()
        
        # Если это raw формат (0:...), извлекаем hex часть
        if address.startswith("0:") or address.startswith("-1:"):
            return address.split(":", 1)[1].lower()
        
        # Если это user-friendly (EQ.../UQ...), убираем префикс
        if address.startswith("EQ") or address.startswith("UQ"):
            return address[2:].lower()
        
        return address.lower()
    
    def convert_to_raw_address(self, address: str) -> str:
        """
        Конвертирует адрес в raw формат (0:hex или -1:hex)
        Это нужно для единообразного хранения в базе данных
        
        Args:
            address: адрес в любом формате (UQ/EQ/raw)
        
        Returns:
            адрес в raw формате (0:abc123...)
        """
        if not address:
            return ""
        
        address = address.strip()
        
        # Если уже в raw формате - возвращаем как есть
        if address.startswith("0:") or address.startswith("-1:"):
            return address
        
        # Для UQ/EQ адресов - декодируем в raw
        if address.startswith("UQ") or address.startswith("EQ"):
            try:
                import base64
                
                # Убираем префикс UQ/EQ
                b64_part = address[2:]
                
                # Заменяем URL-safe символы на стандартные base64
                b64_part = b64_part.replace('-', '+').replace('_', '/')
                
                # Добавляем padding если нужно
                padding = 4 - (len(b64_part) % 4)
                if padding != 4:
                    b64_part += '=' * padding
                
                # Декодируем
                decoded = base64.b64decode(b64_part)
                
                # Структура: tag(1 байт) + hash(32 байта) + crc(2 байта) = 35 байт
                if len(decoded) >= 33:
                    # Извлекаем workchain из первого байта
                    workchain = decoded[0]
                    if workchain > 127:
                        workchain = workchain - 256
                    
                    # Извлекаем hash (32 байта после workchain)
                    hash_bytes = decoded[1:33]
                    hash_hex = hash_bytes.hex()
                    
                    # Формируем raw адрес
                    raw_address = f"{workchain}:{hash_hex}"
                    return raw_address
            except Exception as e:
                if config.DEBUG_MODE:
                    print(f"⚠️ Ошибка конвертации адреса {address}: {e}")
                return address
        
        # Если формат неизвестен - возвращаем как есть
        return address
    
    def get_token_holders(self, limit: int = 1000) -> List[str]:
        """
        Получаем список держателей (holders) Jetton токена
        
        Args:
            limit: максимальное количество holders
        
        Returns:
            Список адресов держателей токена
        """
        url = f"{self.api_endpoint}/jettons/{self.jetton_master}/holders"
        
        params = {"limit": limit, "offset": 0}
        
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        print(f"📊 Получаем список держателей токена...")
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=config.API_TIMEOUT)
            
            if response.status_code != 200:
                print(f"⚠ Ошибка {response.status_code}: {response.text[:200]}")
                return []
            
            data = response.json()
            holders = data.get("addresses", [])
            
            if not holders:
                print(f"⚠ Holders не найдены в ответе")
                return []
            
            # Конвертируем в список адресов
            holder_addresses = []
            for holder in holders:
                if isinstance(holder, dict):
                    address = holder.get("address", "")
                    if address:
                        holder_addresses.append(address)
                elif isinstance(holder, str):
                    holder_addresses.append(holder)
            
            print(f"✓ Найдено {len(holder_addresses)} держателей токена")
            
            return holder_addresses
            
        except requests.exceptions.RequestException as e:
            print(f"⚠ Ошибка при запросе holders: {e}")
            return []
    
    def get_jetton_transfers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получаем список переводов Jetton токена через Tonapi
        
        Args:
            limit: максимальное количество событий на один адрес
        
        Returns:
            Список словарей с данными трансферов
        """
        
        # Шаг 1: Получаем список holders токена
        holder_addresses = self.get_token_holders(limit=1000)
        
        if not holder_addresses:
            print("\n⚠ Не удалось получить список holders")
            return []
        
        # Ограничиваем количество адресов для парсинга
        max_addresses = 100
        if len(holder_addresses) > max_addresses:
            print(f"⚠ Holders слишком много ({len(holder_addresses)})")
            print(f"   Будем парсить только топ-{max_addresses}")
            holder_addresses = holder_addresses[:max_addresses]
        
        # Шаг 2: Парсим события каждого holder'а
        all_transfers = []
        
        print(f"\n🔍 Парсим события {len(holder_addresses)} holders...")
        
        for i, address in enumerate(holder_addresses, 1):
            # Прогресс-бар
            if i % 10 == 0 or i == len(holder_addresses):
                print(f"   [{i}/{len(holder_addresses)}] {i * 100 // len(holder_addresses)}%")
            
            # Получаем события адреса
            url = f"{self.api_endpoint}/accounts/{address}/events"
            
            params = {"limit": limit, "subject_only": "false"}
            
            headers = {"Accept": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            try:
                response = requests.get(url, params=params, headers=headers, timeout=config.API_TIMEOUT)
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                events = data.get("events", [])
                
                # Фильтруем JettonTransfer для нашего токена
                found = 0
                for event in events:
                    actions = event.get("actions", [])
                    for action in actions:
                        if action.get("type") == "JettonTransfer":
                            jetton_transfer = action.get("JettonTransfer", {})
                            
                            # Проверяем, что это наш токен
                            jetton_info = jetton_transfer.get("jetton", {})
                            jetton_address = jetton_info.get("address", "")
                            
                            if self.normalize_address(jetton_address) == self.normalize_address(self.jetton_master):
                                # ВАЖНО: Добавляем timestamp и transaction_hash из события
                                jetton_transfer["timestamp"] = event.get("timestamp", 0)
                                jetton_transfer["event_id"] = event.get("event_id", "")
                                # transaction_hash может быть в самом трансфере или в событии
                                if not jetton_transfer.get("transaction_hash"):
                                    jetton_transfer["transaction_hash"] = event.get("event_id", "")
                                
                                all_transfers.append(jetton_transfer)
                                found += 1
                
                if config.DEBUG_MODE and found > 0:
                    print(f"   Найдено трансферов: {found}")
                
                # Небольшая задержка чтобы не перегрузить API
                time.sleep(0.1)
                
            except Exception as e:
                if config.DEBUG_MODE:
                    print(f"⚠ Ошибка при парсинге адреса {address[:8]}...: {e}")
                continue
        
        # Убираем дубликаты по transaction_hash или event_id
        unique_transfers = {}
        for transfer in all_transfers:
            # Используем transaction_hash, если есть, иначе event_id
            unique_id = transfer.get("transaction_hash") or transfer.get("event_id", "")
            if unique_id and unique_id not in unique_transfers:
                unique_transfers[unique_id] = transfer
        
        if config.DEBUG_MODE:
            print(f"\n✓ Всего трансферов найдено: {len(all_transfers)}")
            print(f"✓ Уникальных трансферов: {len(unique_transfers)}")
            if len(all_transfers) > len(unique_transfers):
                print(f"⚠ Удалено дубликатов: {len(all_transfers) - len(unique_transfers)}")
        else:
            print(f"\n✓ Всего трансферов найдено: {len(all_transfers)}")
            print(f"✓ Уникальных трансферов: {len(unique_transfers)}")
        
        return list(unique_transfers.values())
    
    def parse_transaction(self, transfer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Парсим один Jetton трансфер и извлекаем нужные данные
        
        Args:
            transfer: данные трансфера от Tonapi
        
        Returns:
            Словарь с распарсенными данными или None
        """
        try:
            # Получаем данные трансфера
            timestamp = transfer.get("timestamp", 0)
            
            sender_obj = transfer.get("sender", {})
            recipient_obj = transfer.get("recipient", {})
            
            sender = sender_obj.get("address", "") if isinstance(sender_obj, dict) else ""
            receiver = recipient_obj.get("address", "") if isinstance(recipient_obj, dict) else ""
            
            # Получаем сумму
            amount_str = transfer.get("amount", "0")
            decimals = transfer.get("jetton", {}).get("decimals", 9)
            amount = float(amount_str) / (10 ** decimals) if amount_str else 0
            
            # Получаем comment (там наше сообщение repOWR)
            comment = transfer.get("comment", "")
            
            # Получаем transaction_hash или event_id
            tx_hash = transfer.get("transaction_hash") or transfer.get("event_id", "")
            
            # Проверяем, есть ли comment
            if not comment:
                return None
            
            # Формируем результат
            result = {
                "tx_hash": tx_hash if tx_hash else f"transfer_{timestamp}_{sender[:8]}",
                "sender": sender,
                "receiver": receiver,
                "amount": amount,
                "timestamp": timestamp,
                "memo": comment
            }
            
            return result
            
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"⚠ Ошибка парсинга трансфера: {e}")
            return None
    
    def process_transactions(self, transactions: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Обрабатываем список транзакций: валидируем и сохраняем в БД
        
        Args:
            transactions: список сырых транзакций от API
        
        Returns:
            Словарь со статистикой обработки
        """
        stats = {
            "total": 0,
            "parsed": 0,
            "valid": 0,
            "invalid": 0,
            "saved": 0,
            "duplicates": 0,
            "profiles": 0,  # НОВОЕ: счётчик профилей
            "ratings": 0     # НОВОЕ: счётчик рейтингов
        }
        
        for tx in transactions:
            stats["total"] += 1
            
            # Парсим транзакцию
            parsed_tx = self.parse_transaction(tx)
            
            if not parsed_tx:
                if config.DEBUG_MODE:
                    print(f"⚠ Не удалось распарсить транзакцию #{stats['total']}")
                continue
            
            stats["parsed"] += 1
            
            if config.DEBUG_MODE:
                print(f"\n--- Транзакция #{stats['parsed']} ---")
                print(f"От: {parsed_tx['sender'][:20]}...")
                print(f"Кому: {parsed_tx['receiver'][:20]}...")
                print(f"Сумма: {parsed_tx['amount']}")
                print(f"Комментарий: {parsed_tx['memo'][:50]}...")
            
            # ОБНОВЛЕНО: Валидируем сообщение (упрощённый или JSON формат)
            is_valid, data, error = self.validator.validate(parsed_tx["memo"])
            
            parsed_tx["is_valid"] = is_valid
            
            if is_valid:
                stats["valid"] += 1
                if config.DEBUG_MODE:
                    print(f"✓ Валидно: {data.get('protocol')} - рейтинг {data.get('rating', 'N/A')}")
            else:
                stats["invalid"] += 1
                if config.DEBUG_MODE:
                    print(f"✗ Невалидно: {error}")
            
            # Сохраняем транзакцию в БД
            tx_id = self.db.insert_transaction(parsed_tx)
            
            if tx_id is None:
                # Транзакция уже существует
                stats["duplicates"] += 1
                continue
            
            stats["saved"] += 1
            
            # ОБНОВЛЕНО: Если сообщение валидно, сохраняем данные
            if is_valid:
                data["tx_id"] = tx_id
                
                # Проверяем тип сообщения
                if data.get("type") == "identity":
                    # Это профиль пользователя
                    # ВАЖНО: Конвертируем адрес в raw формат для единообразного хранения
                    raw_address = self.convert_to_raw_address(parsed_tx["sender"])
                    data["address"] = raw_address
                    self.db.insert_profile(data)
                    stats["profiles"] += 1
                    
                    if config.DEBUG_MODE:
                        print(f"✓ Сохранён профиль: {data.get('nickname')} ({raw_address[:20]}...)")
                else:
                    # Это рейтинг
                    self.db.insert_rating(data)
                    stats["ratings"] += 1
        
        return stats
    
    def run(self):
        """Запускаем парсер"""
        print("=" * 60)
        print("🚀 Запуск парсера трансферов TON (протокол repOWR)")
        print(f"📍 Jetton Master: {self.jetton_master}")
        print("=" * 60)
        
        # Получаем трансферы
        print("\n📥 Получаем трансферы из блокчейна...")
        
        transfers = self.get_jetton_transfers(limit=config.TRANSACTIONS_LIMIT)
        
        if not transfers:
            print("⚠ Трансферы не найдены")
            return
        
        print(f"✓ Получено {len(transfers)} трансферов")
        
        # Обрабатываем трансферы
        print("\n⚙️ Обработка трансферов...")
        stats = self.process_transactions(transfers)
        
        # Выводим статистику
        print("\n" + "=" * 60)
        print("📊 СТАТИСТИКА ОБРАБОТКИ")
        print("=" * 60)
        print(f"Всего получено:        {stats['total']}")
        print(f"Успешно распарсено:    {stats['parsed']}")
        print(f"Валидных сообщений:    {stats['valid']}")
        print(f"Невалидных сообщений:  {stats['invalid']}")
        print(f"Сохранено в БД:        {stats['saved']}")
        print(f"Дубликатов (пропущено): {stats['duplicates']}")
        print(f"  - Рейтингов:         {stats['ratings']}")
        print(f"  - Профилей:          {stats['profiles']}")
        
        # Выводим общую статистику БД
        db_stats = self.db.get_stats()
        print("\n" + "=" * 60)
        print("💾 СТАТИСТИКА БАЗЫ ДАННЫХ")
        print("=" * 60)
        print(f"Всего транзакций:      {db_stats['total_transactions']}")
        print(f"Валидных транзакций:   {db_stats['valid_transactions']}")
        print(f"Всего рейтингов:       {db_stats['total_ratings']}")
        print(f"Всего профилей:        {db_stats['total_profiles']}")
        print("=" * 60)
        
        print("\n✅ Парсинг завершён!")
    
    def close(self):
        """Закрываем соединение с базой данных"""
        self.db.close()


# Точка входа скрипта
if __name__ == "__main__":
    # Создаём парсер
    parser = TonParser()
    
    try:
        # Запускаем парсинг
        parser.run()
    except KeyboardInterrupt:
        print("\n\n⚠ Парсинг прерван пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        if config.DEBUG_MODE:
            import traceback
            traceback.print_exc()
    finally:
        # Закрываем соединение с БД
        parser.close()
        print("\n👋 Парсер остановлен")