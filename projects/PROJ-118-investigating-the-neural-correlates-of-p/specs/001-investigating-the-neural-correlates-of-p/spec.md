# Feature Specification: Investigating the Neural Response to Deviance in Auditory Perception

**Feature Branch**: `001-investigating-predictive-coding-errors`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Neural Correlates of Predictive Coding Errors in Auditory Perception"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preprocess Auditory Oddball EEG Data (Priority: P1)

The research pipeline MUST automatically download the OpenNeuro dataset, subsample the EEG channels to a standard montage (Fz, FCz, Cz, Pz, etc.) to fit memory constraints, filter the raw EEG signals (low-frequency range to a moderate upper cutoff), re-reference, and epoch the data into "standard" and "deviant" conditions time-locked to stimulus onset (-200 ms to 600 ms), while removing eye-blink artifacts via ICA.

**Why this priority**: Without clean, correctly labeled epochs, no statistical analysis of MMN components is possible. This is the foundational data preparation step required for all subsequent research.

**Independent Test**: The pipeline can be run in isolation; upon completion, the output directory must contain `.fif` or `.edf` files with epochs labeled "standard" and "deviant", and the number of rejected epochs due to artifacts must be logged (e.g., "Rejected {count} of trials").

**Acceptance Scenarios**:

1. **Given** the OpenNeuro ds003645 dataset is accessible, **When** the preprocessing script runs, **Then** the output contains epoched data with a time window of -200 ms to 600 ms, a frequency filter of 1–30 Hz applied, and data subsampled to a reduced number of channels.
2. **Given** raw EEG data with eye-blink artifacts, **When** ICA is applied and components are rejected (based on correlation with frontal channels > 0.8 or visual inspection of topography), **Then** the resulting epochs show reduced variance (≥10% relative to baseline noise, per Delorme et al., 2007) in frontal channels compared to raw data, and a log confirms the number of removed components.

---

### User Story 2 - Extract MMN Amplitude and Latency Metrics (Priority: P2)

The system MUST calculate the peak MMN amplitude (minimum voltage) and peak latency (time of peak) for each participant within the early post-stimulus window at fronto-central electrodes (Fz, FCz) for both "standard" and "deviant" conditions. If no clear peak is found (defined as peak amplitude ≥ 2.0 µV negative relative to baseline), the system must flag the participant as an outlier.

**Why this priority**: This step translates raw EEG signals into the specific quantitative variables (amplitude and latency) required to test the hypothesis that MMN reflects prediction errors.

**Independent Test**: Running the extraction script on a sample of participants must produce a CSV or JSON file where each row represents a participant, containing columns for "deviant_amplitude", "deviant_latency", "standard_amplitude", and "standard_latency".

**Acceptance Scenarios**:

1. **Given** preprocessed epochs for a single participant, **When** the extraction algorithm runs, **Then** it identifies the most negative voltage peak within the early post-stimulus window at Fz and records its value and time.
2. **Given** a participant with no clear MMN peak in the target window (amplitude < 2.0 µV), **When** the extraction runs, **Then** the system flags this participant as an outlier or records a null value rather than extrapolating a value from outside the window.

---

### User Story 3 - Perform Statistical Comparison and Visualization (Priority: P3)

The pipeline MUST execute paired-sample t-tests (or Wilcoxon signed-rank tests if normality is violated) comparing deviant vs. standard amplitudes and latencies, apply False Discovery Rate (FDR) correction for the comparisons across multiple electrodes and metrics, and generate grand-average ERP plots with confidence intervals and topographic maps. Additionally, the system MUST perform a non-parametric permutation test with a sufficient number of permutations to verify the robustness of the MMN effect against the null hypothesis.

**Why this priority**: This step provides the inferential evidence (p-values, effect sizes) and visual proof required to answer the research question and validate the predictive coding hypothesis.

**Independent Test**: The script must generate a final report containing a p-value, a Cohen's d value, and PNG images of the ERP waveforms and topographic maps.

**Acceptance Scenarios**:

1. **Given** a dataset of extracted MMN metrics from ≥10 participants, **When** the statistical test runs, **Then** it outputs a p-value corrected for multiple comparisons and a Cohen's d effect size for the amplitude difference.
2. **Given** the statistical results, **When** the visualization module runs, **Then** it produces a figure showing the grand-average ERP with shaded 95% confidence intervals and a topographic map highlighting the Fz/FCz region.

