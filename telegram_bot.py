from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import os
from psycopg2 import connect

# Load environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to the database
conn = connect(DATABASE_URL)
cur = conn.cursor()

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
        # Insert the address or increment the sent_count
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
    await update.message.reply_text(
        "🤖 Welcome to the Pazyryk Rug Snitch Bot! 🤖\n\n"
        "➡️ Help train Pazyryk by reporting old rugs 🧵.\n"
        "➡️ The more rugs Pazyryk learns about, the more accurate it becomes 🚀.\n\n"
        "✅ Visit Pazyryk's website for more details.\n\n"
        "🚨 Enter the rug's CA (Contract Address) to report it! 🚨"
    )

# Message handler to process mint addresses
async def process_address(update: Update, context) -> None:
    mint_address = update.message.text.strip()
    
    if validate_mint_address(mint_address):
        save_mint_address(mint_address)  # Save to DB or increment count
        count = get_address_count(mint_address)  # Fetch the updated count
        await update.message.reply_text(f"Valid mint address! It has been sent to this bot {count} times.")
    else:
        await update.message.reply_text("Invalid mint address. Ensure it is 44 characters long and ends with 'pump'.")

# Main function
def main():
    # Replace 'YOUR_TOKEN_HERE' with your bot's token
    application = Application.builder().token("8170738721:AAHXFA2z0nctgDG0bkFSudAWv2CoZ75CzKQ").build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_address))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()