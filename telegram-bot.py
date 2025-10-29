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
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from supabase import create_client, Client
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
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://listen-sound-reflect-create.vercel.app/')

# Инициализация Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

async def start_command(update: Update, context) -> None:
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

async def help_command(update: Update, context) -> None:
    """Помощь"""
    help_text = """
🎵 *Listen.Sound.Reflect.Create Bot*

*Commands:*
• `/start` - Begin your Deep Listening journey
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
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        help_text,
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
    application.add_handler(CallbackQueryHandler(about_callback, pattern="about"))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio_message))
    
    # Запускаем бота
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
