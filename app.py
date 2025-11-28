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
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# ... (qolgan API endpointlar avvalgidek)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print("🚀 Futbol Baholari Boti ishga tushmoqda...")
    print(f"🐍 Python versiyasi: {os.environ.get('PYTHON_VERSION', 'Unknown')}")
    print(f"🌐 Port: {port}")
    print(f"🔧 Debug: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
