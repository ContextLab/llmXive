# Feature Specification: Predicting Sleep Stage Transitions from Scalp EEG Using Deep Learning

**Feature Branch**: `001-predict-sleep-transitions`  
**Created**: 2026-07-06  
**Status**: Draft  
**Input**: User description: "Predicting Sleep Stage Transitions from Scalp EEG Using Deep Learning"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automated Preprocessing and Transition Window Extraction (Priority: P1)

The system MUST automatically download the Sleep-EDF Expanded Database (SC subset), preprocess single-channel EEG (Fpz-Cz) data by first applying linear interpolation for missing data/artifacts, then applying a bandpass filter (0.5–45 Hz) and notch filter (50/60 Hz), and finally segmenting the data into standard 30-second epochs and specific 60-second "transition windows" centered on annotated stage changes.

**Why this priority**: This is the foundational data pipeline. Without clean, correctly segmented data (especially the transition windows), no feature extraction or model training can occur. It addresses the core "Data Acquisition" and "Preprocessing" steps of the methodology.

**Independent Test**: The pipeline can be tested by running the preprocessing script on a subset of the dataset and verifying that the output contains the correct number of transition windows centered on hypnogram changes, and that the spectral content of the filtered data matches expected physiological ranges (e.g., no 50/60Hz line noise).

**Acceptance Scenarios**:

1. **Given** the raw Sleep-EDF SC subset files are available locally, **When** the preprocessing script is executed, **Then** a 60-second segment is extracted centered exactly on every annotated stage transition point (e.g., N2 to N3).
2. **Given** raw EEG data containing 50/60 Hz line noise, **When** the notch filter is applied, **Then** the power spectral density at 50/60 Hz (measured using a 2-second Hamming window and averaging over the 50 Hz and 60 Hz bins) is reduced by ≥ 90% compared to the unfiltered signal.
3. **Given** a subject with multiple sleep stages, **When** the script segments the data, **Then** exactly 30-second epochs are generated for all non-transition periods, and 60-second windows are generated for transition periods.

---

### User Story 2 - Feature Extraction and Transition Characterization (Priority: P2)

The system MUST compute time-domain (RMS, zero-crossing), frequency-domain (absolute/relative power in delta, theta, alpha, sigma, beta), and non-linear (sample entropy, DFA) features for both standard epochs and transition windows. The system MUST perform statistical hypothesis testing using Cluster-Based Permutation Tests to account for temporal autocorrelation, with False Discovery Rate (FDR) correction (Benjamini-Hochberg, q ≤ 0.05) for multiple comparisons, to identify significant differences between transition and stable epochs. Additionally, the system MUST validate these features against an independent physiological target (e.g., EOG/EMG artifacts or expert re-scoring of a subset) to ensure they predict physiological state changes rather than just annotation boundaries.

**Why this priority**: This addresses the core scientific inquiry: "What EEG features... best characterize transitions?" It delivers the "Expected results" regarding spectral power shifts and entropy changes, independent of the deep learning model, while ensuring scientific validity through independent validation and robust statistics.

**Independent Test**: The feature extraction module can be tested by running it on a fixed dataset and verifying that the statistical tests identify known physiological differences (e.g., higher delta power in N3 vs N2) and that transition windows show distinct feature distributions compared to stable epochs. The independent validation must show that features correlate with the independent physiological marker.

**Acceptance Scenarios**:

1. **Given** a set of transition windows (e.g., N2→N3) and stable N2 epochs, **When** features are extracted and compared, **Then** the Cluster-Based Permutation Test with FDR correction identifies at least one feature (e.g., delta power ratio) with a q-value < 0.05.
2. **Given** a specific transition type (e.g., Wake→N1), **When** the system computes non-linear features, **Then** sample entropy values are calculated and stored for every 60-second transition window.
3. **Given** the full feature set, **When** the system aggregates results, **Then** a summary report is generated listing the top 5 features with the highest effect size for distinguishing transitions from stable states, and a validation score against the independent physiological target is reported.

---

### User Story 3 - Lightweight Temporal Model Training and Validation (Priority: P3)

The system MUST train a lightweight 1D-CNN model (≤100k parameters) to predict the *probability* of a sleep stage transition occurring within the next 30 seconds based on the preceding 3 epochs, and validate the model's ability to capture transition trajectories on a held-out subject set. The model MUST be validated to ensure it predicts the *timing* or *probability* of a transition before the annotation change occurs, avoiding tautological validation.

**Why this priority**: This implements the "Temporal Dynamics Analysis" and "Independent Evaluation" steps. It tests the hypothesis that a simple model can learn the specific dynamics of transitions, providing a baseline for future wearable applications, while ensuring the validation is scientifically sound.

**Independent Test**: The model training and validation can be tested by running the training loop on a CPU-only environment, verifying that the model converges within the 4-hour limit, and that the held-out validation accuracy for transition prediction exceeds the random baseline by ≥ 5 percentage points. Memory usage must be measured as peak RSS.

