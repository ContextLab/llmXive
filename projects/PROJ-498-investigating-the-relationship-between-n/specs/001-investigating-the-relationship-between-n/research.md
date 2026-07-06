# Research: Investigating the Relationship Between Neural Synchrony and Attention Switching Costs

## 1. Dataset Strategy

The project relies on OpenNeuro dataset **ds004173** (or equivalent) as the primary source. This dataset contains EEG recordings and behavioral data from a task-switching paradigm.

**Critical Dataset Verification**:
The spec requires a dataset with:
1. **EEG Data**: Raw time-series for frontoparietal electrodes (F3, F4, FC3, FC4, P3, P4, CP3, CP4).
2. **Behavioral Labels**: Trial-by-trial reaction times (RT) and accuracy, distinguishing **switch** vs. **stay** conditions.
3. **Event Markers**: Precise stimulus onset times for epoching.

**Verified Sources & Fit**:
The following sources are verified in the project input. We must map the project requirements to these specific files.

| Requirement | Verified Source URL | Fit Assessment |
|:--- |:--- |:--- |
| **EEG Time-Series** | ` | **Rejected**. This source appears to be fMRI (fsLR space), not raw EEG. |
| **EEG Events** | ` | **Rejected**. This is "restingstate" data. The project requires a "task-switching" paradigm with switch/stay conditions. |
| **EEG (Seizure)** | ` | **Rejected**. Seizure data is not a task-switching paradigm. |
| **LMM Data** | ` | **Rejected**. This is video/multimodal data, not EEG. |

**Gap Analysis & Resolution**:
The provided "Verified datasets" block **does not contain a verified URL** for the specific **OpenNeuro ds004173 task-switching EEG data** required by the spec.
* **Action**: The implementation plan will explicitly attempt to download `ds004173` directly from OpenNeuro (via `mne.datasets.fetch_openneuro_dataset`) as the canonical fallback.
* **Contingency: Null Data**: If the dataset is found but lacks `switch`/`stay` labels:
 1. Check for alternative condition labels (e.g., `Go`, `No-Go`, `Stimulus Type`).
 2. **Decision**: If alternative labels exist but do not map to 'switch/stay' (as per spec), **halt execution** with "Hypothesis Untestable: Missing Condition Labels". No alternative analysis will be substituted.
 3. If no alternative condition labels exist, the pipeline will log a **"Hypothesis Untestable: Missing Condition Labels"** error and halt execution.
* **Decision for Plan**: The plan assumes the use of the `mne` library's built-in OpenNeuro downloader for `ds004173` to ensure the correct task data is retrieved. If this fetch fails or the data lacks the required structure, the pipeline halts with a clear error, satisfying the "Verified Accuracy" gate by failing explicitly rather than proceeding with invalid data.

## 2. Methodology & Statistical Rigor

### Preprocessing (FR-002)
* **Filtering**: 1–45 Hz bandpass (Butterworth or FIR).
* **Artifact Removal**: ICA (Independent Component Analysis) to remove eye blinks and muscle artifacts.
* **Epoching**: -1000ms to +2000ms relative to stimulus onset.
* **Quality Control**: Subjects with >20% artifact trials or <20 switch trials are excluded (Edge Case handling).
* **Batching**: To manage memory, trials are processed in batches within each subject.

### Synchrony Metric (FR-003)
* **Metric 1: Instantaneous Phase Difference (IPD)**.
 * **Window**: -500ms to 0ms (Pre-stimulus).
 * **Bands**: Theta (4–7 Hz), Gamma (30–45 Hz).
 * **Decomposition**: Morlet wavelets (≥7 cycles) to ensure side-lobe attenuation > 20 dB.
 * **Electrodes**: Frontoparietal pairs (F3-P3, F4-P4, FC3-CP3, etc.).
 * **Transformation**: IPD is circular. For linear modeling, we transform: `sin_phase = sin(IPD)`, `cos_phase = cos(IPD)`.
