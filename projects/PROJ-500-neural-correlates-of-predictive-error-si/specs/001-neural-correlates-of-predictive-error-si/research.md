# Research: Neural Correlates of Predictive Error Signals During Tactile Discrimination Learning

## Overview

This research document details the dataset strategy, methodological rationale, and computational constraints for the feature. It addresses the core question: *Does the amplitude of somatosensory MMN attenuate as behavioral accuracy improves during tactile texture discrimination learning?*

## Dataset Strategy

The project relies on EEG datasets from OpenNeuro and HuggingFace that contain tactile/somatosensory odd-ball paradigms. The following table lists the **verified** sources available for this project.

| Dataset Name | Source Type | Verified URL | Relevance to Spec | Status |
|:--- |:--- |:--- |:--- |:--- |
| **OpenNeuro Tactile Oddball (Verified)** | OpenNeuro (via HF mirror) | *See # Verified datasets block* | Contains EEG data with tactile/somatosensory stimuli AND behavioral logs. | **Verified** (If matches criteria) |
| **EEG Resting State** | HuggingFace | ` | Contains events metadata; lacks standard/deviant contrast and behavioral logs. | **Verified but Inapplicable** |
| **Seizure EEG (Train/Eval)** | HuggingFace | ` | Contains EEG but lacks controlled odd-ball paradigm and behavioral accuracy logs. | **Verified but Inapplicable** |
| **MNE-Python Reference** | Library | NO verified source found | Used for preprocessing (filtering, ICA). | **N/A** (Library) |

**Critical Note on Dataset-Variable Fit (SC-004):**
- The spec requires **tactile/somatosensory** odd-ball tasks with **behavioral response logs** (accuracy).
- **Strict Filter**: The ingestion script MUST verify that the dataset metadata explicitly contains `stimulus_type` (standard/deviant) AND `response_correctness` (trial-level accuracy).
- **If Missing**: The dataset is flagged as "Inapplicable for Primary Hypothesis". The pipeline **MUST NOT** proceed with the primary analysis.
- **Fallback**: If `response_correctness` is missing but `stimulus_type` exists, the system falls back to "Stimulus-Driven MMN" (FR-011), but this is a **secondary analysis** with a different hypothesis (probability vs. error). The final report MUST explicitly flag this mode.
- **No Verified Match**: If no dataset in the `# Verified datasets` block meets the criteria, the primary hypothesis is **untestable** with current resources. The project will document this limitation and halt primary analysis.

**Primary Strategy**:
1. Check `# Verified datasets` block for a tactile odd-ball dataset with behavioral logs.
2. If found, load and validate metadata.
3. If not found, log "Primary Hypothesis Untestable" and exit or switch to secondary analysis only if `stimulus_type` exists.

## Methodological Rationale

### 1. Preprocessing (FR-002, FR-003)
- **Filter**: 1–40 Hz bandpass. This range isolates the MMN component (typically within the early to mid-latency range) while removing slow drifts and high-frequency muscle noise.
- **ICA**: Independent Component Analysis is the standard for removing ocular and muscular artifacts in EEG. It is computationally feasible on CPU for typical EEG sizes (≤7 GB RAM) if applied to downsampled or chunked data.
- **Epoching**: -200ms to 500ms relative to stimulus. This captures the pre-stimulus baseline and the post-stimulus MMN window.
- **Rationale**: These steps are mandated by the Constitution (Principle VI) and standard EEG literature. Deviations require explicit justification.

### 2. MMN Calculation & Lagged Alignment (FR-004, Methodological Correction)
- **Lagged Strategy**: To address low SNR in small blocks and avoid circularity (methodology-9c756cf6), we implement a **Lagged Alignment**:
 - **MMN Predictor**: Calculated over a **50-trial window** (trials `t-50` to `t-10`). This ensures sufficient averaging for a stable MMN estimate.
 - **Accuracy Outcome**: Calculated over the **subsequent 10-trial block** (trials `t` to `t+10`).
 - **Independence**: This ensures the noise in the MMN estimate (from block `t-1`) is independent of the noise in the Accuracy estimate (from block `t`), eliminating shared measurement error.
