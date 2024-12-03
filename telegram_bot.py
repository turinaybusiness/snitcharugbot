from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Initialize storage
valid_mint_addresses = []

# Function to validate mint address
def validate_mint_address(mint_address: str) -> bool:
    return len(mint_address) == 44 and mint_address.endswith("pump")

# Start command handler
async def start(update: Update, context) -> None:
    await update.message.reply_text("Welcome! Please send me your mint address.")

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