* **Metric 2: weighted Phase-Lag Index (wPLI)**.
 * **Window**: -500ms to 0ms (Pre-stimulus).
 * **Bands**: Theta (4–7 Hz), Gamma (30–45 Hz).
 * **Method**: wPLI over a sliding window of 5 trials (as per spec alternative).
 * **Nature**: wPLI is a linear scalar (0 to 1), no circular transformation needed.

### Statistical Analysis (FR-004, FR-005)
* **Model**: Linear Mixed-Effects Model (LMM).
 * **Response**: Log-transformed Reaction Time (RT).
 * **Fixed Effects**:
 * **For IPD**: `sin_phase`, `cos_phase`, `Condition` (Switch/Stay), `sin_phase:Condition`, `cos_phase:Condition`.
 * **For wPLI**: `wPLI`, `Condition`, `wPLI:Condition`.
 * **Random Effect**: Random intercept for `subject_id`.
 * **Equation (IPD)**: `log(RT) ~ sin_phase + cos_phase + Condition + sin_phase:Condition + cos_phase:Condition + (1 | subject_id)`
 * **Equation (wPLI)**: `log(RT) ~ wPLI + Condition + wPLI:Condition + (1 | subject_id)`
 * **Hypothesis Test**: The interaction term(s) (`sin_phase:Condition`, `cos_phase:Condition`, or `wPLI:Condition`) test if synchrony modulates the *switching cost* (difference between conditions).
 * **Likelihood Ratio Test (LRT)**: To isolate the modulation effect, the LRT compares the **Full Model** (with interactions) against a **Reduced Model** (with main effects and condition but *without* interactions). A significant LRT p-value indicates that synchrony modulates the switching cost.
* **Multiple Comparisons**: Bonferroni or Benjamini-Hochberg (FDR) correction applied across:
 * Frequency bands (Theta, Gamma)
 * Electrode pairs
 * Metric types (IPD, wPLI)
* **Robustness**: A permutation test on the interaction term(s) with a sufficient number of iterations to ensure robust p-value estimation.
* **Power/Collinearity**:
 * **Power**: Acknowledged limitation. Sample size (N subjects) is fixed by the dataset.
 * **Collinearity**: If electrode pairs are spatially close, collinearity is expected. The plan reports this descriptively.
 * **Causality**: Claims are strictly **associational** (observational study).
* **Note on Subject-Level Aggregation**: The plan explicitly **rejects** using subject-level mean correlations as a primary validation method. Aggregating to subject-level means loses the trial-level variance required to detect the hypothesized effect and introduces ecological fallacy risks. The primary analysis remains trial-level with the correct interaction term.

## 3. Compute Feasibility

* **Environment**: GitHub Actions Free Tier (limited CPU, 7 GB RAM).
* **Strategy**:
 * **Batched Processing**: Trials processed in chunks of a manageable size to prevent memory overflow during wavelet decomposition.
 * **No GPU**: All operations use CPU-optimized libraries (`scipy`, `numpy`, `statsmodels`).
 * **Memory Management**: Garbage collection invoked after each subject and batch.
 * **Runtime**: Estimated < 5 hours for ~15 subjects with batched processing (100 trials/batch).

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Dataset Mismatch** | High | Verified URLs are invalid. **Mitigation**: Fetch from OpenNeuro directly. If missing labels, halt with "Hypothesis Untestable". |
| **Memory Overflow** | High | EEG data is large. **Mitigation**: Batched processing (100 trials/batch); delete variables immediately after use. |
| **Non-Convergence** | Medium | LMM may fail to converge. **Mitigation**: Use robust estimators; log warnings; exclude subjects with <20 trials. |
| **Circular Data Error** | High | Using raw phase in LMM. **Mitigation**: Transform to sine/cosine components; use joint significance test (LRT). |
| **Statistical Power** | Medium | Small N may yield null results. **Mitigation**: Report effect sizes and confidence intervals; use permutation test. |