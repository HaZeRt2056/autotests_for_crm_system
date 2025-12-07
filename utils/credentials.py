import os
from dotenv import load_dotenv
import datetime
import calendar
import locale

load_dotenv()  # загружает переменные из .env

CREDENTIALS = [
    {"login": os.getenv("LOGIN"), "password": os.getenv("PASSWORD")}
]

FAKELOGIN = [
    {"fakeloglogin": os.getenv("FAKELOGIN"), "fakelogpassword": os.getenv("FAKEPASSWORD")}
]

FAKEPASS = [
    {"fakepassLogin": os.getenv("FAKEPASSLOGIN"), "fakepasspassword": os.getenv("FAKEPASSPASSWORD")}
]

NUMBER_LIST = os.getenv("NUMBER_LIST").split(",")
NUMBER_FAKE = [os.getenv("NUMBER_FAKE")]


# DATA = [
#     {
#         "start_choose": "среда, 1 октября 2025 г",
#         "end_choose": "воскресенье, 2 ноября", #тариф
#         "time_for_reason": "2025-10-30T11:44", #причина обращения
#         "start_detailing": "среда, 1 октября", #детализация
#         "end_detailing": "вторник, 7 октября", #детализация
#     }
# ]




# Чтобы день недели был по-русски:
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

def update_data_dates():
    today = datetime.date.today()

    # Определяем — последний ли это день месяца
    last_day_current = calendar.monthrange(today.year, today.month)[1]
    if today.day == last_day_current:
        #если сегодня последнее число месяца → берем след. месяц
        year = today.year + (1 if today.month == 12 else 0)
        month = 1 if today.month == 12 else today.month + 1
    else:
        # иначе остаёмся в текущем месяце
        year = today.year
        month = today.month

    # вычисляем последнее число нужного месяца
    last_day = calendar.monthrange(year, month)[1]
    date_obj = datetime.date(year, month, last_day)

    # форматы
    date_full = date_obj.strftime("%A, %-d %B %Y г")  # среда, 31 октября 2025 г
    date_short = date_obj.strftime("%A, %-d %B")       # среда, 31 октября
    iso_datetime = datetime.datetime.combine(date_obj, datetime.time(11, 44)).isoformat(timespec="minutes")
    # формируем нужную структуру
    return [
        {
            "start_choose": date_full,
            "end_choose": date_short, #тариф
            "time_for_reason": iso_datetime, #причина обращения
            "start_detailing": date_short, #детализация
            "end_detailing": date_short, #детализация
        }
    ]


# Пример использования:
DATA = update_data_dates()
print("Data ======", DATA)
