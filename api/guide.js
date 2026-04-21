import OpenAI from 'openai';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const ASSISTANT_ID = process.env.OPENAI_ASSISTANT_ID;

export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();
    if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

    if (!ASSISTANT_ID || !process.env.OPENAI_API_KEY) {
        return res.status(500).json({ error: 'Assistant not configured' });
    }

    const { message, thread_id } = req.body || {};
    if (!message) return res.status(400).json({ error: 'Message required' });

    try {
        let threadId = thread_id;
        if (!threadId) {
            const thread = await openai.beta.threads.create();
            threadId = thread.id;
        }

        await openai.beta.threads.messages.create(threadId, {
            role: 'user',
            content: message,
        });

        const run = await openai.beta.threads.runs.createAndPoll(threadId, {
            assistant_id: ASSISTANT_ID,
        });

        if (run.status !== 'completed') {
            return res.status(500).json({ error: `Run ended with status: ${run.status}` });
        }

        const messages = await openai.beta.threads.messages.list(threadId, { order: 'desc', limit: 1 });
        const assistantMsg = messages.data.find(m => m.role === 'assistant');
        const reply = assistantMsg?.content?.[0]?.text?.value || 'No response received.';

        return res.status(200).json({ reply, thread_id: threadId });
    } catch (error) {
        console.error('Guide API error:', error);
        return res.status(500).json({ error: 'Failed to get response' });
    }
}
