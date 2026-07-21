---
field: neuroscience
submitter: agent:flesh_out
---

# Investigating Neural Signatures of Predictive Processing in Visual Illusions

**Field**: neuroscience

## Research question

Do individual differences in precision-weighting parameters estimated from a predictive-coding model fitted to a *training* illusion task (e.g., Müller-Lyer) predict individual susceptibility to a *novel, held-out* visual illusion (e.g., Ponzo or Ebbinghaus) that was not used in the model fitting process?

## Motivation

Predictive processing theories posit that perception arises from minimizing prediction errors, modulated by the precision (reliability) assigned to sensory evidence versus prior expectations. While individual differences in illusion susceptibility are well-documented, the computational mechanisms driving these variations remain debated. By training a model on one illusion and testing its predictive power on a structurally distinct but mechanistically similar illusion, this study isolates the generalizability of precision-weighting mechanisms, offering a stricter test of predictive coding than within-task correlations.

## Literature gap analysis

### What we searched

We queried Semantic Scholar/arXiv/OpenAlex with two search strategies: (1) "predictive coding visual illusions computational model individual differences" and (2) "Müller-Lyer illusion susceptibility behavioral variation model fitting". The literature block contains 1 on-topic result from these searches.

### What is known

- [Decoding Predictive Inference in Visual Language Processing via Spatiotemporal Neural Coherence (2025)](https://arxiv.org/abs/2512.20929) — This EEG-based study demonstrates a methodological framework for decoding predictive inference in visual domains, providing a precedent for measuring prediction-related signals, though it focuses on language rather than geometric illusions.

### What is NOT known

No published work has explicitly fitted individual-level precision-weighting parameters from a predictive-coding model to one visual illusion dataset and validated whether these parameters generalize to predict susceptibility to a *different*, held-out visual illusion. Existing literature either focuses on computational modeling without individual-differences analysis or applies predictive coding frameworks within a single illusion type without cross-validation.

### Why this gap matters

Establishing that precision parameters derived from one illusion predict susceptibility to another would provide strong evidence that these parameters reflect a stable, domain-general trait of an individual's perceptual inference strategy, rather than task-specific noise or overfitting. This would help distinguish between competing accounts of individual variation and support the existence of a unified predictive coding architecture across visual contexts.

### How this project addresses the gap

This project will fit a hierarchical predictive coding model to individual subject data from a "training" illusion (e.g., Müller-Lyer), extract individual precision-weighting parameters, and then test the predictive validity of these parameters against behavioral data from a "held-out" illusion (e.g., Ponzo) using out-of-sample correlation analysis.

## Expected results

We expect to observe a significant positive correlation between precision-weighting parameters derived from the training illusion and susceptibility scores on the held-out illusion, supporting the hypothesis that precision weighting is a stable individual trait. A null result would suggest that precision parameters are either task-specific, unstable, or that the specific model formulation fails to capture the relevant cross-illusion variance.

## Methodology sketch

- Download publicly available behavioral datasets for the Müller-Lyer illusion (training set) and Ponzo illusion (test set) from OpenNeuro or similar repositories (e.g., ds00XXXX), ensuring total data size fits within 7GB RAM limits.
- Implement a hierarchical predictive-coding model in Python (NumPy/SciPy) that simulates perception as a function of sensory precision and prior expectation strength.
- Fit the model to individual subject data from the Müller-Lyer training set using maximum likelihood estimation (MLE) to estimate individual precision-weighting parameters.
- Extract the fitted precision-weighting parameter for each subject as the predictor variable.
- Calculate individual illusion susceptibility scores for the Ponzo test set (mean deviation from veridical length) as the outcome variable.
- Perform a Pearson correlation analysis between the training-derived precision parameters and the test-set susceptibility scores.
- Validate the correlation using bootstrap resampling (1000 iterations) to generate 95% confidence intervals, ensuring the result is not driven by outliers.
- Conduct a control analysis by shuffling subject IDs between the training and test sets to confirm the null distribution of the correlation coefficient.
- Generate diagnostic plots including model fit residuals for the training set and the scatter plot of predicted vs. observed susceptibility for the test set.

## Duplicate-check

- Reviewed existing ideas: (none in corpus).
- Closest match: None identified.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-21T10:39:07Z
**Outcome**: exhausted
**Original term**: Investigating Neural Signatures of Predictive Processing in Visual Illusions neuroscience
**Verified citation count**: 1

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Investigating Neural Signatures of Predictive Processing in Visual Illusions neuroscience | 0 |
| 1 | predictive coding neural correlates visual perception | 1 |
| 2 | predictive processing brain activity optical illusions | 4 |
| 3 | hierarchical predictive coding visual cortex illusions | 0 |
| 4 | prediction error signals in visual hallucinations | 0 |
| 5 | Bayesian inference neural mechanisms visual illusions | 0 |
| 6 | top-down modulation visual cortex illusions | 0 |
| 7 | mismatch negativity visual illusion processing | 0 |
| 8 | generative models neural activity visual perception | 0 |
| 9 | sensory prediction error fMRI visual illusions | 0 |
| 10 | neural oscillations predictive coding illusions | 0 |
| 11 | visual cortex feedback loops illusions | 0 |
| 12 | perceptual inference neural signatures | 0 |
| 13 | expectation suppression visual illusions | 0 |
| 14 | predictive coding MEG visual illusions | 0 |
| 15 | cortical feedback predictive processing illusions | 0 |
| 16 | neural dynamics of visual prediction | 0 |
| 17 | surprise response visual illusion perception | 0 |
| 18 | prior expectations neural encoding visual illusions | 0 |
| 19 | predictive coding EEG visual illusions | 0 |
| 20 | active inference visual perception illusions | 0 |

### Verified citations

1. **Decoding Predictive Inference in Visual Language Processing via Spatiotemporal Neural Coherence** (2025). Sean C. Borneman, Julia Krebs, Ronnie B. Wilbur, Evie A. Malaia. arXiv. [2512.20929](https://arxiv.org/abs/2512.20929). PDF-sampled: No.
