# Implementation Plan: Characterization of Exoplanetary Atmospheres through Advanced Spectroscopic Techniques

**Branch**: `001-characterization-of-exoplanetary-atmosph` | **Date**: 2026-06-26 | **Spec**: `specs/001-characterization-of-exoplanetary-atmosph/spec.md`
**Input**: Feature specification from `/specs/001-characterization-of-exoplanetary-atmosph/spec.md`

## Summary

This project implements a reproducible pipeline to characterize exoplanetary atmospheres by correlating water vapor abundances with equilibrium temperatures for hot Jupiters and temperate super-Earths. The technical approach involves downloading transmission spectra from the NASA Exoplanet Archive, processing them with `petitRADTRANS` in CPU-optimized mode to derive water mixing ratios (handling censored data via instrument noise floors), and performing statistical analysis (Akritas-Theil-Sen correlation, Tobit regression with Ridge fallback) using Python libraries compatible with CPU-only GitHub Actions runners.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `petitRADTRANS` (CPU-optimized), `astropy`, `numpy`, `pandas`, `scikit-learn`, `statsmodels`, `scipy`, `requests`, `tqdm`, `lifelines` (for censored stats), `synphot` (for synthetic validation)
**Storage**: Local file system (`data/raw`, `data/processed`), CSV for metadata, YAML for configuration.
**Testing**: `pytest` (unit tests for data parsing, integration tests for pipeline stages, contract tests against YAML schemas), synthetic data validation tests.
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, adequate RAM, no GPU).
**Project Type**: Computational research pipeline / CLI.
**Performance Goals**: Complete full pipeline (download, retrieval, analysis) within 6 hours; memory usage < 6 GB at peak.
**Constraints**: No GPU acceleration; `petitRADTRANS` must run in single-threaded or limited multi-threaded CPU mode; all data must be fetched programmatically on every run (no static data commits).
**Scale/Scope**: Target sample size of a diverse cohort of planets, including Hot Jupiters and Super-Earths.; processing time per planet [deferred].

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **COMPLIANT** | Random seeds pinned in `code/analysis.py`. `petitRADTRANS` and `astropy` versions pinned in `requirements.txt`. Data fetched from NASA Exoplanet Archive API on every run. |
| **II. Verified Accuracy** | **COMPLIANT** | All citations in `research.md` will be validated against the `# Verified datasets` block by the Reference-Validator Agent before any review point is awarded. |
| **III. Data Hygiene** | **COMPLIANT** | Raw data preserved in `data/raw/` with checksums. Derived data written to `data/processed/`. No in-place modifications. |
| **IV. Single Source of Truth** | **COMPLIANT** | All figures and statistics in the final report will be generated directly from `data/processed/` via scripts in `code/`. No hand-typed numbers in the paper. |
| **V. Versioning Discipline** | **COMPLIANT** | Content hashes recorded in `state/`. The Advancement-Evaluator Agent invalidates stale review records when artifacts change. `updated_at` timestamps managed by the Advancement-Evaluator Agent. |
| **VI. Computational Resource Discipline** | **COMPLIANT** | `petitRADTRANS` configured for CPU-only. `statsmodels` used for Tobit regression (CPU-native). Data subsets to fit GB RAM. |
| **VII. Comparative Pipeline Uniformity** | **COMPLIANT** | Single retrieval configuration file applied to all planets; no category-specific parameter tuning that would introduce bias. |

## Project Structure

### Documentation (this feature)

```text
specs/001-characterization-of-exoplanetary-atmosph/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── retrieval.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-554-characterization-of-exoplanetary-atmosph/
├── code/
│   ├── __init__.py
│   ├── config.py              # Configuration loading (paths, seeds)
│   ├── download.py            # NASA Exoplanet Archive API client
│   ├── retrieval.py           # petitRADTRANS wrapper (CPU mode)
│   ├── analysis.py            # Akritas-Theil-Sen, Tobit regression, bootstrapping
│   ├── utils.py               # Logging, error handling, censored data helpers
│   ├── validation.py          # Synthetic data generation for censoring validation
│   └── main.py                # Pipeline orchestrator
├── data/
│   ├── raw/                   # Downloaded spectra (auto-generated)
│   └── processed/             # Retrieved abundances, metadata CSV
├── tests/
│   ├── unit/
│   │   ├── test_download.py
│   │   ├── test_retrieval.py
│   │   └── test_analysis.py
│   └── contract/
│       └── test_schemas.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen to maintain tight coupling between data acquisition, retrieval, and analysis, ensuring reproducibility and minimizing I/O overhead on the limited runner environment.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Censored Data Handling** | Essential for low S/N spectra (US-2). | Ignoring censored data or using simple imputation would introduce bias and violate FR-002. |
| **Tobit Regression** | Required for valid inference on censored outcomes (FR-005). | OLS regression would yield biased coefficients for censored data. |
| **Bootstrapping** | Required for robust CI estimation (FR-004). | Asymptotic normality assumptions are unreliable for small N (approximately three to five dozen) and censored data. |
| **Akritas-Theil-Sen** | Required for valid correlation with censored data (FR-003). | Standard Kendall's tau treats upper limits as exact values, biasing the result. |
| **Ridge Regression Fallback** | Required to handle collinearity between mass and metallicity. | Standard Tobit yields unstable coefficients if VIF > 5. |
| **Synthetic Validation** | Required to verify that 'upper limit' flags reflect physical noise floors, not retrieval artifacts. | Without validation, the censoring logic could be biased by model failure modes. |
| **Retrieval Degeneracy Check** | Required to quantify uncertainty due to retrieval model assumptions. | Using a single cloud model would treat model-dependent results as ground truth. |