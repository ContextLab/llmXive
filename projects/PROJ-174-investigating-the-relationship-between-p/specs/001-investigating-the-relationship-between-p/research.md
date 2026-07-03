# Research: Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

## Dataset Strategy

**Critical Verification Step**: The project requires a verified eye-tracking dataset. The `# Verified datasets` block provided in the user message does **not** currently contain a verified URL for an eye-tracking dataset (ds001734 and ds002642 are fMRI datasets, not eye-tracking).

**Decision**:
1.  **Hard Gate**: The implementation will run `verify_data_availability.py` first. If no verified eye-tracking dataset is found in the `# Verified datasets` block, the pipeline **HALTS** with Exit Code 1.
2.  **No Synthetic Fallback for Empirical Analysis**: Synthetic data will **NOT** be used to answer the research question. It is reserved strictly for unit testing the pipeline logic.
3.  **Scope**: The project is scoped as an empirical investigation. If the verified block lacks a valid source, the project cannot proceed to `research_complete`.
4.  **Spec Contradiction**: The spec cites ds001734 and ds002642. These are fMRI datasets. The pipeline explicitly rejects these. If these are the only sources, the pipeline halts and flags the spec for correction.

**Dataset Table**:

| Dataset Name | Purpose | Verified URL (from block) | Programmatic Loader | Status |
| :--- | :--- | :--- | :--- | :--- |
| OpenNeuro ds001734 | **Invalid** (fMRI, not eye-tracking) | N/A | N/A | **Excluded** |
| OpenNeuro ds002642 | **Invalid** (fMRI, not eye-tracking) | N/A | N/A | **Excluded** |
| Verified Eye-Tracking Dataset | Primary source | **Required** | `datasets.load_dataset(...)` | **Gate: Must Exist** |
| Synthetic Pupil Dataset | Unit tests only | N/A | `code/generate_synthetic_test_data.py` | **Test Only** |

*Note: If the verified block is updated to include a valid eye-tracking dataset (e.g., `openneuro/dsXXXX` with `eyetracking` tag), the pipeline will proceed. Otherwise, it halts.*

## Methodological Rationale

### 1. Preprocessing & Signal Integrity
- **Filtering**: Butterworth th order low-pass (a task-appropriate frequency) is standard for removing blink artifacts and high-frequency noise while preserving task-evoked dilation (Peirce et al., 2019).
- **Blink Interpolation**: Linear interpolation for gaps < 200ms; exclusion if > 30% missing. This balances data retention with signal integrity.
- **Timestamp Validation**: Non-monotonic timestamps will trigger trial exclusion to prevent temporal misalignment.

### 2. Temporal Alignment Strategy (New)
- **Physiological Latency**: Pupil dilation is a slow signal (latency on the order of seconds) compared to rapid visual search events.
- **Strategy**: The plan mandates **time-lagged correlation analysis**. We will shift the pupil signal relative to the search event by 0.5s, 1.0s, 1.5s, and 2.0s to find the optimal alignment.
- **Event-Related Averaging**: For trial-wise analysis, we will average the pupil signal within the window defined by the optimal lag.

### 3. Load Proxies
- **Search Time**: Direct behavioral measure (reaction time).
- **Fixation Count**: Standard cognitive load indicator in visual search.
- **Target Salience**: Computed via Gabor filters on stimulus images if metadata is missing.
    - **Conceptual Redundancy Warning**: 'Fixation count' and 'search time' are often collinear by definition (fixation_count ≈ search_time / mean_fixation_duration). The VIF check in the LME model is a statistical necessity to handle this, not a proof of distinct cognitive processes.
    - **Missing Data**: If stimulus images are missing, the 'target salience' proxy is **uncomputable**. The correlation matrix will record this as `status: UNFULFILLABLE`.

### 4. Statistical Analysis
- **Correlations**:
    - **Assumption Check**: Before Pearson correlation, check for linearity and normality.
    - **Fallback**: If assumptions are violated, use **Spearman's rho** and report both.
    - **Correction**: Apply Benjamini-Hochberg FDR to the set of valid tests.
    - **Missing Proxy Handling**: If 'target salience' is uncomputable, the system logs the exclusion and proceeds with the remaining tests, explicitly recording the missing status as 'UNFULFILLABLE'.
- **LME Model**: `pupil_metric ~ search_time + target_salience + fixation_count + (1|subject)`.
    - **VIF Check**: Variance Inflation Factor calculated before fitting. If VIF > 5, the highest collinear predictor is dropped (FR-005).
    - **Reduced Model**: If 'target salience' is uncomputable, fit a reduced model excluding that predictor and log the reduction.
    - **Causal Inference**: Explicitly framed as **associational** (Assumption in spec). No causal claims.

### 5. Real-Time Classification
- **Sliding Window**: 1-second lookback, 200ms step.
- **Model**: Logistic Regression with L2 regularization (CPU-friendly).
- **Ground Truth**:
    - **Priority**: Use an independent behavioral proxy (e.g., secondary task accuracy, subjective rating).
    - **Fallback**: If unavailable, use median split of search time.
    - **Critical Logic**: If independent truth is missing, **DISCARD** results from empirical claims. Report as "Pipeline Feasibility Check" only. Do not present as validation of cognitive load.
    - **Labeling**: If using search time, explicitly label the output as **"Search-Time Estimation (Self-Validated)"** and document the circularity limitation in the results.
- **Threshold Sensitivity**: Swept over {0.40, 0.50, 0.60} to ensure stability (FR-009).

## Compute Feasibility & Constraints

- **Memory**: Data loaded in chunks. `pandas` operations on subsets.
- **CPU**: No GPU. `scipy.signal` for filtering. `statsmodels` for LME (CPU only). `scikit-learn` for logistic regression.
- **Runtime**: Pipeline designed to complete in < 6 hours.
- **Libraries**: `mne`, `statsmodels`, `scikit-learn`, `pandas`, `numpy`. All have CPU wheels.

## Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **Missing Verified Dataset** | Pipeline halts with Exit 1. No empirical results generated. |
| **Invalid Spec Datasets** | Pipeline halts with Exit 1. Spec flagged for correction. |
| **Missing Target Salience** | Proxy marked 'UNFULFILLABLE'; model refitted reduced; correlation logged as 'UNFULFILLABLE'. |
| **High Collinearity (VIF > 5)** | Drop predictor, log reduction, refit model. |
| **Insufficient Trials (< 20/subject)** | Aggregate or abort with warning. |
| **Memory Overflow** | Stream data; subsample if necessary; use `dtype` optimization. |

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Hard Gate for Data** | Ensures scientific validity. Synthetic data cannot answer the empirical question. |
| **Temporal Alignment** | Addresses the physiological latency of pupil dilation. |
| **Spearman Fallback** | Ensures robustness against non-linear/non-normal distributions. |
| **Circularity Labeling** | Explicitly documents the limitation when independent ground truth is missing. |
| **VIF as Statistical Patch** | Acknowledges conceptual redundancy between search time and fixation count. |
| **Discard Self-Validated Results** | Prevents presenting trivial correlation as validation of cognitive load. |