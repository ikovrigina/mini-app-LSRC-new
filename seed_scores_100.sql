-- ========================================
-- Listen.Sound.Reflect.Create - 100 Original Scores
-- Based on Deep Listening practice by Pauline Oliveros
-- ========================================

-- Clear existing seed scores (optional - comment out if you want to keep them)
-- DELETE FROM scores WHERE source IN ('oliveros_original', 'deep_listening');

-- Insert 100 scores for Deep Listening practice
INSERT INTO scores (text, source, is_public, language) VALUES

-- === BASIC LISTENING (1-15) ===
('Listen to everything you can possibly hear, both inwardly and outwardly.', 'oliveros_original', true, 'en'),
('Close your eyes and listen. When you open your eyes, consider what you heard as music.', 'oliveros_original', true, 'en'),
('Listen for the space between sounds.', 'deep_listening', true, 'en'),
('Listen to a sound until you no longer recognize it.', 'oliveros_original', true, 'en'),
('Listen for beginnings. Listen for endings.', 'oliveros_original', true, 'en'),
('Just listen. Do not play, do not speak. Only listen.', 'oliveros_original', true, 'en'),
('Listen inwardly for your own sound. Choose when and how to express it.', 'oliveros_original', true, 'en'),
('Listen outwardly for a sound from your environment. Let it guide you.', 'oliveros_original', true, 'en'),
('Wherever you are, just listen. Review what you hear as if it were a concert.', 'oliveros_original', true, 'en'),
('Listen for what has not yet sounded, like a fisherman waiting for a bite.', 'oliveros_original', true, 'en'),
('Listen to the resonance in spaces you visit. Find an environment that suits you.', 'oliveros_original', true, 'en'),
('Listen for a trigger. React instantaneously with a sound as short as possible.', 'oliveros_original', true, 'en'),
('Listen to everything. Notice everything. Get a body sense of everything.', 'oliveros_original', true, 'en'),
('Listen until there is a sound. Listen until there is a silence.', 'oliveros_original', true, 'en'),
('Take some time to sit down, close your eyes, and just listen.', 'oliveros_original', true, 'en'),

-- === BREATH & BODY (16-30) ===
('Listen to the sound of your breath as if you are listening to music.', 'deep_listening', true, 'en'),
('Breathe. Allow your breath to flow freely. Keep listening to how it changes.', 'oliveros_original', true, 'en'),
('What is the current tempo of your breathing? What is the tempo of your heart?', 'oliveros_original', true, 'en'),
('Listen from your stomach. Listen from your heart. Listen from your whole body.', 'deep_listening', true, 'en'),
('Walk so silently that the bottoms of your feet become ears.', 'oliveros_original', true, 'en'),
('What is the meter and tempo of your normal walk?', 'oliveros_original', true, 'en'),
('Breathe with the echo of your own steps.', 'deep_listening', true, 'en'),
('Listen to the rhythms of your body: breath, heartbeat, footsteps.', 'deep_listening', true, 'en'),
('Feel the vibrations in your bones as you listen.', 'deep_listening', true, 'en'),
('Let your body resonate with the sounds around you.', 'deep_listening', true, 'en'),
('Listen to your internal sounds: breath, pulse, digestion.', 'deep_listening', true, 'en'),
('Notice how sounds affect your body and your feelings.', 'oliveros_original', true, 'en'),
('Listen with your palms. Listen with the soles of your feet. Listen with your whole body.', 'oliveros_original', true, 'en'),
('Move very slowly while listening. Let sound guide your movement.', 'deep_listening', true, 'en'),
('Be still. Through stillness, hear the most subtle vibrations.', 'deep_listening', true, 'en'),

-- === ENVIRONMENT (31-45) ===
('Listen to the sounds of nature as if they were a symphony.', 'deep_listening', true, 'en'),
('Sit by trees. Notice what kind of tree makes what kind of sound.', 'oliveros_original', true, 'en'),
('By a river or stream, listen for the key tones in the rushing waters.', 'oliveros_original', true, 'en'),
('Listen to the environment. Reinforce a sound you hear with your voice.', 'oliveros_original', true, 'en'),
('Notice an object around you. Acknowledge it with a sound.', 'oliveros_original', true, 'en'),
('Listen to the air. How does it sound today?', 'deep_listening', true, 'en'),
('Listen to a roadway with eyes closed. Distinguish sounds by their character.', 'oliveros_original', true, 'en'),
('Find a favorite natural soundscape and listen along with it.', 'oliveros_original', true, 'en'),
('Listen to the space you are in. What is its resonance?', 'deep_listening', true, 'en'),
('Notice sounds from far away. Notice sounds very close.', 'deep_listening', true, 'en'),
('Listen to the silence between environmental sounds.', 'deep_listening', true, 'en'),
('What sounds are present right now that you usually ignore?', 'deep_listening', true, 'en'),
('Listen to the weather. What does rain sound like? Wind? Sun?', 'deep_listening', true, 'en'),
('Find the quietest place you can. Listen to what remains.', 'deep_listening', true, 'en'),
('Listen to the soundscape as it changes throughout the day.', 'deep_listening', true, 'en'),

