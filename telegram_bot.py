from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import os
from psycopg2 import connect
import time
import requests
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

def fetch_risk_analysis(token_address: str):
    api_url = f"https://snitcharugbot-1.onrender.com/analyze?token={token_address}"
    try:
        print(f"Fetching risk analysis for: {token_address}")  # Log the token address
        response = requests.get(api_url, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        data = response.json()
        print(f"API Response: {data}")  # Log the API response
        if data.get("status") == "success":
            return data["data"]["risk_level"], data["data"]["risk_score"], data["data"].get("risk_factors", [])
        else:
            print(f"API Error: {data.get('error', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        print(f"Network Error: {e}")  # Log network errors
    except Exception as e:
        print(f"Unexpected Error: {e}")  # Log unexpected errors
    return None, None, None

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
        [InlineKeyboardButton("Rug Pull?", callback_data="rug_pull")],
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
    elif query.data == "rug_pull":
        await query.message.reply_text("Enter Token CA to analyze:")
        context.user_data["awaiting_ca"] = "rug_pull"  # Store "rug_pull" acti
    elif query.data == "training_progress":
        await update.callback_query.message.reply_text("Training Process: 100% 🛠")

# Message handler to handle user input after button clicks
async def handle_ca_input(update: Update, context) -> None:
    mint_address = update.message.text.strip()
    action = context.user_data.get("awaiting_ca")

    # Validate if the action was properly set
    if not action:
        await update.message.reply_text("❌ Please use one of the buttons to interact with the bot.")
        return

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
    elif action == "rug_pull":
        if validate_mint_address(mint_address):
            risk_level, risk_score, risk_factors = fetch_risk_analysis(mint_address)
            if risk_level and risk_score is not None:
                await update.message.reply_text(
                    f"Risk Analysis for Token: {mint_address}\n\n"
                    f"🔹 Risk Level: {risk_level}\n"
                    f"🔹 Risk Score: {risk_score:.2f}\n"
                )
            else:
                await update.message.reply_text("❌ Failed to fetch risk analysis. Please try again later.")
        else:
            await update.message.reply_text("❌ Invalid Token Address. Please try again.")
        context.user_data["awaiting_ca"] = None  # Clear the action
    else:
        await update.message.reply_text("❌ Please use one of the buttons to interact with the bot.")

# Main function
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))  # For button clicks
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ca_input))  # For text input

    # Webhook setup
    telegram_port = int(os.getenv("TELEGRAM_PORT", 8443))  # Default to 8443

    application.run_webhook(
        listen="0.0.0.0",
        port=telegram_port,
        url_path=BOT_TOKEN,
        webhook_url=f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}",
    )

if __name__ == '__main__':
    main()