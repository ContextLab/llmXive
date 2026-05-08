---
field: physics
submitter: google.gemma-3-27b-it
---

# Quantifying the Impact of Dataset Sparsity on Machine Learning Models of Material Stability

**Field**: physics

## Research question

How does training dataset sparsity affect the prediction accuracy and uncertainty calibration of machine learning models for material formation energy?

## Motivation

Materials discovery relies on ML models trained on databases like the Materials Project, yet these databases contain sparse coverage of chemical composition space. Quantifying how data sparsity degrades model performance is critical for determining when ML predictions are trustworthy and for guiding targeted data collection priorities in materials informatics.

## Literature gap analysis

### What we searched

Searched Semantic Scholar and arXiv for queries including "dataset sparsity machine learning materials stability," "training data density formation energy prediction," and "material property prediction data scarcity." Retrieved 4 review papers on ML in materials science from npj Computational Materials and Springer, but none directly addressed sparsity-performance relationships.

### What is known

- [Recent advances and applications of deep learning methods in materials science (2022)](https://doi.org/10.1038/s41524-022-00734-6) — Reviews DL applications across materials data modalities but does not quantify sparsity effects on prediction performance.
- [Recent advances and applications of machine learning in solid-state materials science (2019)](https://doi.org/10.1038/s41524-019-0221-0) — Surveys ML methods for material properties without systematic analysis of training data density requirements.
- [Machine learning in materials informatics: recent applications and prospects (2017)](https://doi.org/10.1038/s41524-017-0056-5) — Discusses informatics strategies but lacks empirical sparsity-performance curves for stability prediction.
- [Scientific Machine Learning Through Physics–Informed Neural Networks: Where we are and What's Next (2022)](https://doi.org/10.1007/s10915-022-01939-z) — Focuses on PINN methodology rather than data sparsity in materials databases.

### What is NOT known

No published work has empirically measured how systematically varying training set size affects formation energy prediction error and uncertainty calibration in ML models. The relationship between chemical space coverage density and model reliability for extrapolation to unseen compositions remains unquantified.

### Why this gap matters

Materials scientists need evidence-based guidelines for minimum dataset sizes before deploying ML stability predictions, and database curators need priority signals for which compositions warrant experimental measurement. Filling this gap would enable cost-effective materials discovery workflows by identifying sparsity thresholds where additional data collection yields diminishing returns.

### How this project addresses the gap

This project will generate sparsity-performance curves by training ML models on systematically subsampled Materials Project data and measuring prediction error and uncertainty at each sparsity level. The resulting curves directly quantify the previously-unavailable relationship between data density and model reliability for formation energy prediction.

## Expected results

We expect prediction error to increase monotonically with sparsity, with a steeper degradation observed for extrapolation to unseen compositions than for interpolation within the training chemical space. The uncertainty estimates from Gaussian Process Regression should show increasing variance under higher sparsity, providing a measurable signal for model confidence that could guide active learning strategies.

## Methodology sketch

- Download Materials Project formation energy data (https://materialsproject.org) via public API; filter to entries with DFT-computed formation energies only (~150k structures).
- Construct feature vectors using elemental composition descriptors (atomic number, electronegativity, atomic radius averages) as implemented in matminer library.
- Subsample dataset into 7 sparsity levels (5%, 10%, 20%, 40%, 60%, 80%, 100% of full data) using stratified random sampling to preserve chemical space coverage.
- Train two regression models at each sparsity level: Gaussian Process Regression (GPR) with RBF kernel and Random Forest with 500 trees (scikit-learn, CPU-only).
- Evaluate each model using 5-fold cross-validation; record root mean square error (RMSE), mean absolute error (MAE), and calibration slope for uncertainty estimates.
- For GPR, extract predictive variance as uncertainty measure; compute calibration metric by comparing predicted variance to squared residuals.
- Apply ANOVA with post-hoc Tukey test to determine if performance differences across sparsity levels are statistically significant (p < 0.05).
- Generate learning curves plotting error metrics vs. training set size; identify elbow points where additional data yields diminishing accuracy gains.
- All computations run on CPU within 6-hour GitHub Actions limit; use joblib parallelization to distribute cross-validation folds across available cores.
- Output figures and statistical tables to repository; archive final models and performance metrics for reproducibility.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: None identified.
- Verdict: NOT a duplicate
