import os
import json
import time
import requests
from glob import glob

# === 🔧 Настройки ===
BOT_TOKEN = "BOT_TOKEN"       # ← вставь свой токен от @BotFather
CHAT_ID = "CHAT_ID" #        # ← возьми у @userinfobot
BASE_URL = "http://127.0.0.1:8080/autotest-reports/allure/allure-report/data"
TEST_CASES_DIR = os.path.join("autotest-reports", "allure", "allure-report", "data", "test-cases")

def send_to_tg(message: str):
    """Отправка текста в Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    resp = requests.post(url, data=payload)
    if resp.status_code == 200:
        print("✅ Сообщение успешно отправлено в Telegram")
    else:
        print(f"❌ Ошибка при отправке: {resp.text}")

def main():
    # === 1️⃣ Ищем JSON-файл в test-cases ===
    files = glob(os.path.join(TEST_CASES_DIR, "*.json"))
    if not files:
        print("⚠️ Не найден ни один JSON в test-cases/")
        return

    data_name = os.path.basename(files[0])
    # print(f"📂 Найден JSON: {data_name}")

    # === 2️⃣ Загружаем JSON по адресу ===
    json_url = f"{BASE_URL}/test-cases/{data_name}"
    # print(f"🔗 Загружаем JSON: {json_url}")

    time.sleep(3)  # ждём, чтобы http-server успел стартовать
    try:
        response = requests.get(json_url)
        response.raise_for_status()
        json_data = response.json()
    except Exception as e:
        print(f"❌ Ошибка при загрузке JSON: {e}")
        return

    # === 3️⃣ Ищем stdout в testStage.attachments ===
    test_stage = json_data.get("testStage", {})
    attachments = test_stage.get("attachments", [])
    if not attachments:
        print("⚠️ В JSON нет testStage.attachments")
        return

    source_name = None
    for item in attachments:
        if item.get("name") == "stdout":
            source_name = item.get("source")
            break

    if not source_name:
        print("⚠️ Не найден attachment с name='stdout'")
        return

    # print(f"🧾 Найден stdout source: {source_name}")

    # === 4️⃣ Загружаем сам stdout .txt ===
    txt_url = f"{BASE_URL}/attachments/{source_name}"
    # print(f"📥 Загружаем stdout: {txt_url}")

    try:
        txt_resp = requests.get(txt_url)
        txt_resp.raise_for_status()
        text_content = txt_resp.text.strip()
    except Exception as e:
        print(f"❌ Ошибка при загрузке stdout файла: {e}")
        return

    if not text_content:
        print("⚠️ Файл stdout пустой.")
        return

    # === 5️⃣ Отправляем в Telegram ===
    # print("📤 Отправка содержимого stdout в Telegram...")
    header = f"🧪 CRM autotest result\n📅 {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    message = header + text_content

    if len(message) > 3500:
        print("⚙️ Файл большой — отправляем частями...")
        for i in range(0, len(message), 3500):
            send_to_tg(message[i:i+3500])
            time.sleep(0.5)
    else:
        send_to_tg(message)

if __name__ == "__main__":
    main()
