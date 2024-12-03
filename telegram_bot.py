from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import os
from psycopg2 import connect

# Load environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to the database
conn = connect(DATABASE_URL)
cur = conn.cursor()

# Example query
cur.execute("SELECT 1")
print(cur.fetchone())
# Initialize storage
valid_mint_addresses = []

# Function to validate mint address
def validate_mint_address(mint_address: str) -> bool:
    return len(mint_address) == 44 and mint_address.endswith("pump")

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
        valid_mint_addresses.append(mint_address)
        await update.message.reply_text("Valid mint address! It has been saved.")
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