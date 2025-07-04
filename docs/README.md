# llmXive Interactive Dashboard

A beautiful, interactive dashboard for the llmXive automated scientific discovery project.

## Features

- 📊 **Dynamic Project Board** - Real-time display of all project issues
- 🔍 **Search & Filter** - Find projects by keywords, status, or content
- 👍 **GitHub Reactions** - Vote using GitHub's native thumbs up/down
- ✍️ **Easy Submission** - Create new ideas directly on GitHub
- 📈 **Statistics** - Track views, votes, and project metrics
- 🎨 **Modern Design** - Clean, responsive interface

## How It Works

This site leverages GitHub's native features:

1. **No Complex Auth** - Just optional username for personalization
2. **Direct GitHub Integration** - Creates issues and votes on GitHub
3. **Public API** - Works with public repos, no authentication needed
4. **Native Reactions** - Uses GitHub's 👍 and 👎 as votes

## Usage

### Viewing Projects
- Browse all projects on the main page
- Click any project for details
- Search and filter as needed

### Voting
1. Click the 👍 or 👎 button on any project
2. You'll be redirected to GitHub to sign in (if needed)
3. Click the reaction on the GitHub issue
4. Return to the dashboard to see updated counts

### Submitting Ideas
1. Click "Submit Idea"
2. Fill out the form
3. Click submit to go to GitHub
4. Complete the issue creation on GitHub
5. Refresh the dashboard to see your idea

## Local Development

```bash
# Serve the site locally
cd docs
python -m http.server 8000
# Visit http://localhost:8000
```

## Deployment

Simply enable GitHub Pages:
1. Go to Settings → Pages
2. Source: Deploy from branch
3. Branch: main, folder: /docs
4. Save

The site will be live at: https://[username].github.io/[repo]/

## Tech Stack

- Pure JavaScript (no frameworks)
- GitHub API v3
- Modern CSS with animations
- localStorage for view tracking

## Contributing

Feel free to submit issues or PRs to improve the dashboard!