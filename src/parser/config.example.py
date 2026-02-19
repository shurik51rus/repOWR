"""
Пример конфигурации для парсера repOWR.
Скопируйте этот файл как config.py и заполните свои значения.
"""

# ===== TON API =====
TON_API_ENDPOINT = "https://tonapi.io/v2"
TON_API_KEY = ""  # Ваш API ключ от tonapi.io

# ===== Jetton =====
JETTON_MASTER_ADDRESS = "EQABi71g1y3BFnxA_qcY-giSbtRx9gArA9xXpfeZyTqP_Jwh"

# ===== Database =====
DATABASE_PATH = "reputation.db"

# ===== Parser =====
TRANSACTIONS_LIMIT = 100
API_TIMEOUT = 30
DEBUG_MODE = False

# ===== Reputation =====
TOP_USERS_COUNT = 10
OUTPUT_FORMAT = "both"  # "console", "json", "both"
OUTPUT_JSON_PATH = "reputation_report.json"
