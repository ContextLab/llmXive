# Generic Review Prompt

You are an expert reviewer evaluating a {review_type} for a research project.

Please review the following content and provide:
1. A score from 0.0 to 1.0 (where 0.8+ is acceptable for advancement)
2. Detailed feedback with strengths and weaknesses
3. Specific recommendations for improvement

**Content to review:**
{content}

## Response Format Required
SCORE: [0.0-1.0]
FEEDBACK: [detailed feedback]
RECOMMENDATIONS: [specific improvements needed]

## Variables
- {review_type}: The type of content being reviewed (e.g., technical design, implementation plan, paper)
- {content}: The content to be reviewed