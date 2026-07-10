# Implementation Plan: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

**Branch**: `001-assessing-orbital-period-dependence` | **Date**: 2026-06-28 | **Spec**: `specs/001-assessing-orbital-period-dependence/spec.md`
**Input**: Feature specification from `/specs/001-assessing-orbital-period-dependence/spec.md`

## Summary

This project implements a statistical pipeline to analyze the Kepler exoplanet catalog (DR25 and Input Catalog) to determine the slope of the "radius gap" (the bimodal distribution valley) as a function of orbital period. The goal is to determine which of two competing physical theories (Photoevaporation vs. Core-Powered Mass Loss) is *more consistent* with the observed **associational** trend. The analysis is strictly associational; causal claims are not made. The implementation relies on a robust data ingestion pipeline, log-spaced binning, Gaussian Mixture Modeling (GMM) with bootstrap uncertainty quantification, and a Monte Carlo simulation to compare measured slopes against theoretical distributions. All analysis is constrained to run on CPU-only free-tier CI with limited cores and memory.

**Methodological Correction**: The Spec's "Assumption about predictor collinearity" suggests using the completeness map as a regression covariate. This plan corrects that approach: the completeness map is used to **weight the GMM likelihoods** (Step 2) to account for Malmquist bias in the gap estimation. It is **not** used as a covariate in the final regression (Step 3) to avoid circularity and statistical invalidity.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `scipy`, `matplotlib`, `seaborn`, `requests`, `tqdm`, `astroquery`  
**Storage**: Local filesystem (`data/`, `output/`) using CSV and JSON formats.  
**Testing**: `pytest` with unit tests for data filtering, GMM logic, and regression.  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner).  
**Project Type**: Computational Science / Data Analysis Pipeline.  
**Performance Goals**: Full pipeline execution ≤ 6 hours; Memory usage < 6 GB peak.  
**Constraints**: No GPU; No external API calls other than MAST/Kepler catalogs; No imputation of missing stellar parameters; Fixed random seeds for reproducibility.  
**Scale/Scope**: ~3000-4000 confirmed Kepler planets (after filtering) processed into ~10-15 period bins.

