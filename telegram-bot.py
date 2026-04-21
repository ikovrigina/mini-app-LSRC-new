#!/usr/bin/env python3
"""
LSRC Telegram Bot — Only Humans
Daily score push + weekly digest + OpenAI Assistant + Mini App integration
"""

import os
import asyncio
import logging
import random
from datetime import datetime, time, timedelta
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from supabase import create_client, Client
from openai import OpenAI
import requests

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')
WEBAPP_URL = (
    os.getenv('WEBAPP_URL')
    or os.getenv('TELEGRAM_WEBAPP_URL')
    or 'https://mini-app-lsrc-new.vercel.app/miniapp.html?v=3'
)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_ASSISTANT_ID = os.getenv('OPENAI_ASSISTANT_ID')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

openai_client: OpenAI | None = None
if OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        if OPENAI_ASSISTANT_ID:
            logger.info(f"OpenAI Assistant initialized: {OPENAI_ASSISTANT_ID[:20]}...")
        else:
            logger.warning("OPENAI_ASSISTANT_ID not set")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI: {e}")


# ============================================================
# AUDIO HANDLER
# ============================================================

class AudioHandler:
    @staticmethod
    async def download_audio(bot, file_id: str) -> bytes:
        try:
            file = await bot.get_file(file_id)
            return await file.download_as_bytearray()
        except Exception as e:
            logger.error(f"Failed to download audio: {e}")
            raise

    @staticmethod
    async def upload_to_supabase(audio_data: bytes, user_id: int, audio_type: str) -> dict:
        try:
            timestamp = datetime.now().isoformat().replace(':', '-')
            file_name = f"{audio_type}_{user_id}_{timestamp}.ogg"
            file_path = f"audio/{file_name}"

            supabase.storage.from_("audio").upload(
                file_path, audio_data,
                file_options={"content-type": "audio/ogg"}
            )

            public_url = f"{SUPABASE_URL}/storage/v1/object/public/audio/{file_path}"

            db_result = supabase.table('audio_files').insert({
                'file_name': file_name,
                'file_path': file_path,
                'file_url': public_url,
                'file_size': len(audio_data),
                'mime_type': 'audio/ogg',
                'user_id': str(user_id),
            }).execute()

            return {
                'file_name': file_name,
                'public_url': public_url,
                'audio_file_id': db_result.data[0]['id'] if db_result.data else None
            }
        except Exception as e:
            logger.error(f"Failed to upload to Supabase: {e}")
            raise


# ============================================================
# OPENAI ASSISTANT CHAT
# ============================================================

async def chat_with_assistant(user_text: str) -> str:
    if not openai_client or not OPENAI_ASSISTANT_ID:
        return "Assistant not configured."

    try:
        loop = asyncio.get_event_loop()

        thread = await loop.run_in_executor(
            None, lambda: openai_client.beta.threads.create()
        )

        await loop.run_in_executor(
            None, lambda: openai_client.beta.threads.messages.create(
                thread_id=thread.id, role="user", content=user_text
            )
        )

        run = await loop.run_in_executor(
            None, lambda: openai_client.beta.threads.runs.create(
                thread_id=thread.id, assistant_id=OPENAI_ASSISTANT_ID
            )
        )

        elapsed = 0
        while run.status in ['queued', 'in_progress'] and elapsed < 60:
            await asyncio.sleep(2)
            elapsed += 2
            run = await loop.run_in_executor(
                None, lambda: openai_client.beta.threads.runs.retrieve(
                    thread_id=thread.id, run_id=run.id
                )
            )

        if run.status == 'completed':
            messages = await loop.run_in_executor(
                None, lambda: openai_client.beta.threads.messages.list(
                    thread_id=thread.id, order="asc"
                )
            )
            for message in reversed(messages.data):
                if message.role == 'assistant':
                    content = message.content[0] if message.content else None
                    if content and hasattr(content, 'text'):
                        return content.text.value
            return "No response received."
        else:
            logger.error(f"Assistant run failed: {run.status}")
            return f"Error: {run.status}"

    except Exception as e:
        logger.error(f"Assistant error: {e}", exc_info=True)
        return f"Error: {str(e)}"


# ============================================================
# DAILY PUSH
# ============================================================

PUSH_HOOKS = [
    "Someone wrote this for you. Now it's your turn.",
    "A human created this. Can you hear it?",
    "This began with someone listening. Continue the chain.",
    "20 seconds. One score. Your turn.",
    "Before your next task — listen.",
]


async def get_random_score_for_push() -> Optional[dict]:
    try:
        result = supabase.table('scores').select('id, text, created_at').eq(
            'is_public', True
        ).limit(50).execute()
        if result.data:
            return random.choice(result.data)
    except Exception as e:
        logger.error(f"Failed to fetch score for push: {e}")
    return None


