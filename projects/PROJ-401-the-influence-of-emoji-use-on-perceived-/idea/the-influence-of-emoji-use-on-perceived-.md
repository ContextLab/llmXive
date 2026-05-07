---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Influence of Emoji Use on Perceived Emotional Intensity in Text

**Field**: psychology

## Research question

Does the frequency and type of emoji in digital text messages influence how emotionally intense recipients perceive those messages to be?

## Motivation

Emoji are ubiquitous in digital communication yet their specific contribution to perceived emotional intensity remains poorly understood beyond anecdote. Understanding this relationship would clarify how nonverbal cues function in text-only media and inform theories of emotion expression in computer-mediated communication.

## Literature gap analysis

### What we searched

Searched for literature on emoji effects on emotional perception using queries for "emoji emotional intensity," "emoji perceived emotion," and "digital communication emotional expression" across Semantic Scholar, arXiv, and OpenAlex. The search returned limited results specifically addressing emoji and emotional intensity ratings.

### What is known

- [The Social Effects of Emotions (2021)](https://doi.org/10.1146/annurev-psych-020821-010855) — Reviews evidence that emotional expressions impact observers' affect, cognition, and behavior, establishing theoretical foundation for studying emoji as emotional signals.

### What is NOT known

No published work has systematically quantified the relationship between emoji usage patterns (frequency, type, combinations) and human-rated emotional intensity in text messages. The specific contribution of emoji beyond textual content to perceived intensity remains unmeasured.

### Why this gap matters

Filling this gap would clarify the functional role of emoji in digital communication, inform platform design for emotion-aware systems, and contribute to theories of nonverbal cue substitution in text-based media.

### How this project addresses the gap

This project will analyze existing message corpora with human intensity ratings to measure the statistical relationship between emoji characteristics and perceived emotional intensity, directly quantifying the previously unmeasured effect size.

## Expected results

We expect to find that emoji presence and frequency positively correlate with perceived emotional intensity ratings, with specific emoji types (e.g., heart, exclamation marks) showing stronger associations than others. A null result—no significant relationship—would be equally informative, suggesting emoji function primarily for tone clarification rather than intensity amplification.

## Methodology sketch

- Download CMU Text Message Corpus or similar public dataset with text messages and available emotional annotations from UCI Machine Learning Repository or OpenML
- Parse messages to extract emoji presence, frequency, and type using Python emoji library
- If human intensity ratings are not in dataset, implement crowdsourced rating task with N=50 raters evaluating N=200 messages for emotional intensity on 1-7 Likert scale
- Compute correlation between emoji metrics (binary presence, count, categorical type) and intensity ratings using Pearson/Spearman correlation
- Run linear regression controlling for textual length and punctuation to isolate emoji effect
- Apply Bonferroni correction for multiple emoji-type comparisons
- Generate effect size estimates (Cohen's d) for significant associations
- Visualize results with coefficient plots and correlation heatmaps

## Duplicate-check

- Reviewed existing ideas: None in corpus.
- Closest match: None found.
- Verdict: NOT a duplicate
