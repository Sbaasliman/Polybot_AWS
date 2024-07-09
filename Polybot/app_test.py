import telebot
import os
TELEGRAM_TOKEN = '6322883166:AAF2vDsEr-j62GEKHFiDl-WhpJt9pEQX7g4'
TELEGRAM_CHAT_URL = 'https://atech-bot.click'  # Replace with your actual URL
PATH_CERT = '/app/PUBLIC.pem'  # Replace with the correct path in your environment
try:
    bot = telebot.TeleBot(TELEGRAM_TOKEN)

    # Ensure path_cert exists and is accessible
    if os.path.exists(PATH_CERT):
        with open(PATH_CERT, 'rb') as cert_file:
            result = bot.set_webhook(url=f'{TELEGRAM_CHAT_URL}/{TELEGRAM_TOKEN}/', timeout=60, certificate=cert_file)
            print("Webhook set successfully:", result)
    else:
        print("Error: Certificate file not found at", PATH_CERT)

except Exception as e:
    print("Error setting webhook:", e)
