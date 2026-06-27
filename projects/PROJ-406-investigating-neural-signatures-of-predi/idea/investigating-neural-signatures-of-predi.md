---
field: neuroscience
submitter: agent:flesh_out
---

# Investigating Neural Signatures of Predictive Processing in Visual Illusions

**Field**: neuroscience

## Research question

Does individual variation in a computational predictive-coding model's estimated precision weights predict individual differences in susceptibility to visual illusions?

## Motivation

Predictive processing theories propose that perception results from the brain's minimization of prediction errors, with individual differences arising from variations in precision weighting of sensory evidence versus prior expectations. Visual illusions like the Müller-Lyer provide a natural testbed for this framework, as they reflect conflicts between sensory input and prior expectations. However, it remains unclear whether individual differences in illusion susceptibility can be explained by individual differences in model-derived precision parameters, providing a mechanistic link between computational theory and behavioral variation.

## Literature gap analysis

### What we searched

We queried Semantic Scholar/arXiv/OpenAlex with two search strategies: (1) "predictive coding visual illusions computational model individual differences" (8 results) and (2) "Müller-Lyer illusion susceptibility behavioral variation model fitting" (8 results). The literature block contains 2 on-topic results from these searches.

### What is known

- [Visual illusions via neural dynamics: Wilson-Cowan-type models and the efficient representation principle (2019)](https://arxiv.org/abs/1907.13004) — This computational modeling work demonstrates that Wilson-Cowan neural dynamics can reproduce supra-threshold visual illusion phenomena, establishing a theoretical link between neural population dynamics and illusory perception.
- [Decoding Predictive Inference in Visual Language Processing via Spatiotemporal Neural Coherence (2025)](https://arxiv.org/abs/2512.20929) — This EEG-based study decodes neural responses to predictive inference in visual language processing, providing methodological precedent for measuring prediction-related neural signals, though in a different domain.

### What is NOT known

No published work has directly fitted individual-level precision-weighting parameters from a predictive-coding model to visual illusion behavioral data and tested whether these parameters predict individual differences in illusion susceptibility. Existing work is either computational modeling without individual-differences analysis or uses different domains (language) and different neural measures (EEG coherence).

### Why this gap matters

Filling this gap would provide the first direct empirical test of whether individual differences in illusion susceptibility reflect individual differences in precision-weighting mechanisms as predicted by hierarchical predictive coding theories. This would help distinguish between competing accounts of individual variation in perceptual inference and provide computational biomarkers for perceptual processing styles.

### How this project addresses the gap

This project will fit a hierarchical predictive coding model to individual subject illusion magnitude ratings from publicly available behavioral datasets, extract individual precision-weighting parameters, and test whether these parameters predict individual differences in illusion susceptibility using standard statistical tests.

## Expected results

We expect to observe that individual variation in fitted precision-weighting parameters from the predictive coding model significantly correlates with individual differences in illusion magnitude ratings. A null result would suggest that illusion susceptibility is determined by factors other than precision weighting (e.g., prior strength, noise levels) or that the model fails to capture the relevant individual-differences structure.

## Methodology sketch

- Download published behavioral data on Müller-Lyer illusion magnitude from OpenNeuro or similar repository (e.g., ds00XXXX with illusion task; verify data size <500MB for GHA compatibility)
- Implement a hierarchical predictive coding model (Python, NumPy) with parameters for precision weighting and prediction error computation in early visual layers
- Fit model parameters to individual subject illusion magnitude ratings using maximum likelihood estimation (scipy.optimize)
- Extract individual precision-weighting parameter estimates for each subject from fitted model
- Compute individual illusion susceptibility scores from behavioral ratings (mean deviation from veridical length across trials)
- Compute Pearson correlation between individual precision-weighting parameters and individual illusion susceptibility scores across subjects
- Apply bootstrap resampling (1000 iterations) to estimate confidence intervals on correlation coefficient
- Conduct sensitivity analysis varying model precision-weighting parameters to test robustness of correlation
- Generate diagnostic plots (model fit residuals, correlation scatter plots, parameter distributions) for validation

## Duplicate-check

- Reviewed existing ideas: (none in corpus).
- Closest match: None identified.
- Verdict: NOT a duplicate
