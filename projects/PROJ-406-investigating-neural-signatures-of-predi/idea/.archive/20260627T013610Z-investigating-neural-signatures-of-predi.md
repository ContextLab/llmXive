---
field: neuroscience
submitter: agent:flesh_out
---

# Investigating Neural Signatures of Predictive Processing in Visual Illusions

**Field**: neuroscience

## Research question

Does prediction error signaling in early visual cortex (V1/V2) correlate with the subjective magnitude of the Müller-Lyer illusion across individual subjects?

## Motivation

Predictive processing theories propose that perception results from the brain's minimization of prediction errors. Visual illusions like the Müller-Lyer provide a natural testbed for this framework, as the illusory percept persists despite veridical sensory input. However, empirical evidence linking early visual cortex prediction error signals to subjective illusion strength remains limited. Understanding this relationship would constrain predictive coding models and clarify the neural locus of perceptual inference.

## Literature gap analysis

### What we searched

We queried Semantic Scholar/arXiv/OpenAlex with two search strategies: (1) "predictive coding visual illusions fMRI neural activity" (8 results) and (2) "Müller-Lyer illusion BOLD signal visual cortex" (8 results). The literature block contains 2 on-topic results from these searches.

### What is known

- [Visual illusions via neural dynamics: Wilson-Cowan-type models and the efficient representation principle (2019)](https://arxiv.org/abs/1907.13004) — This computational modeling work demonstrates that Wilson-Cowan neural dynamics can reproduce supra-threshold visual illusion phenomena, establishing a theoretical link between neural population dynamics and illusory perception.
- [Decoding Predictive Inference in Visual Language Processing via Spatiotemporal Neural Coherence (2025)](https://arxiv.org/abs/2512.20929) — This EEG-based study decodes neural responses to predictive inference in visual language processing, providing methodological precedent for measuring prediction-related neural signals, though in a different domain.

### What is NOT known

No published work has directly measured prediction error signaling in early visual cortex (V1/V2) and correlated it with subjective illusion magnitude across individual subjects in human neuroimaging data. Existing work is either computational modeling without empirical validation or uses different domains (language) and different neural measures (EEG coherence rather than fMRI BOLD).

### Why this gap matters

Filling this gap would provide the first direct empirical test of whether prediction error signals in early sensory cortex track subjective perceptual experience as predicted by hierarchical predictive coding theories. This would help distinguish between competing accounts of where in the visual hierarchy perceptual inference occurs and whether individual differences in illusion susceptibility reflect differences in early cortical prediction error processing.

### How this project addresses the gap

This project will use a computational modeling approach to generate testable predictions about V1/V2 prediction error signatures during illusion perception, then validate these predictions against existing published behavioral and neural summary statistics from public repositories. Rather than processing raw fMRI data (which exceeds GHA scope), we will fit a predictive coding model to published illusion magnitude data and derive expected neural correlates that can be compared to existing literature.

## Expected results

We expect to observe that a predictive coding model fitted to behavioral illusion magnitude data generates parameter estimates (precision weights, prediction error magnitudes) that correlate with published V1/V2 activation patterns from prior fMRI studies. A null result would suggest that illusion magnitude is determined by higher-level areas or that prediction error signals do not vary systematically across individuals in a way that affects subjective experience.

## Methodology sketch

- Download published behavioral data on Müller-Lyer illusion magnitude from OpenNeuro or similar repository (e.g., ds00XXXX with illusion task; verify data size <500MB for GHA compatibility)
- Implement a hierarchical predictive coding model (Python, NumPy) with parameters for precision weighting and prediction error computation in early visual layers
- Fit model parameters to individual subject illusion magnitude ratings using maximum likelihood estimation (scipy.optimize)
- Derive predicted V1/V2 prediction error signal magnitudes from model parameters for each subject
- Extract published V1/V2 BOLD response values from supplementary materials of prior fMRI studies (e.g., from OpenNeuro ds001234 or similar; use pre-processed ROI averages, not raw images)
- Compute Pearson correlation between model-derived prediction error magnitudes and published V1/V2 activation values across subjects
- Apply bootstrap resampling (1000 iterations) to estimate confidence intervals on correlation coefficient
- Conduct sensitivity analysis varying model precision-weighting parameters to test robustness of correlation
- Generate diagnostic plots (model fit residuals, correlation scatter plots) for validation

## Duplicate-check

- Reviewed existing ideas: (none in corpus).
- Closest match: None identified.
- Verdict: NOT a duplicate

## Scope note

This methodology avoids raw fMRI processing by using pre-processed summary statistics and behavioral data only. All data sources are publicly available and sized for 6h GHA execution. If no suitable pre-processed neural summary data exists within the GHA envelope, this project will be marked as rejected — out of scope.
