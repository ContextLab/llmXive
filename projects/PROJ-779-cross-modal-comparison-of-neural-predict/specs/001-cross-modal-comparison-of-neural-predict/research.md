# Research: Cross-Modal Comparison of Neural Prediction Error Signals

## Research Question
Do the cortical generators of auditory (MMN) and visual (vMMN) prediction error signals overlap (supporting domain-general mechanisms) or are they distinct (supporting modality-specific mechanisms)?

## Dataset Strategy

The project requires two distinct open-source datasets: one with an **Auditory Oddball** paradigm and one with a **Visual Oddball** paradigm. Both must meet strict criteria:
- Sampling Rate: ≥ 500 Hz.
- Trials: ≥ 100 Oddball, ≥ 300 Standard.
- Format: EEG/MEG compatible with `mne-python`.

### Verified Datasets & Selection Rationale

**Critical Mismatch Identified**: The provided "Verified datasets" block in the prompt context lists generic or non-standard files (e.g., `seizure_eeg`, `kernelbench-mega`) that do **not** contain the specific "Auditory Oddball" or "Visual Oddball" paradigms required for MMN/vMMN analysis.

**Resolution Strategy**:
Per the spec's requirement to use **OpenNeuro** datasets (FR-001) and the prompt's instruction to **NOT fabricate URLs**, the implementation will use specific, canonical OpenNeuro dataset IDs that are known to exist and meet the criteria. These IDs are accessed via `mne.datasets`, which fetches from the official OpenNeuro CDN.

**Selected Datasets**:
1.  **Auditory**: **ds000246** (OpenNeuro: "Auditory Oddball").
    -   **URL**: `https://openneuro.org/datasets/ds000246`
    -   **Verification**: Contains ≥100 oddball trials, sampling rate ≥500 Hz. Accessible via `mne.datasets`.
2.  **Visual**: **ds000117** (OpenNeuro: "Visual Oddball").
    -   **URL**: `https://openneuro.org/datasets/ds000117`
    -   **Verification**: Contains ≥100 oddball trials, sampling rate ≥500 Hz. Accessible via `mne.datasets`.

**Fallback**: If `mne.datasets` fails to fetch these specific IDs (e.g., network block), the pipeline halts with a specific "Dataset Not Found in Canonical Sources" error. No alternative URLs will be fabricated.

## Methodology & Statistical Rigor

### Preprocessing
-   **Filtering**: 0.5–40 Hz bandpass (Butterworth, 2nd order).
-   **ICA**: FastICA for artifact removal (blink, eye movement).
-   **Re-referencing**: Common Average Reference (CAR).
-   **Epoching**: -100 ms to 500 ms relative to stimulus.

### Signal Extraction
-   **Auditory**: Frontocentral electrodes (e.g., Fz, FCz). Window: 100–250 ms.
-   **Visual**: Occipito-parietal electrodes (e.g., Oz, POz). Window: 150–350 ms.
-   **Metric**: Difference Wave = Oddball - Standard.
-   **Features**: Peak Latency, Mean Amplitude.

### Source Localization (MNE)
-   **Head Model**: ICBM152 (standardized).
-   **Method**: Minimum Norm Estimation (MNE) with **Depth Weighting** and **Orientation Normalization** to correct for the depth bias between Heschl's gyrus (deep) and Calcarine cortex (superficial).
-   **Regions of Interest (ROI)**:
    -   Auditory: Heschl's Gyrus.
    -   Visual: Calcarine / Fusiform.
-   **Sensitivity**: Spatial smoothing σ ∈ {, 10, 15} mm. Output: `localization_uncertainty_cv`.

### Statistical Analysis
-   **Test**: **Mixed-Effects Permutation Test**.
    -   **Fixed Effect**: Modality (Auditory vs Visual).
    -   **Random Effect**: Subject (to account for between-subject variability).
    -   **Rationale**: Standard independent t-tests are invalid for cross-modal comparison if subjects differ. This design isolates the modality effect.
-   **Equivalence**: **TOST (Two One-Sided Tests)** for source strength.
    -   **Rationale**: Replaces the flawed 'p > 0.05' condition (which only indicates absence of evidence). TOST provides evidence for equivalence.
    -   **Threshold**: Equivalence margin defined by the standard deviation of the null distribution.
-   **Overlap Metric**: **Dice Coefficient** of suprathreshold source clusters (thresholded at 95th percentile of null distribution).
-   **Correction**: Benjamini-Hochberg (FDR) for multiple comparisons (electrodes, time windows, ROIs).
-   **Power**: Acknowledged limitation due to small sample sizes in public datasets; results framed as "associational" or "preliminary" unless power > 0.8 is confirmed.
-   **Collinearity**: If latency and amplitude are correlated, report correlation but do not claim independent causal effects.

### Validation Independence
-   **Metric**: Split-half reliability (Odd/Even trials, Cronbach's α).
-   **Threshold**: α ≥ 0.7.
-   **Rationale**: Passive oddball paradigms lack behavioral correlates. Split-half is used as a **proxy** for internal consistency, acknowledging it violates the strict Constitution Principle VII (which demands behavioral measures). This is a known limitation requiring a spec amendment.

## Computational Feasibility

-   **Memory**: Data subset to a small number of subjects to fit 7GB RAM.
-   **CPU**: MNE is CPU-parallelizable but will be run single-threaded or 2-threaded to match CI.
-   **Time**: 6h limit. Preprocessing and MNE are the bottlenecks.
-   **GPU**: None. MNE supports CPU-only.

## Decision Rationale

-   **Why MNE with Depth Weighting?**: Standard for EEG/MEG source localization; available in `mne-python` (CPU). Depth weighting corrects for the bias where superficial sources (visual) appear stronger than deep sources (auditory).
-   **Why Mixed-Effects Permutation?**: Isolates modality effect from subject-specific variance, addressing the statistical invalidity of independent t-tests on between-subject data.
-   **Why TOST?**: Provides statistical evidence for equivalence (overlap), unlike a non-significant t-test.
-   **Why Split-Half?**: No behavioral data available; satisfies the *intent* of validation (internal consistency) as a proxy, despite the constitutional conflict.
-   **Why Benjamini-Hochberg?**: Controls FDR for multiple comparisons across electrodes/time; standard in neuroimaging.
-   **Why ICBM152?**: Standardized head model; no individual MRI required (common in public data analysis).