async def get_all_user_ids() -> list[str]:
    try:
        result = supabase.table('capsules').select('user_id').execute()
        if result.data:
            return list(set(r['user_id'] for r in result.data if r['user_id']))
    except Exception as e:
        logger.error(f"Failed to fetch user IDs: {e}")
    return []


def format_days_ago(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        created = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        diff = datetime.now(created.tzinfo) - created
        days = diff.days
        if days == 0:
            return "today"
        if days == 1:
            return "yesterday"
        return f"{days} days ago"
    except Exception:
        return ""


async def send_daily_push(context: ContextTypes.DEFAULT_TYPE) -> None:
    score = await get_random_score_for_push()
    if not score:
        logger.warning("No score found for daily push")
        return

    user_ids = await get_all_user_ids()
    if not user_ids:
        logger.info("No users to push to")
        return

    days_ago = format_days_ago(score.get('created_at', ''))
    hook = random.choice(PUSH_HOOKS)
    meta = f"Created by a human {days_ago}." if days_ago else ""

    text = f'"{score["text"]}"\n\n{meta}\n\n{hook}'

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Listen", web_app={"url": WEBAPP_URL})]
    ])

    sent = 0
    for uid in user_ids:
        try:
            chat_id = int(uid)
        except (ValueError, TypeError):
            continue
        try:
            await context.bot.send_message(
                chat_id=chat_id, text=text, reply_markup=keyboard
            )
            sent += 1
        except Exception as e:
            logger.warning(f"Push failed for {uid}: {e}")

    logger.info(f"Daily push sent to {sent}/{len(user_ids)} users")


# ============================================================
# WEEKLY DIGEST
# ============================================================

async def send_weekly_digest(context: ContextTypes.DEFAULT_TYPE) -> None:
    user_ids = await get_all_user_ids()
    if not user_ids:
        return

    sent = 0
    for uid in user_ids:
        try:
            result = supabase.table('scores').select(
                'id, text, usage_count'
            ).eq('author_user_id', uid).eq('is_public', True).execute()

            scores = result.data or []
            heard = [s for s in scores if (s.get('usage_count') or 0) > 0]
            if not heard:
                continue

            total_listens = sum(s.get('usage_count', 0) for s in heard)
            top = max(heard, key=lambda s: s.get('usage_count', 0))

            text = (
                f"This week, your scores were heard {total_listens} time{'s' if total_listens != 1 else ''}.\n\n"
                f'Your most heard score:\n"{top["text"]}"\n\n'
                f"Someone is listening. Keep creating."
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Listen", web_app={"url": WEBAPP_URL})]
            ])

            try:
                chat_id = int(uid)
            except (ValueError, TypeError):
                continue

            await context.bot.send_message(
                chat_id=chat_id, text=text, reply_markup=keyboard
            )
            sent += 1
        except Exception as e:
            logger.warning(f"Digest failed for {uid}: {e}")

    logger.info(f"Weekly digest sent to {sent} users")


