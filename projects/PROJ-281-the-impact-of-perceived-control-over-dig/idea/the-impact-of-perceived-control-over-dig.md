---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Perceived Control Over Digital Environments on Anxiety

**Field**: psychology

## Research question

Does perceived control over digital interface elements correlate with reduced anxiety markers in public social media traces?

## Motivation

Digital environments often limit user agency, potentially exacerbating stress. Understanding the relationship between control and anxiety can inform better interface design. This study addresses the gap in computational methods for measuring this relationship using existing digital traces rather than new human experiments.

## Related work

- [Connecting Through Technology During the Coronavirus Disease 2019 Pandemic: Avoiding “Zoom Fatigue”](https://doi.org/10.1089/cyber.2020.29188.bkw) — Editorial discussing digital stress and fatigue, relevant to the anxiety component of digital environments.
- [Feeling Anxious? Perceiving Anxiety in Tweets using Machine Learning](http://arxiv.org/abs/1909.06959v1) — Provides a predictive measurement tool to examine perceived anxiety from a longitudinal perspective using non-intrusive machine learning.

## Expected results

We expect to find a negative correlation between indicators of user control (e.g., customization options, content filtering) and anxiety prevalence in text data. Evidence will be confirmed if regression models show significant coefficients (p < 0.05) linking control features to lower anxiety scores.

## Methodology sketch

- Download public social media datasets from HuggingFace Datasets or OpenML (e.g., Twitter sentiment/behavioral archives).
- Preprocess text data (tokenization, removal of non-linguistic tokens) using Python (Pandas, NLTK).
- Apply the anxiety detection model described in [Feeling Anxious? Perceiving Anxiety in Tweets using Machine Learning](http://arxiv.org/abs/1909.06959v1) to label anxiety levels.
- Extract metadata proxies for "perceived control" (e.g., presence of filter keywords, timestamp regularity).
- Perform statistical analysis (Pearson correlation, linear regression) using Scikit-learn to test the hypothesis.
- Generate visualization plots (matplotlib) to display the relationship between control proxies and anxiety scores.
- Validate results using 5-fold cross-validation to ensure model robustness within 6-hour GHA limits.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: None identified.
- Verdict: NOT a duplicate
