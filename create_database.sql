-- ========================================
-- Listen.Sound.Reflect.Create - Database Schema
-- Created: 2025-10-22
-- ========================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- 1. Таблица: scores (Текстовые скоры)
-- ========================================

CREATE TABLE scores (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  text TEXT NOT NULL,
  author_user_id TEXT,
  author_name TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  is_public BOOLEAN DEFAULT true,
  source TEXT NOT NULL DEFAULT 'user_created',
  language TEXT DEFAULT 'en',
  tags TEXT[],
  usage_count INTEGER DEFAULT 0
);

-- Индексы для scores
CREATE INDEX idx_scores_public ON scores(is_public, created_at DESC);
CREATE INDEX idx_scores_source ON scores(source);
CREATE INDEX idx_scores_author ON scores(author_user_id);

-- Комментарии
COMMENT ON TABLE scores IS 'База данных текстовых скоров (scores)';
COMMENT ON COLUMN scores.source IS 'Источник: user_created, oliveros_original, community';

-- ========================================
-- 2. Таблица: audio_files (Аудио файлы)
-- ========================================

CREATE TABLE audio_files (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  file_name TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_url TEXT NOT NULL,
  file_size INTEGER NOT NULL,
  duration_seconds FLOAT,
  mime_type TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  user_id TEXT NOT NULL
);

-- Индексы для audio_files
CREATE INDEX idx_audio_files_user ON audio_files(user_id);
CREATE INDEX idx_audio_files_created ON audio_files(created_at DESC);

-- Комментарии
COMMENT ON TABLE audio_files IS 'Хранилище всех аудио файлов';

-- ========================================
-- 3. Таблица: capsules (Капсулы/Сессии)
-- ========================================

CREATE TABLE capsules (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  initial_score_id UUID NOT NULL REFERENCES scores(id),
  final_score_id UUID REFERENCES scores(id),
  is_public BOOLEAN DEFAULT true,
  transport TEXT DEFAULT 'telegram_webapp'
);

-- Индексы для capsules
CREATE INDEX idx_capsules_user ON capsules(user_id);
CREATE INDEX idx_capsules_created ON capsules(created_at DESC);
CREATE INDEX idx_capsules_initial_score ON capsules(initial_score_id);
CREATE INDEX idx_capsules_final_score ON capsules(final_score_id);

-- Комментарии
COMMENT ON TABLE capsules IS 'Капсулы - завершенные сессии пользователей';
COMMENT ON COLUMN capsules.initial_score_id IS 'Скор, с которого началась сессия';
COMMENT ON COLUMN capsules.final_score_id IS 'Скор, который создал пользователь в конце';

-- ========================================
-- 4. Таблица: fragments (Фрагменты)
-- ========================================

CREATE TABLE fragments (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  capsule_id UUID NOT NULL REFERENCES capsules(id) ON DELETE CASCADE,
  cycle_number INTEGER NOT NULL,
  listen_source TEXT NOT NULL,
  listen_audio_id UUID REFERENCES audio_files(id),
  sound_audio_id UUID REFERENCES audio_files(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для fragments
CREATE INDEX idx_fragments_capsule ON fragments(capsule_id);
CREATE INDEX idx_fragments_cycle ON fragments(capsule_id, cycle_number);

-- Комментарии
COMMENT ON TABLE fragments IS 'Фрагменты - пары Listen/Sound в сессии';
COMMENT ON COLUMN fragments.listen_source IS 'Источник: environment, past_capsule';

-- ========================================
-- 5. Таблица: reflections (Рефлексии)
-- ========================================

CREATE TABLE reflections (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  fragment_id UUID NOT NULL REFERENCES fragments(id) ON DELETE CASCADE,
  audio_id UUID REFERENCES audio_files(id),
  text TEXT NOT NULL,
  keywords TEXT[],
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  transcription_source TEXT NOT NULL
);

-- Индексы для reflections
CREATE INDEX idx_reflections_fragment ON reflections(fragment_id);
CREATE INDEX idx_reflections_audio ON reflections(audio_id);

-- Комментарии
COMMENT ON TABLE reflections IS 'Рефлексии пользователей для каждого фрагмента';
COMMENT ON COLUMN reflections.transcription_source IS 'Источник текста: user_typed, audio_transcribed';

-- ========================================
-- Row Level Security (RLS)
-- ========================================

-- Включаем RLS для всех таблиц
ALTER TABLE scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE audio_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE capsules ENABLE ROW LEVEL SECURITY;
ALTER TABLE fragments ENABLE ROW LEVEL SECURITY;
ALTER TABLE reflections ENABLE ROW LEVEL SECURITY;

-- Политики для scores (публичные скоры доступны всем)
CREATE POLICY "Public scores are viewable by everyone"
  ON scores FOR SELECT
  USING (is_public = true);

CREATE POLICY "Users can insert their own scores"
  ON scores FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Users can update their own scores"
  ON scores FOR UPDATE
  USING (author_user_id = current_setting('app.current_user_id', true));

-- Политики для audio_files (пользователи видят только свои файлы)
CREATE POLICY "Users can view their own audio files"
  ON audio_files FOR SELECT
  USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can insert their own audio files"
  ON audio_files FOR INSERT
  WITH CHECK (user_id = current_setting('app.current_user_id', true));

-- Политики для capsules
CREATE POLICY "Users can view their own capsules"
  ON capsules FOR SELECT
  USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Public capsules are viewable by everyone"
  ON capsules FOR SELECT
  USING (is_public = true);

CREATE POLICY "Users can insert their own capsules"
  ON capsules FOR INSERT
  WITH CHECK (user_id = current_setting('app.current_user_id', true));

-- Политики для fragments
CREATE POLICY "Users can view fragments of their capsules"
  ON fragments FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM capsules
      WHERE capsules.id = fragments.capsule_id
      AND capsules.user_id = current_setting('app.current_user_id', true)
    )
  );

