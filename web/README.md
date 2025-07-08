# llmXive Web Interface

A modern web-based platform for automated scientific discovery and research collaboration.

## 🎯 Overview

The llmXive web interface provides a complete research pipeline from idea submission to published papers, featuring automated peer review, stage-based project advancement, and collaborative research management.

## ✨ Features

### Core Functionality
- **Project Management**: Create, browse, and manage research projects across multiple fields
- **Automated Pipeline**: Stage-based progression from idea → design → implementation → publication
- **Review System**: Multi-criteria peer review with automated advancement based on review scores
- **Real-time Analytics**: Dashboard with project statistics, contributor rankings, and progress tracking
- **Modern UI**: Responsive design with smooth animations and intuitive navigation

### Pipeline Stages
1. **Idea Submission**: Submit research ideas with field classification and timeline estimation
2. **Technical Design**: Develop detailed technical design documents with peer review
3. **Implementation Planning**: Create comprehensive implementation plans with milestone tracking
4. **Active Development**: Code/data development with progress monitoring
5. **Paper Drafting**: LaTeX paper generation with bibliography management
6. **Publication**: Final review and publication with PDF generation

### Review System
- **Multi-type Reviews**: Support for idea, design, implementation, code, data, and paper reviews
- **Scoring System**: 5-star ratings across multiple criteria (novelty, feasibility, impact, etc.)
- **Automated Advancement**: Projects advance based on review points (LLM reviews = 0.5 points, Human reviews = 1.0 points)
- **Recommendation Engine**: Accept/revision/reject recommendations with detailed feedback

## 🚀 Quick Start

### Local Development
```bash
# Clone the repository
git clone https://github.com/ContextLab/llmXive.git
cd llmXive/web

# Serve the files (any HTTP server)
python -m http.server 8000
# OR
npx serve .
# OR
php -S localhost:8000

# Open in browser
open http://localhost:8000
```

### File Structure
```
web/
├── dashboard.html          # Main dashboard with project overview
├── projects.html          # Browse and filter all projects
├── about.html             # About page with pipeline visualization
├── src/
│   ├── data/
│   │   ├── ProjectDataManager.js    # Core data management
│   │   └── DatabaseManager.js       # Database operations
│   ├── managers/
│   │   └── PipelineManager.js       # Pipeline automation
│   └── components/
│       ├── ReviewSystem.js          # Review and voting system
│       └── DocumentViewer.js        # Document display system
├── database/              # JSON data files
└── README.md             # This file
```

## 🔧 Configuration

### Data Storage
The interface uses localStorage for client-side persistence with JSON fallback data:
- Projects stored in `localStorage['llmxive-projects']`
- Reviews stored in `localStorage['llmxive-reviews']`
- Votes stored in `localStorage['llmxive-votes']`
- User sessions in `localStorage['llmxive-github-user']`

### Pipeline Thresholds
Configure advancement thresholds in `PipelineManager.js`:
```javascript
this.stageThresholds = {
    'idea': { minPoints: 0, nextStage: 'design' },
    'design': { minPoints: 3.0, nextStage: 'implementation_plan' },
    'implementation_plan': { minPoints: 5.0, nextStage: 'in_progress' },
    'in_progress': { minPoints: 80, nextStage: 'paper' },
    'paper': { minPoints: 5.0, nextStage: 'done' }
};
```

## 📱 Usage Guide

### Creating Projects
1. Navigate to Dashboard or Browse Projects
2. Click "Submit Idea" in navigation
3. Fill out project form (title, field, description, keywords, timeline)
4. Submit to add to project database

### Reviewing Projects
1. Click on any project card to open details
2. Click "Write Review" button
3. Select review type (idea, design, implementation, etc.)
4. Provide ratings across multiple criteria (1-5 stars)
5. Write detailed feedback and recommendation
6. Submit review to update project and trigger advancement check

### Pipeline Advancement
Projects automatically advance through stages based on accumulated review points:
- **LLM Reviews**: 0.5 points each
- **Human Reviews**: 1.0 points each
- **Stage Thresholds**: 3-5 points typically required for advancement
- **Implementation Phase**: Uses completeness score (0-100%) instead of review points

