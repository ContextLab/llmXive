---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Influence of Visual Salience on Attentional Bias in Moral Decision-Making

**Field**: psychology

## Research question

Does visual salience of actors in morally ambiguous images systematically bias human blame attribution, independent of the actors' actual role in the moral event?

## Motivation

Visual attention mechanisms are well-documented to prioritize salient stimuli (bright colors, high contrast, motion), but it is unclear whether this perceptual bias extends to higher-order moral reasoning. If salient actors are disproportionately blamed regardless of their actual culpability, this could have implications for legal judgments, media framing, and eyewitness testimony. This gap is particularly pressing given the increasing use of visual media in public discourse and legal proceedings.

## Literature gap analysis

### What we searched

Searches were conducted via Semantic Scholar / arXiv / OpenAlex using two distinct queries: (1) "visual salience moral judgment blame attribution" and (2) "attentional bias moral decision-making imagery". The literature search returned one result from the provided verified block, which focuses on LLM gender bias in economics rather than visual attention mechanisms in moral psychology.

### What is known

- None of the retrieved results were on-topic for the specific intersection of visual salience, moral psychology, and blame attribution.

### What is NOT known

No published work has experimentally tested whether systematically varying visual salience of actors in moral scenarios (while holding their actual role constant) produces measurable shifts in blame ratings. The specific mechanism—whether this operates through attentional capture, perceived agency, or heuristic processing—remains unexamined in the literature.

### Why this gap matters

Understanding whether visual design features can unconsciously bias moral judgments would inform evidence-based guidelines for media presentation, legal exhibits, and public communication. If salience effects exist, they represent a systematic source of bias that could be mitigated in high-stakes decision contexts.

### How this project addresses the gap

This project would create controlled stimuli varying only in visual salience of actors while holding moral scenario content constant, then measure blame attribution differences. However, this requires human participant data collection which cannot be executed within the GitHub Actions runner constraints.

## Expected results

We expect a statistically significant positive correlation between objective visual salience measures (e.g., saliency map intensity) and blame attribution ratings. A null result would suggest that moral reasoning operates independently of low-level visual attention mechanisms. Either outcome would be informative: a positive effect would demonstrate a novel bias pathway, while a null effect would support the robustness of moral reasoning against perceptual interference.

## Methodology sketch

- **Stimulus creation**: Use Open Images Dataset or similar public image repository to extract images depicting multi-agent scenarios; manipulate visual salience of target actors via color saturation, contrast, and edge intensity using standard image processing libraries (PIL/OpenCV).
- **Salience quantification**: Compute objective visual salience metrics for each actor (saliency map integration, contrast ratio, color distinctiveness) using existing saliency detection algorithms.
- **Moral scenario annotation**: Have independent raters verify that actors' actual moral role (perpetrator, bystander, victim) remains constant across salience manipulations.
- **Participant data collection**: **Requires external human recruitment** (e.g., Prolific) to rate perceived culpability of each actor on Likert scale. This step violates the "No new experimental data collection" constraint for GitHub Actions runners.
- **Statistical analysis**: Fit linear mixed-effects model with visual salience as predictor, blame rating as outcome, and random effects for participant and stimulus; test significance of salience coefficient.
- **Power analysis**: Pre-register minimum detectable effect size (e.g., r = 0.2) and required N (e.g., 200 participants) for adequate power.

## Duplicate-check

- Reviewed existing ideas: None found in current corpus.
- Closest match: N/A
- Verdict: **rejected — out of scope**
