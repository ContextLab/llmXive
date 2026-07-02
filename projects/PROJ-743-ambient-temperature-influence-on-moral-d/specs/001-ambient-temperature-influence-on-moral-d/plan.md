# Implementation Plan: Ambient Temperature Influence on Moral Decision Speed

**Branch**: `001-ambient-temp-moral-speed` | **Date**: 2026-06-24 | **Spec**: `specs/001-ambient-temp-moral-speed/spec.md`
**Input**: Feature specification from `specs/001-ambient-temp-moral-speed/spec.md`

## Summary

This project investigates the correlation between ambient temperature and the speed of moral decision-making using the Moral Machine dataset merged with ERA5 Reanalysis temperature data. The technical approach involves: (1) ingesting and geospatially/temporally merging the datasets; (2) fitting a linear mixed-effects model (LMM) with log-transformed response times as the outcome, temperature as the primary fixed effect, and random intercepts for participant and cultural region; (3) conducting robustness checks (alternative temperature metrics, sensitivity analysis); and (4) generating diagnostic plots and statistical reports.

**CRITICAL BLOCKER**: This project is currently **BLOCKED** due to a temporal mismatch between the verified ERA5 source (1982) and the Moral Machine dataset (2016-2019). Implementation cannot proceed until a verified ERA5 source for the 2016-2019 period is added to the project's verified datasets block.

The implementation adheres to strict data hygiene (checksums, no in-place modification) and reproducibility (pinned dependencies, random seeds) as mandated by the project constitution.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels` (for mixed-effects), `scipy`, `matplotlib`, `seaborn`, `xarray`, `geopandas`, `requests`  
**Storage**: Local CSV/Parquet files in `data/` and `results/`; no external database.  
**Testing**: `pytest` for unit tests on data ingestion logic and model convergence checks.  
**Target Platform**: Linux (GitHub Actions Free Runner: 2 CPU, ~7 GB RAM, ~14 GB Disk).  
**Project Type**: Computational Research / Data Analysis Pipeline.  
**Performance Goals**: Complete full pipeline (ingestion to reporting) within 6 hours on CPU-only runner; memory usage < 6 GB.  
**Constraints**: 
- No GPU; no large-LLM inference.
- **Memory Management**: Dataset will be subsampled to 100k records (stratified) if >500k rows to ensure LMM convergence within 6 hours on 7GB RAM.
- **Data Availability**: Project halts if verified ERA5 source for 2016-2019 is not available.
- All external data sources must be verified against the "Verified datasets" block.  
**Scale/Scope**: Processing ~100k records (subsampled) and merging with hourly ERA5 data.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Note: Principles II and VI are currently BLOCKED due to data mismatch.*

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | `requirements.txt` will pin all versions. Random seeds (e.g., `np.random.seed(42)`) will be set in `code/`. External datasets fetched via stable URLs. |
| **II. Verified Accuracy** | 🔴 **Blocked** | The verified ERA source (1982) does not match the study period (2016-2019). Implementation cannot proceed until a verified 2016-2019 source is added to the verified datasets block. |
| **III. Data Hygiene** | ✅ Pass | Raw data files in `data/` will be checksummed. Transformations (merging, filtering) will write new files (e.g., `data/merged_v1.parquet`). PII scan will be run on commit. |
| **IV. Single Source of Truth** | ✅ Pass | All statistics in `results/` will be generated programmatically from `data/` and `code/`. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | ✅ Pass | Content hashes for `data/` files will be tracked. `state/` YAML will be updated upon artifact changes. |
| **VI. Dataset Alignment Integrity** | 🔴 **Blocked** | The temporal mismatch between ERA5 (1982) and Moral Machine (2016+) prevents alignment. The ingestion script will log this as a fatal error if the correct data is not found. |
| **VII. Statistical Modeling Transparency** | ⚠️ **Conditional** | Model specifications and diagnostics will be saved, but the model cannot be fitted until the data gap is resolved. |

## Project Structure

### Documentation (this feature)

```text
specs/001-ambient-temp-moral-speed/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-743-ambient-temperature-influence-on-moral-d/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── ingest.py           # Data ingestion, merging, filtering, validation
│   ├── model.py            # Mixed-effects modeling, diagnostics, autocorrelation checks
│   ├── robustness.py       # Sensitivity analysis, alternative metrics
│   └── utils.py            # Helper functions (geo matching, logging, derivation)
├── data/
│   ├── raw/                # Downloaded raw files (checksummed)
│   │   ├── moral_machine.csv
│   │   └── era5_2016_2019.h5  # (Required: verified source for 2016-2019)
│   └── processed/          # Derived datasets (merged, cleaned)
│       └── merged_analysis.parquet
├── results/
│   ├── figures/            # Diagnostic plots, effect plots
│   ├── stats/              # Model summaries, p-values
│   └── logs/               # Data quality logs, exclusion reasons
└── tests/
    ├── test_ingest.py
    └── test_model.py
