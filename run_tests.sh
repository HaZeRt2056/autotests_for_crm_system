#!/bin/bash
set -e

# === Настройки ===
PORT=8080
ALLURE_DIR="autotest-reports/allure"
RESULTS_DIR="$ALLURE_DIR/allure-results"
REPORT_DIR="$ALLURE_DIR/allure-report"
ARCHIVE_DIR="$ALLURE_DIR/allure-archives"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
CURRENT_ARCHIVE_DIR="$ARCHIVE_DIR/$TIMESTAMP"

echo "🚀 Запуск автотестов с сохранением истории и архивацией отчётов..."
echo "------------------------------------------"

# === 1️⃣ Подготовка директорий ===
mkdir -p "$RESULTS_DIR" "$ARCHIVE_DIR"

# очищаем только allure-results (историю не трогаем)
rm -rf "$RESULTS_DIR"
mkdir -p "$RESULTS_DIR"

# === 2️⃣ Копируем историю из предыдущего отчёта (если есть) ===
if [ -d "$REPORT_DIR/history" ]; then
#   echo "🕓 Копирование history из предыдущего отчёта..."
  mkdir -p "$RESULTS_DIR/history"
  cp -r "$REPORT_DIR/history/." "$RESULTS_DIR/history/" || true
fi

# === 3️⃣ Запуск тестов ===
echo "🧪 Запуск pytest..."
PYTHONPATH=. pytest tests/ --alluredir="$RESULTS_DIR" --maxfail=0 || true

# === 4️⃣ Генерация нового отчёта ===
echo "📊 Генерация нового отчёта..."
allure generate "$RESULTS_DIR" -o "$REPORT_DIR" --clean

# === 5️⃣ Архивация отчёта ===
# echo "📦 Архивация отчёта..."
cp -r "$REPORT_DIR" "$CURRENT_ARCHIVE_DIR"
ln -sfn "$CURRENT_ARCHIVE_DIR" "$ARCHIVE_DIR/latest"
# echo "🗂 Отчёт сохранён в архив: $CURRENT_ARCHIVE_DIR"

# === 6️⃣ Проверяем наличие index.html ===
if [ ! -f "index.html" ]; then
  echo "⚠️ Файл index.html не найден! Создайте его в корне проекта."
  exit 1
fi

# === 7️⃣ Запуск локального сервера из корня ===
# echo "🌐 Запуск локального сервера на порту $PORT..."
pkill -f "http-server .* -p $PORT" >/dev/null 2>&1 || true
npx http-server . -p $PORT >/dev/null 2>&1 &
SERVER_PID=$!

sleep 5
# === 🧾 Отправка stdout в Telegram ===
# echo "📤 Отправка stdout в Telegram..."
python send_stdout_from_allure.py || echo "⚠️ Не удалось отправить отчёт в Telegram"


# === 8️⃣ Проброс через ngrok ===
# echo "🌍 Проброс через ngrok..."
# pkill -f ngrok >/dev/null 2>&1 || true
# ngrok http $PORT --log=stdout > ngrok.log &
# NGROK_PID=$!
#
# # === 9️⃣ Ожидание и получение ссылки ===
# echo "⏳ Ожидание запуска ngrok..."
# sleep 5
# NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | grep -o '"public_url":"https:[^"]*' | sed 's/"public_url":"//')

# === 🔟 Вывод ссылок ===
echo "------------------------------------------"
echo "✅ Всё готово!"
echo "🏠 Главная страница:  http://127.0.0.1:$PORT"
echo "📄 Текущий отчёт:      http://127.0.0.1:$PORT/$REPORT_DIR/"
echo "🗂 Последний архив:    http://127.0.0.1:$PORT/$ARCHIVE_DIR/latest/"
# #if [ -n "$NGROK_URL" ]; then
#   echo "🌍 Глобальная ссылка:  $NGROK_URL"
# else
#   echo "❌ Не удалось получить глобальную ссылку (см. ngrok.log)"
# fi
# echo "------------------------------------------"
# echo "Чтобы остановить серверы, введи: kill $SERVER_PID $NGROK_PID"
