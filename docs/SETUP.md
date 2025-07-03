# llmXive GitHub Pages Setup Guide

## Overview

The llmXive interactive website uses GitHub OAuth for secure authentication. This allows users to submit ideas directly to the project board while maintaining security and proper access control.

## Setup Steps

### 1. Create a GitHub OAuth App

1. Go to your GitHub Settings → Developer settings → OAuth Apps
2. Click "New OAuth App"
3. Fill in the following:
   - **Application name**: llmXive
   - **Homepage URL**: https://contextlab.github.io/llmXive/
   - **Authorization callback URL**: https://contextlab.github.io/llmXive/
4. Click "Register application"
5. Note your **Client ID**
6. Generate a new **Client Secret** and save it securely

### 2. Choose an Authentication Method

Since GitHub Pages is static hosting, you need a backend service to handle OAuth securely. Choose one:

#### Option A: Netlify Functions (Recommended)

1. Deploy the site to Netlify instead of GitHub Pages
2. Create a `netlify.toml` file:

```toml
[build]
  publish = "docs"

[functions]
  directory = "docs/netlify/functions"

[build.environment]
  GITHUB_CLIENT_ID = "your-client-id"
  GITHUB_CLIENT_SECRET = "your-client-secret"
```

3. The included `netlify/functions/github-auth.js` will handle OAuth

#### Option B: Vercel Functions

1. Create a `vercel.json`:

```json
{
  "functions": {
    "api/github-auth.js": {
      "maxDuration": 10
    }
  }
}
```

2. Create `api/github-auth.js` with similar code to the Netlify function

#### Option C: GitHub Actions + GitHub App

1. Create a GitHub App instead of OAuth App
2. Use GitHub Actions to handle authentication
3. Generate installation tokens for API access

#### Option D: Personal Access Tokens (Development Only)

For testing/development, users can use Personal Access Tokens:

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a token with `public_repo` scope
3. Enter it when prompted on the site

### 3. Update Configuration

Edit `js/auth.js` and update:

```javascript
this.clientId = 'YOUR_ACTUAL_CLIENT_ID';
this.redirectUri = 'YOUR_SITE_URL';
```

### 4. Deploy

#### For GitHub Pages:
```bash
git add docs/
git commit -m "Add interactive site"
git push origin main
```

Enable GitHub Pages in repository settings, using the `docs` folder.

#### For Netlify:
```bash
# Connect your GitHub repo to Netlify
# Set environment variables in Netlify dashboard
# Deploy automatically on push
```

## Security Considerations

1. **Never commit secrets**: Client secrets should only be stored in environment variables
2. **Use HTTPS**: Always use HTTPS URLs for OAuth
3. **Validate state**: The OAuth flow includes state validation to prevent CSRF
4. **Minimal scopes**: Only request `public_repo` scope
5. **Token storage**: Tokens are stored in localStorage with appropriate security measures

## Features

### Authenticated Features
- Submit new ideas to the project board
- Vote on existing projects
- View personalized content

### Public Features
- View all projects and papers
- Search and filter projects
- View project details
- Track view counts locally

## Troubleshooting

### "Authentication failed"
- Check that your OAuth app is properly configured
- Ensure the callback URL matches exactly
- Verify client ID is correct

### "Cannot create issue"
- Ensure the user has write access to the repository
- Check that the token has the correct scopes
- Verify the GitHub API is accessible

### "Project board not updating"
- The site caches data for 5 minutes
- Force refresh with Ctrl+Shift+R
- Check browser console for errors

## Local Development

To run locally:

```bash
cd docs
python -m http.server 8000
# Visit http://localhost:8000
```

For OAuth testing locally, you'll need to:
1. Create a separate OAuth app for localhost
2. Update the redirect URI to `http://localhost:8000`
3. Use a tool like `ngrok` for HTTPS testing

## Alternative: GitHub App

For production use, consider using a GitHub App instead:

1. Better security model
2. Higher rate limits
3. Can act on behalf of the app, not users
4. Provides installation tokens

To implement:
1. Create a GitHub App
2. Use the GitHub App API to generate installation tokens
3. Update the authentication flow accordingly

## Support

For issues or questions:
- Check the browser console for errors
- Review GitHub OAuth documentation
- Open an issue in the repository