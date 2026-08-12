# Implementation Plan: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

**Branch**: `001-bird-migration-climate-correlation` | **Date**: 2024-05-21 | **Spec**: `specs/001-bird-migration-climate-correlation/spec.md`
**Input**: Feature specification from `/specs/001-bird-migration-climate-correlation/spec.md`

## Summary

This project implements a reproducible statistical pipeline to analyze the correlation between bird migration phenology (arrival dates, stopover duration) and climate variables (temperature, precipitation) using the eBird Basic Dataset (EBD) and Daymet climate data. The core analytical engine utilizes Generalized Additive Mixed Models (GAMMs) with species-specific random slopes for temperature and a **mandatory a priori** Gaussian Process (GP) random effect for spatial autocorrelation. The pipeline prioritizes CPU-tractable methods (streaming large datasets, block bootstrapping for uncertainty) while maintaining statistical rigor through FDR correction and explicit power analysis.

**Critical Data Scope Note**: The project utilizes the verified `vvud/eb-data` sample and `Daymet` climate data (recent years). The full -2024 continental eBird archive is not available via the verified open-source URLs provided. The analysis is explicitly scoped to the available verified data, and success criteria include transparent reporting of power limitations if the sample size is insufficient to detect small effect sizes. FR-001 is interpreted as downloading the full *available* verified dataset for the period, not the entire continental archive.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `polars` (for efficient streaming), `scikit-learn`, `pygam` (or `statsmodels` with `patsy`), `geopy`, `scipy`, `numpy`, `matplotlib`, `seaborn`, `filelock`, `datasets` (from Hugging Face).  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/provenance`) with checksums; no database required for this CI-run analysis.  
**Testing**: `pytest` with fixtures for synthetic data validation.  
**Target Platform**: GitHub Actions Free Tier (CPU, limited RAM) with automatic offload to Kaggle GPU for heavy GAMM/Manifold steps if CPU fails.  
**Project Type**: Data Science Pipeline / Statistical Analysis  
**Performance Goals**: Pipeline completion within 6 hours on CPU; GAMM convergence < 600s per species; Block Bootstrap < 1800s.  
**Constraints**: No local GPU; memory < 7 GB (requires streaming/chunking); no external authentication (public datasets only).  
**Scale/Scope**: Sampled eBird data (-2024 subset), filtered to migratory species in North America; grid resolution of moderate spatial scale.

### Data Access Strategy
- **eBird**: Streamed using the `datasets` library (`load_dataset(..., streaming=True)`) from the verified HuggingFace URL. This ensures consistent caching and versioning.
- **Daymet**: Loaded via `datasets.load_dataset('daymet/annual', ...)` or verified multi-year parquet stream covering recent years.
- **Locking**: The `filelock` library is used to create `data/.pipeline.lock` to serialize access to shared data directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan mandates `random_seed` pinning in `config.py` and strict versioned data directories. All scripts are runnable end-to-end.
- **II. Verified Accuracy**: **Explicitly Mapped**. A pre-run validation step checks the integrity (checksum) and reachability of all dataset URLs against the "Verified Accuracy" gate before processing begins.
- **III. Data Hygiene**: Plan includes checksumming raw downloads and logging derivation steps in `data/provenance/row_mapping.json`. No in-place modification.
- **IV. Single Source of Truth**: All figures and stats trace to `data/processed` CSVs and `code/` scripts. No hand-typed numbers.
- **V. Versioning**: **Explicitly Mapped**. A dedicated "Phase 0.5: State Synchronization" step generates and updates `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml` with artifact hashes after every major step.
- **VI. Ecological Data Provenance**: Raw eBird/Daymet files stored in `data/raw` with metadata; filtering logic recorded in `data/provenance/row_mapping.json` which links processed rows back to original `checklist_id`s.
- **VII. Statistical Model Transparency**: GAMM formulae, random effects (including species-specific temperature slopes), and smoothing parameters explicitly defined in `code/models/gamm.py` with pinned versions. GP included a priori.

## Project Structure

### Documentation (this feature)

```text
specs/001-bird-migration-climate-correlation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── config.py            # Central config, seeds, paths, locks
├── data/
│   ├── download.py      # Data acquisition (HuggingFace/Daymet)
│   ├── preprocess.py    # Filtering, grid aggregation, phenology calc
│   └── stream_utils.py  # Chunked loading for memory constraints
├── models/
│   ├── gamm.py          # GAMM fitting, diagnostics, convergence checks
│   └── manifold.py      # Discrete Centroid Trajectory Analysis (S2)
├── analysis/
│   ├── correlation.py   # FDR correction, effect size stability
│   └── routes.py        # Route shift detection, block bootstrapping
├── utils/
│   ├── locks.py         # File-based locking implementation (filelock)
│   └── logging.py       # Runtime logs, error handling
└── cli/
    └── run_pipeline.py  # Entry point for CI execution

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Single-project structure (`src/`) chosen for simplicity and direct integration with the CI runner. No microservices or complex frontend required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Discrete Centroid Trajectory Analysis | Required by FR-006 and US-3 to detect spatial route shifts. Continuous manifold statistics (Fréchet means) are invalid for sparse grid data. | Linear regression on lat/lon fails to capture spherical geometry and great-circle distances, leading to biased shift vectors. |
| File-based Locking (`filelock`) | Required by T045/T046 to serialize parallel tasks (if any) and prevent race conditions in shared `data/` writes. | Simple file writes without locking risk corruption if the pipeline is re-triggered or if multiple processes access the same intermediate files. |
| Streaming Data Loading | Required by T051 to handle datasets exceeding 7 GB RAM on the CI runner. | Loading full EBD/NOAA datasets into memory would cause OOM crashes on the -core/7GB runner. |
| Block Bootstrap | Required by T054 to preserve temporal autocorrelation in trajectory analysis. | Simple permutation destroys the temporal structure of migration routes, leading to invalid p-values. |