```

**Structure Decision**: Single project structure (Option 1) is selected. The project is a linear data analysis pipeline (Ingest -> Model -> Report) rather than a service or multi-component app. This minimizes overhead and fits the GitHub Actions runner constraints.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Mixed-Effects Modeling** | Required to account for non-independence of observations (multiple responses per participant) and hierarchical structure (cultural regions). | Simple OLS regression would violate independence assumptions, leading to inflated Type I errors. |
| **ERA5 Geospatial Merge** | Required to link ambient temperature to specific decision locations. | Using national average temperatures would introduce significant ecological fallacy and ignore local micro-climates. |
| **Robustness Analysis Suite** | Required to validate findings against data processing artifacts (outliers, indoor/outdoor confound). | A single model run cannot rule out that results are driven by specific data choices or unmeasured confounds. |
| **Subsampling Strategy** | Required to fit LMM on 7GB RAM within 6 hours on 2 CPU cores. | Full dataset (large-scale) would likely exceed memory or timeout limits without aggressive sampling. |

## Phase Breakdown

### Phase 0: Data Availability & Validation (FR-014)
- **Task**: Verify that a source for ERA5 data covering 2016-2019 exists in the "Verified datasets" block.
- **Action**: If no verified source exists, halt and report "Fatal Data Gap".
- **Action**: If source exists, download and checksum.
- **Action**: Validate Moral Machine source against verified block.
- **Output**: `results/logs/data_validation_log.txt` (Pass/Fail status).

### Phase 1: Ingestion & Merging (FR-001, FR-002, FR-009, FR-010)
- **Task**: Load Moral Machine data.
- **Task**: Load ERA5 data (handle HDF5 structure).
- **Task**: Filter responses: `response_time < 100` or `> 10000` (FR-010).
- **Task**: Filter responses: `temperature < -50` or `> 60` (FR-002).
- **Task**: Geospatial match: Find nearest ERA5 grid. Exclude if distance > 100km (FR-009).
- **Task**: Temporal match: Interpolate if gap <= 2 hours; exclude if > 2 hours.
- **Task**: Derive `dilemma_complexity` from static attributes (lives, species) only (avoiding circularity).
- **Task**: Derive `age` and `gender` if available (FR-004).
- **Output**: `data/processed/merged_analysis.parquet`, `results/logs/exclusion_log.csv`.

### Phase 2: Statistical Modeling (FR-003, FR-004, FR-005, FR-011, FR-013)
- **Task**: Fit LMM: `log(response_time) ~ temperature + temperature^2 + dilemma_complexity + time_of_day + choice_type + (1|participant_id) + (1|cultural_region)`.
- **Task**: Test for temporal autocorrelation (AR(1) or cluster-robust SEs) (Scientific Soundness concern).
- **Task**: If LMM fails to converge, fallback to GLMM with log-link or fixed-effects only.
- **Task**: Perform Likelihood-Ratio Test (LRT) vs. null model (FR-005).
- **Task**: Run Anderson-Darling test on residuals (SC-005).
- **Output**: `results/stats/model_summary.json`, `results/figures/diagnostics.png`.

### Phase 3: Robustness & Sensitivity (FR-006, FR-012)
- **Task**: Sensitivity analysis: Sweep temperature outlier thresholds (2SD, 3SD, 4SD) (FR-006).
- **Task**: Alternative metric: 3-hour moving average temperature.
- **Task**: Indoor/Outdoor: Stratify by urban/rural if possible; otherwise, report as limitation and quantify noise (FR-012).
- **Output**: `results/stats/robustness_table.csv`, `results/figures/sensitivity_plots.png`.

### Phase 4: Reporting (FR-008)
- **Task**: Export all results to `results/`.
- **Output**: Final reports and figures.

## Risk Management

- **Risk**: LMM fails to converge on full dataset.
  - **Mitigation**: Pre-emptive stratified subsampling to 100k records.
- **Risk**: ERA5 data unavailable for 2016-2019.
  - **Mitigation**: Project blocked until verified source is added.
- **Risk**: Indoor/Outdoor confound unresolvable.
  - **Mitigation**: Explicitly report as limitation; do not claim causal control.