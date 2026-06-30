# Implementation Plan: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

**Branch**: `feature-001-geomagnetic-correlation` | **Date**: 2026-06-24 | **Spec**: `specs/feature-001-geomagnetic-correlation/spec.md`

## Summary

This feature implements a reproducible, CPU-tractable pipeline to quantify the associational relationships between solar wind composition (proton density, temperature, helium abundance) and geomagnetic indices (Kp, Dst). The pipeline downloads real ACE/OMNI and NOAA data, aligns them to a 1-hour UTC grid, computes lagged correlations (0–6h) with autocorrelation-adjusted p-values, applies Bonferroni correction, and validates results on a held-out period. The analysis is strictly observational and designed to run within GitHub Actions free-tier constraints (limited CPU, 7 GB RAM, 6h runtime).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `matplotlib`, `requests`, `pyyaml`  
**Storage**: Local CSV/JSON/Parquet files under `data/` and `artifacts/`  
**Testing**: `pytest` (unit tests for data alignment, correlation logic; integration test for full pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data analysis CLI / Research pipeline  
**Performance Goals**: Full 20-year analysis ≤ 6 hours; Data sync ≤ 30 minutes; RAM ≤ 7 GB.  
**Constraints**: No GPU; No external API keys required (public data); Linear interpolation max gap h.  
**Scale/Scope**: [deferred] hourly records (20 years); correlation tests per lag window.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ PASS | All scripts pinned to `requirements.txt`; random seeds fixed; data fetched from canonical verified URLs (OMNI2); checksums recorded in `state/`. |
| **II. Verified Accuracy** | ✅ PASS | Dataset URLs cited only from the `# Verified datasets` block (OMNI2); no hallucinated sources. |
| **III. Data Hygiene** | ✅ PASS | Raw data preserved in `data/raw/`; derivatives in `data/processed/`; no in-place modification; PII scan passed (no PII in solar data). |
| **IV. Single Source of Truth** | ✅ PASS | All figures/stats generated programmatically from `data/processed/synced.csv`; no hand-typed values. |
| **V. Versioning Discipline** | ✅ PASS | Artifact hashes updated in `state/` upon data/code changes. |
| **VI. Temporal Alignment** | ✅ PASS | Explicit 1-hour UTC grid alignment; lag consistency enforced in `code/services/correlation.py`. |
| **VII. Statistical Rigor** | ✅ PASS | Bonferroni correction and effective sample size (Neff) calculation implemented as per FR-003/FR-010 on the full continuous time series. |

## Project Structure

### Documentation (this feature)

```text
specs/feature-001-geomagnetic-correlation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Entry point for CLI
├── config.py            # Constants, paths, seeds
├── data/
│   ├── __init__.py
│   └── fetch.py         # Downloaders for ACE/OMNI2 and NOAA
├── services/
│   ├── __init__.py
│   ├── align.py         # Resampling, interpolation, gap handling
│   ├── correlation.py   # Pearson/Spearman, Neff, Bonferroni
│   └── viz.py           # Plot generation
├── validation/
│   └── report.py        # Validation logic for US-3
└── tests/
    ├── test_align.py
    ├── test_correlation.py
    └── test_pipeline.py
```

**Structure Decision**: Single-project Python CLI structure. Separated into `data` (I/O), `services` (logic), and `tests` to ensure modularity and testability. No external database; file-based storage aligns with CI constraints.

## Phase Breakdown (Computational Ordering)

1.  **Phase 0: Data Acquisition & Validation** (FR-001, FR-006)
    *   Download raw ACE/OMNI2 (SWEPAM/SWICS) and NOAA (Kp/Dst) data from verified sources (OMNI2 dataset).
    *   **Strict Variable Verification**: Check that the downloaded ACE/OMNI2 file contains **exactly** the required variable names: `N_p` (proton density), `T_p` (temperature), `He2+_ratio` (helium abundance).
    *   **Abort Condition**: If any of these specific variable names are missing, the pipeline MUST abort with a clear error message (SC-002).
    *   *Output*: `data/raw/ace_raw.csv`, `data/raw/noaa_raw.csv`.
2.  **Phase 1: Synchronization & Cleaning** (FR-002, US-1)
    *   Merge to 1-hour UTC grid.
    *   Linear interpolation for gaps ≤ 6h; log warnings for larger gaps.
    *   *Output*: `data/processed/synced.csv`.
3.  **Phase 2: Correlation Analysis** (FR-003, FR-004, FR-010, US-2)
    *   **Full Series Constraint**: Calculate effective sample size ($N_{eff}$) using the lag-1 autocorrelation ($\rho_1$) of the **full continuous time series** (1998–2020) for each variable, as per FR-010 and Pyper & Peterman ().
    *   Compute Pearson/Spearman for selected lags on the full series.
    *   Apply Bonferroni correction ($\alpha_{adj} = 0.05 / 30$) using the $N_{eff}$ derived from the full series.
    *   *Output*: `data/processed/correlation_results.csv`.
4.  **Phase 3: Validation & Visualization** (FR-008, FR-009, US-3)
    *   Split data: Train (early period), Test (–2020).
    *   **Replication Test**: Calculate correlation coefficients for the Test set. Compare these coefficients against the **global** significance threshold (derived in Phase 2 from the full series) and the pre-registered effect size (|r| > 0.5).
    *   Generate heatmaps and time-series overlays.
    *   Generate Markdown validation report explicitly stating that the significance threshold is global.
    *   *Output*: `artifacts/figures/*.png`, `artifacts/reports/validation.md`.

