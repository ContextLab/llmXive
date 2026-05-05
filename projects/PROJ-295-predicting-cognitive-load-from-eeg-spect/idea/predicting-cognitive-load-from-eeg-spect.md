---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Predicting Cognitive Load from EEG Spectral Power Changes During Naturalistic Viewing

**Field**: neuroscience

## Research question

Can spectral power features (specifically alpha and theta band ratios) extracted from EEG during naturalistic video viewing reliably predict trial-level cognitive load estimates derived from behavioral proxies such as gaze fixation stability?

## Motivation

Current cognitive load measures often rely on subjective reports or intrusive physiological markers that disrupt naturalistic tasks. This project addresses the gap in establishing a continuous, non-invasive EEG-based metric for mental effort that is compatible with real-world viewing paradigms. Validating this relationship could enable adaptive learning systems that adjust content difficulty based on real-time neural feedback.

## Related work

- [Tracking Naturalistic Linguistic Predictions with Deep Neural Language Models (2019)](http://arxiv.org/abs/1909.04400v1) — Supports the use of naturalistic paradigms for neural prediction tasks rather than controlled categorical designs.
- [Human brain distinctiveness based on EEG spectral coherence connectivity (2014)](http://arxiv.org/abs/1403.6384v1) — Validates EEG spectral features as stable neural markers suitable for individual and state-based analysis.
- [A First Step in Combining Cognitive Event Features and Natural Language Representations to Predict Emotions (2017)](http://arxiv.org/abs/1710.08048v1) — Demonstrates the feasibility of linking cognitive features to internal psychological states.

## Expected results

We expect to observe a significant negative correlation between theta/alpha power ratios and gaze fixation stability, indicating higher load corresponds to specific spectral shifts. A ridge regression model trained on these features should achieve a test RMSE significantly lower than a mean-baseline predictor. Evidence will be considered sufficient if cross-validated R² exceeds 0.2 on held-out subjects.

## Methodology sketch

- **Data Acquisition**: Download pre-processed EEG data from OpenNeuro (e.g., ds000246: https://openneuro.org/datasets/ds000246/versions/1.0.0) to ensure public availability and reproducibility.
- **Preprocessing**: Use MNE-Python to bandpass filter (1–45 Hz), downsample to 250 Hz to fit 7GB RAM constraints, and remove line noise (50/60 Hz).
- **Artifact Reduction**: Apply Independent Component Analysis (ICA) to remove eye-blink artifacts; retain only clean epochs.
- **Feature Extraction**: Compute Power Spectral Density (PSD) using Welch's method; extract mean power for theta (4–7 Hz) and alpha (8–12 Hz) bands per channel.
- **Label Generation**: Derive cognitive load proxies from accompanying behavioral logs (e.g., gaze variance or self-report timestamps) aligned to EEG epochs.
- **Model Training**: Train a Ridge Regression model (scikit-learn) using 80% of subjects for training; tune regularization alpha via 5-fold cross-validation.
- **Statistical Validation**: Evaluate performance using Pearson correlation (r) and Root Mean Squared Error (RMSE) on the 20% held-out test set.
- **Computational Constraints**: Limit parallel processing to 2 CPU cores to stay within GitHub Actions runner limits; ensure total runtime does not exceed 4 hours.

## Duplicate-check

- Reviewed existing ideas: None provided in session.
- Closest match: None identified.
- Verdict: NOT a duplicate
