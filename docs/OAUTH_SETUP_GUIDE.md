# GitHub OAuth Setup Guide for llmXive

## Quick Setup with Gatekeeper (5 minutes)

### Step 1: Deploy Gatekeeper to Heroku

1. Click this button to deploy Gatekeeper (a simple OAuth proxy):
   
   [![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/prose/gatekeeper)

2. During setup, you'll need:
   - **App name**: Choose something like `llmxive-auth`
   - **OAUTH_CLIENT_ID**: `Ov23liY5hzeo5JVmlzcH`
   - **OAUTH_CLIENT_SECRET**: Your GitHub OAuth App client secret
   - **REDIRECT_URI**: `https://contextlab.github.io/llmXive/`

3. Deploy the app (takes ~2 minutes)

### Step 2: Update Your Code

Edit `docs/js/github-integrated-auth.js` and update the token exchange URL:

```javascript
// Around line 47, in the handleCallback() function
// Replace this line:
const response = await fetch('https://github.com/login/device/code', {

// With your Gatekeeper URL:
const response = await fetch('https://YOUR-APP-NAME.herokuapp.com/authenticate/' + code, {
```

### Step 3: Get Your Client Secret

1. Go to https://github.com/settings/developers
2. Click on your OAuth App
3. Copy the Client Secret
4. Add it to your Heroku app:
   - Go to your Heroku dashboard
   - Click on your app
   - Settings → Config Vars
   - Add `OAUTH_CLIENT_SECRET` with your secret

## Option 2: Deploy Your Own Simple Backend

If you prefer more control, here's a minimal Node.js server:

### server.js
```javascript
const express = require('express');
const axios = require('axios');
const cors = require('cors');
const app = express();

app.use(cors({
  origin: 'https://contextlab.github.io'
}));

app.get('/authenticate/:code', async (req, res) => {
  const { code } = req.params;
  
  try {
    const response = await axios.post('https://github.com/login/oauth/access_token', {
      client_id: process.env.CLIENT_ID,
      client_secret: process.env.CLIENT_SECRET,
      code
    }, {
      headers: { 
        Accept: 'application/json' 
      }
    });
    
    if (response.data.access_token) {
      res.json({ token: response.data.access_token });
    } else {
      res.status(400).json({ error: 'Failed to get token' });
    }
  } catch (error) {
    res.status(400).json({ error: 'Authentication failed' });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Auth server running on port ${PORT}`);
});
```

### package.json
```json
{
  "name": "llmxive-auth",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "axios": "^1.4.0",
    "cors": "^2.8.5"
  }
}
```

### Deploy to Heroku/Vercel/Railway
1. Create a new app
2. Set environment variables:
   - `CLIENT_ID`: `Ov23liY5hzeo5JVmlzcH`
   - `CLIENT_SECRET`: Your GitHub OAuth App client secret
3. Deploy the code
4. Update `github-integrated-auth.js` with your server URL

## Option 3: Use Netlify Functions (If Moving from GitHub Pages)

If you're willing to move from GitHub Pages to Netlify:

### netlify/functions/github-auth.js
```javascript
exports.handler = async (event) => {
  const { code } = event.queryStringParameters;
  
  if (!code) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: 'No code provided' })
    };
  }
  
  try {
    const response = await fetch('https://github.com/login/oauth/access_token', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        client_id: process.env.CLIENT_ID,
        client_secret: process.env.CLIENT_SECRET,
        code
      })
    });
    
    const data = await response.json();
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({ token: data.access_token })
    };
  } catch (error) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: 'Authentication failed' })
    };
  }
};
```

## Testing Your Setup

1. Click "Login with GitHub"
2. Choose "OAuth Flow"
3. Authorize the app
4. You should be redirected back and logged in!

## Security Reminders

- **NEVER** commit your Client Secret to Git
- **NEVER** expose your Client Secret in frontend code
- Always use HTTPS for your auth server
- Consider adding rate limiting to prevent abuse

## Need Help?

- GitHub OAuth Apps docs: https://docs.github.com/en/developers/apps/building-oauth-apps
- Gatekeeper: https://github.com/prose/gatekeeper
- Heroku: https://www.heroku.com/
- Netlify Functions: https://www.netlify.com/docs/functions/