### Voting System
- **Upvote/Downvote**: Express support or concerns for projects
- **Persistent Tracking**: Votes saved to localStorage and displayed on cards
- **User Attribution**: Tied to logged-in user (demo system currently)

## 🎨 Customization

### Themes
Modify CSS variables in any HTML file:
```css
:root {
    --primary: #6366f1;        /* Primary brand color */
    --secondary: #06b6d4;      /* Secondary accent */
    --success: #10b981;        /* Success notifications */
    --error: #ef4444;          /* Error states */
}
```

### Adding Fields
Update field options in project submission forms:
```javascript
// In submit idea modals
<option value="New Field">New Field</option>
```

### Review Criteria
Customize review criteria in `ReviewSystem.js`:
```javascript
const criteriaByType = {
    idea: [
        { id: 'novelty', label: 'Novelty & Innovation' },
        { id: 'feasibility', label: 'Technical Feasibility' },
        // Add more criteria...
    ]
};
```

## 🔌 API Integration

### GitHub Integration
The interface includes demo GitHub OAuth with real integration points:
```javascript
// Replace demo login with real OAuth
function initiateGitHubLogin() {
    window.location.href = 'https://github.com/login/oauth/authorize?client_id=YOUR_CLIENT_ID';
}
```

### Backend Integration
Ready for backend API integration:
```javascript
// Replace localStorage with API calls
async function saveProject(project) {
    const response = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(project)
    });
    return response.json();
}
```

## 📊 Analytics

### Built-in Metrics
- Project count by field and status
- Author contribution rankings
- Average project completeness
- Review activity tracking
- Pipeline stage distribution

### Custom Analytics
Add custom tracking in `ProjectDataManager.js`:
```javascript
calculateCustomMetrics() {
    // Add your custom analytics logic
}
```

## 🛠️ Troubleshooting

### Common Issues

**CORS Errors**: 
- Serve files via HTTP server, not file:// protocol
- Interface includes embedded fallback data for development

**Data Not Persisting**:
- Check browser localStorage limits
- Verify localStorage is enabled in browser settings

**Reviews Not Advancing Projects**:
- Verify PipelineManager is loaded (`window.PipelineManager`)
- Check console for advancement calculation logs
- Ensure review scores meet threshold requirements

**Styling Issues**:
- Clear browser cache after CSS changes
- Check CSS variable definitions in `:root`
- Verify responsive breakpoints for mobile devices

## 🚀 Deployment

### Static Hosting
The interface is ready for deployment on:
- **GitHub Pages**: Push to gh-pages branch
- **Netlify**: Connect GitHub repository
- **Vercel**: Import project from GitHub
- **Apache/Nginx**: Upload files to web root

### Production Checklist
- [ ] Update GitHub OAuth client ID for production domain
- [ ] Configure analytics tracking (Google Analytics, etc.)
- [ ] Set up error logging and monitoring
- [ ] Optimize images and assets for production
- [ ] Configure proper HTTPS and security headers

## 📈 Performance

### Optimization Features
- **Lazy Loading**: Components load on-demand
- **Caching**: LocalStorage reduces server requests  
- **Efficient DOM**: Minimal reflows and repaints
- **Compressed Assets**: Optimized CSS and JavaScript

### Monitoring
Monitor performance with:
```javascript
// Add to any page
console.time('page-load');
window.addEventListener('load', () => {
    console.timeEnd('page-load');
});
```

## 🔒 Security

### Current Security Features
- **Input Validation**: XSS protection on all form inputs
- **CSRF Protection**: No state-changing GET requests
- **Content Security**: No eval() or unsafe dynamic content
- **Secure Defaults**: All external links open in new tabs

### Production Security
For production deployment:
- Implement proper authentication
- Add HTTPS enforcement
- Configure security headers
- Set up rate limiting for API endpoints

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test locally
4. Commit with descriptive messages
5. Push and create pull request

### Code Style
- Use consistent indentation (2 spaces)
- Follow existing naming conventions
- Add comments for complex logic
- Test all interactive features before committing

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with modern web standards (HTML5, CSS3, ES6+)
- Inspired by GitHub's collaborative development model
- Designed for the llmXive automated scientific discovery platform

---

**Version**: 2.0.0  
**Last Updated**: July 8, 2025  
**Status**: Production Ready ✅