# ============================================================
# COMMAND HANDLERS
# ============================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    keyboard = [
        [InlineKeyboardButton("Listen", web_app={"url": WEBAPP_URL})],
        [InlineKeyboardButton("About", callback_data="about")]
    ]
    if OPENAI_ASSISTANT_ID and openai_client:
        keyboard.append([InlineKeyboardButton("Chat with guide", callback_data="start_chat")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"*LSRC — Only Humans*\n\n"
        f"Hello {user.first_name}.\n\n"
        f"Take a score written by another human.\n"
        f"Listen through it. Respond with sound.\n"
        f"Reflect. Create your own score.\n\n"
        f"No algorithm can do this. Only you."
    )

    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "*LSRC*\n\n"
        "/start — begin\n"
        "/chat — talk to the guide\n"
        "/help — this message\n\n"
        "Open the app, press Listen, and follow the flow."
    )
    keyboard = [[InlineKeyboardButton("Listen", web_app={"url": WEBAPP_URL})]]
    if OPENAI_ASSISTANT_ID and openai_client:
        keyboard.append([InlineKeyboardButton("Chat with guide", callback_data="start_chat")])
    await update.message.reply_text(
        text, parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if not OPENAI_ASSISTANT_ID or not openai_client:
        await update.message.reply_text(
            "Guide is not configured. Add OPENAI_API_KEY and OPENAI_ASSISTANT_ID."
        )
        return

    if 'user_sessions' not in context.bot_data:
        context.bot_data['user_sessions'] = {}
    if user_id not in context.bot_data['user_sessions']:
        context.bot_data['user_sessions'][user_id] = {}
    context.bot_data['user_sessions'][user_id]['chat_mode'] = True

    await update.message.reply_text(
        "Ask me anything about Deep Listening, Pauline Oliveros, or this practice."
    )


async def about_callback(update: Update, context) -> None:
    query = update.callback_query
    await query.answer()

    text = (
        "*About LSRC*\n\n"
        "Deep Listening — a practice by Pauline Oliveros.\n\n"
        "You receive a score (a listening instruction written by a human). "
        "You listen to the world through it. You respond with sound. "
        "You reflect. You create a new score.\n\n"
        "Your score enters the flow. Someone else will begin where you ended.\n\n"
        "_\"Deep Listening is listening in every possible way to everything "
        "possible to hear no matter what you are doing.\"_\n"
        "— Pauline Oliveros"
    )

    keyboard = [[InlineKeyboardButton("Listen", web_app={"url": WEBAPP_URL})]]
    await query.edit_message_text(
        text, parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_voice_message(update: Update, context) -> None:
    user = update.effective_user
    voice = update.message.voice or update.message.audio

    if not voice:
        await update.message.reply_text("Could not process this audio.")
        return

    try:
        processing_msg = await update.message.reply_text("Processing your audio...")

        file_id = voice.file_id
        audio_data = await AudioHandler.download_audio(context.bot, file_id)
        result = await AudioHandler.upload_to_supabase(audio_data, user.id, 'voice_message')

        success_text = (
            f"Audio saved.\n\n"
            f"File: `{result['file_name']}`\n"
            f"Size: {len(audio_data)} bytes"
        )

        keyboard = [[InlineKeyboardButton("Open app", web_app={"url": WEBAPP_URL})]]
        await processing_msg.edit_text(
            success_text, parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        await update.message.reply_text("Sorry, there was an error processing your audio.")


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if context.bot_data.get('user_sessions', {}).get(user_id, {}).get('chat_mode', False):
        user_text = update.message.text
        thinking_msg = await update.message.reply_text("thinking...")

        try:
            assistant_response = await chat_with_assistant(user_text)
            await thinking_msg.delete()
            await update.message.reply_text(assistant_response)

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Ask another question", callback_data="continue_chat")],
                [InlineKeyboardButton("Back to menu", callback_data="main_menu")]
            ])
            await update.message.reply_text(
                "Continue the conversation or go back?",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Chat error for user {user_id}: {e}", exc_info=True)
            await thinking_msg.delete()
            await update.message.reply_text(f"Error: {str(e)}")
    else:
        await update.message.reply_text(
            "Use /start to begin, or /chat to talk to the guide.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Listen", web_app={"url": WEBAPP_URL})]
            ])
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "about":
        await about_callback(update, context)

    elif query.data == "start_chat":
        if not OPENAI_ASSISTANT_ID or not openai_client:
            await query.answer("Guide not configured", show_alert=True)
            return

        if 'user_sessions' not in context.bot_data:
            context.bot_data['user_sessions'] = {}
        if user_id not in context.bot_data['user_sessions']:
            context.bot_data['user_sessions'][user_id] = {}
        context.bot_data['user_sessions'][user_id]['chat_mode'] = True

        await query.edit_message_text(
            "Ask me anything about Deep Listening, Pauline Oliveros, or this practice."
        )

    elif query.data == "continue_chat":
        if 'user_sessions' not in context.bot_data:
            context.bot_data['user_sessions'] = {}
        if user_id not in context.bot_data['user_sessions']:
            context.bot_data['user_sessions'][user_id] = {}
        context.bot_data['user_sessions'][user_id]['chat_mode'] = True

        await query.edit_message_text("Ask your next question:")

    elif query.data == "main_menu":
        if 'user_sessions' in context.bot_data and user_id in context.bot_data['user_sessions']:
            context.bot_data['user_sessions'][user_id]['chat_mode'] = False

        keyboard = [
            [InlineKeyboardButton("Listen", web_app={"url": WEBAPP_URL})],
            [InlineKeyboardButton("About", callback_data="about")]
        ]
        if OPENAI_ASSISTANT_ID and openai_client:
            keyboard.append([InlineKeyboardButton("Chat with guide", callback_data="start_chat")])

        await query.edit_message_text(
            "*LSRC — Only Humans*\n\nReady to listen?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ============================================================
# MAIN
# ============================================================

def main():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Supabase credentials not set!")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("chat", chat_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    job_queue = application.job_queue
    if job_queue:
        job_queue.run_daily(send_daily_push, time=time(hour=12, minute=0))
        logger.info("Scheduled daily push at 12:00 UTC")

        job_queue.run_daily(
            send_weekly_digest,
            time=time(hour=10, minute=0),
            days=(0,),
        )
        logger.info("Scheduled weekly digest for Mondays at 10:00 UTC")
    else:
        logger.warning("JobQueue not available — scheduled jobs disabled")

    logger.info("LSRC bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
