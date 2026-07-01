# Implementation Plan: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

**Branch**: `001-bird-migration-climate-correlation` | **Date**: 2026-06-24 | **Spec**: [link]
**Input**: Feature specification from `specs/001-bird-migration-climate-correlation/spec.md`

## Summary

This project implements a statistical pipeline to analyze the correlation between bird migration phenology (arrival dates, stopover duration) and climate variables (temperature, precipitation) using the eBird Basic Dataset (EBD) and NOAA/PRISM climate data. 

**CI Feasibility Strategy (Critical)**: 
To ensure the pipeline runs within the Multi-core, 7GB RAM, 6-hour CI limit, the analysis is constrained to a **sampled subset** with specific safeguards:
1.  **Species Selection**: Top migratory species by observation count in North America (–2024).
2.  **Spatial Sampling**: **Tail-preserving stratified sampling** of grid cells. We do NOT use random sampling for grid cells. Instead, we stratify cells by observation density and explicitly **oversample cells with early arrival dates** (lower tail of the phenology distribution) to prevent bias in the 'first_arrival_date' metric. Target: A sufficient number of grid cells per species to ensure robust statistical power.
3.  **Temporal Sampling**: Full multi-year range retained for the selected cells.
4.  **Computational Approximation**: 
    -   **Spatial**: Unified Spatial Model (default spatial smooth) instead of conditional GP fitting to avoid data snooping.
 - **Permutation**: A reduced number of shuffles with early stopping (sequential testing) instead of [deferred].
    -   **Riemannian**: Use `geomstats` for manifold calculations on the sampled trajectories.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `geopandas`, `scikit-learn`, `requests`, `tqdm`, `geomstats`, `rpy2` (optional, fallback to `statsmodels` P-splines), `joblib`.  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/interim`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: End-to-end runtime ≤ 4 hours (buffer for 6h limit); memory usage ≤ 6 GB.  
**Constraints**: No GPU; no large language model inference; data must be sampled to fit RAM; no new constraints invented beyond spec.  
**Scale/Scope**: Analysis limited to North America (2020–2024), filtered to **Top 5 species** and **~100 grid cells per species** (tail-preserving stratified) to ensure feasibility.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Plan mandates pinned `requirements.txt`, random seeds, and versioned data directories. |
| **II. Verified Accuracy** | **Blocked** | No verified URLs for full EBD or PRISM in the source block. Plan proceeds with synthetic data fallback; final results pending verified data. |
| **III. Data Hygiene** | **Pass** | Raw data preserved; derivations written to new files; checksums required in state file. |
| **IV. Single Source of Truth** | **Pass** | Output schemas and contracts defined; all figures/statistics trace to processed data. |
| **V. Versioning Discipline** | **Pass** | Artifact hashes tracked; `updated_at` timestamps managed by state file. |
| **VI. Ecological Data Provenance** | **Blocked** | Raw eBird/NOAA files cannot be archived as they are missing. Synthetic data provenance will be recorded as a fallback. |
| **VII. Statistical Model Transparency** | **Pass** | GAMM formulae, random effects, and smoothing parameters explicitly defined in code. |

## Project Structure

### Documentation (this feature)

```text
specs/001-bird-migration-climate-correlation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Downloads and caches raw data (or generates synthetic)
│   ├── preprocess.py        # Aggregates to grid, computes metrics, handles sampling
│   └── impute.py            # Handles missing climate data
├── models/
│   ├── gamm_fit.py          # Fits GAMMs with spatial effects (statsmodels/rpy2)
│   ├── trajectory.py        # Riemannian trajectory analysis (geomstats)
│   └── utils.py             # Statistical helpers (FDR, bootstrapping, early stopping)
├── analysis/
│   └── run_pipeline.py      # Orchestrates the full workflow
├── tests/
│   ├── contract/
│   │   └── test_schemas.py
│   ├── unit/
│   │   └── test_preprocess.py
│   └── integration/
│       └── test_pipeline.py
└── requirements.txt

data/
├── raw/                     # Unmodified downloads (or synthetic)
├── processed/               # Grid-aligned, aggregated data
└── interim/                 # Intermediate calculations
```

**Structure Decision**: Single project structure selected. The pipeline is sequential (download → preprocess → model → analyze), making a monolithic `src/` structure with modular scripts appropriate. No separate backend/frontend is needed as this is a research script, not a service.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Riemannian Manifold Analysis** | Required by FR-006 and US-3 to detect non-linear spatial shifts. | Linear regression on coordinates fails to capture curved migration paths and manifold geometry inherent in global migration. |
| **Unified Spatial Model** | Required by FR-004 to handle spatial autocorrelation without data snooping. | Two-step Moran's I check invalidates p-values (scientific_soundness-9fdb232e). |
| **Tail-Preserving Sampling** | Required to avoid bias in 'first_arrival_date' (methodology-0002e18c). | Random sampling removes rare early events, biasing phenology estimates. |
| **Observer Effort Covariates** | Required to control for sampling bias (methodology-26c416ac). | Without effort covariates, climate coefficients are confounded by observer effort. |
| **CPU-Only Optimization** | Required by CI constraints (no GPU). | GPU-accelerated libraries (e.g., PyTorch with CUDA) are unavailable; must use CPU-optimized stats libraries. |

## Data Acquisition Fallback

**Constraint**: The source spec (FR-001) requires downloading the full eBird Basic Dataset and NOAA/PRISM. The "Verified Datasets" block contains **no** verified URLs for these specific full datasets.

**Fallback Strategy**:
1.  **Code Validation**: The pipeline will generate **synthetic data** conforming exactly to the `dataset.schema.yaml` contract. This allows testing of the ingestion, grid aggregation, GAMM fitting, and Riemannian trajectory logic without external dependencies.
2.  **Production Run**: If verified URLs for EBD/PRISM become available, the `download.py` script will switch to fetching real data. Until then, the project remains in a "validated but data-pending" state.
3.  **Blocking Note**: Final statistical results (phenology-climate correlations) cannot be generated until the real data is sourced. The plan explicitly flags this as a blocking dependency for the `research_complete` stage.