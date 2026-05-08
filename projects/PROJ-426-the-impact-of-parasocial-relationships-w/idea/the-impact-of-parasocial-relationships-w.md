---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Parasocial Relationships with AI Companions on Loneliness

**Field**: psychology

## Research question

Does the frequency and emotional depth of parasocial engagement with AI companions predict changes in self-reported loneliness levels, and do perceived AI empathy and attachment security mediate this relationship?

## Motivation

Loneliness is a growing public health concern, and AI companions are increasingly marketed as solutions. However, it remains unclear whether these relationships genuinely alleviate loneliness or merely substitute for human connection. Understanding the mechanisms (e.g., perceived empathy, attachment patterns) will inform both clinical guidance and ethical design of AI systems.

## Related work

- [Emotional AI and the rise of pseudo-intimacy: are we trading authenticity for algorithmic affection?](https://doi.org/10.3389/fpsyg.2025.1679324) — Establishes the conceptual framework for understanding AI-human emotional bonds and raises concerns about authenticity in algorithmic relationships.
- [Not a Silver Bullet for Loneliness: How Attachment and Age Shape Intimacy with AI Companions](http://arxiv.org/abs/2602.12476v1) — Demonstrates that personal dispositions (attachment style) and life-stage conditions moderate AI companion effectiveness, suggesting heterogeneous outcomes.
- [AI Companions Reduce Loneliness](http://arxiv.org/abs/2407.19096v1) — Provides behavioral evidence that chatbots can offer coping solutions to loneliness, though mechanisms remain unspecified.
- [Chatbot Companionship: A Mixed-Methods Study of Companion Chatbot Usage Patterns and Their Relationship to Loneliness in Active Users](http://arxiv.org/abs/2410.21596v3) — Directly examines usage patterns and loneliness outcomes in active users, raising ethical questions about psychosocial well-being impacts.

## Expected results

We expect to find a negative correlation between parasocial engagement frequency and loneliness scores, but with significant moderation by attachment security. A null result (no correlation or positive correlation) would indicate AI companions may substitute rather than supplement human connection. Evidence at the p<0.05 level with medium effect size (Cohen's d ≥ 0.5) across multiple subreddits would support generalizability.

## Methodology sketch

- Scrape public Reddit posts from r/Replika, r/characterAI, and r/AICompanions using `pushshift.io` API (no authentication required, historical data available)
- Filter posts containing loneliness-related keywords (lonely, isolation, alone, disconnected) and AI interaction descriptors (chatbot, companion, Replika, character.ai)
- Extract text segments and compute: (a) frequency of AI interaction mentions per user, (b) emotional tone using LIWC or NRC Emotion Lexicon, (c) perceived empathy scores via sentiment analysis
- Calculate user-level loneliness indicators from self-reports in posts (e.g., "I feel less lonely after talking to...")
- Merge interaction metrics with self-reported loneliness changes (pre/post if available, or cross-sectional)
- Perform multiple regression: loneliness_change ~ interaction_frequency + perceived_empathy + attachment_proxy + control_variables
- Conduct mediation analysis to test whether perceived empathy mediates the interaction-loneliness relationship
- Validate findings via bootstrapping (1000 iterations) to assess robustness

## Duplicate-check

- Reviewed existing ideas: The Impact of Parasocial Relationships with AI Companions on Loneliness.
- Closest match: None identified in this corpus (first fleshed-out idea in this project field).
- Verdict: NOT a duplicate
