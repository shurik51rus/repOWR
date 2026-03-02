# Протокол repOWR

**Децентрализованная система репутации на блокчейне TON**

[🇬🇧 English documentation](README.md) | [Сайт](https://repowr.tech) | [Telegram-бот](https://t.me/RepOracle_bot)

---

## Что такое repOWR?

repOWR — открытый протокол для построения проверяемой репутации на блокчейне TON. Отзывы и профили хранятся в комментариях Jetton-транзакций, что делает их прозрачными, неизменяемыми и принадлежащими пользователям, а не платформам.

## Ключевые особенности

- Репутация привязана к адресу кошелька, а не к нику
- Два формата: упрощённый (`repOWR:5:Отличная работа:`) и JSON для детальных отзывов
- Децентрализованные профили (identity) на блокчейне
- **Social Power Score** — комплексный показатель влияния (0–2000 SP) с 6 рангами
- **Динамические NFT** — карточка репутации обновляется в реальном времени
- Отзывы нельзя удалить, подделать или накрутить
- Открытый API, виджеты для сайтов, Telegram-бот

## Как это работает

1. **Отправьте отзыв** — переведите любое количество SPW токенов получателю с отзывом в комментарии транзакции
2. **Парсер считывает** — система в реальном времени отслеживает все SPW-транзакции и распознаёт формат repOWR
3. **Репутация доступна** — проверьте репутацию любого кошелька через бот, сайт, виджет или API

## Быстрый старт

### Оставить отзыв (упрощённый формат)
```
repOWR:5:Отличный сервис, быстрая доставка:
```

### Оставить отзыв (JSON формат)
```json
{
  "protocol": "repOWR",
  "rating": 5,
  "type": "deal",
  "comment": "Профессионально и надёжно"
}
```

### Создать профиль (упрощённый — для кошелька Telegram)
Отправьте SPW на адрес ОМР `UQCywBj5RIyKYf1SeLMkmt9gL13pMzCaqORZZ3iFeJyoRaqO` с комментарием:
```
repOWR:identity:ВашНик:
```
Подходит для кошелька Telegram (лимит 54 символа). Только никнейм — больше ничего не нужно.

### Создать профиль (полный JSON формат)
Отправьте SPW на адрес ОМР `UQCywBj5RIyKYf1SeLMkmt9gL13pMzCaqORZZ3iFeJyoRaqO` с комментарием:
```json
{
  "protocol": "repOWR",
  "type": "identity",
  "nickname": "ВашНик",
  "bio": "Ваше описание",
  "skills": ["trading", "development"],
  "links": {"telegram": "@yourname"}
}
```

## Токен SPW

| Параметр | Значение |
|----------|----------|
| Блокчейн | TON |
| Стандарт | Jetton (TEP-74) |
| Общая эмиссия | 100,000,000 SPW |
| Jetton Master | `EQABi71g1y3BFnxA_qcY-giSbtRx9gArA9xXpfeZyTqP_Jwh` |
| DEX | [STON.fi](https://app.ston.fi/swap?ft=TON&tt=EQABi71g1y3BFnxA_qcY-giSbtRx9gArA9xXpfeZyTqP_Jwh&chartVisible=false) |

## Структура репозитория

```
repOWR/
├── docs/
│   └── protocol.md           # Полная спецификация протокола
├── src/
│   ├── parser/
│   │   ├── validator.py       # Валидация сообщений (упрощённый + JSON)
│   │   ├── ton_parser.py      # Парсер транзакций TON блокчейна
│   │   ├── reputation_counter.py  # Расчёт репутации
│   │   ├── social_power.py    # Расчёт Social Power Score и рангов
│   │   ├── database.py        # Работа с SQLite (транзакции, рейтинги, профили, балансы)
│   │   └── config.py          # Настройки парсера и API
│   ├── api/
│   │   └── index.php          # REST API (PHP)
│   └── nft/
│       ├── nft_image.php      # Динамическая SVG-карточка NFT
│       └── nft_metadata.php   # Метаданные NFT (стандарт TEP-64)
├── widget/
│   ├── profile-widget.html    # Виджет профиля для встраивания
│   └── embed.md               # Инструкция по встраиванию виджета
├── examples/
│   ├── send-review.md         # Как отправить отзыв
│   └── create-profile.md      # Как создать профиль
├── README.md                  # Документация (English)
├── README.ru.md               # Документация (Русский)
└── LICENSE                    # Лицензия MIT
```

## API

Базовый URL: `https://repowr.tech/api/`

| Эндпоинт | Описание |
|----------|----------|
| `?endpoint=health` | Статус API |
| `?endpoint=reputation&address=...` | Репутация кошелька (включает Social Power и ранг) |
| `?endpoint=reviews&address=...&limit=5` | Отзывы для кошелька (полученные и выданные) |
| `?endpoint=top&limit=10` | Топ пользователей по Social Power |
| `?endpoint=stats` | Общая статистика системы |

## Виджет

Встройте проверку репутации на любой сайт:
```html
<script src="https://repowr.tech/widget.js"></script>
<div class="repowr-widget" data-default-address="UQATKnig..."></div>
```

## Динамические NFT

Каждый пользователь может выпустить NFT-карточку репутации, которая отображает данные в реальном времени: ник, ранг, Social Power, рейтинг, отзывы и баланс SPW.

Карточка обновляется автоматически при изменении данных — не нужно перевыпускать NFT.

Доступно 5 стилей оформления карточки: Cyberpunk, Web3 Cosmos, P2P Exchange, Freelance, Meme.

Метаданные NFT соответствуют стандарту TEP-64 и поддерживаются маркетплейсом Getgems.

```
https://repowr.tech/nft_metadata.php?address=0:abc...&style=1
```

## Ссылки

- **Сайт:** https://repowr.tech
- **Telegram-бот:** https://t.me/RepOracle_bot
- **Telegram сообщество:** https://t.me/repOWR_protocol
- **Документация протокола:** [docs/protocol.md](docs/protocol.md)

## Лицензия

MIT — свободно для использования в любых проектах.
