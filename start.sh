#!/bin/bash

echo "🚀 Futbol Baholari Boti ishga tushmoqda..."

# Kerakli kutubxonalarni o'rnatish
pip install -r requirements.txt

# Flask API ni fon da ishga tushirish
echo "🌐 Flask API server ishga tushmoqda..."
python app.py &

# 5 soniya kutish (API ishga tushishi uchun)
sleep 5

# Telegram Bot ni ishga tushirish
echo "🤖 Telegram Bot ishga tushmoqda..."
python bot.py
