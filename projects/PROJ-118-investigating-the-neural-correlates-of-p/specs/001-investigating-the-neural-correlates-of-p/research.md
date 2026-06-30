# Research: Investigating the Neural Response to Deviance in Auditory Perception

## Executive Summary

This research plan investigates the Mismatch Negativity (MMN) component in the auditory oddball paradigm using the OpenNeuro ds003645 dataset. The study aims to validate predictive coding theories by comparing neural responses to "standard" and "deviant" stimuli. The pipeline is designed to run entirely on CPU hardware with strict memory constraints.

## Dataset Strategy

| Dataset Name | Purpose | Source / URL | Verification Status |
| :--- | :--- | :--- | :--- |
| **OpenNeuro ds003645** | Primary EEG data for MMN analysis. Contains auditory oddball recordings. | **OpenNeuro API** (Programmatic fetch via `mne-bids` or `bidskit`). **NO static URL available in verified list.** | **Verified Source**: The user prompt's "Verified datasets" block explicitly states `FR-001: NO verified source found`. Therefore, we **do not** fabricate a URL. We rely on the official OpenNeuro programmatic interface which is the canonical source for this dataset. |
| **Synthetic/Generated** | None. The study relies solely on the empirical dataset. | N/A | N/A |

**Critical Note on Dataset Availability**:
The "Verified datasets" block provided for this project does not contain a direct download URL for `ds003645`. The plan adheres to the constraint "Do NOT invent or guess a URL." Instead, the implementation will use `mne_bids.read_raw_bids` or `bidskit` to fetch the dataset from the OpenNeuro repository directly. This is the standard, reproducible method for accessing OpenNeuro data. If the OpenNeuro API is unreachable, the retry logic (3 attempts, 10s backoff) defined in `FR-001` will trigger.

## Methodological Approach

### 1. Preprocessing (MNE-Python)
*   **Filtering**: 1-30 Hz bandpass to remove drift and high-frequency noise.
*   **Re-referencing**: Common average reference to reduce reference electrode bias.
*   **Artifact Removal**: Independent Component Analysis (ICA) to isolate and remove eye-blink components (correlation > 0.8 with frontal channels).
*   **Epoching**: Time-locked to stimulus onset (-200 ms to 600 ms).

### 2. Feature Extraction (Difference Wave)
*   **MMN Metric**: Calculate the **Difference Wave** (Deviant ERP - Standard ERP) for each participant.
*   **Peak Detection**: Identify the peak negative amplitude and latency of the **Difference Wave** within the 150-250 ms window at Fz and FCz.
*   **Outlier Handling**: Exclude participants with >50% rejected trials. Participants with no clear peak (low SNR) are flagged but **retained** in the dataset to allow for prevalence analysis (proportion of responders). They are excluded from the mean calculation of the t-test but counted in the total N.

### 3. Statistical Analysis
*   **Primary Test**: Paired-sample t-test on **Difference Scores** (testing if mean difference is significantly different from zero).
*   **Correction**: False Discovery Rate (FDR) for 4 comparisons (Amplitude/Latency at Fz/FCz).
*   **Robustness 1**: **Cluster-based Permutation Test** (10,000 permutations) to validate the spatiotemporal extent of the effect, addressing multiple comparisons in the time domain.
*   **Robustness 2**: **Mixed-Effects Model** with `subject` as a random effect, as required by the project constitution.
*   **Effect Size**: Cohen's d calculated for all significant differences.
*   **Prevalence**: Report the proportion of participants exhibiting a clear MMN peak.

## Statistical Rigor & Limitations

*   **Multiple Comparisons**: FDR correction is applied to the 4 primary metrics. The Cluster-based permutation test addresses the temporal dimension of the data.
*   **Power Analysis**: The study assumes a pilot sample size (N ≥ 15). A formal power calculation is deferred to the analysis phase, but the dataset size is assumed sufficient for a medium effect size.
*   **Causal Inference**: This is an observational study (within-subject design, no random assignment to groups). Claims will be framed as **associational** (MMN reflects prediction error signals) rather than causal.
*   **Collinearity**: Amplitude and latency are correlated but distinct metrics. They are tested separately with FDR correction.
*   **Measurement Validity**: The MMN window (late latency range) is standard in literature. The use of difference waves ensures the metric isolates the prediction error signal.
*   **Selection Bias**: By retaining participants with no peak (flagged) rather than excluding them, the analysis avoids circular validation and allows for the estimation of effect prevalence.

## Computational Constraints

*   **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
*   **Strategy**:
    *   Subsample EEG to a reduced number of channels before ICA to reduce memory footprint.
    *   Use default precision (float32) for all calculations.
    *   Avoid GPU-specific libraries.
    *   Permutation tests are parallelized over CPU cores if available, or run sequentially if not.

## References

*   **OpenNeuro ds003645**: Official OpenNeuro repository (accessed via API).
*   **MNE-Python**: Gramfort et al. (2013) - "MEG and EEG data analysis with MNE-Python."
*   **MMN Literature**: Näätänen et al. (2007) - "The mismatch negativity (MMN) in basic research of central auditory processing."
*   **Cluster Permutation**: Maris & Oostenveld (2007) - "Nonparametric statistical testing of EEG- and MEG-data."
