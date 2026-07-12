# Research: Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys

## Executive Summary

This research phase validates the feasibility of predicting grain size in rolled aluminum alloys using public data. The primary challenge is data availability: the specific combination of *rolling temperature*, *alloy composition (wt%)*, and *measured grain size* is rare in general materials databases. The strategy involves rigorous schema pre-checks against verified sources. If data is found, the analysis will proceed with a baseline linear model (to establish main effects) followed by a Random Forest model (to capture non-linear interactions). All findings are framed as **associational** due to the observational nature of the data.

**Critical Finding**: The provided "Verified datasets" block (specifically the NOMAD structure CSV) likely lacks the required *processing* variables (rolling temperature, grain size). The pipeline is designed to detect this via schema pre-check and halt with a "Data Missing" report. This outcome is treated as a valid scientific finding: "Current public structural databases do not contain the necessary process data for this prediction task."

## Dataset Strategy

### Verified Sources Analysis

The project relies on the following verified datasets. **Note**: The "Verified datasets" block provided in the spec contains generic or unrelated datasets (e.g., NOMAD structure CSV, C4 text corpus, Solidity code). **Crucially, none of the listed URLs explicitly contain the specific variables required: `rolling_temperature`, `alloy_composition_wt`, and `grain_size` for rolled aluminum.**

| Source Name | Verified URL | Variable Fit Assessment | Action Plan |
|:--- |:--- |:--- |:--- |
| **NOMAD (Structure CSV)** | ` | **Likely Missing**. NOMAD primarily contains crystallographic structure data (lattice parameters, space groups) from DFT or experiments. It rarely contains *processing* parameters like "rolling temperature" or *post-process* grain size for specific rolling operations. | **Pre-check**: Script will scan headers for `temperature`, `grain_size`, `rolling`. If missing, skip immediately. If ALL sources fail, halt with Exit Code 1 and log: "Critical variables missing from all sources: [list of missing variables]". |
| **C4 / OLMOCR / PeS2o** | ` etc. | **Irrelevant**. These are text corpora (Common Crawl, arXiv math, scientific papers). They contain no structured tabular data for this specific regression task. | **Skip**: These are not tabular material science datasets. |
| **Solidity Code / Notebooks** | `https://huggingface.co/datasets/nothingisenough/...` | **Irrelevant**. Code repositories. | **Skip**. |
| **Liber Primus** | `https://huggingface.co/datasets/Type-1-Civilisation/...` | **Irrelevant**. Decoding challenge. | **Skip**. |

**Contingency Strategy**:
1. **Strict Pre-check**: The `ingestion.py` script will attempt to load the NOMAD CSV and inspect headers.
2. **Halt Condition**: If the NOMAD CSV (or any other source we might discover via a broader search *if allowed by the constitution*) lacks `rolling_temperature` or `grain_size`, the system will **HALT** with Exit Code 1 and log: `"Critical variables missing from all sources: [rolling_temperature, grain_size]"`.
3. **No Fabrication**: We will **not** invent a URL or assume a dataset exists. If the verified sources fail, the project outcome is a valid "Data Missing" report.
4. **Scope Limitation**: No generic "OpenML" search will be performed. The project strictly adheres to the "Verified datasets" block. If no suitable source exists in this block, the project halts.

*Note: In a real-world scenario, one might search for specific repositories like "Aluminum Rolling Dataset" or "Materials Data Facility", but per the "Verified datasets" constraint, we are limited to the provided list. If the list is insufficient, the plan correctly identifies this as a blocking gap.*

## Methodological Rigor

### Statistical Approach

1. **Baseline (Linear Regression with Residualization)**:
 * **Step 1**: Regress `Grain Size` against `Alloy Series` (one-hot encoded) and `Composition` (Mg, Si, Cu, Zn). Store residuals.
 * **Step 2**: Regress `Residuals` against `Temperature` and `Temperature × Composition` interactions.
 * **Purpose**: Isolate the temperature effect from the confounding alloy series.
 * **Rigor**: Coefficients will be tested for significance (p-values). Collinearity (VIF > 5 or correlation > 0.8) will be flagged, and independent interpretation suppressed for correlated pairs (e.g., Mg and Si in 6xxx series).

