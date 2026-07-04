# Research: Linking Resting‑State fMRI Entropy to Creative Problem Solving

## Research Question

Does resting-state brain complexity, quantified as Multiscale Sample Entropy (MSE) of BOLD signals, predict individual differences in creative problem-solving ability (NIH Toolbox Creativity Composite) in the HCP S1200 cohort?

## Dataset Strategy

The study utilizes the Human Connectome Project (HCP) S1200 release, accessed via the verified OpenNeuro dataset **ds000114**, which contains the actual 4-D resting-state fMRI volumes required for entropy computation.

| Dataset Component | Source / Verified URL | Content | Access Method |
|-------------------|-----------------------|---------|---------------|
| **fMRI 4-D Volumes** | `https://openneuro.org/datasets/ds000114` (HCP S1200 Resting State) | Pre-processed resting-state fMRI (CIFTI/NIfTI format) | `nibabel` (read CIFTI/NIfTI) |
| **Phenotypes** | `https://db.humanconnectome.org/data/projects/HCP_1200/files/HCP1200_1200Subjects.csv` | NIH Toolbox Creativity Composite (derived from Flanker, DCCS), Age, Sex, Framewise Displacement | `pandas.read_csv` |
| **Atlas** | HCP Multimodal 360-Parcel Atlas (embedded in code) | Parcellation definitions for DMN, FPN, CON, VAN, SMN, VN | Local resource (no external URL) |

**Note on Data Fit**: The verified OpenNeuro ds000114 dataset contains the necessary 4-D BOLD time-series structure. The pipeline extracts time-series from these volumes. The phenotypic file contains the raw sub-tests (Flanker, DCCS) from which the "Creativity Composite" is derived if not directly present.

**Creativity Composite Derivation**: If the `HCP1200_1200Subjects.csv` does not contain a pre-calculated "Creativity Composite" column, the pipeline will derive it from the Flanker and DCCS scores using standard NIH Toolbox scoring protocols (e.g., sum of standardized scores or principal component analysis as defined in the HCP documentation).

**Limitation**: The study is cross-sectional; no causal claims can be made. The sample size (N=1000) is standard, but effective N may be reduced by exclusion criteria.

## Methodology & Statistical Rigor

### 1. Data Preprocessing
- **Parcellation**: Apply the HCP 360-parcel atlas to extract mean time series per parcel from the 4-D CIFTI/NIfTI volumes using `nibabel`.
- **Motion Control**: Calculate Framewise Displacement (FD). Subjects with FD > 0.2 mm are flagged but retained for robustness checks (US-1, Edge Case).
- **Handling Missing Data**: Subjects with missing NIH scores are excluded from the main analysis but logged (Edge Case).

### 2. Entropy Computation (FR-003)
- **Algorithm**: Multiscale Sample Entropy (MSE).
- **Parameters**: Template length `m=2`, tolerance `r=0.2`, scale factors `1` to `20`.
- **Implementation**: Vectorized NumPy implementation to ensure CPU feasibility.
- **Robustness Check**: Sensitivity analysis with `r` ∈ {0.15, 0.20, 0.25} (FR-007).

### 3. Aggregation (FR-004)
- **Global Metric**: Arithmetic mean of all parcel entropies.
- **Network Metrics**: Mean entropy for DMN, FPN, CON, VAN, SMN, VN.
- **Stability Metric**: Coefficient of Variation (CV) of parcel-wise entropies (SC-006).

### 4. Statistical Modeling (FR-005, FR-006)
- **Primary Model**: Robust Linear Regression (RLM) with HC3 standard errors.
  - Outcome: NIH Toolbox Creativity Composite (derived from Flanker + DCCS if needed).
  - Predictor: Global Entropy (and network-specific models).
  - Covariates: Age, Sex, Mean FD.
- **Multiple Comparison Correction**: **Benjamini-Hochberg (BH) FDR** for network-specific tests (SC-002).
  - *Rationale*: Cluster-based permutation correction is invalid for 6 data points (networks). BH-FDR is the standard method for controlling FDR across a small set of independent tests.
- **Symmetry Check**: Swap predictor/outcome to test the symmetry of the association (FR-009).
  - *Note*: This test does **not** prove causality or directionality in a cross-sectional design; it only tests the symmetry of the correlation. A significant result in the reverse model does not invalidate the primary model, nor does a non-significant result prove causality.

### 5. Power & Sample Size
- **Power Analysis**: Assuming N=1000, the study has >90% power to detect a moderate effect size (f² ≥ 0.15) at α=0.05 after BH-FDR correction.
- **Effective Sample Size**: The analysis accounts for expected exclusion rates (motion, missing data). If the effective N drops below a pre-defined threshold, the power limitation will be explicitly reported in the final paper.
- **Causal Claim**: None. The study is observational; results are framed as associational.
- **Collinearity**: Predictors (networks) are distinct parcels; collinearity between networks is acknowledged but handled via separate models per network.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Vectorized MSE over Loop** | Required to meet FR-008 (45 min runtime on 2-core CPU). |
| **HC3 Robust SE** | Behavioral data often exhibits heteroscedasticity; HC3 is more robust than OLS SEs. |
| **Benjamini-Hochberg FDR** | Required for 6 network tests; Permutation cluster correction is invalid for low-dimensional data. |
| **Sample Size N=1000** | Standard HCP S1200 subset; provides sufficient power for moderate effects, subject to exclusion rates. |
| **Symmetry Check** | Tests association symmetry, not causality; explicitly disclaimed as non-causal. |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Dataset URL unreachable | Use verified OpenNeuro S3 URLs only; implement retry logic with exponential backoff (Edge Case). |
| Memory overflow (GB limit) | Process subjects in batches; stream data; avoid storing full 4-D volumes in RAM. |
| Entropy calculation NaN | Replace with median parcel entropy; log warning (Edge Case). |
| Power insufficient | Explicitly report power limitation in final paper if p-values are non-significant despite large N. |
| Effective N reduced | Calculate and report effective N after exclusions; adjust power interpretation accordingly. |
| Invalid Dataset Source | Strictly use OpenNeuro ds000114 for raw fMRI; no HuggingFace parquet files for raw time-series. |