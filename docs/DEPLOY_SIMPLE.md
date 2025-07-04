# Simple Deployment Guide for llmXive Dashboard

This dashboard works perfectly with GitHub Pages - no complex setup needed!

## Prerequisites

- GitHub repository (public recommended for API access)
- GitHub Pages enabled

## Quick Start (2 minutes!)

### 1. Enable GitHub Pages

1. Go to your repository Settings
2. Scroll to "Pages" section
3. Source: "Deploy from a branch"
4. Branch: `main`, Folder: `/docs`
5. Click Save

Your site will be live at: `https://[username].github.io/[repo]/`

### 2. Make Repository Public (Recommended)

For best experience, make your repository public:
1. Settings → General
2. Scroll to "Danger Zone"
3. "Change visibility" → Make public

This enables:
- No authentication needed for viewing
- Higher API rate limits
- Anyone can create issues and vote

## How It Works

### Viewing Projects
- Fetches issues directly from GitHub API
- No authentication required for public repos
- Automatically displays reactions as votes

### Creating Issues
1. User fills out the form
2. Clicks submit
3. Redirected to GitHub with pre-filled issue
4. Completes on GitHub (signs in if needed)
5. Returns to dashboard and refreshes

### Voting
1. User clicks 👍 or 👎
2. Redirected to the issue on GitHub
3. Clicks the reaction on GitHub
4. Returns to see updated counts

## Customization

### Change Repository

Edit `docs/js/config.js`:
```javascript
const CONFIG = {
    github: {
        owner: 'YourUsername',
        repo: 'YourRepo',
        projectNumber: 1  // Your project board number
    },
    // ...
};
```

### Styling

Edit `docs/css/style.css` to match your brand:
- Change `--primary-color` for accent color
- Modify fonts in the HTML `<head>`
- Adjust animations and transitions

### Labels for Status

The dashboard uses labels to determine project status:
- `backlog` → Backlog column
- `ready` → Ready column
- `in-progress` → In Progress column
- `in-review` → In Review column
- `done` → Done column

Add these labels to your repository for proper categorization.

## Features

✅ **No Backend Required** - Pure static site
✅ **No API Keys** - Uses public GitHub API
✅ **Native GitHub Features** - Issues, reactions, labels
✅ **Fast & Responsive** - Pure JavaScript, no frameworks
✅ **View Tracking** - Local storage for analytics
✅ **Search & Filter** - Client-side processing

## Limitations

Since we're using GitHub's native features:
- Users must have GitHub accounts to vote/submit
- Vote counts are GitHub reactions (public)
- No custom authentication flow
- Rate limits apply (60/hour unauthenticated)

## Tips

1. **Pre-create Labels**: Add status labels to your repo
2. **Issue Templates**: Create `.github/ISSUE_TEMPLATE/idea.md`
3. **Project Board**: Set up a GitHub Project for visual management
4. **Custom Domain**: Add a CNAME file in `/docs`

## Troubleshooting

### "No projects found"
- Check repository is public
- Verify issues exist
- Check browser console for API errors

### "Can't vote"
- Must be signed into GitHub
- Click the reaction on the GitHub issue page

### "Submitted idea doesn't appear"
- Refresh the page after creating on GitHub
- Check the issue was created successfully

## Local Development

```bash
cd docs
python -m http.server 8000
# Visit http://localhost:8000
```

## That's It!

Your dashboard is ready to use. The beauty is in its simplicity - it just works with GitHub's existing features!