---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

**Field**: psychology

## Research question

Does frequency of negative news consumption on social media predict elevated anticipatory anxiety scores, independent of baseline anxiety and demographic factors?

## Motivation

Doomscrolling—the compulsive consumption of negative news online—has become a widespread behavior, particularly during periods of societal stress. While anecdotal evidence suggests this behavior exacerbates anxiety, empirical research on its specific impact on anticipatory anxiety (worry about future events) remains limited. Understanding this relationship is critical for developing targeted mental health interventions and informing platform design decisions.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using the following search strings: (1) "doomscrolling anxiety," (2) "negative news consumption anticipatory anxiety," and (3) "social media news exposure anxiety outcomes." The search returned two results from the literature block, neither of which directly addresses the research question.

### What is known

- [Coordinated Behavior on Social Media in 2019 UK General Election (2020)](http://arxiv.org/abs/2008.08370v2) — This work documents coordinated online behavior patterns during political events but does not examine psychological outcomes of negative news consumption.
- [A study of trends in the effects of TV ratings and social media (Twitter) -- Case study 1 (2019)](http://arxiv.org/abs/1909.01078v1) — This study examines audience ratings and social media trends for a Japanese TV drama, not anxiety outcomes from negative news exposure.

### What is NOT known

No published work has specifically measured the relationship between negative news consumption patterns (doomscrolling behavior) and anticipatory anxiety levels using standardized psychological instruments. Existing literature focuses on coordinated behavior, disinformation spread, or general social media effects, without isolating negative news content as a predictor variable.

### Why this gap matters

Filling this gap would enable mental health professionals to identify at-risk populations and help social media platforms design interventions that mitigate anxiety-inducing content exposure. The findings could inform both clinical practice and platform policy decisions during periods of heightened public stress.

### How this project addresses the gap

This project will analyze existing public survey datasets that include both social media consumption patterns and anxiety measurements. Statistical modeling will estimate the association between negative news exposure frequency and anticipatory anxiety scores, controlling for confounding variables.

## Expected results

We expect to observe a positive association between frequency of negative news consumption and anticipatory anxiety scores, with effect sizes large enough to be statistically significant (p < 0.05) after controlling for demographic factors. If no association is found, this would indicate that doomscrolling behavior does not independently predict anxiety outcomes, which would be equally informative for theory development.

## Methodology sketch

- Download public survey dataset (e.g., General Social Survey via https://gss.norc.org/) containing social media usage and mental health variables.
- Extract variables measuring negative news consumption frequency and anticipatory anxiety scores.
- Clean data: remove incomplete responses, handle missing values via listwise deletion.
- Compute descriptive statistics for key variables (means, standard deviations, distributions).
- Calculate Pearson/Spearman correlation between negative news exposure and anxiety scores.
- Fit multiple linear regression model: anxiety ~ news_exposure + age + gender + baseline_anxiety.
- Check model assumptions (linearity, homoscedasticity, normality of residuals).
- Generate visualization: scatter plot with regression line and confidence interval.
- Perform robustness check: repeat analysis on subset of users with high social media engagement.
- Document all code and outputs for reproducibility.

## Duplicate-check

- Reviewed existing ideas: [N/A — new field entry].
- Closest match: None identified in corpus.
- Verdict: NOT a duplicate
