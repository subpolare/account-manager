import os
import logging
from zoneinfo import ZoneInfo
from datetime import datetime
import time
from dotenv import load_dotenv
import telebot
from telebot import apihelper
from apscheduler.schedulers.background import BackgroundScheduler
from requests.exceptions import RequestException, ReadTimeout, ConnectTimeout
from apscheduler.triggers.cron import CronTrigger

from digest import generate_digest

apihelper.CONNECT_TIMEOUT = 15
apihelper.READ_TIMEOUT = 60

logging.basicConfig(level = logging.INFO)
TZ = 'Europe/Moscow'

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
DIGEST_CHAT_ID = os.getenv('DIGEST_CHAT_ID')

bot = telebot.TeleBot(TOKEN, parse_mode = 'HTML')

def send_with_retry(chat_id, text, attempts = 3):
    for i in range(1, attempts + 1):
        try:
            bot.send_message(chat_id, text, disable_web_page_preview = True, timeout = 60, parse_mode = 'Markdown')
            return
        except (ReadTimeout, ConnectTimeout, RequestException) as e:
            if i == attempts:
                raise
            time.sleep(2 ** i)

def send_long_message(chat_id, text):
    limit = 4000
    if len(text) <= limit:
        send_with_retry(chat_id, text)
        return
    start = 0
    while start < len(text):
        send_with_retry(chat_id, text[start:start + limit])
        start += limit

def job_send_digest():
    try:
        digest = generate_digest()
        timestamp = datetime.now(ZoneInfo(TZ)).strftime('%Y-%m-%d %H:%M')
        logging.info('digest @ %s: %d chars', timestamp, len(digest))
        send_long_message(DIGEST_CHAT_ID, digest)
    except Exception as e:
        logging.exception('digest job failed: %s', e)
        bot.send_message(DIGEST_CHAT_ID, f'⚠️ Ошибка при генерации дайджеста: {e}')

@bot.message_handler(commands = ['digest'])
def cmd_digest(message):
    try:
        digest = generate_digest()
        send_long_message(message.chat.id, digest)
    except Exception as e:
        logging.exception('/digest failed: %s', e)
        bot.reply_to(message, f'⚠️ Ошибка: {e}')

@bot.message_handler(commands = ['id'])
def cmd_id(message):
    bot.reply_to(message, f'chat_id: <code>{message.chat.id}</code>')

sched = BackgroundScheduler(timezone = TZ)
sched.add_job(job_send_digest, CronTrigger(hour = 9, minute = 0))
sched.start()

if __name__ == '__main__':
    logging.info('Bot started, timezone = %s', TZ)
    bot.infinity_polling(skip_pending = True)
