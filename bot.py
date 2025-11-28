import os
import json
import logging
import random
import string
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from datetime import datetime, timedelta

# Bot tokeni
TOKEN = "8114630640:AAHqHzsEyL7s7yckyLXfOHltm8m8cYh4F2Q"

# Admin ID
ADMIN_ID = 7081746531

# API manzili
API_URL = "http://localhost:5000/api"

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
        user_response = requests.get(f"{API_URL}/user/{user_id}")
        
        if user_response.status_code != 200 or not user_response.json()['success']:
            # Yangi foydalanuvchi yaratish
            create_response = requests.post(f"{API_URL}/user/{user_id}/create", json={
                'name': user.first_name,
                'username': user.username
            })
            
            if create_response.status_code != 200 or not create_response.json()['success']:
                await update.message.reply_text("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
                return
        
        # Referal tizimi - VEB INTEGRATSIYA
        if context.args:
            ref_id = context.args[0]
            logger.info(f"Referal argument: {ref_id}")
            if ref_id.startswith('ref'):
                try:
                    referrer_id = int(ref_id[3:])
                    
                    # API orqali referal qo'shish
                    response = requests.post(f"{API_URL}/user/{referrer_id}/add_referral")
                    
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
                                         f"👥 Jami referallar: {result['total_referrals']} ta\n\n"
                                         f"🌐 *Veb saytda ko'ring:* futbol-baholari.uz",
                                    parse_mode='Markdown'
                                )
                            except Exception as e:
                                logger.error(f"Referal bildirishnoma yuborishda xato: {e}")
                except Exception as e:
                    logger.error(f"Referal qayd etishda xato: {e}")

        # Foydalanuvchi ma'lumotlarini olish
        user_response = requests.get(f"{API_URL}/user/{user_id}")
        if user_response.status_code == 200:
            user_data = user_response.json()['user']
        else:
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

