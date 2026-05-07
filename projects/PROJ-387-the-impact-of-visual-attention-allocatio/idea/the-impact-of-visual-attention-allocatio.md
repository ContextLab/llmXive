---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Visual Attention Allocation on Recall of Emotionally Valenced Stories

**Field**: psychology

## Research question

Does visual attention allocation during reading—measured by fixation duration, saccade patterns, and gaze distribution—predict subsequent recall accuracy for emotionally valenced narrative content?

## Motivation

Emotional valence influences memory consolidation, yet the attentional mechanisms that mediate this effect during reading remain poorly understood. Identifying attentional signatures that predict memory for emotionally salient details could inform educational strategies and therapeutic interventions that target memory enhancement. This work addresses the gap between established emotional memory effects and the real-time attentional processes that drive them.

## Literature gap analysis

### What we searched

Searches were conducted across Semantic Scholar and arXiv using query terms including "eye-tracking reading emotional text," "visual attention memory recall narrative," and "fixation duration emotional valence story." The literature returned minimal results directly connecting eye-tracking attention metrics with emotional valence effects on story recall.

### What is known

- [The power of negative and positive episodic memories (2022)](https://doi.org/10.3758/s13415-022-01013-z) — Establishes that emotionally valenced episodic memories show enhanced recall compared to neutral content, but does not examine the attentional processes during encoding that produce this effect.

### What is NOT known

No published work has directly measured eye-tracking metrics (fixation duration, saccade length, gaze distribution) while participants read emotionally valenced stories and then correlated these metrics with subsequent recall accuracy. The specific attentional signatures that predict memory for positive versus negative versus neutral narrative details remain uncharacterized in reading contexts.

### Why this gap matters

Understanding attentional predictors of emotional memory could enable real-time assessment of engagement and memory encoding during reading tasks. This has practical implications for educational materials design, therapeutic narrative interventions, and digital learning platforms that aim to optimize information retention.

### How this project addresses the gap

This project re-analyzes existing public eye-tracking reading datasets with emotional valence annotations, extracting fixation and saccade metrics and correlating them with available recall measures. The methodology produces the first quantitative mapping between attentional allocation patterns and memory outcomes for emotionally valenced narratives.

## Expected results

We expect to observe differential fixation durations and saccade patterns for emotionally valenced versus neutral story passages that correlate with higher recall accuracy for those passages. A null result (no correlation) would indicate that emotional memory enhancement operates through mechanisms independent of overt attention allocation, which would also be theoretically informative.

## Methodology sketch

- Download publicly available eye-tracking datasets from OpenNeuro or similar repositories (e.g., datasets containing reading tasks with emotional content annotations)
- Preprocess eye-tracking data to extract fixation duration, saccade amplitude, and gaze heatmaps for each story passage
- Segment stories into emotionally valenced (positive, negative, neutral) and neutral passages using existing valence annotations or NLP-based sentiment scoring
- Extract recall performance scores from associated behavioral data (free recall accuracy, recognition task performance)
- Compute correlation coefficients between attentional metrics (fixation duration, saccade length) and recall accuracy for each valence category
- Apply linear mixed-effects models to account for participant-level random effects and passage-level fixed effects
- Perform statistical significance testing (p < 0.05) with Bonferroni correction for multiple comparisons across valence categories
- Generate visualizations showing attentional metric distributions by valence and recall performance
- Document all data sources, preprocessing steps, and statistical code for reproducibility

## Duplicate-check

- Reviewed existing ideas: None in current field corpus.
- Closest match: None identified.
- Verdict: NOT a duplicate
