# Research: The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress

## Executive Summary

This research phase validates the feasibility of testing the hypothesis: "Does behavioral interoceptive accuracy predict the magnitude of physiological emotional regulation during acute psychosocial stress, independent of baseline HRV?"

**Primary Finding**: The WESAD dataset (DOI: 10.5281/zenodo.1292932) contains high-quality ECG/PPG signals for stress (TSST) and baseline phases but **lacks** a specific behavioral interoceptive accuracy task (e.g., Schandry heartbeat perception). OpenNeuro studies containing "TSST" similarly lack the required behavioral task in their `events.tsv` metadata (verified via BIDS index API). Consequently, the primary outcome of this project is a **Data Gap & Sensitivity Report** confirming the absence of the predictor variable. The report will include a **Minimum Detectable Effect Size (MDES)** calculation based on the **Total Variance of the Outcome** (Stress HRV) and a **Best-Case Scenario Assumption** (R²=0.10) to quantify the study's theoretical sensitivity limit.

## Dataset Strategy

The project relies on two primary data sources. Per the `# Verified datasets` block, we cite only the URLs provided.

| Dataset | Purpose | Source URL | Verification Status |
|:--- |:--- |:--- |:--- |
| **WESAD** | Primary source for ECG/PPG stress/baseline signals. | ` | **Verified** (Parquet format, contains ECG/PPG). |
| **OpenNeuro (Global TSST Index)** | Secondary search for TSST + Interoception across all studies. | ` (Query: `query { datasets(where: {tags: {name: "stress"}}) { id metadata { tasks { name } } } }`) | **Verified** (Official GraphQL API for BIDS index). |
| **WESAD (Zenodo)** | Canonical source for download (fallback). | `10.5281/zenodo.1292932` | **NO verified source found** (DOI only; use HuggingFace mirror if Zenodo URL is unreachable, per FR-001). |
| **TSST** | Stress paradigm definition. | N/A | **NO verified source found** (Task definition only). |
| **HRV** | Validation of HRV calculation. | ` | **Verified** (Used for unit test validation). |

**Dataset Selection Rationale**:
1. **WESAD** is the only verified open dataset with concurrent ECG/PPG and a validated stress paradigm (TSST) in the provided list.
2. **OpenNeuro** is searched via the official **GraphQL API** to query the **global BIDS index** for *all* studies tagged with "stress" (TSST) and "heartbeat". This replaces the invalid "single atlas" scan, ensuring a representative audit of the repository by inspecting the metadata index of all relevant studies.
3. **No Access-Gated Data**: We explicitly avoid ADNI, HCP, or UK Biobank as they require credentials and cannot be fetched by the CI runner.
4. **Zenodo Fallback**: If the Zenodo DOI link is unreachable, the pipeline will automatically fall back to the verified HuggingFace mirror to satisfy FR-001 (download from canonical source).

**Variable Fit Analysis**:
- **Required**: Behavioral Interoceptive Accuracy (Schandry task), Stress HRV, Baseline HRV.
- **WESAD Status**: Contains Stress HRV (ECG/PPG during TSST) and Baseline HRV. **Missing**: Behavioral Schandry task. The dataset contains only resting-state and stress signals, no explicit "heartbeat counting" task.
- **OpenNeuro Status**: API query for studies with "TSST" and "heartbeat" in metadata yielded no matches across the indexed TSST studies.
- **Conclusion**: The dataset-variable fit is **negative** for the primary hypothesis. The plan shifts to documenting this gap and calculating MDES based on outcome variance.

## Methodological Rigor

### Statistical Approach
Since the primary hypothesis cannot be tested due to missing data, the statistical plan is bifurcated:

1. **If Data Exists (Hypothetical)**:
 - **Model**: Linear Regression (ANCOVA).
 - **Outcome**: Stress HRV (RMSSD).
 - **Predictor**: Interoceptive Accuracy (Schandry score).
 - **Covariate**: Baseline HRV (RMSSD).
 - **Rationale**: Controls for individual differences in autonomic tone (Constitution Principle VII).
 - **Multiple Comparisons**: Not applicable for a single primary hypothesis.
 - **Causal Framing**: Strictly **associational**. No randomization exists.

2. **If Data is Missing (Actual Plan)**:
 - **Metric**: Minimum Detectable Effect Size (MDES) / Theoretical Sensitivity Bound.
 - **Calculation**: Based on sample size (N) of WESAD and **Total Variance of the Outcome** (Stress HRV).
 - **Best-Case Scenario Assumption**: Since the predictor is missing, we cannot estimate its contribution to variance. We assume a conservative **R² = 0.10** (the predictor explains [deferred] of the variance) to calculate the detectable effect size.
 - **Rationale**: This MDES represents the smallest effect size a *hypothetical* predictor would need to have to be statistically detectable (at α=0.05, Power=0.8) given the observed noise of the outcome and the sample size. It is explicitly framed as a **Theoretical Sensitivity Bound**, not an empirical test of the hypothesis. This avoids the category error of estimating predictor variance from missing data while still providing a quantitative feasibility metric as required by FR-006.
 - **Note**: This is explicitly framed as a "Feasibility Metric" and not a test of the hypothesis.

### Data Integrity & Preprocessing
- **Artifact Rejection**: Signals with < 5% valid beats during the TSST window will be excluded (Edge Case handling).
- **HRV Calculation**: `hrv-analysis` library (Python) will be used to compute RMSSD and SDNN.
 - **Validation**: Metrics will be cross-checked against the `hrv2` dataset (verified URL) to ensure library correctness.
- **Collinearity**: Baseline HRV is a covariate, not a predictor of change. We avoid regressing "Delta HRV" on "Baseline HRV" to prevent mathematical tautology (Assumption: Statistical Model).

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use WESAD Parquet** | Verified URL available; contains ECG/PPG; fits CPU constraints. |
| **Skip Deep Learning** | No GPU available; classical statistics sufficient for HRV/Regression. |
| **Prioritize Audit** | The "finding" is the data gap; running full regression on synthetic data would be fabrication. |
| **MDES as Sensitivity Bound** | If data is missing, MDES based on **Total Outcome Variance** + **Hypothetical R²** is the only scientifically valid quantitative metric to report (per FR-006), distinct from a formal power analysis of the missing predictor. |
| **OpenNeuro Global Index Query** | Replaced invalid single-atlas scan with official GraphQL API query to scan all TSST-tagged studies in the OpenNeuro repository, ensuring a representative audit of the available data landscape. |
| **Zenodo Fallback** | If Zenodo URL is unreachable, use HuggingFace mirror to satisfy FR-001 download requirement. |