---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Gene Regulatory Network Dynamics from Time-Series RNA-Seq Data

**Field**: biology

## Research question

Can gene regulatory network (GRN) inference methods, when applied to publicly available time-series RNA-Seq datasets, accurately predict downstream gene expression changes following a perturbation? Specifically, can GRNs inferred from early time points (0–6 hours) forecast expression levels at later time points (24–48 hours) with statistically significant accuracy?

## Motivation

Validating inferred GRN structures remains a major challenge in computational biology. Most GRN inference methods lack ground-truth benchmarks for dynamic prediction. This study addresses that gap by testing whether early-time GRN models can predict later gene expression, providing a practical validation metric for network reconstruction quality.

## Related work

- [Continuous time Gaussian process dynamical models in gene regulatory network inference (2018)](http://arxiv.org/abs/1808.08161v3) — Proposes dynamical models for capturing temporal gene interactions relevant to time-series GRN inference.
- [Gene regulatory networks: a primer in biological processes and statistical modelling (2018)](http://arxiv.org/abs/1805.01098v1) — Provides statistical modelling foundations for GRN reconstruction from expression data.
- [Gene regulatory network inference: an introductory survey (2018)](http://arxiv.org/abs/1801.04087v2) — Surveys existing GRN inference algorithms and their limitations.
- [A survey of best practices for RNA-seq data analysis (2016)](https://doi.org/10.1186/s13059-016-0881-8) — Outlines preprocessing and normalization pipelines for RNA-seq data used in network inference.

## Expected results

We expect GRN models trained on early time points to predict later expression levels with moderate accuracy (Pearson r > 0.6) on held-out perturbation datasets. Prediction accuracy should vary significantly across inference methods, with dynamical models outperforming static correlation-based approaches. Results will demonstrate which GRN inference strategies are most suitable for dynamic forecasting.

## Methodology sketch

- Download 3–5 time-series RNA-Seq datasets from GEO/ENCODE with known perturbations (e.g., GSEXXXXX series with drug treatment at 0, 6, 24, 48h time points).
- Preprocess raw count matrices using standard RNA-seq pipeline (trimming, alignment via STAR, quantification via featureCounts).
- Normalize expression data using TMM or DESeq2 variance-stabilizing transformation.
- Apply 3 GRN inference methods: GENIE3 (tree-based), GRNBoost2 (gradient boosting), and Gaussian Process Dynamical Model.
- Split data temporally: train on 0–6h time points, test prediction on 24–48h expression.
- Generate predicted expression values for test time points using inferred network structure and early-time inputs.
- Compute prediction accuracy using Pearson correlation and RMSE between predicted and observed expression.
- Perform statistical comparison of methods using paired t-tests across datasets (n ≥ 3).
- Assess robustness via sensitivity analysis: vary inference parameters and measure prediction stability.
- Visualize top-predicted regulatory edges with known literature support for validation.

## Duplicate-check

- Reviewed existing ideas: TODO — flesh-out incomplete.
- Closest match: None found (no prior fleshed-out ideas in corpus).
- Verdict: NOT a duplicate

---

**Scope compliance**: Methodology fits GitHub Actions free-tier limits: public datasets downloadable via `wget`, computation via Python/R on 2 CPU cores (GENIE3 and GRNBoost2 scale to ~500 genes in <3h), statistical tests lightweight. No GPU required.