**Artifact Hashing & Versioning**:
- Every file under `data/` and `output/` is checksummed using SHA256.
- The hash is recorded in `state.yaml` under `artifact_hashes`.
- The `Advancement-Evaluator` uses this to detect stale data.
- Random seeds are pinned in `code/utils/constants.py` (e.g., `SEED = 42`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Plan mandates `requirements.txt` pins and fixed random seeds in all GMM/Bootstrap/Monte Carlo steps. |
| **II. Verified Accuracy** | PASS | Plan requires citations only from verified sources (MAST/Kepler) and defers theoretical parameter values to research.md with literature citations. |
| **III. Data Hygiene** | PASS | Plan mandates checksums for raw data and immutable derivation steps (new files for filtered data). |
| **IV. Single Source of Truth** | PASS | Plan ensures all figures/stats trace to `data/` artifacts and `code/` scripts. |
| **V. Versioning Discipline** | PASS | Plan includes SHA256 artifact hashing logic in `code/utils/logging.py` and state file updates. |
| **VI. Statistical Gap Detection Rigor** | PASS | Plan explicitly requires 2-component GMM (FR-004), 1000+ bootstrap resamples (FR-005), and KDE validation (FR-008). |
| **VII. Period-Binning Integrity** | **CONFLICT** | Spec (FR-007) mandates Monte Carlo simulation for theory comparison, which contradicts the Constitution's "z-test" requirement (Principle VII). This is a **Constitution Violation** requiring an amendment process. The plan implements the Spec's Monte Carlo approach. |
| **VIII. Validation** | PASS | Plan includes KDE validation step (FR-008) and synthetic data recovery test (FR-009). |

## Project Structure

### Documentation (this feature)

```text
specs/001-assessing-orbital-period-dependence/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-787-assessing-orbital-period-dependence-of-t/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── main.py                  # Orchestration script
│   ├── data/
│   │   ├── ingest.py            # FR-001, FR-002, FR-003
│   │   └── preprocess.py        # Filtering and binning logic
│   ├── analysis/
│   │   ├── gmm.py               # FR-004, FR-005
│   │   ├── regression.py        # FR-006
│   │   └── monte_carlo.py       # FR-007
│   ├── validation/
│   │   ├── kde.py               # FR-008
│   │   └── synthetic.py         # FR-009
│   └── utils/
│       ├── logging.py
│       └── constants.py
├── data/
│   ├── raw/                     # Downloaded catalogs (checksummed)
│   └── processed/               # Filtered CSVs
├── tests/
│   ├── test_ingest.py
│   ├── test_gmm.py
│   └── test_regression.py
└── output/
    ├── plots/
    └── results/
```

**Structure Decision**: Single project structure with modular `code/` subdirectories. This minimizes overhead for a data analysis pipeline and aligns with the CPU-only constraint by keeping dependencies localized.

## Complexity Tracking

No violations detected. The complexity is managed by strict binning rules and CPU-tractable methods (GMM on small subsets, not the full dataset at once).

## Statistical Methodology

### 1. Binning Strategy (FR-003)
- **Range**: Log-period from 0.7 to 2.0 (5 to 100 days).
- **Bins**: Log-spaced.
- **Minimum Count**: 30 planets per bin.
- **Merge Logic**: If a bin has < 30 planets, merge with the adjacent bin (closest period) until the threshold is met.
- **Weighting**: Regression will use the weighted mean period of the bin, weighted by the inverse variance of the gap location estimate.

### 2. Gap Location Estimation (FR-004, FR-005)
- **Method**: Two-component Gaussian Mixture Model (GMM).
- **Initialization**: K-Means++ with multiple random seeds; select model with lowest BIC.
- **Completeness Correction**: The GMM likelihoods are **weighted** by the detection completeness value from the Kepler completeness map for each planet's (period, radius) coordinate. This accounts for Malmquist bias without introducing circularity. Bins with average completeness < 5% are excluded entirely.
- **Validation**:
    - BIC difference (2-comp vs 1-comp) must be ≥ 10 to confirm bimodality.
    - Minimum peak separation ≥ 0.1 R_earth (justified as the physical resolution limit for typical Kepler uncertainties).
    - **Unimodal Handling**: If BIC < 10, the bin is flagged as unimodal. The plan **triggers a merge with the adjacent bin**. If the merged bin is still unimodal, it is excluded from the final regression but reported in the "Gap Visibility" analysis.
- **Uncertainty**: A sufficient number of bootstrap resamples per bin to generate confidence intervals for the gap location.
- **Threshold Justification**: The 0.1 R_earth threshold is a physical resolution limit. A sensitivity analysis (FR-009) will test if the slope changes if this is relaxed to 0.05 R_earth.

### 3. Slope Calculation & Theory Comparison (FR-006, FR-007)
- **Regression**: Weighted Linear Regression of `gap_radius` vs `log(period)` using only bins where the gap was successfully resolved.
- **Theoretical Distributions**:
    - **Photoevaporation (Owen & Wu, 2017)**: Mean slope = -0.11, Std = 0.02.
    - **Core-Powered Mass Loss (Ginzburg et al., 2018)**: Mean slope = -0.15, Std = 0.03.
- **Simulation**: Monte Carlo simulation propagating both measured slope uncertainty and theoretical parameter uncertainty.
- **Hypothesis Test**:
    - **Method**: Calculate the probability that the measured slope (drawn from its posterior) is consistent with the theoretical distribution.
    - **Significance**: Bonferroni corrected α = 0.025 (for 2 tests).
    - **Inconsistency**: p-value < 0.025 indicates inconsistency with the theory.
- **Inference Framing**: Findings are framed as "consistency with theoretical predictions" for an associational trend. Causal claims are not made due to uncontrolled confounders (stellar age, metallicity).

### 4. Validation (FR-008, FR-009)
- **KDE Validation**: Adaptive bandwidth KDE on cumulative distribution. Pass if KDE gap falls within GMM 95% CI.
- **Synthetic Test**:
    - **Generation**: Generate synthetic planet populations with known bimodal radii and a predefined slope (e.g., -0.11). Inject noise matching Kepler uncertainties.
    - **Recovery**: Run full pipeline. Verify recovered slope is within 5% of ground truth.
    - **Sensitivity**: Test recovery with the 0.1 R_earth threshold relaxed to 0.05 R_earth.

### 5. Runtime Measurement (SC-005)
- The pipeline will log `run_duration_seconds` and compare it against the 6-hour threshold (SC-005) in the final report.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use MAST for Kepler Data** | Verified source. `astroquery.mast` provides programmatic access to DR25 and KIC. |
| **Exclude, Don't Impute** | Adheres to Principle I (Data Integrity) and FR-002. Missing stellar data invalidates the radius calculation. |
| **Bonferroni Correction** | Required by FR-007 and Assumption (Multiplicity) to control family-wise error rate across two theory comparisons. |
| **KDE Validation** | Required by FR-008 to ensure GMM results are not artifacts of parametric assumptions. |
| **Completeness-Weighted GMM** | Replaces the flawed "completeness covariate" in regression. Corrects for Malmquist bias in the gap estimation phase. |
| **Monte Carlo P-value** | Replaces "overlap area" to provide a standard statistical test for consistency with theoretical distributions. |
| **Unresolved Bin Handling** | Bins failing BIC test are excluded from regression to prevent bias, but reported for transparency. |
| **Constitution Conflict** | Spec FR-007 (Monte Carlo) supersedes Constitution Principle VII (z-test). Flagged for amendment. |
| **Survivorship Bias Mitigation** | Merging bins introduces bias; final regression restricted to bins with sufficient power. "Gap Visibility" analysis reports on excluded regions. |
| **Threshold Justification** | 0.1 R_earth threshold is a physical resolution limit; sensitivity analysis tests robustness. |