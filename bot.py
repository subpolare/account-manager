from datetime import time as dtime
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import asyncio, logging, os

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    Defaults,
)

from functions.digest import generate_digest

load_dotenv()
BOT_TOKEN      = os.getenv('TELEGRAM_TOKEN')
TZ             = os.getenv('TZ', 'Europe/Moscow')
DIGEST_CHAT_ID = os.getenv('DIGEST_CHAT_ID')

logging.basicConfig(
    format = '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    level  = logging.INFO,
)
logger = logging.getLogger('bot')
MAX_CHUNK = 3500


def chunk_text(text: str, size: int = MAX_CHUNK):
    for i in range(0, len(text), size):
        yield text[i : i + size]


async def send_long_message(ctx: ContextTypes.DEFAULT_TYPE, chat_id: int | str, text: str):
    for part in chunk_text(text):
        try:
            await ctx.bot.send_chat_action(chat_id, ChatAction.TYPING)
            await ctx.bot.send_message(
                chat_id                  = chat_id,
                text                     = part,
                disable_web_page_preview = True,
                parse_mode               = 'Markdown',
            )
        except Exception:
            logger.exception('send_long_message: failed to send chunk')
            try:
                await ctx.bot.send_message(chat_id=chat_id, text=part, parse_mode=None)
            except Exception:
                logger.exception('send_long_message: fallback also failed')
                raise

async def cmd_digest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        digest = await asyncio.to_thread(generate_digest)
        await send_long_message(context, update.effective_chat.id, digest)
    except Exception as e:
        logger.exception('/digest failed: %s', e)
        await update.message.reply_html(f'⚠️ Ошибка: <code>{e}</code>')

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(f'chat_id: <code>{update.effective_chat.id}</code>')

async def job_send_digest(context: ContextTypes.DEFAULT_TYPE):
    try:
        digest = await asyncio.to_thread(generate_digest)
        ts_tz = ZoneInfo(TZ)
        logger.info('digest: len = %d tz = %s', len(digest), ts_tz.key)
        await send_long_message(context, DIGEST_CHAT_ID, digest)
    except Exception as e:
        logger.exception('digest job failed: %s', e)
        try:
            await context.bot.send_message(DIGEST_CHAT_ID, f'⚠️ Ошибка при генерации дайджеста: {e}')
        except Exception:
            logger.exception('failed to notify about digest failure')

async def on_startup(app: Application):
    logger.info('Bot started, timezone = %s', TZ)


def build_app() -> Application:
    if not BOT_TOKEN:
        raise RuntimeError('Не задан BOT_TOKEN в окружении')

    defaults = Defaults(parse_mode=ParseMode.HTML, tzinfo=ZoneInfo(TZ))

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .defaults(defaults)
        .post_init(on_startup)
        .build()
    )

    application.add_handler(CommandHandler('digest', cmd_digest))
    application.add_handler(CommandHandler('id', cmd_id))

    if DIGEST_CHAT_ID:
        application.job_queue.run_daily(
            job_send_digest,
            time = dtime(hour = 9, minute = 0, tzinfo = ZoneInfo(TZ)),
            name = 'daily_digest',
        )
        logger.info('Job scheduled: 09:00 %s -> chat %s', TZ, DIGEST_CHAT_ID)
    else:
        logger.warning('DIGEST_CHAT_ID не задан — ежедневный дайджест отключён')

    async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.exception('Unhandled error: %s', context.error)

    application.add_error_handler(on_error)
    application.post_init(on_startup)

    return application

if __name__ == '__main__':
    app = build_app()
    app.run_polling(allowed_updates = Update.ALL_TYPES, drop_pending_updates=True)