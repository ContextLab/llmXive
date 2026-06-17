---
field: statistics
submitter: openai.gpt-oss-120b
---

# Evaluating the Calibration of Predictive Uncertainty Intervals in Public Regression Benchmarks

**Field**: statistics

## Research question

How well calibrated are the 90 % prediction intervals produced by common uncertainty‑quantification methods (quantile regression, Bayesian linear regression, Gaussian‑process regression, and conformal prediction) when applied to publicly available regression benchmark datasets?

## Motivation

Uncertainty intervals are increasingly used to convey the reliability of point predictions, yet practitioners lack systematic evidence on whether the nominal 90 % coverage actually holds on real‑world regression tasks. Identifying systematic over‑ or under‑coverage will guide the selection and improvement of uncertainty‑quantification techniques for downstream decision‑making.

## Related work

- [CRUDE: Calibrating Regression Uncertainty Distributions Empirically (2020)](https://arxiv.org/abs/2005.12496) — Proposes empirical methods for calibrating regression‑type uncertainty estimates, providing a baseline for interval calibration studies.  
- [Learning Prediction Intervals for Regression: Generalization and Calibration (2021)](https://arxiv.org/abs/2102.13625) — Analyzes the trade‑off between interval width and calibration, offering theoretical tools relevant for evaluating interval quality.  
- [Parametric and Multivariate Uncertainty Calibration for Regression and Object Detection (2022)](https://arxiv.org/abs/2207.01242) — Reviews calibration definitions for regression and proposes metrics that can be adopted for benchmark evaluation.  
- [Self‑Calibrating Conformal Prediction (2024)](https://arxiv.org/abs/2402.07307) — Introduces a conformal method that adapts calibration locally, suggesting a modern baseline for comparison.  
- [ConformaDecompose: Explaining Uncertainty via Calibration Localization (2026)](https://arxiv.org/abs/2604.27149) — Decomposes conformal interval calibration to reveal sources of mis‑coverage, motivating sub‑analyses of heteroscedasticity.  
- [Enhancing reliability in prediction intervals using point forecasters: Heteroscedastic Quantile Regression and Width‑Adaptive Conformal Inference (2024)](https://arxiv.org/abs/2406.14904) — Combines heteroscedastic quantile regression with adaptive conformal inference, directly relevant to the heteroscedastic sub‑analysis.  
- [Assessing the conditional calibration of interval forecasts using decompositions of the interval score (2025)](https://arxiv.org/abs/2508.18034) — Provides a decomposition of the interval score that can be used to diagnose calibration failures in our experiments.  
- [UTOPIA: Universally Trainable Optimal Prediction Intervals Aggregation (2023)](https://arxiv.org/abs/2306.16549) — Proposes an aggregation scheme for prediction intervals that can serve as an additional method to benchmark.

## Expected results

We anticipate observing a spectrum of calibration quality across methods: conformal approaches should achieve near‑nominal coverage on average, while standard quantile regression may under‑cover in heteroscedastic regions. Empirical coverage deviating from 90 % by more than ±2 % will be taken as evidence of mis‑calibration, and interval‑score differences will quantify efficiency trade‑offs.

## Methodology sketch

- **Data acquisition**: Download ten publicly available regression datasets (≤ 10 k samples each) from the UCI Machine Learning Repository and OpenML (provide URLs in the implementation script).  
- **Pre‑processing**: Standardize numeric features, encode categoricals with one‑hot, and split each dataset into 70 % training / 30 % test (random seed fixed).  
- **Model fitting**: For each training split, fit four uncertainty‑quantification methods:
  1. Quantile regression (linear + gradient‑boosted trees).  
  2. Bayesian linear regression (Gaussian priors, analytic posterior).  
  3. Gaussian‑process regression (RBF kernel, exact inference).  
  4. Conformal prediction (split‑conformal using a held‑out calibration set).  
- **Interval generation**: Produce 90 % two‑sided prediction intervals on the test set for each method.  
- **Calibration assessment**:
  - Compute empirical coverage = proportion of test targets falling inside the interval.  
  - Calculate average interval width and the proper interval score (Gneiting & Raftery, 2007).  
  - Perform a binomial test to assess whether observed coverage differs significantly from 0.90.  
- **Sub‑analyses**:
  - **Heteroscedasticity**: Estimate residual variance on the training set and stratify test points into low/medium/high variance bins; report coverage per bin.  
  - **Training‑size effect**: Re‑run each method on subsamples of 20 %, 50 %, and 80 % of the training data and examine coverage trends.  
- **Statistical comparison**: Use paired Wilcoxon signed‑rank tests across datasets to compare coverage deviations and interval scores between methods.  
- **Reproducibility**: All code will be scripted in Python (scikit‑learn, GPyTorch, statsmodels) and containerised; results saved as CSV/JSON for downstream analysis.

## Duplicate-check

- Reviewed existing ideas: none.  
- Closest match: N/A.  
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-17T12:34:57Z
**Outcome**: success
**Original term**: Evaluating the Calibration of Predictive Uncertainty Intervals in Public Regression Benchmarks statistics
**Verified citation count**: 11

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Evaluating the Calibration of Predictive Uncertainty Intervals in Public Regression Benchmarks statistics | 11 |

### Verified citations

1. **ConformaDecompose: Explaining Uncertainty via Calibration Localization** (2026). Fatima Rabia Yapicioglu, Meltem Aksoy, Alberto Rigenti, Tuwe Löfström-Cavallin, Helena Löfström-Cavallin, et al.. arXiv. [2604.27149](https://arxiv.org/abs/2604.27149). PDF-sampled: No.
2. **CRUDE: Calibrating Regression Uncertainty Distributions Empirically** (2020). Eric Zelikman, Christopher Healy, Sharon Zhou, Anand Avati. arXiv. [2005.12496](https://arxiv.org/abs/2005.12496). PDF-sampled: No.
3. **Evaluating Machine Translation Quality with Conformal Predictive Distributions** (2023). Patrizio Giovannotti. arXiv. [2306.01549](https://arxiv.org/abs/2306.01549). PDF-sampled: No.
4. **Self-Calibrating Conformal Prediction** (2024). Lars van der Laan, Ahmed M. Alaa. arXiv. [2402.07307](https://arxiv.org/abs/2402.07307). PDF-sampled: No.
5. **Calibration of Machine Learning Classifiers for Probability of Default Modelling** (2017). Pedro G. Fonseca, Hugo D. Lopes. arXiv. [1710.08901](https://arxiv.org/abs/1710.08901). PDF-sampled: No.
6. **Parametric and Multivariate Uncertainty Calibration for Regression and Object Detection** (2022). Fabian Küppers, Jonas Schneider, Anselm Haselhoff. arXiv. [2207.01242](https://arxiv.org/abs/2207.01242). PDF-sampled: No.
7. **Learning Prediction Intervals for Regression: Generalization and Calibration** (2021). Haoxian Chen, Ziyi Huang, Henry Lam, Huajie Qian, Haofeng Zhang. arXiv. [2102.13625](https://arxiv.org/abs/2102.13625). PDF-sampled: No.
8. **Distribution-free binary classification: prediction sets, confidence intervals and calibration** (2020). Chirag Gupta, Aleksandr Podkopaev, Aaditya Ramdas. arXiv. [2006.10564](https://arxiv.org/abs/2006.10564). PDF-sampled: No.
9. **UTOPIA: Universally Trainable Optimal Prediction Intervals Aggregation** (2023). Jianqing Fan, Jiawei Ge, Debarghya Mukherjee. arXiv. [2306.16549](https://arxiv.org/abs/2306.16549). PDF-sampled: No.
10. **Enhancing reliability in prediction intervals using point forecasters: Heteroscedastic Quantile Regression and Width-Adaptive Conformal Inference** (2024). Carlos Sebastián, Carlos E. González-Guillén, Jesús Juan. arXiv. [2406.14904](https://arxiv.org/abs/2406.14904). PDF-sampled: No.
11. **Assessing the conditional calibration of interval forecasts using decompositions of the interval score** (2025). Sam Allen, Julia Burnello, Johanna Ziegel. arXiv. [2508.18034](https://arxiv.org/abs/2508.18034). PDF-sampled: No.
