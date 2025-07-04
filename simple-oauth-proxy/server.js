const express = require('express');
const cors = require('cors');
const fetch = require('node-fetch');
const app = express();

// Enable CORS for your GitHub Pages site
app.use(cors({
  origin: ['https://contextlab.github.io', 'http://localhost:8000'],
  credentials: true
}));

// Health check endpoint
app.get('/', (req, res) => {
  res.json({ 
    status: 'ok', 
    message: 'llmXive OAuth Proxy',
    endpoints: {
      authenticate: '/authenticate/:code'
    }
  });
});

// OAuth token exchange endpoint
app.get('/authenticate/:code', async (req, res) => {
  const { code } = req.params;
  
  if (!code) {
    return res.status(400).json({ error: 'No code provided' });
  }
  
  try {
    // Exchange code for token with GitHub
    const response = await fetch('https://github.com/login/oauth/access_token', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        client_id: process.env.OAUTH_CLIENT_ID,
        client_secret: process.env.OAUTH_CLIENT_SECRET,
        code: code
      })
    });
    
    const data = await response.json();
    
    if (data.access_token) {
      // Return token to frontend
      res.json({ 
        token: data.access_token,
        token_type: data.token_type || 'bearer'
      });
    } else {
      console.error('GitHub error:', data);
      res.status(400).json({ 
        error: data.error || 'Failed to authenticate',
        description: data.error_description
      });
    }
  } catch (error) {
    console.error('Server error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`OAuth proxy running on port ${PORT}`);
  console.log('Environment check:');
  console.log('- CLIENT_ID:', process.env.OAUTH_CLIENT_ID ? 'Set' : 'NOT SET!');
  console.log('- CLIENT_SECRET:', process.env.OAUTH_CLIENT_SECRET ? 'Set' : 'NOT SET!');
});