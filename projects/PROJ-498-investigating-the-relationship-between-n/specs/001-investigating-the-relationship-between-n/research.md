# Research: Investigating the Relationship Between Neural Synchrony and Attention Switching Costs

## 1. Problem Statement & Hypothesis

**Hypothesis**: Higher pre-stimulus frontoparietal neural synchrony (specifically in theta and gamma bands) predicts lower attention switching costs (faster switching).
**Nature of Claim**: Associational (observational data; no causal manipulation).
**Key Challenge**: The spec requires a task-switching dataset. The "Verified datasets" block does not contain a specific URL for a task-switching dataset. The plan addresses this by implementing a dynamic search via the OpenNeuro API to find ANY dataset containing 'task-switching' events. If no such dataset is found, the project transitions to a 'Data Gap' state with a formal report, ensuring the methodology is sound even if the data is unavailable.

## 2. Dataset Strategy

### 2.1 Verified Datasets Review
Per the project constraints, we must cite ONLY the following verified sources:
- **OpenNeuro (parquet)**: ` (General fMRI/EEG proxy, likely not task-switching specific).
- **EEG (csv/parquet)**: `neurofusion/eeg-restingstate`, `JLB-JLB/seizure_eeg_train/eval`.

**Critical Gap**: None of the verified datasets explicitly contain "task-switching" trials with "switch" vs "stay" labels and associated Reaction Times (RT). Using a resting-state or seizure dataset would violate the core requirement of measuring "switching costs."

**Decision**:
1. **Primary Path**: The implementation will query the OpenNeuro API for ANY dataset containing 'task-switching' or 'switch/stay' event labels.
 - **If Found**: Proceed with the analysis using the first valid dataset (e.g., ds004173 or alternative).
 - **If Not Found**: Generate `data_gap_report.json` (a valid research artifact), log the error, and halt with status `data_gap_unverifiable`. This is a valid research outcome (data unavailability) and does not constitute a methodological failure.
2. **Fallback Path**: **None**. The plan explicitly rejects using resting-state or seizure data as a proxy, as it is a fundamental modality mismatch.
3. **Action**: The `code/download.py` script will be written to perform this dynamic search and strictly validate the schema.

*Note: The "Verified datasets" block is interpreted as a whitelist for *data files* that can be cited. Since no task-switching dataset is in the list, the project relies on the `openneuro` API to fetch it. If the API search fails, the project halts with a formal report.*

### 2.2 Data Requirements
- **Task**: Cognitive Task Switching (Switch vs. Stay trials).
- **Modalities**: EEG (10-20 montage), Behavioral Logs (RT, Accuracy).
- **Variables Needed**:
 - `stimulus_type`: Switch / Stay.
 - `reaction_time`: Milliseconds.
 - `eeg_data`: Time-locked epochs.
 - `electrodes`: F3, F4, FC3, FC4, P3, P4, CP3, CP4.

## 3. Methodological Approach

### 3.1 Preprocessing (FR-002)
- **Filtering**: Bandpass 1–45 Hz (Butterworth, 4th order).
- **Artifact Removal**: ICA. Components rejected if:
 - Kurtosis > 5.
 - Spectral peak > 30 Hz (muscle artifact).
- **Epoching**: -1000ms to +2000ms relative to stimulus onset.
- **Memory Management**: Process one subject at a time. Discard raw data after epoching to stay under a manageable RAM footprint.
- **Exclusion**: Subjects with <10 trials/condition or >50% artifact removal are excluded and logged.

### 3.2 Synchrony Metrics (FR-003)
- **Metric**: Weighted Phase-Lag Index (wPLI) to minimize volume conduction effects.
- **Bands**: Theta (4–7 Hz), Gamma (30–45 Hz).
- **Window**: Pre-stimulus -500ms to 0ms.
- **Electrode Pairs**:
 - Frontal: F3/F4, FC3/FC4 (Proxy for DLPFC).
 - Parietal: P3/P4, CP3/CP4 (Proxy for Parietal).
 - Cross-region pairs: Frontal ↔ Parietal.
- **Scalp-level Proxy**: Acknowledged limitation; no individual MRI for source localization. wPLI is used to mitigate volume conduction, but scalp-level phase synchrony may still be confounded by common reference effects. This is discussed in the Limitations section.

### 3.3 Statistical Analysis (FR-005, FR-009)
- **Primary Analysis**: Pearson/Spearman correlation between mean synchrony and mean switching cost (RT_switch - RT_stay) per subject.
- **Significance**: 1000 permutations (shuffle the entire (Synchrony, Cost) vector for each subject to preserve joint distribution).
- **Correction**: Bonferroni correction for 2 bands (theta, gamma).
- **Secondary Analysis (FR-009)**: **Linear Mixed-Effects (LME) Model** on trial-level data.
 - **Input**: `per_trial_synchrony.csv` (trial-level synchrony linked to trial-level RT).
 - **Model**: `RT ~ Synchrony + (1|Subject)`.
 - **Output**: `trial_level_analysis.json`.
- **Sensitivity**: Repeat primary analysis with windows [-600, 0] and [-400, 0].
- **Power Analysis**: Acknowledged limitation; small N (approx 10-20 subjects) may limit power. The study is exploratory. A non-significant result does not invalidate the methodology, but a significant result must be interpreted with caution.

## 4. Statistical Rigor & Assumptions

- **Multiple Comparisons**: Bonferroni applied for 2 bands.
- **Power**: Acknowledged limitation; small N (approx 10-20 subjects) may limit power.
- **Causality**: Explicitly framed as associational. No randomization of neural state.
- **Collinearity**: Theta and gamma may be correlated; primary analysis treats them separately.
- **Measurement Validity**: wPLI is standard for EEG synchrony; scalp electrodes are accepted proxies for DLPFC/Parietal coupling in the absence of fMRI/MRI, but with acknowledged limitations.
- **Permutation Strategy**: The entire (Synchrony, Cost) vector is shuffled per subject to preserve the joint distribution structure.

## 5. Feasibility & Constraints

- **Runtime**: Sequential processing ensures < 6h total.
- **RAM**: A storage limit is respected by discarding raw data post-epoching.
- **CPU**: All operations (filtering, ICA, wPLI) are CPU-tractable.
- **Dataset Risk**: High. If no verified task-switching dataset is found (or if the search fails), the project halts with a "Data Gap Report". This is the correct behavior under the "Verified Accuracy" constitution.

## 6. Limitations

- **Scalp-Level Proxy**: The use of scalp-level electrodes (F3, P3, etc.) as proxies for DLPFC/Parietal coupling is a limitation. wPLI mitigates volume conduction, but common reference effects and non-neural artifacts (e.g., eye blinks, muscle) may still confound the measure. The biological interpretation of "frontoparietal synchrony" is thus limited to scalp-level coupling.
- **Low Power**: The small sample size (N=10-20) limits the power to detect small effect sizes. The study is exploratory.
- **Dataset Availability**: The project relies on the availability of a task-switching dataset in the OpenNeuro repository. If none is found, the project produces a "Data Gap Report" rather than proceeding with invalid data.