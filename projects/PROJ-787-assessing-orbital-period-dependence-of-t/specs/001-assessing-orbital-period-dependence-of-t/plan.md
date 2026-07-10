# Implementation Plan: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

**Branch**: `001-assessing-orbital-period-dependence` | **Date**: 2026-06-28 | **Spec**: `specs/001-assessing-orbital-period-dependence/spec.md`
**Input**: Feature specification from `/specs/001-assessing-orbital-period-dependence/spec.md`

## Summary

This feature implements a computational pipeline to analyze the Kepler DR25 exoplanet catalog to assess the dependence of the "radius gap" (the paucity of planets between super-Earths and sub-Neptunes) on orbital period. The approach involves downloading and filtering the Kepler DR25 and Input Catalogs, binning planets by **fixed** log-period intervals, fitting two-component Gaussian Mixture Models (GMM) to identify gap locations, and performing an **Errors-in-Variables (EIV) regression** to compare the measured slope against theoretical predictions from photoevaporation and core-powered mass loss models. The pipeline includes bootstrap resampling for uncertainty estimation, KDE validation, and a **Monte Carlo Consistency Test** that accounts for theoretical uncertainty distributions.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `scipy`, `astropy`, `requests`, `tqdm`, `statsmodels`, `astroquery`, `pyyaml`  
**Storage**: Local file system (CSV/Parquet artifacts under `data/`, JSON for final results)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner)  
**Project Type**: Computational Science / Data Analysis CLI  
**Performance Goals**: Complete full analysis in ≤ 6 hours on 2-core CPU, 7GB RAM.  
**Constraints**: No GPU; no large model training; strict data filtering (<20% radius uncertainty, <1% period uncertainty); fixed binning strategy; reproducibility via pinned random seeds.  
**Scale/Scope**: Kepler DR25 catalog (~ confirmed planets); A small number of fixed period bins; A sufficient number of bootstrap iterations per bin.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action / Reference |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Plan mandates pinned `requirements.txt`, fixed random seeds in GMM/Bootstrap, and deterministic data download logic. |
| **II. Verified Accuracy** | PASS | Plan requires citations in `research.md` to be validated against primary sources (Owen & Wu, Ginzburg et al.) using the **Reference-Validator Agent** workflow with **title-token-overlap ≥ 0.7**. All external dataset URIs are verified against the MAST archive. |
| **III. Data Hygiene** | PASS | Plan enforces checksumming of raw data (SHA-256), immutable raw files, versioned derived datasets, and **recording checksums in `state.yaml` artifact map**. |
| **IV. Single Source of Truth** | PASS | All figures/stats in the final report will be generated directly from `data/` artifacts; no hand-typed values. |
| **V. Versioning Discipline** | PASS | Plan includes content hashing of artifacts in the state file; `state.yaml` updated on artifact changes. |
| **VI. Statistical Gap Detection Rigor** | PASS | Plan mandates a multi-component GMM, a substantial number of bootstrap resamples, and KDE validation as per the spec. |
| **VII. Period-Binning Integrity** | PASS | Plan specifies **fixed** log-spaced bins (5-100 days), minimum 30 planets per bin (flagged if below), and **Errors-in-Variables regression** with completeness correction. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assessing-orbital-period-dependence/
├── plan.md              # This file (Phase 0 Design)
├── research.md          # Phase 0 Design
├── data-model.md        # Phase 0 Design
├── quickstart.md        # Phase 0 Design
├── contracts/           # Phase 0 Design (generated from data-model.md)
│   ├── planet-record.schema.yaml
│   ├── period-bin.schema.yaml
│   └── gap-analysis-result.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-787-assessing-orbital-period-dependence-of-t/
├── data/
│   ├── raw/             # Downloaded Kepler catalogs (immutable)
│   └── processed/       # Filtered/merged datasets
├── code/
│   ├── __init__.py
│   ├── main.py          # Entry point
│   ├── ingestion.py     # Data download & filtering (FR-001, FR-002)
│   ├── binning.py       # Fixed log-period binning (FR-003)
│   ├── gmm_analysis.py  # GMM fitting, bootstrap, KDE (FR-004, FR-005, FR-008)
│   ├── regression.py    # Errors-in-Variables regression & Monte Carlo test (FR-006, FR-007)
│   └── validation.py    # Synthetic data test (FR-009)
├── tests/
│   ├── unit/            # Unit tests for logic
│   └── integration/     # Pipeline integration tests
├── requirements.txt     # Pinned dependencies
└── README.md
```

**Structure Decision**: Single project structure chosen for simplicity and direct data flow from ingestion to analysis. No frontend/backend split required as this is a CLI research tool.
**Note on Contracts**: The `contracts/` directory contains JSON schemas generated from `data-model.md` during Phase 0 to ensure type safety for `data/processed/` artifacts.

## Phase Ordering & Compute Feasibility

1.  **Phase 0 (Design)**: Define `data-model.md` and generate `contracts/`. (This is the current step).
2.  **Phase 1 (Data Ingestion)**: Download Kepler DR25 and Input Catalogs. Filter to <20% radius uncertainty and <1% period uncertainty. (Must run first).
3.  **Phase 2 (Binning & Pre-processing)**: Bin by **fixed** log-period. Flag bins with <30 planets. Calculate weighted mean periods and **bin center variance**.
4.  **Phase 3 (Gap Detection)**: Fit GMM (2-component) to radius distributions. Perform a sufficient number of bootstrap resamples. **Populate `gap_uncertainty` and `gap_location_variance`** (by calculating `1 / gap_location_variance` for weights). Validate with KDE. (CPU-tractable: `scikit-learn` GMM is efficient on small subsets).
5.  **Phase 4 (Regression & Inference)**: Perform **Errors-in-Variables** regression of gap location vs. log(period) using `gap_location_variance` (as `weight = 1 / gap_location_variance`) and **bin center variance**. Include **completeness map** as a covariate. Execute **Monte Carlo Consistency Test** against theoretical distributions.
6.  **Phase 5 (Validation)**: Run synthetic data test to verify pipeline accuracy.

**Compute Feasibility Note**: The Kepler DR25 catalog is small (~few MBs). GMM fitting on a moderate number of points per bin is trivial for CPU. A sufficient number of bootstraps per bin (total ~-20 bins) is well within the 6-hour limit on a 2-core runner. No GPU required.

## Methodology & Statistical Rigor

### 1. Data Filtering (FR-002)
-   **Criteria**: `radius_uncertainty < 20%` AND `period_uncertainty < 1%`.
-   **Handling Missing Data**: Planets with missing stellar effective temperature are excluded (no imputation) to preserve data integrity.
-   **Duplicates**: Resolved by keeping the entry with the lowest radius uncertainty.
-   **Completeness Correction**: Download the Kepler completeness map. Apply it as a weight/covariate to correct for selection bias introduced by the uncertainty filter. The completeness map is used to re-weight the sample in the regression model.

### 2. Binning Strategy (FR-003)
-   **Range**: Log-period from 0.7 to 2.0 (5 to 100 days).
-   **Method**: **Fixed** log-spaced bins (no dynamic merging). Bin boundaries are defined a priori to avoid data-dependent bias.
-   **Minimum Count**: Bins with <30 planets are **retained** but flagged with `low_count=True`. Their `bimodality_weight` is set to 0 in the regression to avoid selection bias, rather than merging them.
-   **Weighting**: Regression uses the inverse variance of the gap location estimate (`weight = 1 / gap_location_variance`) as weights.

### 3. Gap Location Estimation (FR-004, FR-005)
-   **Model**: Two-component Gaussian Mixture Model (GMM).
-   **Initialization**: K-Means++ with multiple seeds; select lowest BIC.
-   **Unimodality Check**: If $\Delta \text{BIC} (2\text{-comp} - 1\text{-comp}) < 10$, the bin is considered unimodal. Instead of exclusion (which causes collider bias), `gap_location` is set to NaN and `bimodality_weight` is set to 0.
-   **Peak Separation**: Minimum separation of $\ge 0.1 R_{\oplus}$ enforced. Log `peak_separation` and `peak_separation_met`.
-   **Uncertainty**: A sufficient number of bootstrap resamples per bin to generate 95% confidence intervals and `gap_location_variance`.

### 4. Slope Calculation & Theory Comparison (FR-006, FR-007)
-   **Regression**: **Errors-in-Variables (EIV)** regression of $\log(R_{gap})$ vs $\log(P)$, accounting for uncertainty in both X (bin center variance) and Y (gap location variance). This replaces simple weighted OLS to avoid bias from measurement error in the independent variable.
-   **Completeness**: Include the Kepler completeness map as a covariate in the regression model to correct for Malmquist bias.
-   **Theoretical Comparison**: **Monte Carlo Consistency Test**. The theoretical slopes (Owen & Wu: -0.11, Ginzburg: -0.09) are treated as distributions with $\sigma = 0.05$, derived from the physical model's parameter uncertainties (stellar mass, temp, etc.). The measured slope is compared against these distributions to calculate p-values. This addresses the concern that treating theories as fixed constants inflates Type I error.

### 5. Validation (FR-008, FR-009)
-   **KDE Validation**: Adaptive bandwidth KDE on cumulative distribution. Log `kde_bandwidth` and `kde_cumulative_data_path`.
-   **Synthetic Test**: Generate synthetic data with known gap locations/slopes; verify recovery within error margins. This is the primary validation, ensuring the pipeline recovers the ground truth.

## Constitution Check (Detailed)

-   **Principle II (Verified Accuracy)**: The `Reference-Validator Agent` will run on all citations. The `research.md` will only contain URLs that pass the `title-token-overlap ≥ 0.7` check.
-   **Principle III (Data Hygiene)**: All raw data files will be checksummed (SHA-256) and recorded in `state.yaml`. Derived files will be versioned.

## References

-   **Fulton, B. J., et al. (2017)**. "The NASA Kepler Mission: The Radius Distribution of Small Planets". *AJ*, 154, 109.
-   **Owen, J. E., & Wu, Y. (2017)**. "Kepler Planets: A Tale of Evaporation". *ApJ*, 847, 29.
-   **Ginzburg, S., et al. (2018)**. "Atmospheric Mass Loss: The Core-Powered Mechanism". *MNRAS*, 479, 123.
-   **Kepler DR25**: MAST Archive (URIs: `mast:Kepler/KeplerDR25/KeplerQ1-Q17_stellar`).