# Research: Neural Entropy and Cognitive Flexibility in Aging

## Executive Summary

This research plan investigates the relationship between neural entropy (a measure of signal complexity) and cognitive flexibility in aging. The core hypothesis is that higher neural entropy in specific frequency bands correlates with better cognitive flexibility (fewer perseverative errors on WCST). The study is observational; thus, all findings will be framed as associational.

**Methodological Note**: The plan implements **Multiple Linear Regression (OLS)** with **Benjamini-Hochberg FDR** correction. This deviates from the original Spec (FR-004: Partial Pearson) and Constitution (Principle VII: Bonferroni) to correctly handle binary covariates and multiple comparisons. A formal amendment to the Constitution is requested.

## Dataset Strategy

**Critical Constraint**: The spec requires WCST (Wisconsin Card Sorting Test) scores. The "Verified datasets" block explicitly states: **"WCST: NO verified source found"**.
The spec also requires OpenNeuro datasets (ds000246, ds003104) containing *both* EEG and behavioral data. The verified list provides generic OpenNeuro parquet files but does not confirm the presence of WCST data in them.

**Strategy**:
1. **Primary Source**: Attempt to load the verified OpenNeuro parquet sources (`clane9/openneuro-fslr64k`).
2. **Variable Fit Check**: Before analysis, the pipeline MUST inspect the metadata/headers of the loaded dataset.
 * If `WCST_perseverative_errors` (or equivalent) column is missing, the dataset is **excluded**.
 * If EEG columns are missing or insufficient (e.g., < 60s duration), the dataset is **excluded**.
3. **Fallback**: If no verified dataset contains both EEG and WCST, the pipeline will halt with a `DATASET_VARIABLE_MISMATCH` error, flagging the gap in the spec. **No synthetic data or fabricated URLs will be used.**

**Verified Sources to Cite**:
* **EEG Data**: ` (Source: OpenNeuro FSLR64k subset).
* **EEG Events**: ` (Source: NeuroFusion).
* **Note**: The WCST behavioral data is **not** verified in the provided list. The pipeline must handle its absence gracefully.

| Dataset Name | Verified URL | Expected Variables | Status |
|:--- |:--- |:--- |:--- |
| OpenNeuro FSLR64k | ` | EEG channels, Age, Education | **Pending Verification** (Must check for WCST) |
| NeuroFusion Events | ` | Timestamps, Events | **Pending Verification** |
| WCST Scores | **NO VERIFIED SOURCE** | Perseverative Errors, Accuracy | **MISSING** (Spec Gap) |

## Methodological Approach

### 1. Preprocessing (US-1)
* **Filtering**: Bandpass –45 Hz (low-cut 1 Hz, high-cut 45 Hz) to remove drift and high-frequency noise. Notch filter at /60 Hz (adaptive based on metadata).
* **Artifact Removal**:
 * Detect bad channels (high variance, flatline) and interpolate.
 * Run ICA (Independent Component Analysis) to identify and remove ocular (EOG) and muscular (EMG) components.
* **Epoching**: Segment into short, non-overlapping epochs. Discard epochs with >20% amplitude deviation.
* **Quality Control**:
 * Exclude participants with <60 seconds of valid data.
 * **SNR Check (SC-001)**: Compute median SNR of preprocessed data relative to 1-45 Hz band power. **Exclude** participants with SNR < 5 dB.

### 2. Entropy Computation (US-1)
* **Metrics**: Sample Entropy (SampEn) and Approximate Entropy (ApEn).
* **Parameters**: Standard parameters ($m=2$, $r=0.2 \times \text{std}$).
* **Frequency Bands**: Delta (low-frequency), Theta (4-8), Alpha (8-12), Beta (12-30), Gamma (30-45). *Note: Spec says "beta: 12 Hz" and "gamma: -45 Hz", interpreted as Beta (12-30) and Gamma (30-45) based on standard neurophysiology and the 1-45 Hz filter limit.*
* **Stability**: Use `float64` precision. If NaNs occur, re-compute; if persistent, exclude participant.

### 3. Statistical Analysis (US-2)
* **Primary Test**: **Multiple Linear Regression (OLS)** (Deviation from Spec FR-004 Partial Pearson to handle binary covariates).
 * $Y$: WCST Perseverative Errors.
 * $X$: Entropy (SampEn/ApEn per band).
 * Covariates: Age, Education, Task Accuracy, Neurological Condition (Binary), Medication Use.
* **Collinearity Diagnostics (FR-012)**:
 * Calculate VIF for all predictors within the OLS framework.
 * **Resolution Strategy**: If VIF > 5, prioritize **Sample Entropy (SampEn)** and drop **Approximate Entropy (ApEn)** from the joint model.
 * **Bad Control Check**: Calculate correlation between 'Task Accuracy' and 'WCST Errors'. If $r > 0.7$, flag as a bad control and report bias risk.
* **Correction**: Benjamini-Hochberg FDR at a conventional significance threshold across all 10 tests (5 bands $\times$ 2 metrics).
* **Effect Size**: Partial $r$ (derived from OLS coefficients). Thresholds considered clinically meaningful.

### 4. Sensitivity Analysis (US-3)
* **Exclusion**: Re-run analysis excluding participants with neurological conditions/medications (if metadata available).
* **Threshold Sweep (FR-007)**:
 * **Data Quality Sweep**: Vary artifact rejection threshold across a low-to-moderate range in incremental steps.
 * **Delta Sweep**: Report variation in correlation coefficients (r) and p-values for absolute differences from the baseline, including cases with no deviation and small incremental deviations.
 * **Stability Metric**: Calculate the Coefficient of Variation (CV) of the correlation coefficient across the sweep. If **CV > 0.1**, flag the result as unstable.

## Statistical Rigor & Limitations

* **Multiple Comparisons**: FDR correction applied to the family of 10 tests.
* **Power Analysis**: **Deferred**. The plan acknowledges sample size limitations. A post-hoc power calculation will be included if $N$ allows, but the study is framed as exploratory.
* **Causal Inference**: **None**. The study is observational. All claims are associational. No randomization strategy exists.
* **Measurement Validity**: WCST is the gold standard for cognitive flexibility. Entropy measures are well-validated in EEG literature, but parameters must be consistent.
* **Collinearity**: SampEn and ApEn are highly correlated. The plan will report them separately but note the redundancy in the discussion. **Resolution**: If VIF > 5, ApEn is dropped.

## Compute Feasibility

* **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
* **Strategy**:
 * Process data in chunks (participants).
 * Use `mne`'s efficient I/O.
 * Avoid GPU-specific libraries.
 * Limit epoch count if memory pressure detected (downsample epochs).
* **Runtime**: Target < 4 hours for safety margin. **Note**: If the dataset ingestion fails due to missing WCST data, the pipeline terminates immediately, rendering the time constraint moot for that run.