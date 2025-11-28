from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Production sozlamalari
app.config['JSON_AS_ASCII'] = False

# Bot ma'lumotlari fayli
DATA_FILE = "data.json"

def load_data():
    """Ma'lumotlarni yuklash"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ma'lumotlarni yuklashda xato: {e}")
        # Boshlang'ich ma'lumotlarni yaratish
        initial_data = {
            "users": {},
            "coupons": {
                "available": [
                    {
                        "id": "1001",
                        "time": "20:00",
                        "league": "Premier League",
                        "teams": "Man City vs Arsenal",
                        "prediction": "1X",
                        "odds": "1.50",
                        "confidence": "85%",
                        "codes": {
                            "1xbet": "CITY123",
                            "melbet": "MBC456",
                            "dbbet": "DB789"
                        },
                        "added_date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                ],
                "purchased": {}
            },
            "settings": {
                "referral_points": 5,
                "coupon_price": 15,
                "daily_bonus": 10,
                "welcome_points": 30
            },
            "stats": {
                "total_users": 0,
                "total_points_given": 0,
                "total_coupons_sold": 0,
                "total_referrals": 0
            }
        }
        save_data(initial_data)
        return initial_data

def save_data(data):
    """Ma'lumotlarni saqlash"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Saqlash xatosi: {e}")
        return False

