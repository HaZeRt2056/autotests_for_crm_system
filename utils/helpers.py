import pytest_check as check
import allure

def check_login_request(requests_log, url: str):
    try:
        for req in requests_log:
            if url in req.url:
                resp = req.response()
                if resp:
                    check.equal(resp.status, 200, f"Login API {url} → статус: {resp.status}")
                    return
        check.is_true(False, f"Login API {url}: не найден запрос")
    except Exception as e:
        allure.attach(str(e), name="Login API Ошибка", attachment_type=allure.attachment_type.TEXT)
        check.is_true(False, f"Login API {url}: исключение — {str(e)}")
