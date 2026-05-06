---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Simulated Social Exclusion on Subsequent Prosocial Behavior

**Field**: psychology

## Research question

Does experimentally induced social exclusion reduce subsequent willingness to engage in prosocial behavior (e.g., monetary donation) among adults?

## Motivation

Social exclusion is a frequent experience in online and offline interactions, yet its downstream effects on cooperative behavior remain inconsistent across studies. Understanding this causal link is critical for designing interventions that mitigate antisocial outcomes following perceived rejection. This research addresses the need for robust evidence on whether exclusion directly diminishes prosociality or if the effect is moderated by other factors.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using terms including "social exclusion prosocial behavior," "Cyberball donation," and "rejection cooperation." The search focused on identifying primary empirical studies that measured exclusion manipulations and subsequent economic or behavioral prosocial outcomes.

### What is known

- [Global Brain Dynamics During Social Exclusion Predict Subsequent Behavioral Conformity (2017)](http://arxiv.org/abs/1710.00869v1) — Establishes that social exclusion alters behavioral adaptation, specifically regarding conformity, though not necessarily general prosociality.
- [Toward understanding the functions of peer influence: A summary and synthesis of recent empirical research (2021)](https://doi.org/10.1111/jora.12606) — Synthesizes evidence that peer influence shapes attitudes and behaviors, highlighting the importance of social context in behavioral outcomes.

### What is NOT known

There is no consolidated analysis linking simulated exclusion directly to monetary donation behavior using publicly available secondary datasets. Most existing work focuses on neural correlates or conformity rather than economic generosity following rejection.

### Why this gap matters

Filling this gap would clarify whether online exclusion mechanisms (e.g., being ignored in chat) directly harm community cooperation. This knowledge could inform platform policies and moderation tools designed to preserve prosocial norms in digital spaces.

### How this project addresses the gap

We will aggregate and re-analyze open behavioral datasets from the Open Science Framework containing exclusion tasks and outcome measures. By applying standardized statistical models across these datasets, we will quantify the exclusion-prosociality effect size where primary literature is silent.

## Expected results

We expect to find a statistically significant negative correlation between exclusion intensity and donation amounts, though the effect size may vary by baseline empathy. A null result would suggest that prosocial behavior is resilient to brief exclusion, challenging current intervention models.

## Methodology sketch

- Identify public datasets on Open Science Framework (OSF) using the search query `https://osf.io/search?q=cyberball+prosocial`.
- Download raw CSV/JSON data files using `wget` or `curl` scripts within the GitHub Actions environment.
- Preprocess data to standardize exclusion conditions (e.g., "ignored" vs. "included" groups).
- Clean data by removing outliers and handling missing values using standard imputation techniques.
- Compute descriptive statistics for donation amounts across exclusion conditions.
- Perform Linear Regression with donation amount as the dependent variable and exclusion condition as the predictor.
- Conduct sensitivity analysis using ANOVA to check for group differences.
- Visualize results using Python (Matplotlib/Seaborn) on CPU-only runners.
- Generate a summary report of effect sizes and confidence intervals.
- Ensure all scripts run within 6 hours and under 7GB RAM limits.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: None.
- Verdict: NOT a duplicate