CREATE POLICY "Users can insert fragments for their capsules"
  ON fragments FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM capsules
      WHERE capsules.id = fragments.capsule_id
      AND capsules.user_id = current_setting('app.current_user_id', true)
    )
  );

-- Политики для reflections
CREATE POLICY "Users can view reflections of their fragments"
  ON reflections FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM fragments
      JOIN capsules ON capsules.id = fragments.capsule_id
      WHERE fragments.id = reflections.fragment_id
      AND capsules.user_id = current_setting('app.current_user_id', true)
    )
  );

CREATE POLICY "Users can insert reflections for their fragments"
  ON reflections FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM fragments
      JOIN capsules ON capsules.id = fragments.capsule_id
      WHERE fragments.id = reflections.fragment_id
      AND capsules.user_id = current_setting('app.current_user_id', true)
    )
  );

-- ========================================
-- Начальные данные (seed data)
-- ========================================

-- Добавляем базовые скоры от Полин Оливерос
INSERT INTO scores (text, source, is_public, language) VALUES
  ('Walk so silently that the bottoms of your feet become ears.', 'oliveros_original', true, 'en'),
  ('Listen to a sound until you no longer recognize it.', 'oliveros_original', true, 'en'),
  ('Take a walk at night. Walk so silently that the bottoms of your feet become ears.', 'oliveros_original', true, 'en'),
  ('Breathe with the echo of your own steps.', 'community', true, 'en'),
  ('Listen to the space between sounds.', 'community', true, 'en'),
  ('Close your eyes and become aware of all the sounds around you.', 'community', true, 'en'),
  ('Make a sound that no one has ever heard before.', 'oliveros_original', true, 'en'),
  ('Listen to the sound of your breath as if you are listening to music.', 'community', true, 'en')
ON CONFLICT DO NOTHING;

-- ========================================
-- Функции (Functions)
-- ========================================

-- Функция для обновления usage_count скора
CREATE OR REPLACE FUNCTION increment_score_usage(score_id UUID)
RETURNS void AS $$
BEGIN
  UPDATE scores
  SET usage_count = usage_count + 1
  WHERE id = score_id;
END;
$$ LANGUAGE plpgsql;

-- Функция для получения случайного скора
CREATE OR REPLACE FUNCTION get_random_score()
RETURNS scores AS $$
  SELECT * FROM scores
  WHERE is_public = true
  ORDER BY RANDOM()
  LIMIT 1;
$$ LANGUAGE sql;

-- ========================================
-- Триггеры (Triggers)
-- ========================================

-- Триггер для автоматического увеличения usage_count при создании капсулы
CREATE OR REPLACE FUNCTION update_score_usage()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM increment_score_usage(NEW.initial_score_id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_capsule_insert
  AFTER INSERT ON capsules
  FOR EACH ROW
  EXECUTE FUNCTION update_score_usage();

-- ========================================
-- Storage Buckets
-- ========================================

-- Создание bucket для аудио файлов (выполнить в Supabase Dashboard)
-- INSERT INTO storage.buckets (id, name, public) VALUES ('audio', 'audio', true);

-- Политики для storage bucket (выполнить в Supabase Dashboard)
-- CREATE POLICY "Users can upload audio files"
--   ON storage.objects FOR INSERT
--   WITH CHECK (bucket_id = 'audio' AND auth.uid()::text = (storage.foldername(name))[1]);

-- CREATE POLICY "Anyone can view public audio files"
--   ON storage.objects FOR SELECT
--   USING (bucket_id = 'audio');

-- ========================================
-- Завершение
-- ========================================

COMMENT ON DATABASE postgres IS 'Listen.Sound.Reflect.Create Database - Deep Listening Mini App';

-- Вывод информации о созданных таблицах
SELECT 
  schemaname,
  tablename,
  tableowner
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('scores', 'audio_files', 'capsules', 'fragments', 'reflections')
ORDER BY tablename;
