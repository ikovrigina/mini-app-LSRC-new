# 🎤 Интеграция аудио записи с Telegram

## Проблема
Веб-приложение не может надежно записывать аудио в Telegram Mini App из-за ограничений браузера и песочницы.

## Решение: Telegram Bot API

### Вариант 1: Голосовые сообщения через бота
1. Пользователь нажимает "Record" в Mini App
2. Mini App отправляет команду боту через `tg.sendData()`
3. Бот просит пользователя отправить голосовое сообщение
4. Бот получает аудио файл и сохраняет в Supabase Storage
5. Бот уведомляет Mini App о готовности аудио

### Вариант 2: Inline кнопки для записи
1. Mini App показывает Inline кнопку "🎤 Record Audio"
2. Кнопка открывает чат с ботом
3. Пользователь записывает голосовое сообщение
4. Бот обрабатывает и возвращает в Mini App

### Вариант 3: Telegram WebApp API
Использовать новые возможности Telegram WebApp для записи аудио.

## Техническая реализация

### 1. Обновить Mini App
```javascript
// В Mini App добавить функцию для запроса аудио
function requestAudioRecording(type) {
    if (tg && tg.sendData) {
        const request = {
            action: 'request_audio',
            type: type, // 'listen' или 'sound'
            session_id: currentSessionId,
            fragment_id: currentFragmentId
        };
        tg.sendData(JSON.stringify(request));
        
        // Показать пользователю инструкции
        showAudioInstructions(type);
    }
}

function showAudioInstructions(type) {
    const message = type === 'listen' 
        ? 'Теперь отправьте голосовое сообщение с тем, что вы слышите...'
        : 'Отправьте голосовое сообщение с вашим звуковым ответом...';
    
    // Показать модальное окно с инструкциями
    showModal(message);
}
```

### 2. Создать Telegram бота
```python
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
import supabase

async def handle_voice_message(update: Update, context):
    voice = update.message.voice
    user_id = update.effective_user.id
    
    # Скачать аудио файл
    file = await context.bot.get_file(voice.file_id)
    audio_data = await file.download_as_bytearray()
    
    # Сохранить в Supabase Storage
    file_path = f"audio/{user_id}/{voice.file_id}.ogg"
    supabase_client.storage.from_("audio").upload(file_path, audio_data)
    
    # Получить публичный URL
    audio_url = supabase_client.storage.from_("audio").get_public_url(file_path)
    
    # Сохранить в базу данных
    # ... код для сохранения в таблицу audio_files
    
    # Уведомить пользователя
    await update.message.reply_text("✅ Аудио записано и сохранено!")
```

### 3. Настроить Supabase Storage
```sql
-- Создать bucket для аудио
INSERT INTO storage.buckets (id, name, public) VALUES ('audio', 'audio', true);

-- Политики для аудио файлов
CREATE POLICY "Users can upload audio" ON storage.objects
FOR INSERT WITH CHECK (bucket_id = 'audio');

CREATE POLICY "Public audio access" ON storage.objects
FOR SELECT USING (bucket_id = 'audio');
```

## Преимущества Telegram подхода
- ✅ Надежная запись аудио
- ✅ Автоматическое сжатие Telegram
- ✅ Нет проблем с разрешениями браузера
- ✅ Работает на всех устройствах
- ✅ Интегрировано с экосистемой Telegram

## Недостатки
- ❌ Требует дополнительного шага (отправка в чат)
- ❌ Нужен отдельный бот
- ❌ Более сложная архитектура

## Альтернативы
1. **MediaRecorder API** с улучшенной обработкой ошибок
2. **Загрузка файлов** - пользователь загружает готовые аудио
3. **Внешние сервисы** - интеграция с SpeechToText API
