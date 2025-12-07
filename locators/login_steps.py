import re

from config.urls import LOGIN_URL
from utils.helpers import check_login_request
from config.urls import urls
from utils.credentials import DATA

def login(page, login, password, requests_log):
    page.goto(LOGIN_URL, wait_until="load")
    page.wait_for_timeout(2000)

    page.get_by_role("textbox", name="Пароль").click()
    page.get_by_role("textbox", name="Пароль").fill(password)
    page.get_by_role("textbox", name="Логин").dblclick()
    page.get_by_role("textbox", name="Логин").fill(login)
    page.get_by_role("button", name="Вход").click()
    page.wait_for_timeout(3000)

    check_login_request(requests_log, urls["token"])
    # check_login_request(requests_log, urls["user"])



#создание тикета
def fill_reason_form(page):
    """Заполняем форму тикета без отправки"""
    page.get_by_role("button", name="Добавить тикет").click()
    page.get_by_role("combobox", name="Выбрать проект").click()
    page.get_by_role("combobox", name="Выбрать топик").click()
    page.get_by_role("textbox", name="Тема *").fill("test")
    page.locator("label").filter(has_text="Все").nth(1).click()
    page.get_by_role("button", name="Тип сети Все 2G 3G 4G 5G").click()
    page.get_by_role("combobox", name="Заявка принята *").click()
    page.get_by_role("option", name="КЦ").locator("data").click()
    page.get_by_role("textbox", name="Date and time of detection").fill(f"{DATA[0]['time_for_reason']}")
    page.get_by_role("textbox", name="Описание *").fill("test")
    page.get_by_role("combobox", name="Watchers/ Наблюдатели").click()



