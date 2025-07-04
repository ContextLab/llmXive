# Simple OAuth Proxy for llmXive

This is a minimal OAuth proxy server for the llmXive project.

## Deploy to Heroku

1. Make sure you're in this directory:
   ```bash
   cd simple-oauth-proxy
   ```

2. Initialize git (if needed):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

3. Add Heroku remote:
   ```bash
   heroku git:remote -a llmxive-auth-b300c94fab60
   ```

4. Deploy:
   ```bash
   git push heroku master --force
   ```

5. Set environment variables:
   ```bash
   heroku config:set OAUTH_CLIENT_ID=Ov23liY5hzeo5JVmlzcH
   heroku config:set OAUTH_CLIENT_SECRET=your_secret_here
   ```

6. Check logs:
   ```bash
   heroku logs --tail
   ```

## Testing

Visit https://llmxive-auth-b300c94fab60.herokuapp.com/ to see if it's running.