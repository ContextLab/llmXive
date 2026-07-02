# Implementation Plan: Quantifying Spatial Correlations in Perovskite Solar Cell Efficiency

**Branch**: `001-quantify-spatial-correlations` | **Date**: 2024-05-21 | **Spec**: [link]
**Input**: Feature specification from `specs/001-quantify-spatial-correlations/spec.md`

## Summary

This project implements a reproducible Python pipeline to quantify the impact of spatial correlations in perovskite solar cell (PSC) efficiency. The technical approach involves downloading elemental maps (Pb, I, MA) and performance metrics (PCE, J_sc, V_oc), computing 2-D autocorrelation and Fourier spectral metrics, and performing statistical modeling (Pearson/Spearman correlation, GAM, Benjamini-Hochberg correction) to test the hypothesis that spatial ordering correlates with efficiency. The implementation is constrained to run on free-tier GitHub Actions (CPU-only, limited RAM).

**Critical Constraint**: This project is **blocked** until a verified, programmatic source for EDS elemental maps is identified. If no verified source exists, the project will halt at the Data Feasibility Check and produce a "Data Availability Report" instead of a statistical analysis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `scikit-learn`, `pandas`, `hyperSpy` (CPU mode), `pyyaml`, `matplotlib`, `statsmodels`, `pygam`  
**Storage**: Local file system (`data/raw/`, `data/processed/`), CSV/JSON outputs  
**Testing**: `pytest` (unit tests for metric extraction, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions Free Tier)  
**Project Type**: Data Analysis Pipeline / Research Tool  
**Performance Goals**: Complete full pipeline (ingestion to report) within 6 hours on 2 vCPU, <7GB RAM.  
**Constraints**: No GPU/CUDA; no large model training; dataset size limited to fit RAM; all random seeds pinned.  
**Scale/Scope**: Processing of available public PSC datasets (estimated <200 samples for initial run).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|-----------------------|
| **I. Reproducibility** | **Compliant** | `requirements.txt` pins all versions; random seeds fixed in `code/modeling/`; data checksums recorded in `state/`. |
| **II. Verified Accuracy** | **Non-Compliant (EDS Maps)** | No verified URL for EDS maps exists. Project halts if source not found. |
| **III. Data Hygiene** | **Compliant** | Raw data stored in `data/raw/` unchanged; derived data in `data/processed/` with checksums; no PII expected. |
| **IV. Single Source of Truth** | **Compliant** | Final report CSV/PDF generated directly from `code/modeling/` outputs; no manual transcription. |
| **V. Versioning Discipline** | **Compliant** | Artifacts hashed; `state` updated on change via `code/utils/update_state.py`; `code/` scripts versioned. |
| **VI. Spatial Characterization Consistency** | **Compliant** | Raw EDS maps preserved; preprocessing via `code/preprocess/` logs parameters; derived maps linked to raw. |
| **VII. Statistical Modeling Transparency** | **Compliant** | `code/modeling/` explicitly logs method, r, p-value, CI, and CV strategy; results map 1:1 to CSV. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-spatial-correlations/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-204-quantifying-the-impact-of-spatial-correl/
├── code/
│   ├── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── update_state.py   # Updates state YAML with artifact hashes
│   ├── data/
│   │   ├── __init__.py
│   │   ├── download.py       # FR-001: Download from verified sources
│   │   └── align.py          # FR-001: Align to common grid, mask defects
│   ├── preprocess/           # VI: Preprocessing scripts
│   │   ├── __init__.py
│   │   └── calibrate.py      # Calibration and masking logic
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── spatial_metrics.py # FR-002, FR-003: Autocorr, Fourier, decay fits
│   │   └── robustness.py     # FR-005: LOO-CV
│   ├── modeling/
│   │   ├── __init__.py
│   │   ├── correlation.py    # FR-004: Pearson, Spearman, BH correction
│   │   └── gam.py            # FR-004: GAM for non-linearity
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── co_location.py    # FR-007: Co-location validation
│   │   └── depth_check.py    # FR-008: Depth resolution validation
│   └── report/
│       ├── __init__.py
│       └── generate.py       # FR-006: CSV/PDF generation
├── data/
│   ├── raw/                  # Unmodified downloads
│   └── processed/            # Aligned, masked, derived metrics
├── tests/
│   ├── unit/
│   │   └── test_spatial_metrics.py # Synthetic test for SC-001
│   └── integration/
│       └── test_pipeline.py
├── data/contracts/           # Schema definitions
├── requirements.txt
└── README.md
└── code/main_pipeline.py     # Main entry point
```

**Structure Decision**: A modular monolithic structure (`code/data`, `code/preprocess`, `code/analysis`, `code/modeling`) is selected to facilitate the linear pipeline flow (Download -> Process -> Analyze -> Report) while keeping unit testing isolated. This aligns with the "Data Hygiene" and "Reproducibility" principles by ensuring clear separation of raw vs. processed data and distinct analysis stages.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **GAM Implementation** | Required by FR-004 to detect non-linear relationships as per Assumptions. | Simple linear regression only would miss potential non-monotonic effects of spatial ordering on PCE. |
| **Benjamini-Hochberg Correction** | Required by FR-004 to control FDR across multiple elemental tests (Pb, I, MA). | Uncorrected p-values would inflate Type I error rates in a multi-hypothesis context. |
| **HyperSpy Integration** | Required for robust EDS map handling and preprocessing (VI). | `scipy` alone lacks native support for complex EDS metadata and spectral unmixing if needed later. |
| **Multivariate Analysis** | Required to address chemical coupling of Pb, I, MA (scientific_soundness-fa22ca9f). | Testing elements independently leads to spurious inference due to mass balance constraints. |

## Computational Task Ordering

1.  **Data Feasibility Check**: Verify programmatic link between metadata and EDS images. If failed, terminate and report "Data Availability Report".
2.  **Data Ingestion**: Download verified JSONs, attempt EDS fetch, align grids, mask defects (FR-001).
3.  **Co-location Validation**: Verify EDS and PCE originate from same device with unique ID (FR-007).
4.  **Depth Resolution Validation**: Check EDS depth vs PCE active layer depth (FR-008).
5.  **Spatial Metric Extraction**: Compute autocorrelation, fit decay models, calculate spectral power (FR-002, FR-003).
6.  **Statistical Modeling**: Calculate correlations, apply BH correction, fit GAMs, perform partial correlation (FR-004).
7.  **Robustness**: Perform LOO-CV (FR-005).
8.  **Sensitivity Analysis & Conditional Exclusion**: Exclude samples based on sensitivity thresholds (FR-008).
9.  **Reporting**: Generate CSV/PDF with ingestion success rate (SC-004) and power limitation report.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **EDS Data Unavailability** | High: No data to analyze. | FR-001: Exclude samples with missing EDS; report exclusion rate; halt if no verified source. |
| **Low Sample Count (<30)** | High: Low statistical power. | Report power limitation explicitly; avoid over-interpreting non-significant results; calculate MDES. |
| **Correlation Length Undefined** | Medium: Missing predictor. | FR-002: Flag as "undefined"; exclude from regression or use lower bound for censored analysis. |
| **Confounding (Surface vs Bulk)** | Medium: Spurious correlations. | FR-008: Flag samples; perform sensitivity analysis excluding flagged samples; use depth-corrected metrics if available. |
| **Chemical Coupling** | High: Spurious inference. | Use composite spatial metrics or partial correlation; acknowledge inability to claim independent effects. |

## Power Analysis & Feasibility

- **Minimum Detectable Effect Size (MDES)**: For N=30, 80% power, α=0.05, MDES ≈ r=0.35.
- **Action**: If expected effect size < 0.35, the study is underpowered. The plan will explicitly report this limitation as a primary finding.
- **Data Feasibility**: If no verified source for EDS maps is found, the project halts and produces a "Data Availability Report" instead of a statistical analysis.