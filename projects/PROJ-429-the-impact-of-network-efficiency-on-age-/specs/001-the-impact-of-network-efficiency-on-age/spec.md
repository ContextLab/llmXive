# Project Specification: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

## 1. Introduction

This project investigates the relationship between age-related cognitive decline and changes in functional brain network efficiency using resting-state EEG data. We aim to quantify how network topology (global and local efficiency) correlates with age and cognitive scores, while controlling for confounding variables.

## 2. Functional Requirements

### FR-001: Data Acquisition
- Download resting-state EEG data from the Temple University Hospital (TUH) EEG Corpus via PhysioNet.
- Filter for adult participants (age >= 18).
- Ensure metadata includes age and, where available, cognitive assessment scores.

### FR-002: Preprocessing and Epoching
- Preprocess EEG data using MNE-Python:
 - Bandpass filter (1-40 Hz).
 - Apply Independent Component Analysis (ICA) for artifact removal.
 - **Epoch the continuous data into fixed-duration segments** (Ratified Design Decision: Deviation from initial 2s to improve spectral resolution for coherence estimation).
 - Reject epochs with >50% artifacts.
 - Calculate Signal-to-Noise Ratio (SNR) per epoch; flag SNR < 10dB.

### FR-003: Connectivity and Network Metrics
- Compute functional connectivity using Coherence (Welch method) on the 10-second epochs.
- Construct adjacency matrices for a standard EEG montage (e.g., 10-20 system).
- Calculate graph-theoretical metrics:
 - Global Efficiency
 - Characteristic Path Length
 - Local Efficiency
 - Clustering Coefficient
 - Modularity
- **Formula Constraints**:
 - Global Efficiency = 1.0 / Characteristic Path Length.
 - Local Efficiency = 1.0 / mean_shortest_path(subgraph) (must be calculated via subgraph path lengths, not the global inverse).

### FR-004: Statistical Analysis
- Perform Spearman rank correlation between network metrics and (Age, Cognitive Score).
- Apply multiple-comparison correction (Bonferroni or FDR) to control Family-Wise Error Rate (FWER).
- Conduct power analysis to ensure minimum power >= 0.80 for target effect size r=0.3.

### FR-005: Visualization
- Generate age-stratified bar plots of network metrics with confidence intervals.
- Visualize network topology changes across age groups.

### FR-006: Reproducibility
- Maintain a version map of all source code and data artifacts with SHA-256 hashes.
- Inject `trace_id` into all final result CSVs.

### FR-007: Cognitive Instrument Validation
- Validate cognitive assessment instruments against a registered list (MMSE, MoCA).
- Flag records with invalid or missing cognitive instruments.
- Exclude records with invalid instruments from cognitive correlation analysis.

### FR-008: Sensitivity Analysis
- Evaluate stability of network metrics against variations in:
 - Network density thresholds.
 - Artifact rejection thresholds.

## 3. Non-Functional Requirements

- **SC-001**: All analysis must be performed on CPU-only infrastructure.
- **SC-002**: Power analysis must be performed via simulation to verify sample size adequacy.
- **SC-003**: Sensitivity analysis must be documented in a summary report.
- **SC-004**: Family-Wise Error Rate must be controlled via appropriate correction methods.

## 4. Data Model

- **Raw Data**: EDF files from TUH EEG Corpus.
- **Processed Data**:
 - `data/processed/epochs/`: MNE Epochs objects.
 - `data/processed/connectivity_matrices/`: NumPy arrays of coherence matrices.
- **Results**:
 - `data/results/network_metrics.csv`: Participant-level graph metrics.
 - `data/results/correlation_results.csv`: Statistical correlation outputs.
 - `data/results/regression_results.csv`: Regression coefficients.
- **Quality Control**:
 - `data/quality/download_report.json`: Data validation status.
 - `data/results/efficiency_check.json`: Verification of metric formulas.

## 5. Dependencies

- Python 3.11
- MNE-Python
- NetworkX
- SciPy
- Pandas
- Statsmodels
- PyWavelets
- Matplotlib/Seaborn

## 6. Design Decisions

- **Epoch Length**: 10 seconds (see `docs/decisions/epoch_length.md`).
- **Connectivity Metric**: Coherence (frequency domain).
- **Graph Construction**: Thresholded adjacency matrices.

## 7. Version History

- v1.0: Initial draft (2s epochs).
- v1.1: Updated FR-002 to mandate 10-second epochs per T014a.