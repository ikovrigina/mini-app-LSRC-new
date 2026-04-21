const OpenAI = require('openai');

let openai = null;

function getClient() {
    if (!openai && process.env.OPENAI_API_KEY) {
        openai = new OpenAI.default
            ? new (OpenAI.default)({ apiKey: process.env.OPENAI_API_KEY })
            : new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
    }
    return openai;
}

module.exports = async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();
    if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

    const ASSISTANT_ID = process.env.OPENAI_ASSISTANT_ID;
    const client = getClient();

    if (!client || !ASSISTANT_ID) {
        return res.status(500).json({
            error: 'Assistant not configured',
            details: {
                hasApiKey: !!process.env.OPENAI_API_KEY,
                hasAssistantId: !!ASSISTANT_ID
            }
        });
    }

    const { message, thread_id } = req.body || {};
    if (!message) return res.status(400).json({ error: 'Message required' });

    try {
        let threadId = thread_id;
        if (!threadId) {
            const thread = await client.beta.threads.create();
            threadId = thread.id;
        }

        await client.beta.threads.messages.create(threadId, {
            role: 'user',
            content: message,
        });

        const run = await client.beta.threads.runs.createAndPoll(threadId, {
            assistant_id: ASSISTANT_ID,
        });

        if (run.status !== 'completed') {
            return res.status(500).json({ error: `Run ended with status: ${run.status}` });
        }

        const messages = await client.beta.threads.messages.list(threadId, { order: 'desc', limit: 1 });
        const assistantMsg = messages.data.find(m => m.role === 'assistant');
        const reply = assistantMsg?.content?.[0]?.text?.value || 'No response received.';

        return res.status(200).json({ reply, thread_id: threadId });
    } catch (error) {
        console.error('Guide API error:', error);
        return res.status(500).json({ error: 'Failed to get response', message: error.message });
    }
};
