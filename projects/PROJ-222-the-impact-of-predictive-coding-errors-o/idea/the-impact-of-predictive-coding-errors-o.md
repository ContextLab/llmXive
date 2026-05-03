---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Predictive Coding Errors on Subjective Time Perception

**Field**: psychology

## Research question

Does manipulating the predictability of sequential stimuli alter participants' duration estimates, and do larger prediction errors correlate with overestimation of elapsed time?

## Motivation

Predictive coding theory suggests the brain continuously updates internal models based on prediction errors, yet its role in temporal perception remains underexplored. Understanding whether prediction error signals stretch subjective time could bridge computational neuroscience models with behavioral time perception research, addressing a gap in how cognitive resource allocation affects temporal experience.

## Related work

- [Whatever next? Predictive brains, situated agents, and the future of cognitive science (2013)](https://doi.org/10.1017/s0140525x12000477) — Foundational review establishing predictive coding as a unifying framework for brain function, providing theoretical basis for prediction error manipulation in temporal tasks.

## Expected results

We expect that unpredictable stimulus sequences will produce systematically longer duration estimates compared to predictable sequences. This would be confirmed by a significant main effect of predictability condition in duration estimation data, with effect sizes (Cohen's d) exceeding 0.5 indicating medium-to-large evidence for prediction error's temporal impact.

## Methodology sketch

- **Data source**: Download existing time perception datasets from OpenML (e.g., temporal bisection tasks) and HuggingFace Datasets (cognitive science section) using `wget`/`curl` with explicit DOIs documented in `data/README.md`.
- **Preprocessing**: Filter datasets for studies using sequential stimuli with known predictability manipulations; extract duration estimates, stimulus timing, and condition labels into standardized CSV format.
- **Prediction error quantification**: Compute sequence predictability metrics (e.g., entropy, transition probability) for each trial based on stimulus patterns.
- **Statistical modeling**: Fit linear mixed-effects models with duration estimate as outcome, predictability level as fixed effect, and participant ID as random intercept using Python's `statsmodels` or `pingouin`.
- **Hypothesis testing**: Apply paired t-tests (or Wilcoxon signed-rank for non-normal data) comparing duration estimates between high vs. low predictability conditions.
- **Effect size calculation**: Compute Cohen's d and 95% confidence intervals for main effects.
- **Visualization**: Generate forest plots of condition effects and residual diagnostic plots using `matplotlib`/`seaborn`.
- **Power analysis**: Run post-hoc power analysis with `statsmodels.stats.power` to assess whether existing sample sizes (N≥30 per condition) provide adequate power (≥0.80).
- **Reproducibility**: All code and analysis scripts stored in `analysis/` with requirements.txt pinned; Dockerfile provided for environment consistency.
- **Runtime optimization**: Process datasets in chunks to stay within 7GB RAM; parallelize bootstrap resampling across 2 CPU cores using `joblib`.

## Duplicate-check

- Reviewed existing ideas: None in current corpus (first fleshed-out idea in psychology field).
- Closest match: N/A (no prior ideas in this field).
- Verdict: NOT a duplicate