2. **Non-Linear (Random Forest)**:
 * **Model**: `RandomForestRegressor` (Scikit-learn).
 * **Grid Search**: `n_estimators`: [50, 100, 200]; `max_depth`: [5, 10, 15, 20].
 * **Constraint**: If grid search exceeds 4 hours, fallback to `n_estimators=100, max_depth=10`.
 * **Rigor**:
 * **Multiple Comparisons**: Not applicable for regression feature importance in the same way as hypothesis testing, but we will use **Permutation Importance** to validate feature contributions.
 * **Power/Sample Size**: Acknowledged limitation. If $N < 50$, results are exploratory. If $N$ is small, we will use Leave-One-Out Cross-Validation (LOOCV) or K-Fold (K=5) with **Stratified Group K-Fold** (groups=Alloy Series).
 * **Causal Inference**: Explicitly stated as **Associational**. No randomization exists. Claims are limited to "predictive association" and "modulation of the temperature-grain size relationship".

### Interaction-Specific Validation

To ensure the R² improvement is driven by the *interaction* and not just better composition modeling:
* **Permutation Importance**: We will specifically measure the drop in R² when `Temp × Mg` and `Temp × Si` are permuted, compared to permuting `Mg` or `Temp` alone.
* **Partial Dependence Plots (PDP)**: We will generate PDPs for `Temperature` at different levels of `Mg` to visualize the non-linear modulation.
* **Success Metric**: The improvement in R² must be statistically significant (p < 0.05 via permutation test) AND (absolute improvement > 0.05 OR relative improvement > 10%).

### Sensitivity Analysis (FR-005)

* **Threshold Sweep**: Feature importance cutoffs will be swept: $\{0.01, 0.05, 0.1\}$.
* **Metric**: Stability of the top-5 interaction terms (e.g., `Temp×Mg`).
* **Success**: >80% of top-5 terms remain consistent across sweeps.

### Confounder Sensitivity (FR-008)

* **Proxy Variables**: Check for `strain_rate`, `cooling_rate`, `rolling_reduction`.
* **Action**: If present, re-run model with proxies. Report $\Delta R^2$.
* **Caveat**: If absent, explicitly state in the final report: "Unmeasured confounders (e.g., strain rate) may bias results; analysis is correlational. The model attributes variance to temperature/composition interactions conditional on the observed data."

### Industrial Rolling Context

* **Validation**: The plan attempts to validate the "Industrial Rolling Context" (Principle VII).
* **Limitation**: If the dataset lacks metadata fields like `strain_rate` or `reduction_ratio`, the model cannot explicitly filter for "industrial" vs "lab-scale" data.
* **Reporting**: In such cases, the final report will explicitly state: "The 'Industrial Rolling' constraint could not be verified due to missing metadata in the source dataset. Results are presented for the available data distribution."

## Compute Feasibility

* **Hardware**: GitHub Actions `ubuntu-latest` (2 vCPU, ~7GB RAM).
* **Software**: `scikit-learn` (CPU optimized), `pandas` (streaming if needed).
* **Memory**:
 * Data subset: If raw data > 500MB, sample to 100k rows or use chunked processing.
 * Model: Random Forest with `n_estimators=200` and `max_depth=20` on ~50k rows fits within 7GB RAM.
* **Time**:
 * Ingestion: < 15 mins.
 * Preprocessing: < 10 mins.
 * Linear Model: < 1 min.
 * RF Grid Search: Estimated -4 hours on 2 cores. Fallback mechanism ensures < 5 hours total.
* **No GPU**: All models are CPU-native. No CUDA dependencies.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **No suitable dataset found** | Project Halts (Exit Code 1). | **Valid Outcome**: The "Data Missing" report is a successful execution of the spec's requirement to verify data availability. This is the primary scientific result if no data exists. |
| **High Collinearity** | Uninterpretable coefficients. | **Descriptive Framing**: Report joint effects (e.g., "Mg and Si jointly influence...") rather than independent coefficients. |
| **Timeout during Grid Search** | Job killed. | **Fallback**: Hard timeout logic triggers single-pass training with default params. |
| **Small Sample Size** | Low statistical power. | **Exploratory Framing**: Report results as "preliminary associations" with confidence intervals. |
| **Unmeasured Confounders** | Bias in "Impact" estimation. | **Residualization**: Use residualization to isolate temperature effects. Explicitly state limitations in the report. |
| **Missing Metadata** | Cannot validate "Industrial Rolling" context. | **Transparent Reporting**: Explicitly state in the final report that the context could not be verified due to missing data. |