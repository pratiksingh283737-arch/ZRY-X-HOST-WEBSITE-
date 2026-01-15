import os
import time
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash
from github import Github

app = Flask(__name__)
app.secret_key = "bhohot_secret_key_hai_ye"  # Session key

# ==========================================
# ⚙️ ADMIN SETTINGS (Yahan Edit Karein)
# ==========================================
ADMIN_UPI_ID = "your_upi_id@okhdfcbank"  # <--- APNI UPI ID YAHAN DALEIN
ADMIN_NAME = "Bot Hosting Admin"         # <--- APNA NAAM LIKHEIN

# ==========================================
# 🔑 API KEYS (GitHub & Render)
# ==========================================
GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
RENDER_API_KEY = "rnd_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
GITHUB_USERNAME = "YourGitHubUsername"

# --- Deployment Logic (Same as before) ---
def deploy_bot(user_name, bot_token, file_code):
    try:
        g = Github(GITHUB_TOKEN)
        user = g.get_user()
        unique_name = f"bot-{user_name}-{int(time.time())}"
        
        # 1. GitHub Repo Create
        repo = user.create_repo(unique_name, private=True) # Private Repo
        repo.create_file("main.py", "Init", file_code)
        repo.create_file("requirements.txt", "Reqs", "pyTelegramBotAPI\nrequests\nflask")
        
        repo_url = f"https://github.com/{GITHUB_USERNAME}/{unique_name}"
        
        # 2. Render Deploy
        url = "https://api.render.com/v1/services"
        payload = {
            "serviceDetails": {
                "type": "background_worker",
                "name": unique_name,
                "env": "python",
                "repo": repo_url,
                "branch": "main",
                "envVars": [{"key": "BOT_TOKEN", "value": bot_token}],
                "startCommand": "pip install -r requirements.txt && python main.py",
                "plan": "free"
            }
        }
        headers = {"Authorization": f"Bearer {RENDER_API_KEY}", "Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            return True, "✅ Bot Successfully Deployed on Render!"
        else:
            return False, f"❌ Render Error: {response.text}"
            
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

# --- ROUTES ---

@app.route('/')
def index():
    if 'plan' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/pay/<price>')
def payment_page(price):
    # Google Charts API ya QRServer API use karke Dynamic QR generate karenge
    # Format: upi://pay?pa=UPI_ID&pn=NAME&am=AMOUNT&cu=INR
    upi_string = f"upi://pay?pa={ADMIN_UPI_ID}&pn={ADMIN_NAME}&am={price}&cu=INR"
    
    # QR Code Image URL (Public API)
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={upi_string}"
    
    return render_template('payment.html', price=price, qr_url=qr_url, upi_id=ADMIN_UPI_ID)

@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    # Manual Verification Logic
    utr_number = request.form.get('utr')
    plan_price = request.form.get('price')
    
    # Filhal hum maan lete hain ki UTR sahi hai aur user ko allow karte hain.
    # (Future mein aap yahan Database mein UTR save kar sakte hain aur Admin Panel se approve kar sakte hain)
    
    if len(utr_number) < 10:
        flash("Invalid Transaction ID! Please check again.", "error")
        return redirect(url_for('payment_page', price=plan_price))
    
    # Session Activate
    session['plan'] = plan_price
    session['user'] = f"user_{utr_number[-4:]}" # User ID based on UTR
    
    flash(f"Payment Received! Plan ₹{plan_price} Activated.", "success")
    return redirect(url_for('dashboard'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'plan' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        bot_token = request.form.get('bot_token')
        file = request.files['file']
        
        if file and bot_token:
            code_content = file.read().decode("utf-8")
            success, msg = deploy_bot(session['user'], bot_token, code_content)
            if success:
                flash(msg, "success")
            else:
                flash(msg, "error")
                
    return render_template('dashboard.html', plan=session['plan'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)