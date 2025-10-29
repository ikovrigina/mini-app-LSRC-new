// API endpoint для получения конфигурации из переменных окружения Vercel
export default function handler(req, res) {
  // Устанавливаем CORS заголовки
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  try {
    const config = {
      SUPABASE_URL: process.env.SUPABASE_URL || '',
      SUPABASE_ANON_KEY: process.env.SUPABASE_ANON_KEY || '',
      VERCEL_URL: process.env.VERCEL_URL || '',
      TELEGRAM_BOT_USERNAME: process.env.TELEGRAM_BOT_USERNAME || 'ListenSoundReflectCreateBot',
      MAX_AUDIO_FILE_SIZE_MB: process.env.MAX_AUDIO_FILE_SIZE_MB || '10',
      ALLOWED_AUDIO_FORMATS: process.env.ALLOWED_AUDIO_FORMATS || 'webm,wav,mp3,m4a',
      AUDIO_STORAGE_BUCKET: process.env.AUDIO_STORAGE_BUCKET || 'audio',
      DEFAULT_LANGUAGE: process.env.DEFAULT_LANGUAGE || 'en',
      ENABLE_ANALYTICS: process.env.ENABLE_ANALYTICS || 'false',
      DEBUG_MODE: process.env.DEBUG_MODE || 'false'
    };

    // Не отправляем пустые значения
    const filteredConfig = {};
    Object.keys(config).forEach(key => {
      if (config[key] && config[key] !== '') {
        filteredConfig[key] = config[key];
      }
    });

    res.status(200).json(filteredConfig);
  } catch (error) {
    console.error('Config API error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}
