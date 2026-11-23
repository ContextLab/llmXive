# Research: Cross-Dataset Consistency of Alpha Peak Frequency Estimates in Resting-State EEG

## Overview

This research phase validates the feasibility of the implementation plan, confirms dataset availability, and details the statistical methodology for variance decomposition.

## Dataset Strategy

The project requires resting-state EEG data with sufficient subjects (N ≥ 20 per dataset) and raw voltage time-series. The plan targets multiple distinct OpenNeuro datasets.

**Verified Datasets Strategy**:
The "Verified datasets" block provided for this project contains **NO** verified source for raw, multi-subject resting-state OpenNeuro EEG datasets (e.g., `ds003865`) in a directly downloadable format suitable for this specific analysis. The available links are for specific derived formats (parquet/arrow) or unrelated tasks (seizure, summarization).

**Decision**: Since the spec explicitly requires OpenNeuro datasets (ds003865, ds003392, ds003775) and the "Verified datasets" block does not provide a direct URL for these, the implementation **MUST** rely on the `openneuro-py` library to fetch data from the official OpenNeuro API. This is the only valid programmatic path for these specific IDs.
*   **Action**: The `download.py` script will use `openneuro-py` to fetch `ds003865`, `ds003392`, and `ds003775`.
*   **Risk Mitigation**: If `openneuro-py` fails or datasets are removed, the system will halt with a "Data Integrity" error (SC-004), preventing fabrication.
*   **Feasibility**: OpenNeuro datasets are public and do not require credentials. The `openneuro-py` library supports partial downloads and streaming, fitting the CPU-only constraint.

**Dataset Selection Rationale**:
1.  **ds003865**: Resting-state EEG, healthy adults, high sampling rate.
2.  **ds003392**: Resting-state EEG, clinical/healthy mix, different hardware.
3.  **ds003775**: Resting-state EEG, distinct population, verifying cross-dataset generalizability.

*Note: A pre-check step will verify that each dataset contains 'eeg' files and ≥20 subjects. If not, the dataset is skipped and logged.*

## Methodology & Statistical Rigor

### 1. Preprocessing Pipelines
Two pipelines are implemented to isolate variance:
*   **Pipeline A (Standard)**: `mne.filter.filter_data` (1-45 Hz), `mne.filter.notch_filter` (50/60 Hz), `mne.set_eeg_reference('average')`, `mne.preprocessing.ICA` (FastICA, 20 components, auto-reject based on EOG correlation > 0.8).
*   **Pipeline B (Alternative)**: `mne.filter.filter_data` (0.5-40 Hz), `mne.filter.notch_filter` (50/60 Hz), `mne.set_eeg_reference('mastoids')`, **No ICA**.

### 2. APF Estimation & Calibration
* **Method 1 (Frequency-Domain)**: Welch's method (`scipy.signal.welch`) with 2s windows, [deferred] overlap. Peak detection in 8-13 Hz range.
*   **Method 2 (Time-Domain)**: Autocorrelation of the filtered signal (8-13 Hz bandpass). First significant peak > 0.5 lag converted to frequency.
*   **Ground Truth Calibration**: A synthetic EEG signal with a known dominant peak frequency is generated. Both methods are applied to this synthetic signal to calculate absolute error (Accuracy). This breaks the circularity of comparing two methods on real data by providing an external reference.
*   **Validity**: Both methods are standard in neurophysiology. The dual-method approach addresses measurement validity by cross-validating the peak against a synthetic ground truth.

### 3. Variance Decomposition
*   **Model**: Linear Mixed-Effects Model (LMM).
    *   Formula: `APF ~ dataset_source + pipeline_type + estimation_method + (1|subject_id) + (1|subject_id:pipeline) + (estimation_method|subject_id)`
    *   **Rationale**: The fixed effects capture the main factors. The random effects `(1|subject_id:pipeline)` and `(estimation_method|subject_id)` explicitly model the correlation of the 4 measurements (2 pipelines x 2 methods) per subject, resolving pseudoreplication.
    *   **Library**: `statsmodels` (MixedLM).
    *   **Interpretation**:
        *   `dataset_source`: Framed as "Between-Study Heterogeneity (Confounded)" (includes hardware, population, acquisition confounds), NOT purely biological.
        *   `estimation_method`: Framed as "Algorithmic Bias" (measurement artifact).
    *   **Assumption**: Observational data. Claims are strictly **associational**.
