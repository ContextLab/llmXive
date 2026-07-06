# Research: Neural Correlates of Error Monitoring During Simulated Navigation

## 1. Problem Statement & Hypothesis

**Core Question**: Is there an **associational** relationship between the amplitude of the Medial Frontal Negativity (MFN) component, recorded via EEG during simulated navigation, and the magnitude of directional error (angular deviation)?

**Hypothesis**: Based on the Reinforcement Learning theory of error monitoring (Holroyd & Coles, 2002), we hypothesize a positive **association**: larger directional errors are associated with larger (more negative) MFN mean amplitudes.
*Note: This analysis is strictly **associational**. While the study design involves simulated navigation, without randomization of error magnitude (which is determined by participant behavior), we cannot claim causal directionality (e.g., errors "elicit" MFN). The model will estimate the strength and significance of the association.*

## 2. Dataset Strategy

### Verified Datasets

The specification references the "Navigation Error Corpus" (Zenodo). However, the **# Verified datasets** block provided in the project context does **not** contain a verified URL for a "Navigation Error Corpus" or a specific dataset containing synchronized EEG and navigation trajectory data with the required variables (error magnitude, optimal path).

The available verified datasets are:
1.  `neurofusion/eeg-restingstate` (events.csv) - Resting state, not navigation.
2.  `JLB-JLB/seizure_eeg_train/eval` - Seizure data, not navigation error monitoring.
3.  `kjngansgfa/ds_mfn4rrjdsq` (parquet) - Labeled "MFN" but lacks context on navigation/trajectory variables.
4.  `ecnu-icalk/cmm-math` & others - Educational/Chat data, irrelevant.

**Critical Gap**: The required dataset (Navigation Error Corpus with synchronized EEG and trajectory) is **missing** from the verified list.

**Plan Adjustment**:
1.  **Immediate Action**: The implementation will attempt to download the dataset from the Zenodo record URL *if* provided in the spec's assumptions, but since no verified URL exists in the context, the `download.py` script must handle the case where the dataset is unavailable.
2.  **Fallback Strategy**: For the purpose of the *planning* and *testing* of the pipeline, we will use a **synthetic dataset generator** that mimics the structure of the Navigation Error Corpus (EEG epochs + error magnitude columns) to verify the code logic.
3.  **Real Data Execution**: The pipeline will only produce valid scientific results once a verified URL for the "Navigation Error Corpus" is provided in the `# Verified datasets` block. The **Verified Accuracy** gate (Constitution Principle II) is currently **BLOCKED** until this is resolved.

*Note: If the `kjngansgfa/ds_mfn4rrjdsq` dataset contains the necessary navigation metadata, it will be used. If not, the pipeline will fail gracefully with a clear error message indicating missing variables.*

### Variable Mapping (Hypothetical)

| Variable | Source Column (Expected) | Role |
| :--- | :--- | :--- |
| `participant_id` | `subject_id` / `participant` | Random Intercept |
| `eeg_data` | `eeg_signal` (matrix) or multiple channels | Input for MFN extraction |
| `error_timestamp` | `error_time` | Epoching trigger |
| `error_magnitude` | `angular_deviation` | Fixed Effect (Predictor) |
| `optimal_path` | `path_optimal` | Derivation of error magnitude |

## 3. Methodology

### 3.1 Data Preprocessing (FR-002, FR-003, FR-004)
1.  **Filtering**: Bandpass 1-40 Hz, Notch 60 Hz (MNE-Python `filter_data`).
2.  **ICA**: Run FastICA to identify ocular/muscular components. Components will be automatically flagged based on correlation with EOG channels (if available) or topography, then removed.
3.  **Epoching**: Extract epochs from -200ms to 800ms relative to `error_timestamp`.
4.  **Baseline Correction**: Baseline period: -200ms to 0ms.
5.  **Feature Extraction**: **Mean Amplitude** in the 200-400ms window at FCz, Cz, Fz. (Replaces "Peak" to reduce noise sensitivity).
6.  **Angular Deviation**: Calculate the angle between heading and optimal path vectors at error onset (see Plan for algorithm).