- **Window**: 150–250ms. This is the canonical window for somatosensory MMN.
- **Electrodes**: CP, CP4, C3, C4. These are central/parietal sites where somatosensory activity is maximal.
- **Metric**: Mean amplitude of the difference wave (Deviant - Standard).
- **Rationale**: Directly addresses the spec's hypothesis while ensuring statistical validity.

### 3. Behavioral Alignment (FR-005)
- **Binning**: -trial blocks for accuracy.
- **Stationarity Check**: Accuracy trend <10% within a block. Ensures that accuracy is stable during the block.
- **Rationale**: Aligns neural error signals with the behavioral state of the subject.

### 4. Statistical Modeling (FR-006, Methodological Correction)
- **Model**: **Gaussian Linear Mixed-Effects Model (LME)**.
 - **Outcome**: `MMN_Amplitude` (continuous, Gaussian).
 - **Predictors**: `Accuracy` (proportion, continuous), `Learning_Phase`, and their interaction.
 - **Random Effects**: `(1|Subject)` to account for inter-subject variability.
 - **Correction**: Bonferroni or FDR for multiple electrodes.
 - **Validation**: Permutation test (n=1000) to generate a null distribution.
- **Why Gaussian?**: MMN amplitude is a continuous voltage difference, not a bounded proportion. Beta regression (as suggested in spec FR-006) is inappropriate for continuous outcomes and would fail at boundaries ([deferred] or [deferred] accuracy are predictors, not outcomes here). *Note: This corrects the spec's FR-006 and US-3 which incorrectly specified Beta GLMM.*
- **Causal Framing**: The study is observational (no random assignment). Claims will be framed as **associational**, not causal.
- **Rationale**: Addresses the spec's statistical rigor requirements (multiple comparisons, power, causal assumptions) with the correct statistical distribution.

### 5. Robustness & Sensitivity (FR-010)
- **Time Window Sweep**: 140–240ms, 160–260ms.
- **Rationale**: Ensures results are not an artifact of the specific 150–250ms boundary.

## Computational Feasibility

- **Hardware**: multi-core CPU, 7 GB RAM, 14 GB disk.
- **Strategy**:
 - **Streaming**: Raw data is downloaded and processed in chunks. Never held in memory entirely.
 - **Downsampling**: If necessary, EEG data is downsampled (e.g., to a reduced sampling rate) to reduce memory footprint without losing MMN fidelity.
 - **Library Choice**: `mne` (CPU optimized), `statsmodels` (LME), `scikit-learn` (ICA). No GPU-dependent libraries.
 - **Runtime**: Estimated ≤ 6 hours for 20 subjects. If a dataset is too large, it is sub-sampled (e.g., a subset of subjects) for the initial run, with a note on power.

## Limitations & Edge Cases

- **Missing Metadata**: If `stimulus_type` or `response_correctness` is missing, the dataset is skipped (log warning) or flagged as "Inapplicable".
- **Zero Accuracy**: Subjects with [deferred] accuracy in all blocks are excluded from LME to avoid singularity.
- **Artifact Rejection**: If >50% of trials are rejected in a block, the MMN amplitude is marked NaN.
- **Underpowered Datasets**: Datasets with <20 subjects are included but flagged. Primary hypothesis tests are restricted to ≥20 subjects if available.
- **Spec Kickback**: The spec (FR-006, US-3) mandates a Beta GLMM. This plan implements a Gaussian LME because MMN is continuous. This is a documented deviation for statistical soundness; the spec must be updated to reflect the correct model.

## Decision Log

| Decision | Rationale | Alternative Rejected |
|:--- |:--- |:--- |
| **Gaussian LME** | Outcome (MMN) is continuous. Beta regression is for bounded proportions (accuracy as outcome). | Beta GLMM (statistically invalid for continuous MMN). |
| **Lagged Alignment** | Ensures SNR for MMN (50 trials) and eliminates circularity with accuracy (10 trials). | Same-block alignment (low SNR, circular error). |
| **Permutation Test** | Non-parametric validation of LME p-values; robust to small sample sizes. | Bootstrap (less standard for mixed models in this context). |
| **CPU-Only** | Constraint of GitHub Actions free tier; feasible with MNE/Statsmodels. | GPU/8-bit quantization (not supported in free tier, unnecessary for EEG). |