# Research Protocol: Network Structure and Neural Avalanche Dynamics

## 1. Objective
To investigate the statistical association between structural connectome properties (derived from dMRI) and neural avalanche dynamics (derived from resting-state EEG) in human subjects, specifically testing whether network topology influences the criticality of neural activity.

## 2. Data Sources
- **Primary Source**: OpenNeuro dataset `ds004231` (FR-002).
 - Contains both diffusion MRI (dMRI) and resting-state EEG recordings.
 - **Strict Constraint**: The pipeline requires data from this specific source. If `ds004231` is unavailable, the pipeline halts and triggers the Null Result Protocol. No synthetic data or fallback to other datasets (e.g., HCP, ds004503) is permitted for the primary analysis.
- **Structural Parcellation**: HCP-MMP1.0 (Glasser et al., 2016).
 - Downloaded from the official HCP repository.
 - Verified via SHA-256 checksum against the value stored in `code/config.py`.

## 3. Methodology

### 3.1 Data Acquisition & Preprocessing
1. **dMRI Processing**:
 - Tractography conversion to connectome matrices using MRtrix3 (`tck2connectome`).
 - Mapping to HCP-MMP parcellation (180 regions per hemisphere).
 - Quality Control: Exclusion of participants with disconnected graphs or >30% channel loss.
2. **EEG Processing**:
 - Band-pass filtering (1-40 Hz).
 - Downsampling to 250 Hz.
 - ICA-based artifact removal.
 - **Strict Constraint**: If real EEG data from `ds004231` is missing, the pipeline raises `RuntimeError` and halts.

### 3.2 Metric Computation
- **Structural Metrics**: Degree centrality, clustering coefficient, rich-club coefficient (NetworkX, BCTpy).
- **Avalanche Metrics**:
 - Z-score normalization of EEG signals.
 - Thresholding at the 75th percentile of the z-scored distribution.
 - Identification of spatiotemporal cascades.
 - Power-law fitting of avalanche size and duration distributions (using `powerlaw` package).

### 3.3 Statistical Analysis
- **Correlation**: Spearman rank correlation between structural metrics and avalanche exponents.
- **Robustness**:
 - Permutation testing (max-t correction) for family-wise error control.
 - Sensitivity analysis across thresholds {0.70, 0.75, 0.80}.
 - Collinearity diagnostics (VIF).
- **Sample Size Gate**: If N < 10 participants pass QC, the correlation analysis is skipped, and a "Null Result" report is generated.

## 4. Ethical Considerations
- All data is from public, de-identified repositories (OpenNeuro).
- No causal claims are made; findings are strictly framed as associational.

## 5. Reproducibility
- All random seeds are fixed in `code/config.py`.
- Data integrity is enforced via SHA-256 checksums.
- The pipeline is fully automated via `code/main.py`.