### 3.2 Statistical Modeling (FR-005)
1.  **Primary Model**: Linear Mixed-Effects (LMM).
    *   Formula: `MFN_Mean_Amplitude ~ Error_Magnitude + (1 | Participant_ID)`
    *   Library: `statsmodels` or `pymer4`.
2.  **Non-Linearity Check**: Fit a Generalized Additive Model (GAM) with a smooth term for `Error_Magnitude`.
    *   **Model Selection Strategy**: Compare LMM and GAM using **AIC/BIC**. If $\Delta AIC > 2$, select the model with lower AIC. If $\Delta AIC < 2$, report both. This avoids p-hacking by not using the training data's p-value to select the model.
3.  **Collinearity Check**: Calculate Variance Inflation Factor (VIF) for predictors. If VIF ≥ 5, flag and report.
4.  **Power Analysis**: Acknowledging that power in LMMs depends on the number of clusters (participants) and the intra-class correlation (ICC), a formal power calculation will be performed using simulation-based methods (e.g., `powerlmm` or `simr`) in the implementation phase, rather than a simple correlation power calculation.

### 3.3 Robustness & Corrections (FR-006, FR-007, FR-008)
1.  **Sensitivity Analysis**: Sweep `min_error_threshold` = {5, 10, 15, 20} degrees.
    *   **Important**: The predictor `Error_Magnitude` is calculated for **ALL** events. The threshold is applied only as an **inclusion filter** for the regression subset to check robustness, avoiding truncation bias.
    *   **Primary Threshold**: If a primary threshold is required, it must be defined a priori based on behavioral theory. Otherwise, the continuous predictor is used for the primary claim.
2.  **Multiple Comparison**: If testing multiple electrodes (FCz, Cz, Fz), apply Bonferroni correction to p-values.
3.  **Output Artifacts**: Generate a **Sensitivity Analysis Summary Table** and **Sensitivity Plot** to explicitly measure stability (SC-002).

## 4. Compute Feasibility Assessment

*   **Hardware**: GitHub Actions Free Tier (multi-core CPU, substantial RAM).
*   **Data Size**: Estimated ~500 MB for [deferred] participants (raw EEG).
*   **Memory**: Preprocessing (filtering/ICA) is memory intensive.
    *   *Mitigation*: Process participants in batches. Do not load all raw data into RAM simultaneously. Use `mne`'s memory mapping where possible.
*   **Runtime**:
    *   ICA on [deferred] participants: Estimated 2-3 hours on CPU (if N=47).
    *   Modeling: < 10 minutes.
    *   Total: Target < 6 hours.
*   **Dependencies**: `mne`, `scipy`, `statsmodels` are CPU-optimized and do not require GPU.
*   **Validation**: The pipeline includes an explicit `validate_feasibility()` step to log runtime and memory usage against the 6h/7GB constraints.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Missing** | High | Pipeline includes a synthetic data generator for testing. Real analysis paused until verified URL provided. **Verified Accuracy Gate BLOCKED.** |
| **ICA Failure** | Medium | If ICA fails to remove artifacts, epochs are flagged and excluded from analysis (FR-004 edge case). |
| **Non-Linearity** | Medium | GAM fallback is implemented with AIC-based selection. |
| **Memory Overflow** | Medium | Batch processing of participants; clear intermediate variables. |
| **Circular Inference** | High | Model selection based on AIC/BIC, not p-values on training data. |

## 6. Decision Rationale

*   **LMM over OLS**: Chosen to account for within-subject correlation (random intercepts), which is standard in EEG/behavioral studies.
*   **Bonferroni over FDR**: Bonferroni is more conservative and appropriate for the small number of comparisons (3 electrodes).
*   **Sensitivity Sweep**: Essential to address the "threshold artifact" concern raised in the methodology panel.
*   **Mean vs Peak Amplitude**: Mean amplitude is preferred for single-trial analysis to reduce noise sensitivity and improve construct validity.
*   **AIC vs P-value Model Selection**: Prevents researcher degrees of freedom and circular validation.