*   **Bootstrapping**: Non-parametric bootstrapping (1000 resamples) of subject-level residuals to generate 95% CIs for variance components (R²).
*   **Power Analysis**: **Simulation-based**. Generate 1000 synthetic datasets with known variance components (dataset=0.4, pipeline=0.1, residual=0.5) using `numpy` and `pandas`. Fit the LMM to each. Calculate the proportion of simulations where the pipeline variance is significantly > 0 (via Likelihood Ratio Test). This replaces the invalid fixed-effect power analysis.

### 4. Multiple Comparisons & Corrections
*   **Correction**: Since the primary hypothesis is a single omnibus test of variance components, no multiple comparison correction is needed for the main LMM.
*   **Sensitivity Analysis (SC-005)**: The alpha band is swept (Lower: 7.5, 8.0, 8.5; Upper:, 13.0, 13.5). This is a robustness check. The output is a "Sensitivity Table" showing the delta mean APF for each combination. Success is defined as the max delta ≤ 0.2 Hz.

## Compute Feasibility

*   **CPU-First**:
    *   **Preprocessing**: `mne` operations (filtering, ICA) are highly optimized for CPU. For < 50 subjects, memory usage is < 4GB.
    *   **APF Estimation**: Welch's method and autocorrelation are O(N log N) and trivial for < 100 subjects.
    *   **Modeling**: `statsmodels` MixedLM is CPU-based and efficient for this sample size.
*   **GPU Escape Hatch**:
    *   **Not Required**: The methodology (ICA, Welch, LMM) does not require GPU acceleration. No transformers or deep learning models are used.
    *   **Decision**: The entire pipeline is planned for CPU execution. The "GPU escape hatch" is reserved for future iterations if deep learning-based artifact removal is introduced.

## Data Availability & Feasibility Check

*   **Dataset Fit**: The selected OpenNeuro datasets (ds003865, ds003392, ds003775) contain raw `.edf` or `.vhdr` files which are the source for APF calculation. This matches the requirement for "raw voltage time-series".
*   **Access**: Public access via `openneuro-py`. No credentials needed.
*   **Size**: Estimated total size for multiple datasets is in the range of several gigabytes.
    *   **Strategy**: `download.py` will use `openneuro-py` with `--include` flags to download only `eeg` and `participants` files.
    *   **Streaming**: If a single dataset > 4GB, the script will process subjects sequentially (download -> process -> delete raw) to stay within 7GB RAM limit.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Missing Subjects** | High (Power analysis fails) | Pre-check skips dataset. If < 2 datasets remain, halt. |
| **BIDS Metadata Incomplete** | High (Cannot determine sampling rate) | Pre-check validates BIDS. If `sampling_frequency` missing, skip subject. |
| **No Alpha Peak Found** | Medium (Missing data) | Flag as "Indeterminate" (US-2). Exclude from mean calculation but report count. |
| **RAM Exceeded** | High (CI Job Fail) | Implement sequential processing: Process Dataset 1 (Download->Process->Model) -> Delete -> Dataset 2. |
| **API Fetch Failure** | High (No Data) | System halts with "Data Integrity" error. No fabrication. |

## Decision Rationale

The choice of OpenNeuro via `openneuro-py` is the only viable path given the spec's requirement for specific dataset IDs and the absence of verified direct URLs in the provided block. The CPU-first approach is justified because the statistical methods (LMM, Welch, ICA) are computationally tractable on the free-tier runner for the target sample size (N < 150). The simulation-based power analysis and random slope model ensure statistical rigor. No synthetic data or GPU offload is planned, ensuring the results reflect real-world variability.