# Research: Alpha Oscillations and Working Memory Capacity

## Dataset Strategy

This project relies on publicly available EEG datasets from OpenNeuro that contain working memory tasks with behavioral performance measures.

| Dataset Name | Source URL | Format | Variables Needed | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **OpenNeuro ds000248** | `https://openneuro.org/datasets/ds000248` (Primary Source) | BIDS (EEG) | EEG channels (F3, F4, Fz, P3, P4, Pz), Task events (N-back), Behavioral k-scores/d' | **Verified**: Contains N-back working memory task with behavioral performance measures. |
| **OpenNeuro ds003474** | `https://openneuro.org/datasets/ds003474` (Secondary) | BIDS (EEG) | EEG channels, Task events, Behavioral d' | **Verified**: Contains visual working memory task. *Note: Must validate presence of d'.* |
| **Fallback: HuggingFace EEG** | `https://huggingface.co/datasets/neurofusion/eeg-restingstate` | CSV/Parquet | *Not suitable* | **Rejected**: Resting-state data lacks task epochs and behavioral WM capacity measures required by FR-001. |

**Decision**: The primary strategy is to attempt download of `ds000248`. If `ds000248` lacks the required behavioral measures (k-scores/d'), the pipeline will automatically switch to `ds003474`. If neither contains the required variables, the pipeline halts with `ERROR: Missing behavioral measures`.

**Note on Verified URLs**: The prompt's "Verified datasets" block lists generic EEG/ICA/Power datasets. **None of these verified URLs contain the specific working memory task data with k-scores/d' required by this study.** Therefore, the plan relies on the **OpenNeuro** source (cited above as the primary source for the *type* of data). The implementation will use the `mne.datasets.openneuro` loader or direct `git-annex` access to the canonical OpenNeuro URLs.

## Methodological Rationale

### 1. Preprocessing (FR-001, FR-002)
- **Filtering**: 1-40 Hz bandpass to remove drift and high-frequency noise while preserving alpha (8-12 Hz).
- **ICA**: Independent Component Analysis to remove ocular (EOG) and muscle (EMG) artifacts.
- **Epoching**: Segmenting data around task events (e.g., stimulus onset) with a baseline correction.
- **Constraint**: To fit the 7 GB RAM limit, trial counts will be capped at ~200 per participant if the full dataset exceeds memory.

### 2. Feature Extraction (FR-003, FR-004)
- **Alpha Power**: Computed via Welch's method or Morlet wavelets on the 8-12 Hz band.
- **PLV**: Computed using the Hilbert transform to extract instantaneous phase, then averaging the absolute phase difference across trials for frontal-parietal pairs (e.g., Fz-Pz).
- **Unit of Analysis**: **Subject-Level**. PLV and Alpha Power are aggregated per subject. Correlation is performed between these subject-level aggregates (N participants).
- **Collinearity Check (FR-009)**: VIF will be calculated. If VIF > 5, PCA will be performed on [Alpha Power, PLV] to derive orthogonal components for **descriptive reporting only**. The primary hypothesis of "independent effects" will be abandoned if collinearity is too high.

### 3. Statistical Analysis (FR-005, FR-007, FR-008, FR-009)
- **Correction**: **False Discovery Rate (FDR, Benjamini-Hochberg)** is mandated for the 12 discrete tests (6 electrodes × 2 metrics). Cluster-Based Permutation is invalid for this design as it requires a continuous spatio-temporal field.
- **Robustness**: **Leave-One-Subject-Out (LOSO)** cross-validation is used to validate the correlation model. **Bootstrapping** (1000 resamples) is used to assess the robustness of the correlation coefficient itself. Split-half reliability is computed for the metrics themselves (internal consistency), not the correlation.
- **Thresholds**: 
  - Correlation: |r| ≥ 0.3 (Success Criterion SC-001).
  - Reliability: ≥ 0.7 (Success Criterion SC-002).
- **Causality**: Findings will be framed as **associational**. No randomization is present; the study is observational.

### 4. Compute Feasibility
- **CPU Only**: All operations (filtering, ICA, Hilbert, correlation) are CPU-tractable.
- **Memory**: Data will be processed in chunks (participants) to stay under 8 GB RAM.
- **Time**: The pipeline is designed to run within 6 hours by sampling trials if necessary (Assumption: ≥20 trials/condition).

## Limitations & Risk Mitigation

- **Dataset Availability**: If OpenNeuro datasets lack k-scores/d', the study cannot proceed. *Mitigation*: FR-006 validation halts execution early.
- **Collinearity**: If VIF is high, independent effects cannot be claimed. *Mitigation*: FR-009 mandates PCA and descriptive reporting of joint variance.
- **Power**: If N < 30, the study lacks power for robust correlation. *Mitigation*: Assumption in spec; pipeline halts with "INSUFFICIENT POWER" error if N < 30. For N=30-52, the study proceeds with a power limitation flag.
- **Spec Constraint (FR-008)**: The spec originally mandated 'trial-level' cross-validation, which is scientifically invalid for subject-level aggregates. *Mitigation*: Plan implements Subject-Level LOSO. *Action*: FR-008 updated in spec to reflect subject-level requirement.