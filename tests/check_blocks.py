import allure
from utils.api_checker import check_api_response, compare_json_fields_from_urls
from config.urls import urls
from playwright.sync_api import Error as PlaywrightError
from utils.credentials import DATA
from locators.login_steps import *
import os
from dotenv import load_dotenv

load_dotenv()  # Подгрузит все переменные из .env
MY_ACALLID = os.getenv("MY_ACALLID")
def intercept_create_sbms(route):
    import json
    try:
        request = route.request
        body = request.post_data_json

        # Меняем только main_acallid из .env
        body["main_acallid"] = MY_ACALLID

        print(f"[intercept_create_sbms] main_acallid → {MY_ACALLID}")

        route.continue_(post_data=json.dumps(body))
    except Exception as e:
        print(f"[intercept_create_sbms] Ошибка при подмене: {e}")
        route.continue_()


def run_crm_checks(page, requests_log, number, current_subscriber_id, current_customer_id):
    # print("3", current_subscriber_id, current_customer_id)
    def _click_and_wait_for_create_sbms(page):
        """
        Создание SBMS-причины — ждём ответ на createSbmsReason
        """
        print("🟦 Ждём createSbmsReason...")
        page.route("**/ocp/createSbmsReason", intercept_create_sbms)

        # Ждём именно ответ на createSbmsReason
        with page.expect_response(lambda r: "createSbmsReason" in r.url, timeout=30000):
            page.locator("#root").get_by_role("button", name="Сохранить").click()

    tabs_clicker_checks = [
        {
            "step": "Tariff tab",
            "url": urls["tariff_tab"].format(subscriberId=current_subscriber_id),
            "action": "Вкладка Тариф",
            "click": lambda: (
                page.get_by_role("link", name="Тарифы").dblclick()
            ),
            "json_path": "listInfo"
        },
        {
            "step": "Packets tab",
            "url": urls["packet_tab"].format(subscriberId=current_subscriber_id),
            "action": "Вкладка Пакеты",
            "click": lambda: (
                page.get_by_role("link", name="Пакеты").dblclick(),
                page.get_by_role("button", name="Активные").click(),
                page.get_by_role("button", name="Доступные").click(),
                page.get_by_role("button", name="Отключенные").click(),
            ),
            "json_path": "items"
        },
        {
            "step": "Services tab",
            "url": urls["services_tab"].format(subscriberId=current_subscriber_id),
            "action": "Вкладка Услуги",
            "click": lambda: (
                page.get_by_role("link", name="Услуги", exact=True).click(),
                page.get_by_role("button", name="Доступные").click(),
            ),
            "json_path": "items"
        },
        {
            "step": "Content tab",
            "url": urls["content_tab"].format(number=number),
            "action": "Вкладка Контент-услуги",
            "click": lambda: (
                page.get_by_role("link", name="Контент-услуги").dblclick()
            )
        },
        {
            "step": "SMS tab",
            "url": urls["sms_tsb"],
            "action": "Вкладка СМС",
            "click": lambda: (
                page.get_by_role("link", name="SMS").click(),
            ),
            "json_path": "count"
        },
        # {
        #     "step": "HLRstatus tab",
        #     "url": urls["hlrstatus_tab"].format(customerId=current_customer_id),
        #     "action": "Вкладка HLRстатус",
        #     "click": lambda: (
        #         page.get_by_role("link", name="HLR Статус").click()
        #     ),
        #     "json_path": "FORM"
        # },
        {
            "step": "History  reasons tab",
            "url": urls["history_reasons"].format(number=number),
            "action": "Вкладка История обращений",
            "click": lambda: (
                page.get_by_role("link", name="История обращений").click()
            )
        },
    ]
    sms_send_checks = [
        {
            "step": "Check SMS Sending",
            "url": urls["sms_sending"].format(number=number),
            "action": "Проверка отправки смс",
            "click": lambda: (
                page.get_by_role("link", name="SMS").click(),
                page.get_by_role("button", name="Русский").click(),
                page.get_by_role("button", name="Отправить SMS").click()
            ),
            "json_path": "status",
            "optional": True
        }]
    balance_info_checks = [
        # {
        #     "step": "Check MsisdnList (опционально)",
        #     "url": urls["MsisdnList"].format(customerId=current_customer_id),
        #     "action": "Номерной Лист",
        #     "click": None,
        #     "json_path": "result",
        #     "optional": True
        # },
        {
            "step": "Check SIM info",
            "url": urls["sim_info"],
            "action": "Sim Info",
            "click": lambda: (
                page.get_by_role("button", name="SIM").click(),
                page.get_by_role("dialog").get_by_role("button").click()
            ),
            "json_path": "SIMCards.0.status.name"
        },
        {
            "step": "Check Info",
            "url": urls["info"].format(customerId=current_customer_id),
            "action": "Информация",
            "click": lambda: (
                page.get_by_role("button", name="Info").click(),
                page.get_by_role("button", name="Да", exact=True).click(),
                page.get_by_role("dialog").get_by_role("button").click(),
            ),
            "json_path": "name"
        },
        {
            "step": "Check Balance",
            "url": urls["balance"].format(customerId=current_customer_id),
            "action": "Баланс обновление",
            "click": lambda: page.get_by_test_id("update_balance").click(),
            "json_path": "availableBalance"
        },
        {
            "step": "Check History of balance",
            "url": urls["story_balans"],
            "action": "История баланса",
            "click": lambda: (
                page.get_by_test_id("story_balance").click(),
                page.get_by_role("dialog").get_by_role("button").click()
            ),
            "json_path": "listInfo"
        },
        {
            "step": "Check update tarif info",
            "url": urls["update_tariff_info"].format(subscriberId=current_subscriber_id),
            "action": "Кнопка обновления информации о тарифе",
            "click": page.get_by_test_id("update_tariff_info").click(),
            "json_path": "ratePlan"
        },
        {
            "step": "Check tariffs",
            "url": urls["tariffs"].format(subscriberId=current_subscriber_id),
            "action": "Тарифы",
            "click": lambda: (
                page.get_by_test_id("info_tariff_history").click(),
                page.get_by_role("button", name="Да").click()
            ),
            "json_path": "items"
        },
        {
            "step": "Check status tp info",
            "url": urls["charge_hist"].format(number=number),
            "action": "Check status tp info",
            "click": lambda: (
                page.get_by_test_id("status_tp_info").click(),
                page.get_by_role("dialog").get_by_role("button").click()
            ),
            "json_path": "result"
        },
        {
            "step": "Check Status",
            "url": urls["status"].format(subscriberId=current_subscriber_id),
            "action": "Статус",
            "click": lambda: page.get_by_test_id("update_status").click(),
            "json_path": "lcState.def"
        },
        {
            "step": "Check status info",
            "url": urls["status_info"].format(subscriberId=current_subscriber_id),
            "action": "Check status info",
            "click": lambda: (
                page.get_by_test_id("status_info").click(),
                page.get_by_role("dialog").get_by_role("button").click()
            ),
            "json_path": "items"
        }
    ]
    reasons_for_contacting = [
        {
            "step": "Create SBMS reason",
            "urls": [
                urls["type"],
                urls["category"],
                urls["reason"],
            ],
            "action": "Create SBMS reason",
            "click": lambda: (
                page.get_by_role("link", name="Причины обращения").click(),
                page.get_by_role("button", name="Создать причину").click(),
                page.get_by_role("combobox", name="Тип").click(),
                page.get_by_text("305Обслуживание").click(),
                page.get_by_role("combobox", name="Категория").click(),
                page.get_by_role("option", name="Обслуживание").click(),
            ),
            "json_path": "detailsRequest",
        },
        {
            "step": "Create SBMS reason (отправка запроса)",
            "url": urls["create_sbms"],
            "action": "Создание SBMS",
            "click": lambda: _click_and_wait_for_create_sbms(page),
            "json_path": "inquiry_id"
        },
        {
            "step": "Поиск по имени",
            "url": urls["name"],
            "action": "reasons",
            "click": lambda: (
                fill_reason_form(page),
            ),
            "json_path": "users"
        },
        {
            "step": "Check reasons for contacting",
            "url": urls["reasons_for_c"],
            "action": "reasons for contacting",
            "click": lambda: (
                page.get_by_role("button", name="Создать", exact=True).click()),
            "json_path": "id"
        },
    ]
    tariff_checks = []



