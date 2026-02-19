# Виджет repOWR — инструкция по встраиванию

## Быстрый старт

Добавьте две строки на ваш сайт:

```html
<script src="https://repowr.tech/widget.js"></script>
<div class="repowr-widget" data-default-address="UQATKnigdlBIuU3FJ57VSh4Aqxel9oLbQ4hBzIZ6YzWkbZys"></div>
```

## Параметры

| Атрибут | Описание |
|---------|----------|
| `data-default-address` | Адрес кошелька для отображения по умолчанию. Если не указан, виджет покажет форму поиска |

## Примеры

### Виджет с поиском (без адреса по умолчанию)
```html
<script src="https://repowr.tech/widget.js"></script>
<div class="repowr-widget"></div>
```

### Виджет с конкретным профилем
```html
<script src="https://repowr.tech/widget.js"></script>
<div class="repowr-widget" data-default-address="EQD...ваш_адрес"></div>
```

### Несколько виджетов на одной странице
```html
<script src="https://repowr.tech/widget.js"></script>

<div class="repowr-widget" data-default-address="EQD...адрес_1"></div>
<div class="repowr-widget" data-default-address="EQD...адрес_2"></div>
```

## Совместимость

Виджет работает на любом сайте, включая WordPress, HTML, React и другие платформы. Скрипт загружается асинхронно и не блокирует рендеринг страницы.
