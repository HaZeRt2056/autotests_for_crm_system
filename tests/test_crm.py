# playwright codegen demo.playwright.dev/todomvc - запуск окна для просмотра
# PYTHONPATH=. pytest tests/ --alluredir=allure-results - запуск автотестов
# allure serve allure-results - просмотр отчета
# pkill -f ngrok - отключение всех серверов ngrok
# ./run_tests.sh - запуск автотестов
# ngrok config add-authtoken 34jmAQSjoxAnFTuUBey2Hs8YozT_595Cn27hnSw8YFuyvbTNB

import pytest
import allure
import pytest_check as check
from playwright.sync_api import Page
from utils.api_checker import check_api_response, compare_json_fields_from_urls
from utils.credentials import *
from config.urls import urls, LOGIN_URL
from tests.check_blocks import run_crm_checks

subscriber_ids_by_number = {}

def mask_creds(c):
    return f"login={c['login']}, password=***"

# В параметризацию прокидываем id, а не сами данные для отображения
CREDS_PARAMS = [ pytest.param(c['login'], id=f"user_{c['login']}") for c in CREDENTIALS ]

NUMBERS_PARAMS = [
    pytest.param(n, id=f"num_{n}") for n in NUMBER_LIST
]


@pytest.mark.parametrize("creds_login", CREDS_PARAMS)
@pytest.mark.parametrize("number", NUMBERS_PARAMS)
@allure.feature("CRM Functional Checks")
def test_crm_flow(creds_login, number, browser_context_args, page: Page):
    creds = {c['login']: c for c in CREDENTIALS}[creds_login]

    # показываем в Allure только замаскированное значение
    allure.dynamic.parameter("user", creds_login)
    allure.dynamic.parameter("creds", mask_creds({'login': creds_login, 'password': creds['password']}))
    requests_log = []
    page.on("request", lambda req: requests_log.append(req))

    with allure.step("Негативный кейс: неправильный логин"):
        requests_log.clear()
        try:
            page.goto(LOGIN_URL, wait_until="load")
            page.get_by_role("textbox", name="Пароль").fill(FAKELOGIN[0]["fakeloglogin"])
            page.get_by_role("textbox", name="Логин").fill(FAKELOGIN[0]["fakelogpassword"])
            page.get_by_role("button", name="Войти").click()
            page.wait_for_timeout(2000)

            auth_requests = [r for r in requests_log if "/auth/token" in r.url]
            assert auth_requests, "Запрос на /auth/token не найден"
            resp = auth_requests[-1].response()
            json_data = resp.json()

            check.equal(resp.status, 406, "Статус не 406 при неправильном логине")
            check.equal(json_data.get("detail"),
                        "Внимание. Логин либо Пароль не верный. Введите корректный Логин и пароль")
        except Exception as e:
            allure.attach(str(e), "Ошибка при проверке неправильного логина", allure.attachment_type.TEXT)

    with allure.step("Негативный кейс: неправильный пароль"):
        requests_log.clear()
        try:
            page.goto(LOGIN_URL, wait_until="load")
            page.get_by_role("textbox", name="Пароль").fill(FAKEPASS[0]["fakepasspassword"])
            page.get_by_role("textbox", name="Логин").fill(FAKEPASS[0]["fakepasslogin"])
            page.get_by_role("button", name="Войти").click()
            page.wait_for_timeout(2000)

            auth_requests = [r for r in requests_log if "/auth/token" in r.url]
            assert auth_requests, "Запрос на /auth/token не найден"
            resp = auth_requests[-1].response()
            json_data = resp.json()

            check.equal(resp.status, 406, "Статус не 406 при неправильном пароле")
            check.equal(json_data.get("detail"),
                        "Внимание. Логин либо Пароль не верный. Введите корректный Логин и пароль")
        except Exception as e:
            allure.attach(str(e), "Ошибка при проверке неправильного пароля", allure.attachment_type.TEXT)

    with allure.step("Позитивный кейс: успешная авторизация"):
        requests_log.clear()
        page.goto(LOGIN_URL, wait_until="load")
        page.get_by_role("textbox", name="Пароль").fill(creds["password"])
        page.get_by_role("textbox", name="Логин").fill(creds["login"])
        page.get_by_role("button", name="Войти").click()
        page.wait_for_timeout(3000)

    with allure.step("Негативный кейс: неправильный номер"):
        try:
            page.get_by_role("banner").get_by_role("button").first.click()
            page.get_by_role("button", name="Обслуживание").click()
            page.get_by_role("link", name="Окно оператора КЦ").click()
            page.get_by_role("textbox", name="__ ___ __ __").click()
            page.get_by_role("textbox", name="__ ___ __ __").fill(NUMBER_FAKE[0])
            page.get_by_test_id("search_number_button").click()
            page.wait_for_timeout(2000)
            fake_auth_requests = [r for r in requests_log if "/searchBase" in r.url]
            assert fake_auth_requests, "Запрос на /searchBase не найден после ввода фейкового номера"

            resp = fake_auth_requests[-1].response()
            json_data = resp.json()


            assert json_data.get("searchResults") == [], "searchResults должен быть пустым при некорректном номере"


            list_info = json_data.get("listInfo", {})
            assert list_info.get("count") == 0, "listInfo.count должен быть 0 при некорректном номере"


            for r in fake_auth_requests:
                requests_log.remove(r)

        except Exception as e:
            allure.attach(str(e), "Ошибка при проверке неправильного номера", allure.attachment_type.TEXT)
            raise

    current_subscriber_id = None
    current_customer_id = None

    def extract_and_set_subscriber_data(response):
        nonlocal current_subscriber_id, current_customer_id
        try:
            json_data = response.json()
            results = json_data.get("searchResults", [])
            if results:
                current_subscriber_id = results[0].get("subscriberId")
                current_customer_id = results[0].get("customerId")
                print("1", current_subscriber_id, current_customer_id)
        except Exception:
            pass

    page.on("response", lambda r: "searchBase" in r.url and extract_and_set_subscriber_data(r))
    print("3", current_subscriber_id, current_customer_id)
    with allure.step("Search base"):
        check_api_response(
            page,
            requests_log,
            urls["search"],
            f"Поиск (номер: {number})",
            click_locator=lambda : (
                page.get_by_role("textbox", name="__ ___ __ __").click(),
                page.get_by_role("textbox", name="__ ___ __ __").press("ControlOrMeta+a"),
                page.get_by_role("textbox", name="__ ___ __ __").fill(number),
                page.get_by_test_id("search_number_button").click()
            ),
            json_array_path="searchResults"
        )

        assert current_subscriber_id and current_customer_id, f"❌ subscriberId или customerId не получены для номера {number}"

    subscriber_ids_by_number[number] = current_subscriber_id
    print("2", current_subscriber_id, current_customer_id)

    run_crm_checks(page, requests_log, number, current_subscriber_id, current_customer_id)