---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Visual Search Strategies on Attentional Capture by Emotional Faces

**Field**: psychology

## Research question

Do individuals employ global (holistic) or local (feature-based) visual search strategies when detecting emotional faces in complex scenes, and does fixation pattern predict detection efficiency?

## Motivation

Emotional face detection is a core component of social cognition, yet the relative contributions of holistic versus feature-based processing remain contested. Understanding this distinction matters for identifying attentional biases in clinical populations and optimizing visual interface design. This project addresses the gap between behavioral detection data and underlying eye-movement strategies.

## Related work

- [Gaze cueing of attention: Visual attention, social cognition, and individual differences](https://doi.org/10.1037/0033-2909.133.4.694) — Foundational review on how eyes convey attentional and emotional information, establishing gaze as a key variable in social attention.
- [Unlocking the Emotional World of Visual Media: An Overview of the Science, Research, and Impact of Understanding Emotion](http://arxiv.org/abs/2307.13463v1) — Discusses computational approaches to emotion recognition in visual media, relevant for automated stimulus analysis.
- [GLA in MediaEval 2018 Emotional Impact of Movies Task](http://arxiv.org/abs/1911.12361v1) — Presents methods for quantifying emotional impact from audiovisual stimuli, offering parallels for eye-movement metric extraction.

*Note: TODO — additional literature search needed for specific visual search with emotional face paradigms.*

## Expected results

We expect local feature fixation (eyes/mouth) to correlate with faster detection of high-arousal emotions (fear, anger) compared to global processing. Detection speed will be measured via response time in a target-absent/target-present paradigm, with statistical significance determined by mixed-effects modeling. A medium effect size (Cohen's d ≈ 0.5) would support the feature-based hypothesis.

## Methodology sketch

- **Data acquisition**: Download publicly available eye-tracking datasets from HuggingFace Datasets (e.g., `eyetracking-emotion-face-search` if available) or OpenML repositories; verify accessibility via `wget`/`curl` in GHA job.
- **Stimulus filtering**: Extract trials containing emotional faces (happy, fearful, neutral) from the dataset; exclude trials with missing gaze coordinates or response times.
- **Feature extraction**: Compute fixation duration on eye regions vs. mouth regions using predefined face ROI masks; calculate saccade amplitude and dispersion metrics.
- **Strategy classification**: Cluster participants into "local" vs. "global" processors using k-means on fixation distribution features (k=2).
- **Statistical analysis**: Fit linear mixed-effects model with detection time as outcome, processing strategy as fixed effect, and participant as random intercept (using `lme4` in R or `statsmodels` in Python).
- **Power analysis**: Run post-hoc power calculation to confirm sample size adequacy (target N ≥ 30 participants, achievable within 7GB RAM).
- **Visualization**: Generate publication-ready plots of fixation heatmaps and detection time distributions using `matplotlib` or `ggplot2`.
- **Execution**: All steps must complete within a single 6-hour GHA job; decompose into ≤30-minute atomic tasks if needed.

## Duplicate-check

- Reviewed existing ideas: [N/A — existing_idea_paths not provided]
- Closest match: [None identified]
- Verdict: NOT a duplicate

*Note: Scope constraint check — methodology uses only public datasets, no GPU, no wet-lab components, and all analysis fits within GHA free-tier limits.*
