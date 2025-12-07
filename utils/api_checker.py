# utils/api_checker.py
import pytest_check as check
from playwright.sync_api import Page

def extract_value_by_path(data, path):
    try:
        # ✅ Автоматически разворачиваем массив с одним элементом
        if isinstance(data, list) and len(data) == 1:
            data = data[0]

        for key in path.split("."):
            if isinstance(data, list):
                data = data[int(key)]
            elif isinstance(data, dict):
                data = data.get(key)
            else:
                return None
        return data
    except Exception:
        return None


import allure

def check_api_response(page, requests_log, url, action_name, click_locator=None, json_array_path=None, timeout=10000, optional=False, expected_status=200):
    response = None

    with allure.step(f"[{action_name}] Подготовка запроса"):
        allure.attach(url, name="Ожидаемый URL", attachment_type=allure.attachment_type.TEXT)

    for req in requests_log:
        if url in req.url:
            resp = req.response()
            if resp:
                response = resp
                break

    try:
        if not response:
            with allure.step(f"[{action_name}] Ждём ответ после клика"):
                if click_locator:
                    with page.expect_response(lambda r: url in r.url, timeout=timeout) as response_info:
                        if callable(click_locator):
                            click_locator()
                        else:
                            click_locator.click()
                    response = response_info.value
                else:
                    with page.expect_response(lambda r: url in r.url, timeout=timeout) as response_info:
                        page.wait_for_timeout(1000)
                    response = response_info.value

        with allure.step(f"[{action_name}] Ответ получен"):
            allure.attach(f"{response.status} {response.url}", name="Статус + URL", attachment_type=allure.attachment_type.TEXT)
            print(f"🟩 [{action_name}] — успешно выполнен ({response.status})")

        if response.status != expected_status:
            msg = f"{action_name}: ожидался статус {expected_status}, получено {response.status}"
            if optional:
                check.equal(response.status, expected_status, msg)
            else:
                raise AssertionError(msg)

        if json_array_path:
            body = response.json()
            value = extract_value_by_path(body, json_array_path)

            with allure.step(f"[{action_name}] JSON-фрагмент"):
                preview = str(value)[:300]
                allure.attach(preview, name=f"{json_array_path}", attachment_type=allure.attachment_type.TEXT)

            if isinstance(value, list):
                if optional:
                    check.greater(len(value), 0, f"{action_name}: массив '{json_array_path}' пустой")
                else:
                    assert len(value) > 0, f"{action_name}: массив '{json_array_path}' пустой"
            else:
                if optional:
                    check.is_not_none(value, f"{action_name}: поле '{json_array_path}' не найдено или пустое")
                else:
                    assert value is not None, f"{action_name}: поле '{json_array_path}' не найдено или пустое"

    except Exception as e:
        if optional:
            allure.attach(str(e), name=f"[{action_name}] Ошибка (опционально)", attachment_type=allure.attachment_type.TEXT)
            check.is_true(False, f"{action_name} (опционально): ошибка — {str(e)}")
        else:
            raise


def extract_json_from_requests_log(requests_log, target_url):
    for req in requests_log:
        if target_url in req.url:
            try:
                return req.response().json()
            except:
                return None
    return None

def compare_json_fields_from_urls(page: Page, requests_log: list, url1: str, path1: str, url2: str, path2: str, label: str = "Сравнение"):
    page.wait_for_timeout(1000)
    data1 = extract_json_from_requests_log(requests_log, url1)
    data2 = extract_json_from_requests_log(requests_log, url2)

    assert data1 is not None, f"{label}: не удалось получить JSON по URL 1: {url1}"
    assert data2 is not None, f"{label}: не удалось получить JSON по URL 2: {url2}"

    v1 = extract_value_by_path(data1, path1)
    v2 = extract_value_by_path(data2, path2)

    assert str(v1) == str(v2), f"{label}: значения не совпадают → {v1} != {v2}"

