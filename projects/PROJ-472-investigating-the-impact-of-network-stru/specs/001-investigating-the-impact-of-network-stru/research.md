# Research Plan: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

## Overview
This research project investigates the statistical associations between structural brain network properties (derived from diffusion MRI) and neural avalanche dynamics (derived from EEG/MEG or simulated data). The primary hypothesis is that specific topological features of the structural connectome, such as rich-club organization and degree distribution, constrain the statistical properties of neural avalanches, particularly their size and duration distributions.

## Research Questions
1. **RQ1**: Do structural network metrics (degree, clustering, rich-club coefficient) correlate with neural avalanche exponents?
2. **RQ2**: Is the power-law scaling of neural avalanches robust across different thresholding parameters?
3. **RQ3**: How does the structural topology influence the criticality of neural dynamics?

## Data Sources
### Primary Source (dMRI)
- **Dataset**: OpenNeuro ds004230
- **Modality**: Diffusion MRI (tractography)
- **Processing**: Converted to HCP-MMP parcellated adjacency matrices using MRtrix3 `tck2connectome`.
- **Constraint**: Strict single-source constraint. No fallback to other datasets (e.g., ds004503) is permitted.

### Secondary Source (EEG)
- **Probe**: OpenNeuro ds004231 (FR-002)
- **Status**: **Unavailable**. The pipeline attempts to download this dataset. If unavailable (HTTP 404 or empty), it fails loudly and triggers the simulation contingency path.
- **Contingency**: Synthetic EEG generated via Wilson-Cowan equations driven by the structural connectomes.

## Methodology
1. **Data Acquisition & Preprocessing**:
 - Download dMRI data (streaming enabled to prevent OOM).
 - Preprocess tractography to structural connectomes.
 - Attempt real EEG download; if failed, generate synthetic EEG using `code/data/simulate_EEG.py`.
2. **Metric Computation**:
 - **Structural**: Node degree, mean clustering coefficient, rich-club coefficient (NetworkX, BCTpy).
 - **Dynamics**: Neural avalanche detection (75th percentile threshold on z-scored signal), size/duration calculation, power-law fitting (`powerlaw` package).
3. **Statistical Analysis**:
 - Spearman rank correlation between structural metrics and avalanche exponents.
 - Non-parametric permutation tests (max-t method) for significance correction.
 - Sensitivity analysis across thresholds [0.70, 0.75, 0.80].
4. **Reporting**:
 - Generate associational reports (no causal claims).
 - Validate null result protocol if N < 10 subjects.

## Ethical Considerations
- All data is anonymized and publicly available via OpenNeuro.
- Synthetic data generation uses random seeds logged for reproducibility.

## Limitations
- Reliance on simulation for EEG dynamics due to data unavailability.
- Cross-dataset registration is not performed (single-source constraint).
- Power-law fit convergence failures are excluded from correlation analysis.
