# Setting up GitHub OAuth for llmXive

To enable users to login and post issues directly from the dashboard, you need to create a GitHub OAuth App.

## Step 1: Create GitHub OAuth App

1. Go to https://github.com/settings/developers
2. Click "New OAuth App"
3. Fill in the form:
   - **Application name**: llmXive Dashboard
   - **Homepage URL**: https://contextlab.github.io/llmXive/
   - **Authorization callback URL**: https://contextlab.github.io/llmXive/
   - **Application description**: Interactive dashboard for llmXive scientific discovery

4. Click "Register application"
5. Copy your **Client ID**

## Step 2: Update the Code

1. Edit `docs/js/github-oauth-app.js`
2. Replace `YOUR_CLIENT_ID` with your actual client ID:
   ```javascript
   this.clientId = 'YOUR_CLIENT_ID'; // Replace with your OAuth App client ID
   ```

## Step 3: Set up Token Exchange Service

Since GitHub Pages is static, you need a backend service to exchange the OAuth code for an access token. Options:

### Option A: Use Gatekeeper (Recommended)
1. Deploy Gatekeeper: https://github.com/prose/gatekeeper
2. Update the token exchange URL in `github-oauth-app.js`

### Option B: Use Netlify Functions
1. Deploy to Netlify instead of GitHub Pages
2. Create a serverless function to handle the OAuth flow

### Option C: Use a Simple Proxy Service
1. Deploy a simple Node.js app to Heroku/Vercel that handles the token exchange
2. Example code:

```javascript
// server.js
const express = require('express');
const axios = require('axios');
const app = express();

app.get('/authenticate/:code', async (req, res) => {
  const { code } = req.params;
  
  try {
    const response = await axios.post('https://github.com/login/oauth/access_token', {
      client_id: process.env.CLIENT_ID,
      client_secret: process.env.CLIENT_SECRET,
      code
    }, {
      headers: { Accept: 'application/json' }
    });
    
    res.json({ token: response.data.access_token });
  } catch (error) {
    res.status(400).json({ error: 'Authentication failed' });
  }
});

app.listen(process.env.PORT || 3000);
```

## Step 4: Update HTML

Replace the current auth script in `index.html`:
```html
<script src="js/native-github-auth.js"></script>
```

With:
```html
<script src="js/github-oauth-app.js"></script>
```

## Benefits

With proper OAuth setup:
- Users click "Login with GitHub" and authorize once
- Direct voting on issues without redirects
- Create issues directly from the dashboard
- Better user experience overall

## Security Notes

- Never expose your Client Secret in frontend code
- Use environment variables for sensitive data
- Consider rate limiting your token exchange service