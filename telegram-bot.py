#!/usr/bin/env python3
"""
Telegram Bot для обработки голосовых сообщений
Интеграция с Mini App "listen.sound.reflect.create"
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from supabase import create_client, Client
from openai import OpenAI
import requests

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация (загружается из переменных окружения)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')
WEBAPP_URL = os.getenv('WEBAPP_URL') or os.getenv('TELEGRAM_WEBAPP_URL') or 'https://mini-app-lsrc-new.vercel.app/miniapp.html?v=2'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_ASSISTANT_ID = os.getenv('OPENAI_ASSISTANT_ID')

# Инициализация Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Инициализация OpenAI (опционально)
openai_client: OpenAI | None = None
if OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        if OPENAI_ASSISTANT_ID:
            logger.info(f"✅ OpenAI Assistant initialized: {OPENAI_ASSISTANT_ID[:20]}...")
        else:
            logger.warning("⚠️ OPENAI_ASSISTANT_ID not set")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI: {e}")

class AudioHandler:
    """Обработчик аудио файлов"""
    
    @staticmethod
    async def download_audio(bot, file_id: str) -> bytes:
        """Скачивает аудио файл из Telegram"""
        try:
            file = await bot.get_file(file_id)
            return await file.download_as_bytearray()
        except Exception as e:
            logger.error(f"Failed to download audio: {e}")
            raise
    
    @staticmethod
    async def upload_to_supabase(audio_data: bytes, user_id: int, audio_type: str) -> dict:
        """Загружает аудио в Supabase Storage"""
        try:
            # Генерируем имя файла
            timestamp = datetime.now().isoformat().replace(':', '-')
            file_name = f"{audio_type}_{user_id}_{timestamp}.ogg"
            file_path = f"audio/{file_name}"
            
            # Загружаем в Storage
            result = supabase.storage.from_("audio").upload(
                file_path, 
                audio_data,
                file_options={"content-type": "audio/ogg"}
            )
            
            if result.error:
                raise Exception(f"Upload error: {result.error}")
            
            # Получаем публичный URL
            public_url = supabase.storage.from_("audio").get_public_url(file_path)
            
            # Сохраняем метаданные в БД
            db_result = supabase.table('audio_files').insert({
                'file_name': file_name,
                'file_path': file_path,
                'file_url': public_url.data.get('publicUrl'),
                'file_size': len(audio_data),
                'mime_type': 'audio/ogg',
                'audio_type': audio_type,
                'user_id': str(user_id),
                'created_at': datetime.now().isoformat()
            }).execute()
            
            return {
                'file_name': file_name,
                'public_url': public_url.data.get('publicUrl'),
                'audio_file_id': db_result.data[0]['id'] if db_result.data else None
            }
            
        except Exception as e:
            logger.error(f"Failed to upload to Supabase: {e}")
            raise

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Создаем клавиатуру с Mini App
    keyboard = [
        [InlineKeyboardButton(
            "🎵 Open Mini App", 
            web_app={"url": WEBAPP_URL}
        )],
        [InlineKeyboardButton(
            "ℹ️ About Deep Listening", 
            callback_data="about"
        )]
    ]
    
    # Добавляем кнопку чата с Assistant, если настроен
    if OPENAI_ASSISTANT_ID and openai_client:
        keyboard.append([InlineKeyboardButton(
            "💬 Chat with Assistant",
            callback_data="start_chat"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🎵 *Welcome to Listen.Sound.Reflect.Create*

Hello {user.first_name}! This bot helps you explore Deep Listening practices inspired by Pauline Oliveros.

*How it works:*
• Open the Mini App to start a session
• Follow the Listen → Sound → Reflect → Create flow
• Send voice messages when prompted
• Your audio will be saved and processed

*Ready to begin your sonic journey?*
"""
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def about_callback(update: Update, context) -> None:
    """Информация о Deep Listening"""
    query = update.callback_query
    await query.answer()
    
    about_text = """
🎼 *About Deep Listening*

Deep Listening is a practice developed by composer Pauline Oliveros. It involves:

• *Listening* to the environment around you
• *Sounding* in response to what you hear  
• *Reflecting* on the experience
• *Creating* new sonic possibilities

This practice enhances awareness, creativity, and connection with sound environments.

*"Deep Listening is listening in every possible way to everything possible to hear no matter what you are doing."* - Pauline Oliveros
"""
    
    keyboard = [[InlineKeyboardButton("🎵 Start Session", web_app={"url": WEBAPP_URL})]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        about_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_voice_message(update: Update, context) -> None:
    """Обработчик голосовых сообщений"""
    user = update.effective_user
    voice = update.message.voice
    
    try:
        # Показываем что обрабатываем
        processing_msg = await update.message.reply_text("🎤 Processing your audio...")
        
        # Скачиваем аудио
        audio_data = await AudioHandler.download_audio(context.bot, voice.file_id)
        
        # Определяем тип аудио (по умолчанию 'reflection')
        audio_type = 'reflection'  # Можно улучшить логику определения типа
        
        # Загружаем в Supabase
        result = await AudioHandler.upload_to_supabase(audio_data, user.id, audio_type)
        
        # Уведомляем об успехе
        success_text = f"""
✅ *Audio saved successfully!*

📁 File: `{result['file_name']}`
🔗 URL: [Listen]({result['public_url']})
💾 Size: {len(audio_data)} bytes

Your audio is now part of your Deep Listening journey.
"""
        
        keyboard = [[InlineKeyboardButton("🎵 Continue in Mini App", web_app={"url": WEBAPP_URL})]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await processing_msg.edit_text(
            success_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        await update.message.reply_text(
            "❌ Sorry, there was an error processing your audio. Please try again."
        )

async def handle_audio_message(update: Update, context) -> None:
    """Обработчик аудио файлов"""
    # Аналогично голосовым сообщениям
    await handle_voice_message(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Помощь"""
    help_text = """
🎵 *Listen.Sound.Reflect.Create Bot*

*Commands:*
• `/start` - Begin your Deep Listening journey
• `/chat` - Chat with Assistant about Deep Listening
• `/help` - Show this help message

*How to use:*
1. Open the Mini App to start a session
2. Follow the guided experience
3. Send voice messages when prompted
4. Your audio will be automatically saved

*Voice Messages:*
Send voice messages anytime to save them as part of your sonic exploration.

*Need help?* The Mini App will guide you through each step of the Deep Listening process.
"""
    
    keyboard = [[InlineKeyboardButton("🎵 Open Mini App", web_app={"url": WEBAPP_URL})]]
    if OPENAI_ASSISTANT_ID and openai_client:
        keyboard.append([InlineKeyboardButton("💬 Chat with Assistant", callback_data="start_chat")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /chat для общения с Assistant"""
    user_id = update.effective_user.id
    
    if not OPENAI_ASSISTANT_ID or not openai_client:
        await update.message.reply_text(
            "⚠️ Assistant не настроен. Добавьте OPENAI_API_KEY и OPENAI_ASSISTANT_ID в переменные окружения."
        )
        return
    
    # Включаем режим чата для пользователя
    if 'user_sessions' not in context.bot_data:
        context.bot_data['user_sessions'] = {}
    if user_id not in context.bot_data['user_sessions']:
        context.bot_data['user_sessions'][user_id] = {}
    context.bot_data['user_sessions'][user_id]['chat_mode'] = True
    
    logger.info(f"✅ Chat mode enabled for user {user_id} via /chat command")
    
    await update.message.reply_text(
        "💬 Напишите ваш вопрос о Deep Listening, и я передам его моему Assistant."
    )

async def chat_with_assistant(user_text: str) -> str:
    """Отправляем текст в OpenAI Assistant и получаем ответ."""
    if not openai_client or not OPENAI_ASSISTANT_ID:
        return "⚠️ Assistant не настроен"
    
    try:
        loop = asyncio.get_event_loop()
        
        # Создаем thread для диалога
        thread = await loop.run_in_executor(
            None,
            lambda: openai_client.beta.threads.create()
        )
        
        # Добавляем сообщение пользователя
        await loop.run_in_executor(
            None,
            lambda: openai_client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_text
            )
        )
        
        # Запускаем Assistant
        run = await loop.run_in_executor(
            None,
            lambda: openai_client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=OPENAI_ASSISTANT_ID
            )
        )
        
        # Ждем ответа (максимум 60 секунд)
        timeout = 60
        elapsed = 0
        while run.status in ['queued', 'in_progress'] and elapsed < timeout:
            await asyncio.sleep(2)
            elapsed += 2
            
            run = await loop.run_in_executor(
                None,
                lambda: openai_client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            )
        
        if run.status == 'completed':
            # Получаем ответы от Assistant
            messages = await loop.run_in_executor(
                None,
                lambda: openai_client.beta.threads.messages.list(
                    thread_id=thread.id,
                    order="asc"
                )
            )
            
            # Возвращаем последнее сообщение от assistant
            for message in reversed(messages.data):
                if message.role == 'assistant':
                    content = message.content[0] if message.content else None
                    if content and hasattr(content, 'text'):
                        return content.text.value
            
            return "❌ Ответ не получен от Assistant"
        else:
            logger.error(f"Assistant run failed: {run.status}")
            return f"❌ Ошибка: {run.status}"
            
    except Exception as e:
        logger.error(f"Ошибка работы с Assistant: {e}", exc_info=True)
        return f"❌ Ошибка: {str(e)}"

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    
    # Проверяем, находится ли пользователь в режиме чата с Assistant
    if context.bot_data.get('user_sessions', {}).get(user_id, {}).get('chat_mode', False):
        user_text = update.message.text
        logger.info(f"💬 Chat mode activated for user {user_id}: {user_text[:50]}")
        
        # Показываем индикатор набора
        thinking_msg = await update.message.reply_text("🤔 Думаю...")
        
        try:
            # Отправляем в Assistant
            assistant_response = await chat_with_assistant(user_text)
            logger.info(f"✅ Assistant response received for user {user_id}")
            
            # Удаляем индикатор и отправляем ответ
            await thinking_msg.delete()
            await update.message.reply_text(assistant_response)
            
            # Спрашиваем, хочет ли пользователь продолжить
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Задать еще вопрос", callback_data="continue_chat")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ])
            await update.message.reply_text(
                "Хотите продолжить разговор или вернуться в главное меню?",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"❌ Error in chat_with_assistant for user {user_id}: {e}", exc_info=True)
            await thinking_msg.delete()
            await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")
    else:
        # Обычное сообщение - показываем помощь
        await update.message.reply_text(
            "Привет! Используйте /start для начала или /help для помощи."
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == "start_chat":
        if not OPENAI_ASSISTANT_ID or not openai_client:
            await query.answer("⚠️ Assistant не настроен", show_alert=True)
            return
        
        # Включаем режим чата
        if 'user_sessions' not in context.bot_data:
            context.bot_data['user_sessions'] = {}
        if user_id not in context.bot_data['user_sessions']:
            context.bot_data['user_sessions'][user_id] = {}
        context.bot_data['user_sessions'][user_id]['chat_mode'] = True
        
        logger.info(f"✅ Chat mode enabled for user {user_id} via button")
        
        await query.edit_message_text(
            "💬 Напишите ваш вопрос о Deep Listening, и я передам его моему Assistant."
        )
    
    elif query.data == "continue_chat":
        # Сохраняем режим чата
        if 'user_sessions' not in context.bot_data:
            context.bot_data['user_sessions'] = {}
        if user_id not in context.bot_data['user_sessions']:
            context.bot_data['user_sessions'][user_id] = {}
        context.bot_data['user_sessions'][user_id]['chat_mode'] = True
        
        await query.edit_message_text(
            "💬 Напишите ваш следующий вопрос о Deep Listening:"
        )
    
    elif query.data == "main_menu":
        # Выключаем режим чата
        if 'user_sessions' in context.bot_data and user_id in context.bot_data['user_sessions']:
            context.bot_data['user_sessions'][user_id]['chat_mode'] = False
        
        keyboard = [
            [InlineKeyboardButton("🎵 Open Mini App", web_app={"url": WEBAPP_URL})],
            [InlineKeyboardButton("ℹ️ About Deep Listening", callback_data="about")]
        ]
        
        if OPENAI_ASSISTANT_ID and openai_client:
            keyboard.append([InlineKeyboardButton("💬 Chat with Assistant", callback_data="start_chat")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
🎵 *Welcome to Listen.Sound.Reflect.Create*

Hello {query.from_user.first_name}! This bot helps you explore Deep Listening practices.

*Ready to begin your sonic journey?*
"""
        await query.edit_message_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

def main():
    """Запуск бота"""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Supabase credentials not set!")
        return
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("chat", chat_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CallbackQueryHandler(about_callback, pattern="about"))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Запускаем бота
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
