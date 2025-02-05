# Интеграция с Chat2Desk

## Описание
Этот проект предоставляет API для интеграции с Chat2Desk через вебхуки.

## Установка
1. Клонируйте репозиторий:
   git clone https://github.com/nightsteve/C2D_Test_task.git
2. Установите зависимости
   pip install -r requirements.txt
3. Задайте переменную окружения:
   export CHAT2DESK_TOKEN="ТокенChat2Desk"
4. Запустите сервер:
   python app.py

Использование:

Вебхук для событий: POST /webhook/event

Вебхук для диалогов: POST /webhook/dialog-open

Схема алгоритмов:

1. Получение вебхука → Проверка события → Поиск клиента (с пагинацией) → 
Отправка сообщения с флагом dont_open_dialog → Поиск тега VIP → Присвоение тега

2. Открытие диалога → Проверка тегов клиента → Поиск оператора (с пагинацией) → 
Системное сообщение + назначение оператора ИЛИ комментарий об отсутствии