## Phase Breakdown

### Phase 0: Validation & Synchronization
- **0.1**: Pre-run validation of dataset URLs and checksums (Constitution Principle II).
- **0.2**: Download raw data to `data/raw/` with checksumming.
- **0.3**: **State Synchronization**: Generate/update `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml` with raw data hashes.

### Phase 1: Preprocessing
- **1.1**: Stream eBird data, filter for migratory species (recent years), aggregate to a fine-resolution grid.
- **1.2**: Compute phenology metrics (th-90th percentile for stopover, median for arrival).
- **1.3**: Join with Daymet climate data (recent stream).
- **1.4**: **Provenance Generation**: Create `data/provenance/row_mapping.json` linking processed rows to original `checklist_id`s.
- **1.5**: **State Synchronization**: Update state file with processed data hashes.

### Phase 2: Modeling
- **2.1**: Fit GAMMs with species-specific random slopes for temperature and **a priori** GP random effect (Matérn).
- **2.2**: Post-hoc Moran's I diagnostic on residuals (validation only, no model selection).
- **2.3**: Apply FDR correction to p-values.
- **2.4**: **State Synchronization**: Update state file with model result hashes.

### Phase 3: Route Analysis
- **3.1**: Compute migration centroids on S² (Discrete method).
- **3.2**: Perform Block Bootstrap (block size weeks) for uncertainty quantification.
- **3.3**: Generate shift vectors (mean displacement) and p-values.
- **3.4**: **State Synchronization**: Update state file with trajectory result hashes.

### Phase 4: Reporting
- **4.1**: Calculate success metrics (SC-001 to SC-005) with fallback criteria.
- **4.2**: Generate final report and figures.

## Success Criteria & Fallbacks

- **SC-001 (Power)**: Measured against total species. **Fallback**: If underpowered, report MDES and state "Study underpowered to detect effects < X".
- **SC-002 (Data Coverage)**: Target ≥95% cells with sufficient data. **Fallback**: If <95%, report the actual proportion and the resulting power loss.
- **SC-003 (Convergence)**: Target ≥90% convergence. **Fallback**: If <90%, report the convergence rate and diagnostic summary of failures.
- **SC-004 (CI Width)**: Target ≤7 days. **Fallback**: If >7 days, report actual width and MDES.
- **SC-005 (Runtime)**: Must complete within 6 hours. **Fallback**: If exceeded, report the step that failed and the estimated time.

