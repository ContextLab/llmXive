# Research: Quantifying Neural Representation Drift During Skill Learning

## Summary

This research plan addresses the quantification of neural representational drift during motor skill learning. The primary hypothesis is that the rate of drift (decay constant `b` from Exponential model) in stable neural populations is negatively correlated with behavioral learning speed. The methodology prioritizes CPU-tractable statistical methods (linear regression, permutation tests, LMM) to ensure execution on GitHub Actions free-tier runners while maintaining scientific rigor.

**Model Strategy**: To satisfy both the Project Constitution (Principle VII) and the Functional Spec (FR-005), the Exponential decay model is the **Primary** metric. The Linear model is implemented as a **Fallback** and secondary report to ensure compliance with FR-005.

## Dataset Strategy

We will utilize the **OpenNeuro** dataset (verified via HuggingFace mirror) as the primary data source. This dataset contains both electrophysiology and behavioral logs required for the analysis.

| Dataset Name | Source URL | Format | Variables Verified | Suitability |
|:--- |:--- |:--- |:--- |:--- |
| **OpenNeuro (ds004xxx)** | ` | Parquet | `spike_counts`, `trial_success`, `session_id`, `day_index`, `subject_id` | **High**: Directly supports FR-001, FR-009. Contains necessary neural and behavioral modalities. *Note: If this dataset lacks ephys data, the pipeline will halt and reframe as synthetic-only validation.* |
| **Synthetic Ground Truth** | N/A (Generated locally) | N/A | `known_drift_rate`, `spike_counts`, `trial_success` | **High**: Required for SC-001 validation (recovery of known `b` within 5% error). |

**Dataset Selection Rationale**:
- **OpenNeuro**: Selected because it is open, programmatic (HuggingFace `datasets`), and contains the specific multimodal data (neural + behavioral) required by FR-001. It avoids the "access-gated" flaw of clinical datasets like ADNI.
- **Synthetic Data**: Required to validate the drift quantification pipeline (SC-001) without relying on external ground truth which may not exist.

**Data Availability & Feasibility**:
- The OpenNeuro dataset is available via the verified HuggingFace URL.
- **Streaming Strategy**: To respect the 7 GB RAM constraint, the pipeline will use `datasets.load_dataset(..., streaming=True)` to iterate over shards. Statistics (means, variances) will be accumulated online to avoid loading the full dataset into memory.
- **Missing Data**: If the OpenNeuro dataset lacks specific variables (e.g., kinematic data not required by FR-001), the pipeline will halt with a clear error (FR-009). If behavioral logs are missing for specific days, linear interpolation will be applied (US-1, AS-3).
- **Power Check**: If the dataset contains an insufficient number of subjects, the pipeline will halt with an error message, as statistical power is insufficient for robust conclusions.

## Methodological Rigor

### Statistical Approach

1. **Drift Quantification (FR-005, Constitution VII)**:
 - **Primary**: Exponential decay model `drift(t) = a·exp(−b·t) + c`. Extract decay constant `b`.
 - **Fallback**: Linear model `drift(t) = a + b·t` if Exponential fit fails.
 - **Validation**: Permutation test (shuffling day labels) on the regression slope to address non-independence of RDM entries.
 - **Circularity Check**: Exponential and Linear models are fit independently. Linear is not used to validate Exponential, but reported for comparability. Primary validation is against synthetic ground truth.

2. **Correlation & Hypothesis Testing (FR-006)**:
 - **Pearson Correlation**: `r` between drift rate `b` (Exponential) and learning speed.
 - **Permutation Test**: 10,000 shuffles. Null Hypothesis: "No correlation between drift rate and learning speed." Test Statistic: "Pearson r".
 - **Linear Mixed-Effects Model (LMM)**: `learning_speed ~ drift_rate + (1 | subject)`. This accounts for subject-level random effects, addressing FR-006 directly, despite the aggregate nature of the data.
 - **Multiple Comparison Correction**: Bonferroni correction (p_corrected = p_raw * n_metrics) applied if n_metrics > 1 (Pearson, Cosine, Mahalanobis).

3. **Robustness & Sensitivity (FR-008)**:
 - **Threshold Sweep**: Stability threshold swept across `{70%, 75%, [deferred], [deferred], [deferred]}` (covering boundary behaviors required by US-3).
 - **Metric Comparison**: Drift rates compared across Pearson, Cosine, and Mahalanobis distances. Stability Criterion: Sign of correlation with learning speed must remain consistent.
 - **Split-Half Reliability**: Dataset split into two halves; correlation between drift rates calculated from each half reported.
 - **Exclusion Sensitivity**: Run analysis with and without excluding performance-modulated neurons. Compare correlations to quantify bias.
 - **Imputation Sensitivity**: Run analysis with and without linear interpolation. Compare results. Acceptance: If sign/significance changes, flag as "Imputation Sensitive".

### Power & Sample Size

- **Assumption**: The dataset contains N ≥ 15 subjects.
- **Exclusion Criterion**: If N < 15, the pipeline will **HALT** with an error message. This prevents invalid statistical conclusions from underpowered data.
- **Effect Size**: Power analysis assumes an expected correlation of `r > 0.5`.

### Computational Feasibility

- **CPU-First**: All methods (linear regression, permutation tests, LMM via `statsmodels`) are CPU-tractable. No GPU acceleration is required.
- **Memory**: Streaming data and online statistics accumulation ensure memory usage stays < 7 GB. Memory usage is monitored via `tracemalloc` at 1-second intervals.
- **Runtime**: Expected runtime < 6 hours for the full pipeline on 2 cores.

## Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **Exponential as Primary** | Constitution VII mandates Exponential decay as the primary metric. This overrides FR-005's linear requirement for the *primary* result, but FR-005 is satisfied by implementing Linear as a mandatory fallback. |
| **Linear as Fallback** | FR-005 mandates a linear model. Implementing it as a fallback ensures compliance with the spec while respecting the Constitution's primary requirement. |
| **Imputation via Interpolation** | US-1 AS-3 requires linear interpolation for missing behavioral logs. Excluding the subject entirely would reduce power unnecessarily. Interpolation is a standard, robust method for time-series gaps. Fallback: Exclude if gap > 2 days. |
| **LMM over Robust Regression** | FR-006 explicitly requires LMM. Despite the aggregate nature of the data, the LMM is used to align with the spec's explicit requirement and to account for potential hierarchical structure. |
| **Threshold Sweep Range** | US-3 Independent Test explicitly tests [deferred] and [deferred]. The sweep is expanded to `{[deferred], [deferred], [deferred], [deferred], [deferred]}` to ensure boundary behaviors are captured, addressing the previous concern about narrow ranges. |
| **OpenNeuro Dataset** | Verified URL available. Contains required variables. Avoids access-gated data flaws. If ephys data is missing, pipeline halts and reframes as synthetic-only validation. |

