#!/bin/bash

echo "🚀 Futbol Baholari Boti ishga tushmoqda..."
echo "📊 Python versiyasi: $(python --version)"
echo "🌐 Port: $PORT"

# Kerakli kutubxonalarni o'rnatish
pip install -r requirements.txt

# Templates papkasini yaratish
mkdir -p templates

# Flask API ni ishga tushirish
echo "🌐 Flask API server ishga tushmoqda..."
python app.py &
FLASK_PID=$!

# 10 soniya kutish (API ishga tushishi uchun)
echo "⏳ API server ishga tushishini kutish..."
sleep 10

# Health check
echo "🔍 Health check..."
curl -f http://localhost:$PORT/api/health || echo "❌ Health check failed"

# Telegram Bot ni ishga tushirish
echo "🤖 Telegram Bot ishga tushmoqda..."
python bot.py

# Agar bot to'xtasa, flask ni ham to'xtatish
kill $FLASK_PID
