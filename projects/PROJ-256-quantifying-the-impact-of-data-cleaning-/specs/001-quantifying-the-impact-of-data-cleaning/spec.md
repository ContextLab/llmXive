# Specification for Quantifying the Impact of Data Cleaning

## Overview
This document defines the functional requirements, success criteria, and research hypotheses for the project **Quantifying the Impact of Data Cleaning on Statistical Inference**.

## Functional Requirements

### FR-001 – Baseline Analysis
- Download public datasets.
- Run t‑tests and linear regressions on the raw (uncleaned) data.
- Store p‑values, 95 % confidence intervals, and effect‑size metrics in `data/processed/baseline_metrics.json`.

### FR-002 – Outlier Removal
- Implement IQR‑based outlier detection with configurable threshold *k*.
- Log the number of rows removed and warn if ≥ 50 % of rows are removed.

### FR-003 – Imputation
- Provide mean, median, and K‑nearest‑neighbour imputation strategies.
- Ensure no missing values remain after imputation and warn if variance reduction ≥ 20 %.

### FR-004 – Categorical Recoding
- Encode categorical variables using factor/label encoding suitable for statistical testing.

### FR-005 – Re‑analysis of Cleaned Data
- Re‑run the same statistical tests on each cleaned variant.
- Store results in `data/processed/cleaned_metrics.json`.

### FR-006 – Outlier Threshold Sweep & False‑Positive‑Rate (FPR) Estimation
**Outlier Threshold Sweep**
- Perform outlier removal using the IQR method with a set of threshold multipliers (e.g., *k* = 1.5, 2.0).
- For each threshold, generate a cleaned version of every dataset and re‑run the baseline statistical analyses.
- Record per‑threshold metrics (p‑values, confidence intervals, effect sizes).

**False‑Positive‑Rate (FPR) Estimation**
- Generate permutation null datasets by randomly shuffling the outcome variable while preserving all other columns.
- Run the full analysis pipeline on each null dataset for every outlier‑threshold setting.
- Compute the proportion of tests that incorrectly declare significance (p < 0.05) to obtain the FPR.
- Store FPR results in `data/processed/null_fpr_metrics.json` with fields `{outlier_k, fpr, dataset_id}`.

*The above description replaces any previous unrelated “LLM” or “glioblastoma” paragraphs that were erroneously included.*

## Success Criteria
- **SC‑001**: Per‑dataset delta reporting with qualitative directionality assessment (no median/IQR aggregation).
- **SC‑002**: All metrics (baseline, cleaned, differences, bootstrap CIs) are written to the declared JSON files with ≥ 3‑decimal precision.
- **SC‑03**: Visualizations (forest plot, heatmap) are saved under `output/figures/` and referenced in the final report.

## Research Hypotheses
- Outlier removal is expected to reduce p‑values when outliers are present.
- Imputation and recoding are expected to stabilize effect‑size estimates.