**Acceptance Scenarios**:

1. **Given** a training set of feature sequences, **When** the 1D-CNN model is trained, **Then** the training completes within 4 hours on a CPU-only environment with peak RSS ≤ 7 GB.
2. **Given** a held-out test set of subjects not used in training, **When** the model predicts the probability of a transition, **Then** the transition prediction accuracy is reported separately from the overall epoch classification accuracy, and must exceed the random baseline accuracy by ≥ 5 percentage points.
3. **Given** the trained model, **When** attention weights or feature importance are analyzed, **Then** the system outputs a visualization or metric showing which input epochs contributed most to the transition prediction.

---

### Edge Cases

- **What happens when** a subject has a hypnogram with no transitions (e.g., stays in Wake for the entire recording)? The system must handle this gracefully by skipping transition-window extraction for that subject without crashing.
- **How does the system handle** missing data or artifacts in the EEG signal within a transition window? The system MUST apply linear interpolation to fill missing values *before* applying bandpass or notch filters, and flag the imputed segments in the output metadata.
- **What happens when** the dataset contains subjects with missing annotations for specific sleep stages? The system must exclude these subjects or epochs from the transition analysis to ensure label integrity.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the Sleep-EDF SC subset from PhysioNet and verify file integrity before processing. (See US-1)
- **FR-002**: System MUST apply linear interpolation for missing data *before* applying a bandpass filter (0.5–45 Hz) and a notch filter (50/60 Hz) to raw EEG data. (See US-1)
- **FR-003**: System MUST extract 60-second transition windows centered on annotated stage changes and 30-second epochs for stable periods. (See US-1)
- **FR-004**: System MUST compute time-domain, frequency-domain, and non-linear features for all extracted windows. (See US-2)
- **FR-005**: System MUST perform statistical hypothesis testing using Cluster-Based Permutation Tests with False Discovery Rate (FDR) correction (Benjamini-Hochberg, q ≤ 0.05) to compare feature distributions between transition and stable windows. (See US-2)
- **FR-006**: System MUST train a lightweight 1D-CNN model with ≤100k parameters to predict the probability of a sleep stage transition occurring within the next 30 seconds. (See US-3)
- **FR-007**: System MUST validate the trained model on a held-out set of subjects to ensure generalizability and that it predicts transition timing/probability rather than trivial annotation boundaries. (See US-3)
- **FR-008**: System MUST execute the entire pipeline (download, preprocess, train, validate) within 6 hours on a CPU-only environment. (See US-3)
- **FR-009**: System MUST complete the model training phase within 4 hours on a CPU-only environment. (See US-3)
- **FR-010**: System MUST validate extracted features against an independent physiological target (e.g., EOG/EMG artifacts or expert re-scoring) to ensure they predict physiological state changes. (See US-2)

### Key Entities

- **EEG_Epoch**: Represents a 30-second or 60-second segment of EEG data with associated features and a sleep stage label.
- **Transition_Window**: A specific type of EEG_Epoch centered on a stage change, containing features derived from the transition dynamics.
- **Feature_Vector**: A collection of computed features (time, frequency, non-linear) for a specific epoch.
- **Model_Checkpoint**: The saved state of the trained lightweight neural network.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The number of successfully extracted transition windows is measured against the total number of annotated stage changes in the dataset. (See US-1)
- **SC-002**: The statistical significance (q-value) of feature differences between transition and stable windows is measured against the FDR threshold of 0.05. (See US-2)
- **SC-003**: The model's transition prediction accuracy must exceed the random baseline accuracy by at least 5 percentage points. (See US-3)
- **SC-004**: The total execution time of the pipeline is measured against the 6-hour CPU limit, and the training phase is measured against the 4-hour limit. (See US-3)
- **SC-005**: The peak memory usage (Resident Set Size) of the training process is measured against the 7 GB RAM limit. (See US-3)

## Assumptions

- The Sleep-EDF SC subset is available on PhysioNet and can be downloaded via `wget` without authentication barriers or rate-limiting issues that would exceed the 6-hour window.
- The single-channel EEG (Fpz-Cz) data in the Sleep-EDF SC subset is sufficient to capture the spectral and temporal dynamics of sleep stage transitions, despite the lack of multi-channel data.
- The lightweight 1D-CNN model with ≤100k parameters is capable of learning the transition dynamics from the extracted features without requiring GPU acceleration.
- The statistical tests (Cluster-Based Permutation Tests with FDR correction) are appropriate for the distribution of the extracted features and the temporal autocorrelation inherent in EEG data.
- The held-out subject set is large enough to provide a meaningful validation of the model's generalizability, given the constraints of the dataset size.
- The "transition windows" (60 seconds) are an appropriate temporal scale to capture the dynamics of sleep stage transitions, as defined in the methodology sketch.
- Independent physiological markers (EOG/EMG) or expert re-scoring data are available for a subset of the dataset to validate the features as per FR-010.