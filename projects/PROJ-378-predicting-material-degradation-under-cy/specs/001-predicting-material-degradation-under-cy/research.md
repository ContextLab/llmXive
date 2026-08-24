# Research: Predicting Material Degradation Under Cyclic Loading from Public Datasets

## Executive Summary

This research plan investigates the **feasibility** of predicting material degradation (remaining useful life or stiffness loss) under cyclic loading using public datasets. The analysis relies on **only** the verified datasets provided in the execution context.

**Critical Finding**: The "Verified datasets" block contains **no** materials fatigue data (e.g., from Materials Project). It contains:
1. **NIST**: Security policy documents (JSONL/Parquet) - *Irrelevant to material science*.
2. **UCI**: Human Activity Recognition (HAR), Shopper behavior, and URL classification - *Irrelevant to material science*.

**Decision**: The original scientific hypothesis ("Composition + Loading predict Degradation") is **untestable** with the available verified data. The research goal is therefore **pivoted** to a **Data Availability Study**: "Do public, verified datasets contain sufficient material fatigue data to support machine learning modeling?"

**Revised Scope**: The implementation will:
1. Attempt to load the verified NIST/UCI datasets.
2. Explicitly verify the absence of required columns (e.g., `stress_amplitude`, `elemental_percent`).
3. Log a **Fatal Coverage Gap** and halt the pipeline with a clear error message indicating that no verified source exists for the required data.
4. **Do NOT** fabricate data or use unverified URLs.
5. **Do NOT** perform statistical analysis on irrelevant data (as this would be scientifically invalid).

## Dataset Strategy

| Dataset Name | Source Type | Verified URL | Suitability for Spec | Action |
|:--- |:--- |:--- |:--- |:--- |
| NIST 800-53 (Security) | HuggingFace | ` | **None**. Contains security policy text, not material properties. | **Exclude**. |
| UCI HAR (Human Activity) | HuggingFace | ` | **None**. Contains accelerometer data for human motion, not material fatigue. | **Exclude**. |
| UCI Shopper | HuggingFace | ` | **None**. Contains customer behavior data. | **Exclude**. |
| UCI DROP | HuggingFace | ` | **None**. Contains reading comprehension QA data. | **Exclude**. |
| Reddit URLs / Malicious URLs | HuggingFace | Various | **None**. Text/URL classification. | **Exclude**. |

**Conclusion**: No verified dataset exists in the provided list that supports the study of material degradation under cyclic loading. The plan explicitly states that the **required data is unavailable** in the verified sources.

## Hypothesis Termination

**Original Hypothesis**: "Material composition and loading parameters predict degradation metrics."
**Status**: **UNTESTABLE**.
**Reason**: The independent variables (composition, stress) and dependent variable (degradation) are absent from all available data sources.
**New Research Question**: "Do public, verified datasets contain sufficient material fatigue data to support machine learning modeling?"
**Expected Answer**: **NO**.

## Methodological Rigor

### Statistical Approach (Conditional on Data Availability)
*Note: Since data is unavailable, these methods are theoretical only for this plan. They will NOT be executed.*

1. **Imputation**: If data were available, `IterativeImputer` (max_iter=10) would be used.
2. **Modeling**: ElasticNet, RF, GB would be used.
3. **Inference**: Permutation tests, t-tests, Bonferroni correction.
4. **Uncertainty**: Quantile Regression Forests.

**Execution Status**: **SKIPPED**. The pipeline will terminate before these steps to avoid scientific invalidity.

### Compute Feasibility
* **CPU-First**: All models are available in `scikit-learn` and run efficiently on CPU.
* **Memory**: If the dataset exceeds 7 GB, the plan includes a fallback to subsampling (FR-007).
* **GPU**: Not required for these classical ML models.

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|:--- |:--- |:--- |:--- |
| **No Valid Data Source** | **High (Confirmed)** | **Fatal**. The study cannot proceed as specified. | The pipeline will detect missing columns and exit gracefully with a "Data Unavailable" status, adhering to the "No Fabrication" rule. |
| **Data Leakage** | Medium | High | Strict separation of training/validation splits; imputation fitted only on training folds. (Skipped in this run). |
| **Overfitting** | Medium | Medium | 5-fold CV; tree depth limits. (Skipped in this run). |
| **Collinearity** | High | Medium | Elemental percentages sum to [deferred]. (Skipped in this run). |

## Decision Rationale

**Why not use a different dataset?**
The project constitution (Principle II: Verified Accuracy) and the execution rules strictly forbid using URLs not listed in the "Verified datasets" block. Using a real but unverified URL (e.g., a real Materials Project API) would violate the "Verified Accuracy" gate and result in a rejection.

**Why not synthesize data?**
Synthesizing data would violate Principle III (Data Hygiene) and the "No Fabrication" rule. The plan must reflect reality: the required data is not available in the allowed sources.

**Why not run the models on irrelevant data?**
Running regression on Human Activity data to predict Material Degradation would produce **scientifically meaningless** results (noise fitting). This violates the principle of **Scientific Soundness**. The plan must terminate rather than produce invalid science.

**Next Steps**:
The implementation will be a "stub" that attempts to load the verified NIST/UCI data, confirms the absence of material fatigue variables, and reports the gap. This is the only compliant path forward given the constraints.