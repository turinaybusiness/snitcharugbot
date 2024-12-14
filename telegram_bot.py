from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import os
from psycopg2 import connect
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
from flask_cors import CORS
DATABASE_URL = os.getenv("DATABASE_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")


for i in range(5):
    try:
        conn = connect(DATABASE_URL)
        cur = conn.cursor()
        break
    except Exception as e:
        print(f"Database connection failed: {e}. Retrying {i + 1}/5...")
        time.sleep(5)
else:
    raise Exception("Database connection failed after 5 attempts")

# Create table if it doesn't exist
cur.execute("""
CREATE TABLE IF NOT EXISTS mint_addresses (
    id SERIAL PRIMARY KEY,
    address TEXT NOT NULL UNIQUE,
    sent_count INTEGER NOT NULL DEFAULT 1
);
""")
conn.commit()

# Function to validate mint address
def validate_mint_address(mint_address: str) -> bool:
    return len(mint_address) == 44 and mint_address.endswith("pump")

# Function to save or update the mint address in the database
def save_mint_address(address: str):
    try:
        cur.execute("""
        INSERT INTO mint_addresses (address)
        VALUES (%s)
        ON CONFLICT (address)
        DO UPDATE SET sent_count = mint_addresses.sent_count + 1;
        """, (address,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error saving address: {e}")

# Function to get the sent_count for a mint address
def get_address_count(address: str) -> int:
    cur.execute("SELECT sent_count FROM mint_addresses WHERE address = %s", (address,))
    result = cur.fetchone()
    return result[0] if result else 0

# Start command handler
async def start(update: Update, context) -> None:
    # Create buttons
    keyboard = [
        [InlineKeyboardButton("Snitch CA", callback_data="report_ca")],
        [InlineKeyboardButton("Check CA", callback_data="check_ca")],
        [InlineKeyboardButton("Current Training Process", callback_data="training_progress")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = (
        "➡️ Welcome to Pazyryk rug snitch bot 🤖\n\n"
        "➡️ You can help train Pazyryk by snitching old rugs 👨‍🏫.\n\n"
        "➡️ The more rug Pazyryk learns, the more accurate it gets 🚀.\n\n"
        "✅ Pazyryk [(X)](https://x.com/Pazyrykfirstrug)\n\n"
        "✅ Visit Pazyryk's [website] for more details (https://www.pullrug.com/)\n\n"
        "🚨 Write rug CA to snitch 🚨"
    )
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown",  # Use Markdown for clickable links
    )

# CallbackQueryHandler to process button clicks
async def button_handler(update: Update, context) -> None:
    query = update.callback_query
    await query.answer()

    # Handle each button action
    if query.data == "report_ca":
        await update.callback_query.message.reply_text("Enter Token CA:")
        context.user_data["awaiting_ca"] = "report"
    elif query.data == "check_ca":
        await update.callback_query.message.reply_text("Enter Token CA to check:")
        context.user_data["awaiting_ca"] = "check"
    elif query.data == "training_progress":
        await update.callback_query.message.reply_text("Training Process: 100% 🛠")

# Message handler to handle user input after button clicks
async def handle_ca_input(update: Update, context) -> None:
    mint_address = update.message.text.strip()
    action = context.user_data.get("awaiting_ca")

    if action == "report":
        if validate_mint_address(mint_address):
            save_mint_address(mint_address)
            await update.message.reply_text("Thank you for your report 🙏")
        else:
            await update.message.reply_text("Invalid Token Address.")
        context.user_data["awaiting_ca"] = None  # Clear the action
    elif action == "check":
        if validate_mint_address(mint_address):
            count = get_address_count(mint_address)
            await update.message.reply_text(f"This CA reported {count} times 🚨")
        else:
            await update.message.reply_text("Invalid Token Address.")
        context.user_data["awaiting_ca"] = None  # Clear the action
    else:
        await update.message.reply_text("Please use one of the buttons to interact with the bot.")

# Main function
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))  # For button clicks
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ca_input))  # For text input

    # Webhook setup
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        url_path=BOT_TOKEN,
        webhook_url=f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
    )
    port = int(os.getenv('PORT', 5000))  # Render provides the PORT env variable
    app.run(host='0.0.0.0', port=port)


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
CORS(app)
# Initialize API key from environment variable
API_KEY = os.getenv('HELIUS_API_KEY', '4b72d62d-6176-4939-918b-b486fe647122')
if not API_KEY:
    raise ValueError("HELIUS_API_KEY environment variable is not set")

