import os
import json
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime

# Environment variables
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8114630640:AAHqHzsEyL7s7yckyLXfOHltm8m8cYh4F2Q')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '7081746531'))
API_URL = os.environ.get('API_URL', 'http://localhost:5000/api')

# Bukmekerlar havolalari
BUKMAKER_LINKS = {
    "1xbet": "https://reffpa.com/L?tag=d_4147173m_1599c_&site=4147173&ad=1599&r=registration",
    "melbet": "https://refpa42380.com/L?tag=s_4856673m_57037c_&site=4856673&ad=57037", 
    "dbbet": "https://refpa96317.com/L?tag=d_4585917m_11213c_&site=4585917&ad=11213"
}

# Loggerni sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_admin(user_id):
    return user_id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        user_id = user.id
        
        logger.info(f"Start command from user {user_id} ({user.first_name})")
        
        # API orqali foydalanuvchi ma'lumotlarini olish yoki yaratish
        try:
            user_response = requests.get(f"{API_URL}/user/{user_id}", timeout=5)
            
            if user_response.status_code != 200 or not user_response.json()['success']:
                # Yangi foydalanuvchi yaratish
                create_response = requests.post(
                    f"{API_URL}/user/{user_id}/create", 
                    json={'name': user.first_name, 'username': user.username},
                    timeout=5
                )
                
                if create_response.status_code != 200 or not create_response.json()['success']:
                    await update.message.reply_text("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
                    return
        except requests.exceptions.RequestException as e:
            logger.error(f"API connection error: {e}")
            await update.message.reply_text("❌ Server bilan aloqa xatosi. Iltimos, keyinroq urinib ko'ring.")
            return

        # Referal tizimi
        if context.args:
            ref_id = context.args[0]
            logger.info(f"Referal argument: {ref_id}")
            if ref_id.startswith('ref'):
                try:
                    referrer_id = int(ref_id[3:])
                    
                    # API orqali referal qo'shish
                    response = requests.post(f"{API_URL}/user/{referrer_id}/add_referral", timeout=5)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result['success']:
                            # Muvaffaqiyatli xabar
                            try:
                                await context.bot.send_message(
                                    chat_id=referrer_id,
                                    text=f"🎉 *Tabriklaymiz!*\n\n"
                                         f"📤 Sizning referal havolangiz orqali yangi foydalanuvchi qo'shildi!\n"
                                         f"👤 Yangi foydalanuvchi: {user.first_name}\n"
                                         f"💰 Sizga {result['points_added']} ball qo'shildi!\n"
                                         f"🎯 Jami ball: {result['new_points']}\n"
                                         f"👥 Jami referallar: {result['total_referrals']} ta",
                                    parse_mode='Markdown'
                                )
                            except Exception as e:
                                logger.error(f"Referal bildirishnoma yuborishda xato: {e}")
                except Exception as e:
                    logger.error(f"Referal qayd etishda xato: {e}")

        # Foydalanuvchi ma'lumotlarini olish
        try:
            user_response = requests.get(f"{API_URL}/user/{user_id}", timeout=5)
            if user_response.status_code == 200:
                user_data = user_response.json()['user']
            else:
                user_data = {'points': 0, 'referrals': 0, 'referral_points': 0}
        except:
            user_data = {'points': 0, 'referrals': 0, 'referral_points': 0}

        welcome_text = f"""
🎉 *SALOM {user.first_name}!* 🏆

⚽ *FUTBOL BAHOLARI BOTIGA XUSH KELIBSIZ!*

💰 *BALL TIZIMI:*
• 🎁 *Yangi foydalanuvchi bonus:* 30 ball
• 📤 1 do'st taklif = *5 ball*
• 📅 *Kunlik bonus:* 10 ball
• 🎯 15 ball = *1 ta VIP kupon*

📊 *SIZNING HOLATINGIZ:*
👥 Referallar: {user_data.get('referrals', 0)} ta
💰 HISOBINGIZDA: {user_data.get('points', 0)} ball
💎 Referal ballar: {user_data.get('referral_points', 0)} ball
"""

        welcome_text += f"\n\n🚀 *HOZIRROQ BOSHLANG!*\nBall to'plang va VIP kuponlar oling! 🎯"

        keyboard = [
            [
                InlineKeyboardButton("🎯 VIP KUPONLAR", callback_data="get_coupons"),
                InlineKeyboardButton("🎁 BONUSLAR", callback_data="bonuses")
            ],
            [
                InlineKeyboardButton("📊 MENING BALLIM", callback_data="my_points"),
                InlineKeyboardButton("📤 REFERAL HAVOLA", callback_data="get_referral_link")
            ]
        ]
        
        if is_admin(user_id):
            keyboard.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Start commandda xato: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

# ... (qolgan funksiyalar avvalgidek, faqat API_URL ni ishlatish)

def main():
    """Asosiy dastur"""
    try:
        application = Application.builder().token(TOKEN).build()
        
        # Handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("bonus", daily_bonus_command))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        logger.info("Bot ishga tushmoqda...")
        print("✅ Bot muvaffaqiyatli ishga tushdi!")
        print(f"👑 Admin ID: {ADMIN_ID}")
        print(f"🌐 API URL: {API_URL}")
        print("🎯 YANGILANGAN TIZIM:")
        print("   • 🎁 Yangi foydalanuvchi: 30 ball")
        print("   • 📅 Kunlik bonus: 10 ball") 
        print("   • 📤 Referal: 5 ball")
        print("   • 🎯 Kupon narxi: 15 ball")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Main da xato: {e}")
        print(f"❌ Xato: {e}")

if __name__ == "__main__":
    main()
