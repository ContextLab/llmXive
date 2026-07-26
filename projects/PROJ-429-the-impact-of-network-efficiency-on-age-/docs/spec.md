# Project Specification: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

## Overview
This project investigates how network efficiency metrics derived from resting-state EEG change with age and cognitive decline. We utilize the TUH EEG corpus to compute graph-theoretical metrics and correlate them with age and cognitive scores.

## Functional Requirements

### FR-001: Data Acquisition
The system shall download and validate EEG data from the TUH EEG corpus (PhysioNet).
- Source: PhysioNet / TUH EEG Corpus (`tuh_eeg`)
- Validation: Check file integrity via checksums and verify metadata presence.

### FR-002: Preprocessing and Epoching
The system shall preprocess raw EEG data and segment it into epochs for analysis.
- **Epoch Length**: The system shall segment continuous data into **10-second epochs**.
 *Rationale*: Longer epochs provide sufficient spectral resolution for coherence estimation in the 1-40Hz band, reducing variance compared to shorter epochs. This supersedes initial draft requirements of 2-second epochs.
- **Filtering**: Bandpass filter (1-40 Hz) to remove slow drifts and high-frequency noise.
- **Artifact Removal**: Apply ICA to identify and remove ocular and muscular artifacts.
- **Rejection**: Reject epochs containing >50% artifact-contaminated channels.
- **Quality Flag**: Flag recordings with Signal-to-Noise Ratio (SNR) < 10dB.

### FR-003: Network Metric Calculation
The system shall compute the following graph-theoretical metrics from functional connectivity matrices:
- Global Efficiency
- Characteristic Path Length
- Local Efficiency
- Clustering Coefficient
- Modularity
*Constraint*: Local Efficiency must be calculated as the inverse of the mean shortest path in the neighborhood subgraph, not as the inverse of global path length.

### FR-004: Statistical Analysis
The system shall perform Spearman rank correlation between network metrics and:
- Age
- Cognitive Scores (if available)
- Multiple comparison correction (Bonferroni or FDR) must be applied to the family of tests.

### FR-005: Traceability
All output artifacts must include a `trace_id` derived from the SHA-256 hash of the source code and input data versions to ensure reproducibility.

### FR-006: Data Quality Reporting
The system shall generate a quality report (`download_report.json`) detailing:
- Valid records count
- Invalid instrument count
- Missing cognitive data count
- Per-record status flags

### FR-007: Cognitive Instrument Validation
The system shall validate cognitive assessment instruments against a registered list (e.g., MMSE, MoCA). Records using unregistered instruments shall be flagged as "Invalid Instrument" and excluded from cognitive correlation analysis.

### FR-008: Sensitivity Analysis
The system shall perform sensitivity analysis on:
- Network density thresholds (Low, Medium, High)
- Artifact rejection thresholds
Results must be aggregated into a summary report indicating stability.

## Non-Functional Requirements

### SC-001: Reproducibility
All pipelines must be deterministic given the same input data and random seeds.

### SC-002: Power Analysis
A power analysis must be conducted to ensure the study is sufficiently powered (≥ 0.80) for the target effect size (r=0.3).

### SC-003: Robustness
The pipeline must handle missing data gracefully (e.g., missing cognitive scores) without crashing, logging warnings where appropriate.

### SC-004: Error Control
Family-wise error rate (FWER) must be controlled via appropriate multiple comparison corrections.

## Data Model
- **Raw Data**: TUH EEG EDF files with associated JSON metadata.
- **Processed Data**: MNE Epochs objects, Connectivity Matrices (N x N).
- **Results**: CSV files containing metrics, correlations, and regression coefficients.
- **Quality**: JSON reports detailing data validity and flags.

## Configuration
- **Epoch Length**: 10 seconds (Ratified Decision).
- **Frequency Band**: 1-40 Hz.
- **SNR Threshold**: 10 dB.
- **Artifact Rejection**: >50% bad channels.

## Deliverables
1. `data/raw/`: Downloaded TUH EEG data.
2. `data/processed/`: Preprocessed epochs and connectivity matrices.
3. `data/results/`: Network metrics, correlation results, regression outputs.
4. `data/quality/`: Download and quality reports.
5. `docs/spec.md`: This specification document.