🌐 *Veb sayt:* http://localhost:5000
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
            ],
            [
                InlineKeyboardButton("🌐 VEB SAYT", url="http://localhost:5000"),
                InlineKeyboardButton("📱 STATISTIKA", callback_data="stats")
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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        logger.info(f"Button handler: {query.data} from user {user_id}")
        
        # Foydalanuvchi ma'lumotlarini olish
        user_response = requests.get(f"{API_URL}/user/{user_id}")
        if user_response.status_code == 200:
            user_data = user_response.json()['user']
        else:
            user_data = {'points': 0, 'referrals': 0}

        if query.data == "get_coupons":
            await show_coupon_selection(query, user_id, user_data)
        elif query.data == "get_ball_coupon":
            await get_ball_coupon(query, user_id)
        elif query.data == "bonuses":
            await show_bonuses(query)
        elif query.data == "my_points":
            await show_my_points(query, user_id, user_data)
        elif query.data == "get_referral_link":
            await show_referral_link(query, user_id)
        elif query.data == "share_referral":
            await share_referral_link(query, user_id)
        elif query.data == "stats":
            await show_stats(query)
        elif query.data == "back":
            await back_to_main(query, user_id)
        elif query.data == "admin":
            if is_admin(user_id):
                await show_admin_panel(query)
            else:
                await query.edit_message_text("❌ Siz admin emassiz!")
                
    except Exception as e:
        logger.error(f"Button handlerda xato: {e}")
        await query.edit_message_text("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

async def show_coupon_selection(query, user_id, user_data):
    """Kupon olish sahifasi"""
    try:
        user_points = user_data.get('points', 0)
        
        # Kuponlar va narxni olish
        coupons_response = requests.get(f"{API_URL}/coupons")
        if coupons_response.status_code == 200:
            coupons_data = coupons_response.json()
            coupon_price = coupons_data['coupon_price']
            available_coupons = coupons_data['coupons']
        else:
            coupon_price = 15
            available_coupons = []

        text = f"""
🎯 *VIP KUPON OLISH*

💰 **Sizning balansingiz:** {user_points} ball
🎟️ **Kupon narxi:** {coupon_price} ball

💎 *Ballaringiz yetarli bo'lsa VIP kuponlar olishingiz mumkin:*
"""

        keyboard = []
        
        if available_coupons:
            if user_points >= coupon_price:
                keyboard.append([InlineKeyboardButton(f"💰 VIP KUPON OLISH ({coupon_price} ball)", callback_data="get_ball_coupon")])
                text += f"\n✅ *{len(available_coupons)} ta VIP kupon mavjud!*"
            else:
                text += f"\n❌ *Ball yetarli emas!* {coupon_price - user_points} ball yetishmayapti."
        else:
            text += f"\n📭 *Hozircha yangi kuponlar mavjud emas.*"
        
        keyboard.extend([
            [InlineKeyboardButton("📤 Bal To'plash", callback_data="get_referral_link")],
            [InlineKeyboardButton("🔙 Bosh Menyu", callback_data="back")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"show_coupon_selection da xato: {e}")
        await query.edit_message_text("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

async def get_ball_coupon(query, user_id):
    """VIP KUPON sotib olish"""
    try:
        # API orqali kupon sotib olish
        response = requests.post(f"{API_URL}/user/{user_id}/buy_coupon")
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                coupon = result['coupon']
                
                coupon_text = f"""
🎉 *TABRIKLAYMIZ!*

✅ Siz {result['points_used']} ball evaziga VIP kupon sotib oldingiz!

🎟️ *Kupon ma'lumotlari:*
🏆 **O'yin:** {coupon['teams']}
⏰ **Vaqt:** {coupon['time']}
🌍 **Liga:** {coupon['league']}
🎯 **Bashorat:** {coupon['prediction']}
📊 **Koeffitsient:** {coupon['odds']}
💎 **Ishonch:** {coupon['confidence']}

🔑 *Kupon kodlari:*
• 1xBet: `{coupon['codes']['1xbet']}`
• MelBet: `{coupon['codes']['melbet']}`
• DB Bet: `{coupon['codes']['dbbet']}`

💰 **Qolgan ball:** {result['new_points']}
"""
                
                keyboard = [
                    [
                        InlineKeyboardButton("🎰 1xBet", url=BUKMAKER_LINKS['1xbet']),
                        InlineKeyboardButton("🎯 MelBet", url=BUKMAKER_LINKS['melbet']),
                        InlineKeyboardButton("💰 DB Bet", url=BUKMAKER_LINKS['dbbet'])
                    ],
                    [InlineKeyboardButton("🔄 Yana Kupon Olish", callback_data="get_coupons")],
                    [InlineKeyboardButton("💰 Mening Ballim", callback_data="my_points")],
                    [InlineKeyboardButton("🔙 Bosh Menyu", callback_data="back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(coupon_text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await query.edit_message_text(f"❌ {result['error']}")
        else:
            await query.edit_message_text("❌ Server xatosi. Iltimos, keyinroq urinib ko'ring.")
        
    except Exception as e:
        logger.error(f"get_ball_coupon da xato: {e}")
        await query.edit_message_text("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

async def show_bonuses(query):
    """Bonuslar sahifasi"""
    try:
        text = """
🎁 *BONUSLAR*

💰 *Ball olish usullari:*
• 🎁 *Yangi foydalanuvchi bonus:* 30 ball
• 📅 *Kunlik bonus:* Har kuni 10 ball
• 📤 *Referal bonus:* Har bir do'st uchun 5 ball

🏆 *Bukmeker kontorlarida ro'yxatdan o'ting va bonus oling!*

🎰 **1xBet:**
• Yangi foydalanuvchilar uchun 100% bonus
• INSAYDER PROMOKODINI kiriting va Birinchi depozitga 100% gacha bonus

🎯 **MelBet:**
• Ro'yxatdan o'ting va bonus oling
• AIFUT promokodini kiriting

📱 **DB Bet:**
• Yangi foydalanuvchilar uchun maxsus takliflar
• Tezkor to'lovlar va yuqori koeffitsientlar

🌐 *Veb sayt:* http://localhost:5000
"""

        keyboard = [
            [
                InlineKeyboardButton("🎰 1xBet", url=BUKMAKER_LINKS['1xbet']),
                InlineKeyboardButton("🎯 MelBet", url=BUKMAKER_LINKS['melbet']),
                InlineKeyboardButton("💰 DB Bet", url=BUKMAKER_LINKS['dbbet'])
            ],
            [
                InlineKeyboardButton("🎯 Kupon Olish", callback_data="get_coupons"),
                InlineKeyboardButton("📤 Referal Havola", callback_data="get_referral_link")
            ],
            [InlineKeyboardButton("🔙 Bosh Menyu", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"show_bonuses da xato: {e}")
        await query.edit_message_text("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

async def show_my_points(query, user_id, user_data):
    """Foydalanuvchi ballari va statistikasi"""
    try:
        points = user_data.get('points', 0)
        referrals = user_data.get('referrals', 0)
        referral_points = user_data.get('referral_points', 0)
        
        text = f"""
🏆 *MENING HISOBIM*

💰 **HISOBINGIZDA:** {points} ball
👥 **Referallar:** {referrals} ta
💎 **Referal ballar:** {referral_points} ball
💵 **1 referal:** 5 ball
📅 **Kunlik bonus:** 10 ball
🎟️ **Kupon narxi:** 15 ball

📊 **Kupon olish imkoniyatlari:**
"""

        if points >= 15:
            text += f"✅ **Kupon olish mumkin!** - {points // 15} ta kupon"
        else:
            text += f"❌ **Kupon uchun:** {15 - points} ball yetishmayapti"
        
        # Kunlik bonus holati
        today = datetime.now().strftime("%Y-%m-%d")
        last_bonus = user_data.get('last_daily_bonus')
        
        if last_bonus == today:
            text += "\n\n📅 *Bugun kunlik bonus olgansiz!*"
        else:
            text += "\n\n📅 *Bugun kunlik bonus olish uchun /bonus ni bosing!*"
        
        keyboard = [
            [InlineKeyboardButton("🎯 Kupon Olish", callback_data="get_coupons")],
            [InlineKeyboardButton("📤 Referal Havola", callback_data="get_referral_link")],
            [InlineKeyboardButton("📅 Kunlik Bonus", callback_data="daily_bonus")],
            [InlineKeyboardButton("🔙 Bosh Menyu", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"show_my_points da xato: {e}")
        await query.edit_message_text("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

async def show_referral_link(query, user_id):
    """Referal havolasini ko'rsatish"""
    try:
        bot_username = (await query.message._bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start=ref{user_id}"
        
        # Foydalanuvchi ma'lumotlarini olish
        user_response = requests.get(f"{API_URL}/user/{user_id}")
        if user_response.status_code == 200:
            user_data = user_response.json()['user']
            referrals_count = user_data.get('referrals', 0)
            user_points = user_data.get('points', 0)
            referral_points = user_data.get('referral_points', 0)
        else:
            referrals_count = 0
            user_points = 0
            referral_points = 0
        
        text = f"""
📤 *BAL TO'PLASH USULI*

🔗 **Sizning referal havolangiz:**
`{ref_link}`

💰 **Ball to'plash formulasi:**
• Har bir do'st = 5 ball
• Ko'proq do'st = Ko'proq ball

📊 **Sizning holatingiz:**
• Do'stlar: {referrals_count} ta
• HISOBINGIZ: {user_points} ball
• Referal ballar: {referral_points} ball
• Jami olingan ball: {referrals_count * 5} ball

💡 **Qanday ball to'plasaniz:**
1. Havolani nusxalang
2. Do'stlaringizga yuboring  
3. Har bir yangi do'st = 5 ball
4. Ballarni VIP kuponlarga aylantiring!

🌐 *Veb saytda to'liq nazorat:* http://localhost:5000

🚀 *Ko'proq do'st taklif qiling, tezroq ball to'plang!*
"""

        keyboard = [
            [InlineKeyboardButton("🔗 TELEGRAMDA ULASHISH", callback_data="share_referral")],
            [InlineKeyboardButton("🎯 Kupon Olish", callback_data="get_coupons")],
            [InlineKeyboardButton("💰 Mening Ballim", callback_data="my_points")],
            [InlineKeyboardButton("🌐 VEB SAYT", url="http://localhost:5000")],
            [InlineKeyboardButton("🔙 Bosh Menyu", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"show_referral_link da xato: {e}")
        await query.edit_message_text("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

async def share_referral_link(query, user_id):
    """Havolani ulashish"""
    try:
        bot_username = (await query.message._bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start=ref{user_id}"
        
        share_text = f"""🎯 *Futbol Baholari Boti*

⚽ Kunlik bepul VIP kuponlar
💰 Ball evaziga ekskluziv