# Тут проверка и шаги при смене тарифов
    def try_change_tariff(page) -> bool:
        try:
            page.get_by_role("link", name="Тарифы").click()
            page.get_by_test_id("choose-tariff_1").click()
            page.get_by_role("textbox", name="Выберите дату").click()
            page.wait_for_timeout(500)
            page.get_by_role("option", name=f"Choose {DATA[0]['end_choose']}").click()
            page.wait_for_timeout(500)

            # Проверка: доступна ли кнопка
            button = page.get_by_role("button", name="Сменить тариф")
            if button.is_disabled():
                # Закрываем модалку
                page.get_by_role("dialog").click()
                allure.attach("Недостаточно денег — кнопка 'Сменить тариф' недоступна",
                              name="Skip reason", attachment_type=allure.attachment_type.TEXT)
                return False

            button.click()
            return True

        except PlaywrightError as e:
            allure.attach(str(e), name="Playwright error", attachment_type=allure.attachment_type.TEXT)
            return False
    was_tariff_changed = try_change_tariff(page)
    if was_tariff_changed:
        tariff_checks.append({
            "step": "Check change tariff",
            "url": urls["change_tariff"].format(subscriberId=current_subscriber_id),
            "action": "Check change tariff",
            "click": lambda: page.wait_for_timeout(500),
            "json_path": "status.name"
        })

        tariff_checks.append({
            "step": "Check cancel tariff",
            "url": urls["cancel_tariff"].format(subscriberId=current_subscriber_id),
            "action": "Check cancel tariff",
            "click": lambda: (
                page.get_by_role("link", name="Тарифы").click(),
                page.wait_for_selector('[data-testid="choose-tariff_planned"]', timeout=5000),
                page.get_by_test_id("choose-tariff_planned").click(),
                page.get_by_role("button", name="Да, отменить").click()
            ),
            "json_path": "",
            "status": 204
        })

        # 👉 выполняем сразу
        print("арива2")
        tariff_checks[-1]["click"]()  # вызываем отмену сразу
    else:
        with allure.step("Check change tariff (пропущено)"):
            allure.attach("Тариф не был сменён: недостаточно средств",
                          name="Пропущено", attachment_type=allure.attachment_type.TEXT)
    # Основной проход по шагам
    def run_group(group_name, items):
        with allure.step(group_name):
            for item in items:
                try:
                    with allure.step(item["step"]):
                        urls = item.get("urls") or [item.get("url")]  # ✅ поддержка нескольких URL
                        first_click = True

                        for u in urls:
                            check_api_response(
                                page,
                                requests_log,
                                u,
                                f"{item['action']} → {u.split('/')[-1]}",  # красивое имя шага в allure
                                click_locator=item.get("click") if first_click else None,  # клик только один раз
                                json_array_path=item.get("json_path"),
                                expected_status=item.get("status", 200),
                                optional=item.get("optional", False)
                            )
                            first_click = False

                except Exception as e:
                    if item.get("optional"):
                        allure.attach(
                            str(e),
                            name=f"{item['step']} (Optional Error)",
                            attachment_type=allure.attachment_type.TEXT
                        )
                    else:
                        raise


    run_group("Карточка абонента", balance_info_checks)
    run_group("Вкладки", tabs_clicker_checks)
    run_group("Вкладка: Тарифы", tariff_checks)
    run_group("Отправка смс", sms_send_checks)
    run_group("Причина обращения", reasons_for_contacting)
    with allure.step("Check Language Switching"):
        for lang_key, lang_name in [("lang_uz", "Uz"), ("lang_en", "En"), ("lang_ru", "Ру")]:
            try:
                check_api_response(
                    page,
                    requests_log,
                    urls[lang_key].format(subscriberId=current_subscriber_id),
                    f"Смена языка на {lang_name}",
                    click_locator=lambda lang=lang_name: (
                        page.get_by_test_id("language").click(),
                        page.get_by_role("option", name=lang).click()
                    ),
                    json_array_path="detail"
                )
            except Exception as e:
                allure.attach(str(e), name=f"Ошибка при смене языка на {lang_name}",
                              attachment_type=allure.attachment_type.TEXT)
                raise
    with allure.step("Compare client name between Search and Info"):
        try:
            compare_json_fields_from_urls(
                page,
                requests_log,
                urls["search"],
                "searchResults.0.customer.name",
                urls["info"].format(customerId=current_customer_id),
                "name",
                "Имя клиента"
            )
        except Exception as e:
            allure.attach(str(e), name="Ошибка при сравнении имени клиента",
                          attachment_type=allure.attachment_type.TEXT)
            raise




    # Сравнение имени