class RugPullDetector:
    def __init__(self, api_key):
        self.API_KEY = api_key
        self.RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={self.API_KEY}"
        self.session = requests.Session()

    def get_token_metadata(self, token_address: str):
        payload = {
            "jsonrpc": "2.0",
            "id": "my-id",
            "method": "getAsset",
            "params": [token_address]
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = self.session.post(self.RPC_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "result" in data:
                return data["result"]
            return None
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching token metadata: {str(e)}")
            return None

    def get_token_supply(self, token_address: str):
        payload = {
            "jsonrpc": "2.0",
            "id": "my-id",
            "method": "getTokenSupply",
            "params": [token_address]
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = self.session.post(self.RPC_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "result" in data and "value" in data["result"]:
                return data["result"]["value"]
            return None
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching token supply: {str(e)}")
            return None

    def calculate_risk_score(self, token_data, supply_data):
        risk_score = 0.0
        risk_factors = []
        
        if not token_data:
            return 1.0, ["No token metadata available"]
        
        if not token_data.get("name"):
            risk_score += 0.2
            risk_factors.append("Missing token name")
            
        if not token_data.get("symbol"):
            risk_score += 0.1
            risk_factors.append("Missing token symbol")

        if supply_data:
            try:
                supply = float(supply_data.get("uiAmount", 0))
                if supply == 0:
                    risk_score += 0.3
                    risk_factors.append("Zero supply")
                elif supply > 1000000000000:
                    risk_score += 0.2
                    risk_factors.append("Extremely high supply")
            except:
                risk_score += 0.2
                risk_factors.append("Invalid supply data")

        decimals = supply_data.get("decimals") if supply_data else None
        if decimals is None or decimals == 0:
            risk_score += 0.2
            risk_factors.append("Invalid decimals")

        if token_data.get("frozen"):
            risk_score += 0.3
            risk_factors.append("Token is frozen")

        return min(risk_score, 1.0), risk_factors

    def analyze_token(self, token_address: str):
        token_data = self.get_token_metadata(token_address)
        supply_data = self.get_token_supply(token_address)
        
        if not token_data and not supply_data:
            return {
                "error": "Unable to fetch token data",
                "status": "error"
            }
        
        risk_score, risk_factors = self.calculate_risk_score(token_data, supply_data)
        
        return {
            "status": "success",
            "data": {
                "token_address": token_address,
                "name": token_data.get("name", "Unknown") if token_data else "Unknown",
                "symbol": token_data.get("symbol", "Unknown") if token_data else "Unknown",
                "supply": supply_data.get("uiAmount", 0) if supply_data else 0,
                "decimals": supply_data.get("decimals", 0) if supply_data else 0,
                "risk_score": risk_score,
                "risk_factors": risk_factors,
                "risk_level": "HIGH" if risk_score > 0.7 else "MEDIUM" if risk_score > 0.4 else "LOW",
                "timestamp": datetime.now().isoformat()
            }
        }

# Create detector instance
detector = RugPullDetector(API_KEY)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "ok",
        "message": "Rug Pull Detector API",
        "version": "1.0.0",
        "endpoints": {
            "health_check": "/health",
            "analyze_token": "/analyze?token=TOKEN_ADDRESS"
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv('ENVIRONMENT', 'production')
    })

@app.route('/analyze', methods=['GET'])
def analyze():
    token_address = request.args.get('token')
    
    if not token_address:
        return jsonify({
            "error": "Token address is required",
            "status": "error"
        }), 400
    
    try:
        result = detector.analyze_token(token_address)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error analyzing token: {str(e)}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

if __name__ == '__main__':
    main()
