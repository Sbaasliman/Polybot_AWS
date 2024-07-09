import telebot
import os
TELEGRAM_TOKEN = ''
TELEGRAM_CHAT_URL = 'https://sabaa.atech-bot.click'  # Replace with your actual URL
PATH_CERT = 'PUBLIC.pem'  # Replace with the correct path in your environment
try:
    bot = telebot.TeleBot(TELEGRAM_TOKEN)

    # Ensure path_cert exists and is accessible
    if os.path.exists(PATH_CERT):
        with open(PATH_CERT, 'rb') as cert_file:
            result = bot.set_webhook(url=f'{TELEGRAM_CHAT_URL}/{TELEGRAM_TOKEN}/', certificate = open(PATH_CERT, 'r'),  timeout=60)
            print("Webhook set successfully:", result)
    else:
        print("Error: Certificate file not found at", PATH_CERT)

except Exception as e:
    print("Error setting webhook:", e)