---

### Edge Cases

- What happens if the OpenNeuro dataset download fails or is incomplete? The system MUST retry up to 3 times with a 10-second backoff before failing the job.
- How does the system handle participants with excessive artifact contamination (>50% rejected trials)? The system MUST exclude these participants from the final statistical analysis and log their IDs.
- What happens if the MMN peak is not found within the 150–250 ms window? The system MUST flag the data point as missing rather than forcing a value, to avoid false positives.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST download and extract the OpenNeuro ds003645 dataset using `wget` or `curl`, ensuring the processing pipeline handles data efficiently (See US-1).
- **FR-001b**: The system MUST subsample the EEG data from a high-density channel configuration to a standard 32-channel montage (including Fz, FCz, Cz, Pz) prior to ICA decomposition to ensure the memory footprint fits within the available RAM limit (See US-1).
- **FR-002**: The system MUST apply a bandpass filter of 1–30 Hz and re-reference the EEG data to a common average before epoching (See US-1).
- **FR-003**: The system MUST automatically detect and reject eye-blink artifacts using Independent Component Analysis (ICA), removing components that correlate with frontal channels (correlation > 0.8) or exhibit frontal topography (See US-1).
- **FR-004**: The system MUST calculate the peak negative amplitude and corresponding latency within the 150–250 ms window for each participant at Fz and FCz electrodes (See US-2).
- **FR-005**: The system MUST perform a paired-sample t-test (or Wilcoxon signed-rank test) between deviant and standard conditions, applying False Discovery Rate (FDR) correction for the multiple comparisons (Amplitude Fz, Amplitude FCz, Latency Fz, Latency FCz) (See US-3).
- **FR-006**: The system MUST perform a non-parametric permutation test to verify the robustness of the MMN effect against the null hypothesis, as a substitute for linear scaling analysis (See US-3).
- **FR-007**: The system MUST output grand-average ERP plots with 95% confidence intervals and topographic maps of the MMN difference (deviant minus standard) (See US-3).

### Key Entities

- **EEG Epoch**: A time-locked segment of EEG data (−200 ms to 600 ms) labeled as either "standard" or "deviant".
- **MMN Metric**: A derived value containing the peak amplitude (µV) and latency (ms) of the Mismatch Negativity component.
- **Statistical Result**: A record containing the p-value, effect size (Cohen's d), and confidence intervals for the comparison between conditions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The percentage of epochs rejected due to artifacts is measured against the threshold of <50% per participant; participants exceeding this are excluded (See US-1).
- **SC-002**: The statistical significance of the MMN amplitude difference is measured against the corrected p-value threshold of <0.05 (See US-3).
- **SC-003**: The effect size of the prediction-error signal is measured by calculating Cohen's d for the amplitude difference between deviant and standard conditions (See US-3).
- **SC-004**: The computational feasibility is measured by ensuring the total analysis time on a GitHub Actions free-tier runner (limited CPU, 7 GB RAM) is ≤6 hours (See US-1, US-2, US-3).
- **SC-005**: The validity of the MMN window is measured by confirming the peak latency falls within the 150–250 ms range for ≥80% of valid participants, OR within a secondary search window of 100–300 ms if no peak is found in the primary window (See US-2).

## Assumptions

- The OpenNeuro ds003645 dataset contains the necessary metadata to distinguish "standard" and "deviant" trials with sufficient probability contrast to elicit MMN.
- The GitHub Actions free-tier runner provides sufficient disk space to store the raw and processed EEG data without needing external storage.
- The MNE-Python library version or later is compatible with the CI environment and supports all required preprocessing steps (ICA, filtering, epoching) on CPU-only hardware.
- The study design is observational (no random assignment of participants to conditions within the same session), so all findings regarding MMN and prediction error will be framed as associational, not causal.
- The dataset includes a sufficient number of participants (N ≥ 15) to achieve statistical power for a paired t-test with a medium effect size, as the power calculation is deferred to the analysis phase but the dataset size is assumed adequate for a pilot.
- No GPU acceleration is available or required; all signal processing and statistical tests are CPU-tractable.
- Subsampling to a reduced channel count retains sufficient spatial resolution to detect the fronto-central MMN component, as per standard EEG literature.