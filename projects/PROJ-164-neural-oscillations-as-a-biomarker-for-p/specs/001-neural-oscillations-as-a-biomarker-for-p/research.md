# Research: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

## 1. Problem Statement & Hypothesis

**Hypothesis**: Resting-state and task-related EEG oscillatory features (specifically power in beta/gamma bands and connectivity via PLV/wPLI) predict individual motor performance improvement after a single session of anodal tDCS over the primary motor cortex.

**Challenge**: Public datasets often contain EEG recordings or tDCS outcomes separately, but rarely paired for the same subjects. This creates a "data gap" for direct predictive modeling.

**Strategy**:
1.  **Primary Mode**: Skipped. No verified paired dataset exists in the provided list.
2.  **Positive Control Mode**: Generate synthetic tDCS response variables with a **known, injected signal** correlated to specific EEG features (e.g., C3-C4 beta power). This allows validation of the *pipeline's ability to detect a known signal* without making false claims about real tDCS response.
3.  **Fallback Mode (Legacy)**: If no signal can be injected, generate random noise (decoupled from EEG) for structural validation only. This mode is deprecated for scientific claims.

## 2. Verified Datasets

The following datasets have been verified for availability and format. **Only these sources are used.**

| Dataset Name | Type | Verified URL | Relevance to Feature |
| :--- | :--- | :--- | :--- |
| **PhysioNet EEG Motor Movement/Imagery** | EEG (Parquet) | https://huggingface.co/datasets/JasiekKaczmarczyk/physionet-preprocessed/resolve/main/data/train-00000-of-00001-f9e59a1e6cd4938c.parquet | Provides resting-state and task-related EEG epochs (motor imagery). Used for feature extraction. |
| **OpenNeuro tDCS Motor Task** | **N/A** | **No verified paired source** | **Gap**: The previously cited OpenNeuro URL points to fMRI data. No verified paired EEG/tDCS dataset exists. Primary Mode is impossible. |
| **Neurofusion EEG Resting State** | **N/A** | **No verified source** | **Gap**: The previously cited URL points to events only. No raw EEG data available. |

**Dataset Fit Analysis**:
*   **PhysioNet**: Contains high-quality EEG epochs for motor imagery. **Missing**: tDCS intervention data. It will be used for the *EEG feature extraction* component.
*   **Decision**: The pipeline will load PhysioNet. Since no paired tDCS data exists, the system **must** switch to **Positive Control Mode**. Synthetic targets will be generated with a known injected signal (e.g., `target = 0.15 * beta_power + noise`) to validate the pipeline's sensitivity.

## 3. Methodology & Statistical Rigor

### 3.1 Preprocessing (FR-003)
*   **Filtering**: Band-pass 1–45 Hz (Butterworth, 4th order) to remove DC drift and high-frequency noise.
*   **Referencing**: Common Average Reference (CAR) to minimize reference electrode bias.
*   **Bad Channels**: Automated rejection via z-score > 3.0 on variance; logged but not imputed (data integrity).
*   **Epoching**: 2-second windows aligned to task onset (or resting blocks).

### 3.2 Feature Extraction (FR-004, FR-005)
* **Spectral Power**: Welch's method (2s windows, [deferred] overlap) to compute power in Delta (1–4), Theta (4–8), Alpha (8–13), Beta (13–30), Gamma (30–45) bands.
*   **Connectivity**:
    *   **ROI Connectivity**: PLV and wPLI computed specifically for **Motor ROI pairs** (C3-C4, C3-Cz, C4-Cz) to preserve spatial specificity for the motor hypothesis.
    *   **Global Mean**: Mean PLV/wPLI across all pairs for control.
*   **Dimensionality**: Features aggregated per subject (mean power per band, mean connectivity per ROI pair).

### 3.3 Modeling Strategy (FR-005)
*   **Model**: Ridge Regression (L2 regularization).
*   **Rationale**: EEG features are often highly correlated (collinearity). Ridge handles this better than OLS.
*   **Validation**: 5-fold Cross-Validation.
*   **Hyperparameters**: Nested search for `alpha` (regularization strength).
*   **Positive Control Constraint**: In Positive Control Mode, the model must detect the injected signal (R² > 0, p < 0.05). If it fails, the pipeline is flagged as broken.

### 3.4 Validation & Rigor (FR-006, FR-007)
*   **Permutation Testing**: 1,000 permutations of the target variable to establish a null distribution. P-value = (count of permuted R² ≥ observed R² + 1) / 1001.
*   **Multiple Comparison Correction**: False Discovery Rate (FDR, Benjamini-Hochberg) applied across all frequency bands and connectivity pairs to control family-wise error.
*   **Sensitivity Analysis**:
    *   Sweep significance thresholds: p ∈ {0.01, 0.05, 0.1}.
    *   Sweep variance explained thresholds: R² ∈ {0.2, 0.3, 0.4}.
    *   Report stability: **Success defined as `stability_variance ≤ 0.05`**.

### 3.5 Power Analysis & Compute Feasibility
*   **Power Analysis**: With N < 100 and small effect sizes (typical for tDCS), the study is **underpowered** for detecting individual predictors with high confidence. The study is framed as **Exploratory**. Power calculations are deferred to a larger future cohort.
*   **Hardware**: CPU-only (2 cores, 7 GB RAM).
*   **Mitigation**:
    *   Data subset to ~100 subjects if available.
    *   Epochs downsampled to 128 Hz if original is higher.
    *   Permutation test run in batches to stay under RAM.
    *   No GPU/CUDA dependencies.

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **No Paired Data** | High | System switches to **Positive Control Mode** with injected signal; pipeline validated for sensitivity; no false biomarker claims about real data. |
| **Collinearity** | Medium | Ridge regression handles correlated predictors; results interpreted as "joint predictive power" not independent effects. |
| **Small Sample Size** | High | Power analysis acknowledges limitation; results framed as "exploratory"; permutation tests used to avoid parametric assumptions. |
| **Memory Overflow** | Medium | Process data in batches; limit connectivity pairs to Motor ROI. |

## 5. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use Ridge over Lasso** | EEG features are continuous and correlated; Lasso (L1) might zero out too many relevant features. Ridge is more stable for small N. |
| **Positive Control (Injected Signal)** | Required to validate the pipeline's *sensitivity* (FR-001) without hallucinating a real biomarker. Decoupled from real data but coupled to known synthetic signal. |
| **FDR over Bonferroni** | EEG features are not independent; Bonferroni is too conservative. FDR is standard in neuroimaging. |
| **CPU-Only Execution** | GitHub Actions free tier has no GPU. Models must be lightweight (Ridge) and data sampled. |
| **Deferred Cross-Dataset Validation** | No second verified paired dataset exists. Principle VII is deferred until a new dataset is identified. |