-- === ATTENTION & AWARENESS (46-60) ===
('Expand your listening. Defocus your ears as you would your eyes for wider vision.', 'oliveros_original', true, 'en'),
('Focus on one sound. Then gradually expand to include all sounds.', 'deep_listening', true, 'en'),
('Listen in all directions at once.', 'oliveros_original', true, 'en'),
('How can you detect the energy of a sound?', 'oliveros_original', true, 'en'),
('How does the energy of a sound affect your energy?', 'oliveros_original', true, 'en'),
('Notice sounds that attract you. Follow them with your attention.', 'oliveros_original', true, 'en'),
('Listen to the foreground. Listen to the background. Listen to everything at once.', 'deep_listening', true, 'en'),
('What sounds are calling for your attention right now?', 'deep_listening', true, 'en'),
('Listen without judgment. Accept all sounds equally.', 'deep_listening', true, 'en'),
('Shift your attention from one sound to another, like changing channels.', 'deep_listening', true, 'en'),
('Notice when your attention wanders. Gently return to listening.', 'deep_listening', true, 'en'),
('Listen as if you are hearing for the very first time.', 'deep_listening', true, 'en'),
('What would it mean to listen with your whole being?', 'deep_listening', true, 'en'),
('Listen to what is sounding just inside your ear.', 'oliveros_original', true, 'en'),
('Listen to what is sounding just outside your ear.', 'oliveros_original', true, 'en'),

-- === SOUND QUALITIES (61-75) ===
('Make a familiar sound strange. Make a strange sound familiar.', 'oliveros_original', true, 'en'),
('Make a soft sound loud. Make a loud sound soft.', 'oliveros_original', true, 'en'),
('Make a slow sound fast. Make a fast sound slow.', 'oliveros_original', true, 'en'),
('Make a near sound far. Make a far sound near.', 'oliveros_original', true, 'en'),
('Make a real sound imaginary. Make an imaginary sound real.', 'oliveros_original', true, 'en'),
('Make a beautiful sound ugly. Make an ugly sound beautiful.', 'oliveros_original', true, 'en'),
('Make a sad sound happy. Make a happy sound sad.', 'oliveros_original', true, 'en'),
('Make a simple sound complex. Make a complex sound simple.', 'oliveros_original', true, 'en'),
('Listen for old sounds. Listen for new sounds.', 'oliveros_original', true, 'en'),
('Listen for borrowed sounds. Listen for blue sounds.', 'oliveros_original', true, 'en'),
('What color is the sound you hear? Can you see sounds in color?', 'deep_listening', true, 'en'),
('What texture does this sound have? Rough? Smooth? Sharp?', 'deep_listening', true, 'en'),
('What temperature is this sound? Warm? Cool? Hot? Cold?', 'deep_listening', true, 'en'),
('What shape is this sound? Round? Angular? Flowing?', 'deep_listening', true, 'en'),
('What emotion does this sound carry?', 'deep_listening', true, 'en'),

-- === SILENCE (76-85) ===
('Make a silence. Make another silence. Keep making silence.', 'oliveros_original', true, 'en'),
('Listen to the silence before a sound. Listen to the silence after.', 'deep_listening', true, 'en'),
('Imagine silence. What do you hear?', 'oliveros_original', true, 'en'),
('Find the silence within the noise.', 'deep_listening', true, 'en'),
('How many different kinds of silence can you notice?', 'deep_listening', true, 'en'),
('Listen to silence as if it were music.', 'deep_listening', true, 'en'),
('What is the sound of stillness?', 'deep_listening', true, 'en'),
('Rest in silence. Let silence speak to you.', 'deep_listening', true, 'en'),
('Notice the space between sounds. That space is also sound.', 'deep_listening', true, 'en'),
('Listen until the silence feels complete.', 'oliveros_original', true, 'en'),

-- === MEMORY & IMAGINATION (86-95) ===
('Remember a sound from long ago. Hear it again in your mind.', 'oliveros_original', true, 'en'),
('Imagine a sound you have never heard before.', 'deep_listening', true, 'en'),
('Listen inwardly to a sound from your memory.', 'oliveros_original', true, 'en'),
('Can you hear music in your imagination? What does it sound like?', 'deep_listening', true, 'en'),
('Listen to a sound, then imagine it continuing after it stops.', 'deep_listening', true, 'en'),
('What sound would describe this moment perfectly?', 'deep_listening', true, 'en'),
('Imagine the sound of sunrise. Imagine the sound of sunset.', 'oliveros_original', true, 'en'),
('What does joy sound like? What does peace sound like?', 'deep_listening', true, 'en'),
('Listen to your dreams. What sounds do you remember?', 'oliveros_original', true, 'en'),
('If this place had a voice, what would it say?', 'deep_listening', true, 'en'),

-- === VOICE & EXPRESSION (96-100) ===
('Listen to the sound of your voice. How does it feel inside?', 'oliveros_original', true, 'en'),
('Sound a word until it becomes just sound. Sound until it becomes a word.', 'oliveros_original', true, 'en'),
('Make a sound that no one has ever heard before.', 'oliveros_original', true, 'en'),
('Express in sound what you cannot express in words.', 'deep_listening', true, 'en'),
('Let your voice blend with the sounds around you.', 'oliveros_original', true, 'en')

ON CONFLICT DO NOTHING;

-- ========================================
-- Summary
-- ========================================
-- Total: 100 scores
-- Sources:
--   - oliveros_original: ~45 scores (directly inspired by Pauline Oliveros)
--   - deep_listening: ~55 scores (based on Deep Listening principles)
-- Language: English
-- All scores are public (is_public = true)

-- Verify count
SELECT COUNT(*) as total_scores FROM scores WHERE source IN ('oliveros_original', 'deep_listening');

