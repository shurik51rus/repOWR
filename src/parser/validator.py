"""
Модуль для валидации сообщений протокола repOWR.
Поддерживает два формата:
1. Упрощённый: repOWR:5:Комментарий:
2. JSON: {"protocol":"repOWR","rating":5,...}
"""

import json
import re
from typing import Dict, Any, Tuple, Optional


class RepOWRValidator:
    """Класс для валидации сообщений протокола repOWR"""
    
    # Допустимые значения для полей
    ALLOWED_TYPES = ["deal", "service", "product", "general"]
    MIN_RATING = 1
    MAX_RATING = 5
    MAX_COMMENT_LENGTH = 500
    
    # Поддерживаемые форматы
    PROTOCOL_NAME = "repOWR"
    
    def __init__(self):
        """Инициализация валидатора"""
        pass
    
    def validate(self, memo: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Проверяем сообщение на корректность.
        Автоматически определяет формат (упрощённый или JSON).
        
        Args:
            memo: строка с сообщением из поля memo транзакции
        
        Returns:
            Кортеж из трёх элементов:
            - bool: True если сообщение валидно, False если нет
            - dict: распарсенные данные (или пустой словарь при ошибке)
            - str: описание ошибки (пустая строка если всё ОК)
        """
        
        # Определяем формат сообщения
        if memo.startswith(f"{self.PROTOCOL_NAME}:"):
            # Упрощённый формат
            return self._validate_simple_format(memo)
        elif memo.strip().startswith("{"):
            # JSON формат
            return self._validate_json_format(memo)
        else:
            # Неизвестный формат
            return False, {}, "Сообщение не соответствует протоколу repOWR"
    
    def _validate_simple_format(self, memo: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Валидация упрощённого формата: repOWR:RATING:COMMENT:
        
        Args:
            memo: строка сообщения
        
        Returns:
            Кортеж (валидность, данные, ошибка)
        """
        
        # Проверка 1: Должен начинаться с "repOWR:"
        if not memo.startswith(f"{self.PROTOCOL_NAME}:"):
            return False, {}, f"Сообщение должно начинаться с '{self.PROTOCOL_NAME}:'"
        
        # Проверка 2: Должен заканчиваться двоеточием
        if not memo.endswith(":"):
            return False, {}, "Сообщение должно заканчиваться двоеточием ':'"
        
        # Убираем префикс "repOWR:" и последнее двоеточие
        content = memo[len(self.PROTOCOL_NAME) + 1:-1]
        
        # Разделяем на части: RATING:COMMENT (где COMMENT опциональный)
        parts = content.split(":", 1)
        
        # Проверка 3: Должен быть хотя бы рейтинг
        if len(parts) == 0 or not parts[0]:
            return False, {}, "Отсутствует рейтинг"
        
        # Проверка 4: Рейтинг должен быть числом
        try:
            rating = int(parts[0])
        except ValueError:
            return False, {}, f"Рейтинг должен быть числом, получено: '{parts[0]}'"
        
        # Проверка 5: Рейтинг в диапазоне 1-5
        if not (self.MIN_RATING <= rating <= self.MAX_RATING):
            return False, {}, f"Рейтинг должен быть от {self.MIN_RATING} до {self.MAX_RATING}, получено: {rating}"
        
        # Извлекаем комментарий (если есть)
        comment = parts[1] if len(parts) > 1 else ""
        
        # Проверка 6: Длина комментария
        if len(comment) > self.MAX_COMMENT_LENGTH:
            return False, {}, f"Комментарий слишком длинный: {len(comment)} символов (максимум {self.MAX_COMMENT_LENGTH})"
        
        # Формируем данные в стандартном формате
        data = {
            "protocol": self.PROTOCOL_NAME,
            "rating": rating,
            "format": "simple"  # Помечаем как упрощённый формат
        }
        
        # Добавляем комментарий, если он не пустой
        if comment:
            data["comment"] = comment
        
        return True, data, ""
    
    def _validate_json_format(self, memo: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Валидация JSON формата
        
        Args:
            memo: строка с JSON-сообщением
        
        Returns:
            Кортеж (валидность, данные, ошибка)
        """
        
        # Шаг 1: Проверяем, что это валидный JSON
        try:
            data = json.loads(memo)
        except json.JSONDecodeError as e:
            return False, {}, f"Некорректный JSON: {str(e)}"
        
        # Шаг 2: Проверяем обязательное поле "protocol"
        if "protocol" not in data:
            return False, {}, "Отсутствует обязательное поле 'protocol'"
        
        if data["protocol"] != self.PROTOCOL_NAME:
            return False, {}, f"Неподдерживаемая версия протокола: {data['protocol']}"
        
        # Шаг 3: Определяем тип сообщения
        message_type = data.get("type")
        
        # Если это профиль (identity), валидируем отдельно
        if message_type == "identity":
            return self._validate_identity(data)
        
        # Для оценок проверяем обязательное поле "rating"
        if "rating" not in data:
            return False, {}, "Отсутствует обязательное поле 'rating'"
        
        # Проверяем, что rating - это число
        if not isinstance(data["rating"], int):
            return False, {}, f"Поле 'rating' должно быть целым числом, получено: {type(data['rating'])}"
        
        # Проверяем диапазон rating
        if not (self.MIN_RATING <= data["rating"] <= self.MAX_RATING):
            return False, {}, f"Поле 'rating' должно быть от {self.MIN_RATING} до {self.MAX_RATING}, получено: {data['rating']}"
        
        # Шаг 4: Проверяем опциональные поля
        
        # Проверяем type (если указан)
        if message_type and message_type not in self.ALLOWED_TYPES:
            return False, {}, f"Недопустимое значение поля 'type': {message_type}. Допустимые: {', '.join(self.ALLOWED_TYPES)}"
        
        # Проверяем длину comment (если указан)
        if "comment" in data:
            if not isinstance(data["comment"], str):
                return False, {}, "Поле 'comment' должно быть строкой"
            if len(data["comment"]) > self.MAX_COMMENT_LENGTH:
                return False, {}, f"Поле 'comment' слишком длинное: {len(data['comment'])} символов (максимум {self.MAX_COMMENT_LENGTH})"
        
        # Проверяем link (если указан)
        if "link" in data:
            if not isinstance(data["link"], str):
                return False, {}, "Поле 'link' должно быть строкой"
            if not self._is_valid_url(data["link"]):
                return False, {}, f"Некорректный URL в поле 'link': {data['link']}"
        
        # Проверяем ref (если указан)
        if "ref" in data:
            if not isinstance(data["ref"], str):
                return False, {}, "Поле 'ref' должно быть строкой"
        
        # Помечаем как JSON формат
        data["format"] = "json"
        
        # Все проверки пройдены успешно
        return True, data, ""
    
    def _validate_identity(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """
        Валидация профиля пользователя (identity)
        
        Args:
            data: словарь с данными профиля
        
        Returns:
            Кортеж (валидность, данные, ошибка)
        """
        
        # Проверка обязательных полей для профиля
        if "nickname" not in data:
            return False, {}, "Профиль должен содержать поле 'nickname'"
        
        if "bio" not in data:
            return False, {}, "Профиль должен содержать поле 'bio'"
        
        # Проверяем типы полей
        if not isinstance(data["nickname"], str):
            return False, {}, "Поле 'nickname' должно быть строкой"
        
        if not isinstance(data["bio"], str):
            return False, {}, "Поле 'bio' должно быть строкой"
        
        # Проверяем длину bio
        if len(data["bio"]) > 200:
            return False, {}, f"Поле 'bio' слишком длинное: {len(data['bio'])} символов (максимум 200)"
        
        # Проверяем опциональные поля
        if "skills" in data:
            if not isinstance(data["skills"], list):
                return False, {}, "Поле 'skills' должно быть массивом"
            for skill in data["skills"]:
                if not isinstance(skill, str):
                    return False, {}, "Элементы 'skills' должны быть строками"
        
        if "languages" in data:
            if not isinstance(data["languages"], list):
                return False, {}, "Поле 'languages' должно быть массивом"
            for lang in data["languages"]:
                if not isinstance(lang, str):
                    return False, {}, "Элементы 'languages' должны быть строками"
        
        if "birth_year" in data:
            if not isinstance(data["birth_year"], int):
                return False, {}, "Поле 'birth_year' должно быть числом"
            if data["birth_year"] < 1900 or data["birth_year"] > 2020:
                return False, {}, f"Некорректный год рождения: {data['birth_year']}"
        
        if "links" in data:
            if not isinstance(data["links"], dict):
                return False, {}, "Поле 'links' должно быть объектом"
        
        # Помечаем как JSON формат профиля
        data["format"] = "json"
        
        return True, data, ""
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Простая проверка URL на корректность
        
        Args:
            url: строка с URL
        
        Returns:
            True если URL выглядит корректно, False если нет
        """
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return url_pattern.match(url) is not None


# Тестирование валидатора
if __name__ == "__main__":
    validator = RepOWRValidator()
    
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ВАЛИДАТОРА repOWR")
    print("=" * 60)
    
    # Тест 1: Упрощённый формат - только рейтинг
    print("\n1. Упрощённый формат (только рейтинг):")
    test1 = "repOWR:5:"
    is_valid, data, error = validator.validate(test1)
    print(f"   Входные данные: {test1}")
    print(f"   Результат: {'✓ Валидно' if is_valid else '✗ Ошибка'}")
    if is_valid:
        print(f"   Данные: {data}")
    else:
        print(f"   Ошибка: {error}")
    
    # Тест 2: Упрощённый формат - с комментарием
    print("\n2. Упрощённый формат (с комментарием):")
    test2 = "repOWR:4:Хорошая работа!:"
    is_valid, data, error = validator.validate(test2)
    print(f"   Входные данные: {test2}")
    print(f"   Результат: {'✓ Валидно' if is_valid else '✗ Ошибка'}")
    if is_valid:
        print(f"   Данные: {data}")
    else:
        print(f"   Ошибка: {error}")
    
    # Тест 3: JSON формат - минимальный
    print("\n3. JSON формат (минимальный):")
    test3 = '{"protocol":"repOWR","rating":5}'
    is_valid, data, error = validator.validate(test3)
    print(f"   Входные данные: {test3}")
    print(f"   Результат: {'✓ Валидно' if is_valid else '✗ Ошибка'}")
    if is_valid:
        print(f"   Данные: {data}")
    else:
        print(f"   Ошибка: {error}")
    
    # Тест 4: JSON формат - полный
    print("\n4. JSON формат (полный):")
    test4 = '{"protocol":"repOWR","rating":5,"type":"deal","comment":"Отлично!","link":"https://t.me/chat","ref":"EQC333"}'
    is_valid, data, error = validator.validate(test4)
    print(f"   Входные данные: {test4}")
    print(f"   Результат: {'✓ Валидно' if is_valid else '✗ Ошибка'}")
    if is_valid:
        print(f"   Данные: {data}")
    else:
        print(f"   Ошибка: {error}")
    
    # Тест 5: Профиль (identity)
    print("\n5. JSON формат (профиль):")
    test5 = '{"protocol":"repOWR","type":"identity","nickname":"CryptoDevPro","bio":"Full-stack разработчик","skills":["python","ton"],"languages":["ru","en"]}'
    is_valid, data, error = validator.validate(test5)
    print(f"   Входные данные: {test5}")
    print(f"   Результат: {'✓ Валидно' if is_valid else '✗ Ошибка'}")
    if is_valid:
        print(f"   Данные: {data}")
    else:
        print(f"   Ошибка: {error}")
    
    # Тест 6: Ошибка - неверный рейтинг
    print("\n6. Ошибка (неверный рейтинг):")
    test6 = "repOWR:10:"
    is_valid, data, error = validator.validate(test6)
    print(f"   Входные данные: {test6}")
    print(f"   Результат: {'✓ Валидно' if is_valid else '✗ Ошибка'}")
    if not is_valid:
        print(f"   Ошибка: {error}")
    
    # Тест 7: Ошибка - нет закрывающего двоеточия
    print("\n7. Ошибка (нет закрывающего двоеточия):")
    test7 = "repOWR:5"
    is_valid, data, error = validator.validate(test7)
    print(f"   Входные данные: {test7}")
    print(f"   Результат: {'✓ Валидно' if is_valid else '✗ Ошибка'}")
    if not is_valid:
        print(f"   Ошибка: {error}")
    
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)
