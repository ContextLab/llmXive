# Plan for Predicting the Yield Strength of High‑Entropy Alloys

## Overview

This document outlines the methodological plan for acquiring data, engineering compositional descriptors, training predictive models, and performing statistical validation for the yield strength of high‑entropy alloys (HEAs). It aligns with the functional requirements (FR‑001 … FR‑012) and serves as the guiding reference for implementation tasks throughout the project.

## Data Acquisition & Descriptor Engineering

* **Data Sources** – Primary verified dataset URL is defined in `research.md`. If unavailable, fallback sources are attempted in the order specified (Materials Project, NIST HEA Database, Zenodo).
* **Descriptor Set** – For each composition we compute:
 - Atomic size mismatch (δ)
 - Electronegativity difference (Δχ)
 - Valence electron concentration (VEC)
 - Mixing entropy (S<sub>mix</sub>)
 - Melting‑temperature variance (σ<sub>Tm</sub>)
* **Filtering** – Only single‑phase, room‑temperature alloys with complete elemental property data are retained.

## Model Training

* **Data Split** – A stratified 80/20 split based on elemental ratios (seed = 42).
* **Algorithms** – Linear Regression baseline, Random Forest, and Gradient Boosting, each with 5‑fold cross‑validation and hyper‑parameter grids constrained to ≤ 50 trees and depth ≤ 10.
* **Evaluation** – R², MAE, RMSE are computed on the held‑out test set; the best model is selected for downstream statistical analysis.

## Statistical Validation

### Permutation‑Importance Testing

* **Fixed Permutation Count** – All permutation‑importance analyses must use a **large, fixed number of permutations** (currently set to **1 000 permutations**) to ensure statistical robustness.
* **Adaptive Logic Removed** – Any previously described adaptive permutation‑count logic (e.g., reducing the number of permutations for small datasets) has been **removed** from this plan. The same 1 000 permutations are applied regardless of dataset size, satisfying FR‑006.
* **Implementation** – The permutation routine is invoked in `code/models/evaluate.py` via `run_permutation_importance`, which now respects the fixed count. A warning will be logged if the dataset is extremely small, but the full permutation set will still be executed.

### Multiple‑Comparison Correction

* Both Bonferroni and Benjamini‑Hochberg corrections are applied to the permutation‑derived p‑values.

### Bootstrap Resampling

* A sufficient number of bootstrap resamples (e.g., 1 000) are generated for the linear baseline (or its corrected version) and the best tree‑based model to derive confidence intervals for R².

### Sensitivity Analysis

* The analysis sweeps α ∈ {0.01, 0.05, 0.1} and records significant descriptor counts and absolute R² values for each threshold.

## Reporting

* The final report (`output/report.md`) includes:
 - Model performance metrics
 - All statistical validation results (VIF, permutation importance, bootstrap CIs, sensitivity analysis)
 - Mandatory disclaimer **“Associational analysis only; no causal inference”** injected via `utils.report_utils`
 - A **Data Limitation Warning** section when the processed dataset contains fewer than 500 entries (as flagged in `output/data_status.json`).

## Runtime & Power Considerations

* Total pipeline runtime is tracked and must not exceed 6 hours (21 600 seconds).
* Power analysis (`output/power_analysis.json`) flags low‑power situations (N < 50) but does not halt downstream analyses.

## Documentation Updates

* `spec.md` has been updated (see T048) to reflect the stratified split approach.
* This `plan.md` now explicitly states the fixed permutation count, fulfilling FR‑006.