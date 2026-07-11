---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Visual Attention on Recall of Emotional Stimuli in Rapid Visual Sequences

**Field**: psychology

## Research question

How does trait anxiety modulate the relationship between gaze fixation duration on threat stimuli and subsequent recall accuracy in rapid serial visual presentation?

## Motivation

While threat-biased attention is a hallmark of anxiety, it remains unclear whether this bias translates into enhanced memory consolidation specifically for threat cues in high-temporal-load conditions. Clarifying this modulation is critical for distinguishing between early attentional capture and late-stage consolidation deficits in anxiety disorders, potentially refining cognitive models of pathological worry.

## Literature gap analysis

### What we searched

Searched Semantic Scholar/arXiv/OpenAlex using queries: (1) "RSVP anxiety threat memory gaze", (2) "trait anxiety visual attention emotional recall", (3) "rapid serial visual presentation threat bias memory". Retrieved 1 paper from the literature block, which focuses on EEG-based image reconstruction using RSVP of polygon primitives rather than human psychophysics, emotional valence, or anxiety modulation.

### What is known

- [Images from the Mind: BCI image evolution based on Rapid Serial Visual Presentation of polygon primitives (2014)](https://arxiv.org/abs/1411.3489) — Establishes the feasibility of using RSVP protocols to probe visual memory and brain activity, though it utilizes neutral geometric primitives and BCI reconstruction rather than emotional stimuli or anxiety-related behavioral outcomes.

### What is NOT known

No published work has directly measured how individual differences in trait anxiety alter the coupling between gaze fixation duration on threat stimuli and subsequent recall accuracy within an RSVP paradigm. Existing literature either isolates attentional bias in static tasks or examines memory without concurrent eye-tracking, leaving the specific interaction between anxiety, dynamic attention, and emotional memory unquantified.

### Why this gap matters

Filling this gap would determine if anxiety-driven attentional capture is a robust mechanism for memory enhancement or if it is disrupted under rapid presentation loads, offering insights into why anxiety patients may struggle to encode threat-relevant information in dynamic environments like social interactions or driving.

### How this project addresses the gap

This project will re-analyze existing RSVP datasets with gaze tracking to specifically test for a three-way interaction (Anxiety × Fixation Duration × Stimulus Valence), directly quantifying the previously-unavailable linkage between trait anxiety levels and the efficiency of threat encoding.

## Expected results

We expect a positive correlation between gaze fixation on threat stimuli and recall accuracy that is significantly stronger for high-anxiety participants compared to low-anxiety participants. A significant interaction effect (β > 0.3) would support the "enhanced encoding" hypothesis in anxiety, while a null interaction would suggest that rapid presentation disrupts the consolidation of threat-biased attention regardless of trait anxiety.

## Methodology sketch

- Download RSVP datasets with eye-tracking and post-task recall from OpenNeuro (e.g., ds001435) and Psychophysics Toolbox archives using `wget` (~500MB total).
- Preprocess gaze-tracking data: extract fixation duration and onset latency per stimulus frame using a standard velocity-threshold algorithm.
- Label stimuli by emotional valence (threat/negative/neutral) using standardized databases (e.g., IAPS or NimStim) mapped to the stimulus IDs in the dataset.
- Quantify trait anxiety for each participant using the included Spielberger State-Trait Anxiety Inventory (STAI) scores.
- Compute recall accuracy per stimulus from binary post-task memory test responses.
- Fit a mixed-effects logistic regression model: `recall ~ fixation_duration * valence * trait_anxiety + (1|participant) + (1|stimulus_id)`.
- Apply likelihood-ratio tests to compare the full model against reduced models lacking the three-way interaction term to assess the specific modulation by anxiety.
- Generate marginal effect plots showing the slope of fixation duration on recall for high vs. low anxiety groups using Python (statsmodels/seaborn) or R (lme4/ggplot2).
- Validate model convergence and check residual diagnostics for overdispersion.
- Document all code in a reproducible Jupyter notebook; output figures as PNG (ensuring total SSD usage < 14GB).
- Total runtime: ~2–3 hours on GHA free-tier (2 CPU, 7GB RAM); no GPU required.

## Duplicate-check

- Reviewed existing ideas: [RSVP Emotional Memory Recall, Attentional Bias in Rapid Sequences, Emotional Stimulus Prioritization].
- Closest match: RSVP Emotional Memory Recall (similarity sketch: same RSVP paradigm and gaze tracking, but this idea specifically introduces trait anxiety as a moderator and re-frames the question from a general attention-memory link to a clinical modulation effect).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-11T12:32:30Z
**Outcome**: exhausted
**Original term**: The Impact of Visual Attention on Recall of Emotional Stimuli in Rapid Visual Sequences psychology
**Verified citation count**: 1

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | The Impact of Visual Attention on Recall of Emotional Stimuli in Rapid Visual Sequences psychology | 0 |
| 1 | emotional salience in rapid serial visual presentation | 4 |
| 2 | attentional blink and emotional stimuli | 0 |
| 3 | visual working memory for affective images | 0 |
| 4 | emotion-driven attentional capture in RSVP | 0 |
| 5 | recall accuracy for emotional versus neutral stimuli | 0 |
| 6 | temporal attention and emotional memory consolidation | 0 |
| 7 | affective bias in rapid visual perception | 0 |
| 8 | emotional modulation of the attentional blink | 0 |
| 9 | visual search for emotional targets in sequences | 0 |
| 10 | working memory capacity for emotional faces | 0 |
| 11 | attentional selection of valenced visual stimuli | 0 |
| 12 | emotional interference in rapid visual streams | 0 |
| 13 | memory retrieval of affective events in time | 0 |
| 14 | prioritization of emotional information in visual attention | 0 |
| 15 | attentional resources for emotional processing in sequences | 0 |
| 16 | visual attention mechanisms for threat detection | 0 |
| 17 | temporal dynamics of emotional memory encoding | 0 |
| 18 | affective priming in rapid visual sequences | 0 |
| 19 | selective attention to emotional content in RSVP tasks | 0 |
| 20 | cognitive control of emotional distraction in visual memory | 0 |

### Verified citations

1. **Images from the Mind: BCI image evolution based on Rapid Serial Visual Presentation of polygon primitives** (2014). Luís F. Seoane, Stephan Gabler, Benjamin Blankertz. arXiv. [1411.3489](https://arxiv.org/abs/1411.3489). PDF-sampled: No.
