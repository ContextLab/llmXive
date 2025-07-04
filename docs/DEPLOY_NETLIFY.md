# Deploying llmXive to Netlify

This guide walks you through deploying the llmXive interactive site to Netlify with full OAuth authentication support.

## Prerequisites

- A GitHub account
- A Netlify account (free tier works fine)
- Admin access to the llmXive repository (or your fork)

## Step 1: Create GitHub OAuth App

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Click "New OAuth App"
3. Fill in:
   - **Application name**: llmXive (Netlify)
   - **Homepage URL**: `https://your-site-name.netlify.app`
   - **Authorization callback URL**: `https://your-site-name.netlify.app`
4. Click "Register application"
5. Save your **Client ID** and generate a **Client Secret** (keep it secure!)

## Step 2: Deploy to Netlify

### Option A: Deploy with Netlify Button (Easiest)

[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/ContextLab/llmXive)

### Option B: Manual Deploy via GitHub

1. Log in to [Netlify](https://app.netlify.com)
2. Click "Add new site" → "Import an existing project"
3. Choose "GitHub" and authorize Netlify
4. Select the `ContextLab/llmXive` repository
5. Configure build settings:
   - **Base directory**: (leave empty)
   - **Build command**: (leave empty - we're serving static files)
   - **Publish directory**: `docs`
6. Click "Deploy site"

### Option C: Deploy via Netlify CLI

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login to Netlify
netlify login

# Deploy
cd /path/to/llmXive
netlify deploy --dir=docs --prod
```

## Step 3: Configure Environment Variables

1. In Netlify dashboard, go to Site settings → Environment variables
2. Add the following variables:
   - `GITHUB_CLIENT_ID` = Your OAuth App Client ID
   - `GITHUB_CLIENT_SECRET` = Your OAuth App Client Secret

## Step 4: Update OAuth App Settings

1. Go back to your GitHub OAuth App settings
2. Update the URLs with your actual Netlify URL:
   - **Homepage URL**: `https://your-site-name.netlify.app`
   - **Authorization callback URL**: `https://your-site-name.netlify.app`

## Step 5: Update Site Configuration

1. Edit `docs/js/config.js` in your repository:

```javascript
const CONFIG = {
    github: {
        owner: 'ContextLab',
        repo: 'llmXive',
        projectNumber: 13,
        // Remove any hardcoded token
        token: null
    },
    // ... rest of config
};
```

2. Edit `docs/js/auth.js` to use your Netlify URL:

```javascript
this.redirectUri = 'https://your-site-name.netlify.app/';
```

3. Commit and push these changes

## Step 6: Test the Deployment

1. Visit your Netlify site: `https://your-site-name.netlify.app`
2. Click "Login with GitHub"
3. Authorize the application
4. Try submitting a new idea

## Custom Domain (Optional)

To use a custom domain:

1. In Netlify, go to Domain settings
2. Add your custom domain
3. Update your GitHub OAuth App URLs to use the custom domain
4. Update the redirect URI in your code

## Troubleshooting

### "Authentication failed"
- Check that environment variables are set correctly in Netlify
- Ensure OAuth App URLs match your Netlify URL exactly
- Check the browser console for specific errors

### "Cannot read properties of null"
- Make sure the GitHub token is being properly exchanged
- Check that the serverless function is deployed

### Functions not working
- Check Netlify Functions logs in the dashboard
- Ensure the functions directory is correctly specified
- Verify environment variables are accessible

## Security Notes

1. **Never commit secrets**: Client Secret should only be in Netlify environment variables
2. **Use HTTPS**: Netlify provides free SSL certificates
3. **Restrict OAuth scopes**: Only request necessary permissions
4. **Monitor usage**: Check your GitHub OAuth App usage regularly

## Local Development with Netlify Dev

```bash
# Install dependencies
npm install -g netlify-cli

# Set up environment variables locally
cp .env.example .env
# Edit .env with your OAuth credentials

# Run Netlify Dev
netlify dev

# Visit http://localhost:8888
```

## Updating the Site

When you push changes to GitHub:
1. Netlify automatically detects the changes
2. Rebuilds and redeploys your site
3. Changes are live in about 30 seconds

## Support

- [Netlify Documentation](https://docs.netlify.com)
- [GitHub OAuth Documentation](https://docs.github.com/en/developers/apps/building-oauth-apps)
- [llmXive Issues](https://github.com/ContextLab/llmXive/issues)