@app.route('/')
def serve_index():
    return send_from_directory('templates', 'index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Futbol Baholari API',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Foydalanuvchi ma'lumotlarini olish"""
    data = load_data()
    user = data['users'].get(str(user_id))
    
    if user:
        # Sotib olingan kuponlar sonini hisoblash
        purchased_count = 0
        for coupon_id in data['coupons']['purchased']:
            if str(user_id) in data['coupons']['purchased'][coupon_id]:
                purchased_count += 1
        
        return jsonify({
            'success': True,
            'user': {
                'id': user_id,
                'name': user.get('name', 'Foydalanuvchi'),
                'username': user.get('username', ''),
                'points': user.get('points', 0),
                'referrals': user.get('referrals', 0),
                'referral_points': user.get('referral_points', 0),
                'purchased_coupons': purchased_count,
                'points_history': user.get('points_history', []),
                'joined_date': user.get('joined_date', ''),
                'last_active': user.get('last_active', ''),
                'last_daily_bonus': user.get('last_daily_bonus', '')
            }
        })
    else:
        return jsonify({'success': False, 'error': 'Foydalanuvchi topilmadi'})

@app.route('/api/user/<int:user_id>/add_referral', methods=['POST'])
def add_referral(user_id):
    """Yangi referal qo'shish"""
    data = load_data()
    user_key = str(user_id)
    
    if user_key not in data['users']:
        return jsonify({'success': False, 'error': 'Foydalanuvchi topilmadi'})
    
    # Referal qo'shish
    data['users'][user_key]['referrals'] = data['users'][user_key].get('referrals', 0) + 1
    
    # Ball qo'shish
    referral_points = data['settings']['referral_points']
    current_points = data['users'][user_key].get('points', 0)
    data['users'][user_key]['points'] = current_points + referral_points
    
    # Referal ballarini hisoblash
    current_ref_points = data['users'][user_key].get('referral_points', 0)
    data['users'][user_key]['referral_points'] = current_ref_points + referral_points
    
    # Ball tarixiga qo'shish
    if 'points_history' not in data['users'][user_key]:
        data['users'][user_key]['points_history'] = []
    
    data['users'][user_key]['points_history'].append({
        'type': 'add',
        'points': referral_points,
        'reason': 'Yangi referal taklif',
        'date': datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    
    # Faollikni yangilash
    data['users'][user_key]['last_active'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Statistikani yangilash
    data['stats']['total_referrals'] = data['stats'].get('total_referrals', 0) + 1
    data['stats']['total_points_given'] = data['stats'].get('total_points_given', 0) + referral_points
    
    save_data(data)
    
    return jsonify({
        'success': True,
        'points_added': referral_points,
        'new_points': data['users'][user_key]['points'],
        'total_referrals': data['users'][user_key]['referrals'],
        'message': f'+{referral_points} ball! Yangi referal taklif'
    })

@app.route('/api/user/<int:user_id>/buy_coupon', methods=['POST'])
def buy_coupon(user_id):
    """Kupon sotib olish"""
    data = load_data()
    user_key = str(user_id)
    coupon_price = data['settings']['coupon_price']
    
    if user_key not in data['users']:
        return jsonify({'success': False, 'error': 'Foydalanuvchi topilmadi'})
    
    user_points = data['users'][user_key].get('points', 0)
    
    if user_points < coupon_price:
        return jsonify({'success': False, 'error': 'Ballaringiz yetarli emas'})
    
    # Mavjud kuponlarni tekshirish
    available_coupons = [c for c in data['coupons']['available'] 
                        if user_key not in data['coupons']['purchased'].get(c['id'], [])]
    
    if not available_coupons:
        return jsonify({'success': False, 'error': 'Hozircha yangi kuponlar mavjud emas'})
    
    # Tasodifiy kupon tanlash
    import random
    coupon = random.choice(available_coupons)
    
    # Ballarni olib tashlash
    data['users'][user_key]['points'] = user_points - coupon_price
    
    # Ball tarixiga qo'shish
    data['users'][user_key]['points_history'].append({
        'type': 'remove',
        'points': coupon_price,
        'reason': f'VIP kupon sotib olish: {coupon["teams"]}',
        'date': datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    
    # Faollikni yangilash
    data['users'][user_key]['last_active'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Kuponni sotib olinganlar ro'yxatiga qo'shish
    if coupon['id'] not in data['coupons']['purchased']:
        data['coupons']['purchased'][coupon['id']] = []
    
    data['coupons']['purchased'][coupon['id']].append(user_key)
    
    # Statistika
    data['stats']['total_coupons_sold'] = data['stats'].get('total_coupons_sold', 0) + 1
    
    save_data(data)
    
    return jsonify({
        'success': True,
        'points_used': coupon_price,
        'new_points': data['users'][user_key]['points'],
        'coupon': coupon,
        'message': 'VIP kupon muvaffaqiyatli sotib olindi! 🎉'
    })

@app.route('/api/user/<int:user_id>/daily_bonus', methods=['POST'])
def daily_bonus(user_id):
    """Kunlik bonus olish"""
    data = load_data()
    user_key = str(user_id)
    bonus_points = data['settings']['daily_bonus']
    
    if user_key not in data['users']:
        return jsonify({'success': False, 'error': 'Foydalanuvchi topilmadi'})
    
    # Kunlik bonusni tekshirish
    today = datetime.now().strftime("%Y-%m-%d")
    last_bonus = data['users'][user_key].get('last_daily_bonus')
    
    if last_bonus == today:
        return jsonify({'success': False, 'error': 'Bugun bonus olgansiz. Ertaga qayta urinib ko\'ring!'})
    
    # Ball qo'shish
    current_points = data['users'][user_key].get('points', 0)
    data['users'][user_key]['points'] = current_points + bonus_points
    data['users'][user_key]['last_daily_bonus'] = today
    data['users'][user_key]['last_active'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Ball tarixiga qo'shish
    data['users'][user_key]['points_history'].append({
        'type': 'add',
        'points': bonus_points,
        'reason': 'Kunlik bonus',
        'date': datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    
    # Statistika
    data['stats']['total_points_given'] = data['stats'].get('total_points_given', 0) + bonus_points
    
    save_data(data)
    
    return jsonify({
        'success': True,
        'points_added': bonus_points,
        'new_points': data['users'][user_key]['points'],
        'message': f'Kunlik bonus muvaffaqiyatli qo\'shildi! +{bonus_points} ball 🎉'
    })

@app.route('/api/coupons', methods=['GET'])
def get_coupons():
    """Barcha kuponlarni olish"""
    data = load_data()
    return jsonify({
        'success': True,
        'coupons': data['coupons']['available'],
        'coupon_price': data['settings']['coupon_price']
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Global statistikani olish"""
    data = load_data()
    return jsonify({
        'success': True,
        'stats': data['stats'],
        'total_users': len(data['users']),
        'settings': data['settings']
    })

@app.route('/api/user/<int:user_id>/create', methods=['POST'])
def create_user(user_id):
    """Yangi foydalanuvchi yaratish (bot uchun)"""
    data = load_data()
    user_key = str(user_id)
    
    if user_key in data['users']:
        return jsonify({'success': False, 'error': 'Foydalanuvchi allaqachon mavjud'})
    
    # Yangi foydalanuvchi yaratish
    user_data = request.json
    data['users'][user_key] = {
        'name': user_data.get('name', 'Foydalanuvchi'),
        'username': user_data.get('username', ''),
        'referrals': 0,
        'referral_points': 0,
        'points': data['settings']['welcome_points'],
        'joined_date': datetime.now().strftime("%Y-%m-%d"),
        'last_active': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'points_history': [{
            'points': data['settings']['welcome_points'],
            'reason': "Yangi foydalanuvchi bonus",
            'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'type': 'add'
        }]
    }
    
    # Statistika
    data['stats']['total_users'] = data['stats'].get('total_users', 0) + 1
    data['stats']['total_points_given'] = data['stats'].get('total_points_given', 0) + data['settings']['welcome_points']
    
    save_data(data)
    
    return jsonify({
        'success': True,
        'user': data['users'][user_key],
        'message': 'Yangi foydalanuvchi yaratildi'
    })

if __name__ == '__main__':
    # Templates papkasini yaratish
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    port = int(os.environ.get('PORT', 5000))
    
    print("🚀 Futbol Baholari Boti ishga tushmoqda...")
    print(f"🌐 API manzili: http://0.0.0.0:{port}")
    print(f"📊 Health check: http://0.0.0.0:{port}/api/health")
    print("🎯 YANGILANGAN TIZIM:")
    print("   • 🎁 Yangi foydalanuvchi: 30 ball")
    print("   • 📅 Kunlik bonus: 10 ball") 
    print("   • 📤 Referal: 5 ball")
    print("   • 🎯 Kupon narxi: 15 ball")
    
    app.run(host='0.0.0.0', port=port, debug=False)
