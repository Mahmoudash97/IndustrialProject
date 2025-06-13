export const config = {
  api: { bodyParser: false },
};

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  let userMessage = '';

  try {
    if (req.headers['content-type']?.includes('multipart/form-data')) {
      const formidable = require('formidable');
      const form = new formidable.IncomingForm();
      
      const { fields } = await new Promise((resolve, reject) => {
        form.parse(req, (err, fields, files) => {
          if (err) reject(err);
          resolve({ fields, files });
        });
      });

      // Handle array values from Formidable
      userMessage = Array.isArray(fields.query) 
        ? fields.query[0]?.trim() || ''
        : typeof fields.query === 'string'
          ? fields.query.trim()
          : '';

      console.log('Received FormData fields:', fields);
    } else {
      const buffers = [];
      for await (const chunk of req) {
        buffers.push(chunk);
      }
      const body = JSON.parse(Buffer.concat(buffers).toString() || '{}');
      userMessage = (body.query || '').trim();
    }

    console.log('Extracted user message:', `"${userMessage}"`);

    if (!userMessage) {
      return res.status(400).json({ error: 'Empty message received' });
    }

    const ollamaRes = await fetch('http://localhost:11434/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: process.env.OLLAMA_MODEL || 'llama3',
        prompt: userMessage,
        stream: false
      }),
    });

    if (!ollamaRes.ok) {
      throw new Error(`Ollama API error: ${ollamaRes.statusText}`);
    }

    const data = await ollamaRes.json();
    console.log('Ollama response:', data);

    return res.status(200).json({
      message: data.response?.trim() || ''
    });

  } catch (error) {
    console.error('API Error:', error);
    return res.status(500).json({ 
      error: error.message || 'Internal Server Error',
      ...(process.env.NODE_ENV === 'development' && { stack: error.stack })
    });
  }
}
