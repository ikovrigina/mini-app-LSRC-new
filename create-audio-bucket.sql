-- Создание bucket для аудио файлов
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'audio',
    'audio', 
    true,
    10485760, -- 10MB limit
    ARRAY['audio/webm', 'audio/wav', 'audio/mp3', 'audio/m4a', 'audio/ogg']
);

-- Политики доступа для bucket
CREATE POLICY "Public audio upload" ON storage.objects
FOR INSERT WITH CHECK (bucket_id = 'audio');

CREATE POLICY "Public audio access" ON storage.objects
FOR SELECT USING (bucket_id = 'audio');

CREATE POLICY "Public audio update" ON storage.objects
FOR UPDATE USING (bucket_id = 'audio');

CREATE POLICY "Public audio delete" ON storage.objects
FOR DELETE USING (bucket_id = 'audio');
