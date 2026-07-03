# Research: Predicting Cognitive Fatigue from Resting-State EEG Complexity

## Executive Summary

This research plan investigates the association between resting-state EEG complexity and subjective cognitive fatigue. The primary hypothesis is that increased cognitive fatigue correlates with changes in EEG signal complexity, specifically measured by Lempel-Ziv Complexity (LZC) and Permutation Entropy (PE). The analysis will be conducted on a public dataset containing paired resting-state EEG and fatigue ratings, adhering to strict computational constraints (CPU-only, ≤7 GB RAM).

**Critical Design Note**: The analysis strategy is conditional. The pipeline first validates the data structure. If paired pre/post resting-state segments exist, an ANCOVA model is used to avoid collinearity. If only single-timepoint data exists, the analysis pivots to a cross-sectional design.

## Dataset Strategy

### Verified Datasets

The following datasets have been verified for availability and format. The plan relies **only** on these sources.

| Dataset Name | Source URL | Format | Relevance to Study |
|:--- |:--- |:--- |:--- |
| **PhysioNet Preprocessed** | ` | Parquet | **Validation Required**: Must confirm raw voltage time-series (not pre-filtered features) and presence of fatigue labels. |
| **PhysioNet Sleep** | ` | ZIP | Contains sleep EEG; may contain resting-state segments but fatigue labels may be absent. |
| **CIRCOR Digiscope** | ` | Parquet | **Validation Required**: Must confirm raw voltage time-series and presence of fatigue labels. |
| **PVT Dataset** | ` | ZIP | Contains PVT (fatigue proxy) data; requires verification of paired resting-state EEG. |
| **PVT Historical Signal** | ` | Parquet | Contains PVT data; requires verification of paired resting-state EEG. |

*Note: Datasets containing only metadata (e.g., CSVs of events) without raw signal (.edf/.bdf/.fif) are excluded from primary consideration for this specific pipeline.*

### Dataset Selection & Validation Plan

**Step 1: Data Structure & Format Validation**
The `code/download.py` script will attempt to load the first candidate dataset. It will inspect the schema and file types to confirm the presence of:
1. **Raw EEG Time Series**: Data in a format suitable for MNE-Python (e.g., EDF, BDF, FIF, or raw voltage arrays in Parquet).
2. **Segment Metadata**: Indication of resting-state segments.
3. **Fatigue Scores**: Subjective ratings (e.g., NASA-TLX, Borg Scale) or PVT-derived metrics.
4. **Participant ID**: To link measures.
5. **Longitudinal Check**: Verification of whether **two distinct resting-state epochs** (pre-task and post-task) exist for the same participants.

**Step 2: Data Integrity Checks**
- **Raw Signal Check**: If the dataset is a Parquet file, the script will verify it contains raw voltage columns (e.g., `Fp1`, `Fz`) rather than pre-computed features. If only features are present, the dataset is skipped.
- **Single vs. Longitudinal**: The script will count the number of resting-state epochs per participant.
 - If **≥2** epochs exist (pre/post), the plan proceeds with **ANCOVA** (Post ~ Pre + Fatigue).
 - If **1** epoch exists, the plan pivots to **Cross-Sectional** analysis (Baseline Complexity vs. Baseline Fatigue).
 - If **0** resting-state epochs exist, the dataset is rejected.

**Step 3: Fallback Strategy**
If the primary candidate lacks required variables (raw signal OR fatigue scores), the system will **halt** with a clear error message listing available variables. **No cross-dataset merging** (e.g., merging EEG from one dataset with Fatigue from another) will be attempted, as participant IDs are rarely consistent across public repositories.

**Step 4: Sample Size Verification**
The script will count participants with complete data (EEG + Fatigue). If N < 30, the system will log a warning regarding power limitations (SC-001) but proceed if the spec allows (or halt if strict).

**Dataset Mismatch Warning**:
*Critical Note*: If the selected dataset contains only **trait** measures (e.g., personality) or **task-based** EEG without paired **subjective fatigue ratings**, the analysis cannot proceed as specified. The plan explicitly **does not** assume the presence of fatigue scores. The `download.py` script will enforce this check.

## Methodology

### 1. Preprocessing (FR-002)
- **Tool**: MNE-Python.
- **Filtering**: Bandpass filter in the low-frequency to high-frequency range to remove slow drifts and high-frequency noise.
- **Line Noise**: Notch filter at 50 Hz (or 60 Hz depending on dataset metadata) to attenuate line noise (US-1).
- **Artifact Rejection**: Channels/epochs with amplitude > ±100 µV will be rejected (US-1, FR-002).
- **Re-referencing**: Average reference.
- **Segmentation**: Extract resting-state segments ≥ 120s.

### 2. Complexity Feature Extraction (FR-003)
- **Metrics**:
 - **Lempel-Ziv Complexity (LZC)**: Measures the rate of new patterns in the signal.
 - **Permutation Entropy (PE)**: Measures the complexity of the ordinal patterns in the signal.
- **Implementation**:
 - **SSoT**: The `lempel-ziv-complexity` Python library will be the primary implementation for LZC. A custom implementation is used only as a fallback if the library fails.
 - **PE**: Implemented via `pyentropy` or custom implementation.
- **Validation**: Test on synthetic signals (e.g., sine wave, white noise) to ensure values fall within expected ranges (US-2).

### 3. Statistical Analysis (FR-004, FR-005, FR-006)

**Conditional Logic**:
- **Scenario A (Longitudinal Data Available)**:
 - **Model**: ANCOVA (Analysis of Covariance).
 - **Equation**: `Post_Complexity ~ Pre_Complexity + Fatigue_Delta`.
 - **Rationale**: This avoids the collinearity trap of correlating `Delta_Complexity` with `Delta_Fatigue` while controlling for `Pre_Complexity`. It models the post-task state directly, adjusting for baseline.
 - **Confounds**: If metadata (age, medication, etc.) is available, they are added as covariates. If not, the model proceeds with a note on unmeasured confounding.
- **Scenario B (Single-Timepoint Data Only)**:
 - **Model**: Simple Correlation (Pearson/Spearman).
 - **Equation**: `Baseline_Complexity ~ Baseline_Fatigue`.
 - **Rationale**: If no pre/post design exists, we test the association between baseline complexity and baseline fatigue.

**Multiple Comparison Correction (FR-005)**:
- Apply **Benjamini-Hochberg (BH)** correction to p-values across all tested electrodes to control False Discovery Rate (FDR).

**Sensitivity Analysis (FR-006)**:
- Report the count of significant electrodes at p ≤ 0.05 and p ≤ 0.01.
- This addresses the small sample size (N=30) robustness.

**Power & Sensitivity (N=30)**:
- Given N=30, the study is likely underpowered for small effect sizes (r=0.3).
- **Action**: The analysis will prioritize reporting **effect sizes with 95% Confidence Intervals** over binary p-value significance. Results will be framed as "preliminary associations" rather than definitive causal claims.

### 4. Collinearity Diagnostics (SC-004)
- If multiple metrics are combined, calculate Variance Inflation Factor (VIF). If VIF ≥ 5, report collinearity and avoid claiming independent effects.

### 5. Reproducibility & Constraints
- **Seeds**: All random operations (e.g., shuffling, initialization) will use `np.random.seed(42)`.
- **Compute**: All operations must run on CPU. No GPU libraries.
- **Memory**: Data will be processed in chunks if necessary to stay under available memory limits.

## Decision Rationale

- **Why ANCOVA?**: To avoid the statistical redundancy of correlating change scores while controlling for baseline. ANCOVA provides a more robust estimate of the fatigue effect on post-task complexity.
- **Why Conditional Design?**: Public datasets rarely offer perfect pre/post resting-state pairs. The plan must adapt to the data available (cross-sectional vs. longitudinal) to avoid a "halt" condition.
- **Why LZC and PE?**: These are standard non-linear metrics for EEG complexity, sensitive to state changes like fatigue. They are computationally tractable on CPU.
- **Why BH Correction?**: With multiple electrodes (e.g., -64 channels), the risk of false positives is high. BH is less conservative than Bonferroni and appropriate for exploratory neuroscience.
- **Why CPU-Only?**: The deployment constraint (DC-001) mandates execution on GitHub Actions free tier. GPU dependencies would break the pipeline.

## Limitations & Risks

- **Dataset Availability**: The primary risk is the absence of paired EEG and fatigue data in the verified datasets. If no dataset meets FR-001, the project cannot proceed.
- **Sample Size**: N=30 provides limited power for detecting small effect sizes (r=0.3). Results should be interpreted as preliminary.
- **Confounding**: Unmeasured confounders (e.g., sleep quality, caffeine intake) may bias results. The analysis is observational.
- **Signal Quality**: Artifacts (muscle movement, eye blinks) may not be fully removed by amplitude thresholding, potentially affecting complexity metrics.
- **Data Structure**: If the dataset lacks a longitudinal design, the primary hypothesis (change in complexity) cannot be tested directly; the analysis will shift to cross-sectional associations.