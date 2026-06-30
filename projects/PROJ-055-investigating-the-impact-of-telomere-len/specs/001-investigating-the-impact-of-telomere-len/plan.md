# Implementation Plan: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

**Branch**: `001-telomere-lifespan-impact` | **Date**: 2026-06-24 | **Spec**: `specs/001-telomere-lifespan-impact/spec.md`
**Input**: Feature specification from `/specs/001-telomere-lifespan-impact/spec.md`

## Summary

This project implements a reproducible statistical pipeline to investigate the association between early-life telomere length and maximum lifespan in wild bird populations. The approach involves aggregating telomere data from Dryad and ecological covariates (migration, body mass) from AnAge, merging them by species, and fitting a Phylogenetic Generalized Least Squares (PGLS) model to account for evolutionary non-independence. The pipeline includes robust data cleaning, unit standardization, sensitivity analysis (LOOCV/jackknife), and visualization of results. All steps are designed to run within the constraints of a GitHub Actions free-tier runner (CPU-only, limited RAM).

**Critical Methodological Note**: The analysis is a **species-level meta-analysis**. The unit of analysis is the species (N = number of species), not the individual. Telomere length is aggregated to the species mean (filtered for early-life measurements only) and regressed against species-level maximum lifespan. Power is limited by the number of species (target >15), not the number of individuals.

## Technical Context

**Language/Version**: Python 3.11 (orchestrator) + R 4.3 (statistical engine).
**Primary Dependencies**:
- **Python**: `pandas`, `requests`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `rpy2`, `rotl` (R wrapper), `sha256` utilities.
- **R**: `lme4`, `phylolm`, `ape`, `rotl`, `caper`.
**Storage**: Local filesystem (`data/`, `results/`, `state/`). No external database.
**Testing**: `pytest` (unit tests for data cleaning, integration tests for pipeline flow).
**Target Platform**: Linux (GitHub Actions Free Runner).
**Project Type**: Computational Research / Data Analysis Pipeline.
**Performance Goals**: Complete data ingestion, cleaning, modeling, and plotting within 6 hours on 2 vCPU/7GB RAM. Memory usage < 6 GB.
**Constraints**: No GPU. No deep learning. PGLS implementation MUST use R (`phylolm`/`lme4`) via `rpy2` to satisfy Constitution Principle VII. The `phylolm` package is selected specifically for its ability to iteratively estimate Pagel's lambda, ensuring the phylogenetic covariance structure is derived from the data rather than assumed.
**Scale/Scope**: Meta-analysis of bird species (target >15 species, potentially up to 500 individuals contributing to species means).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Verification Notes |
|-----------|--------|-------------------|
| I. Reproducibility | **PASS** | Plan mandates pinned `requirements.txt` (Python) and `renv.lock` (R), random seeds, and deterministic data fetching. |
| II. Verified Accuracy | **PASS** | Plan requires citing only verified dataset URLs (Dryad/AnAge sources) and logging provenance. No fabricated URLs. |
| III. Data Hygiene | **PASS** | Plan includes checksumming raw data, preserving raw files, and creating versioned derivation files. |
| IV. Single Source of Truth | **PASS** | All figures/statistics will be generated programmatically from `data/` and `code/`. No hand-typed numbers. |
| V. Versioning Discipline | **PASS** | Artifacts will carry content hashes; state updates triggered by artifact changes via `utils.py`. |
| VI. Ecological Data Integration | **PASS** | Covariates (migration, body mass) will be sourced strictly from AnAge/BirdLife as per spec. Provenance fields added. |
| VII. Statistical Modeling Transparency | **PASS** | Models will be defined and executed in R (`lme4`, `phylolm`) via `rpy2`, satisfying the constitutional mandate for R tooling. Model formulas recorded in script headers. |

## Project Structure

### Documentation (this feature)

```text
specs/001-telomere-lifespan-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── model_output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-055-investigating-the-impact-of-telomere-len/
├── data/
│   ├── raw/             # Downloaded raw CSVs from Dryad/AnAge
│   ├── processed/       # Merged, cleaned, unit-standardized data
│   └── phylogeny/       # Bird phylogenetic tree (Newick format)
├── code/
│   ├── requirements.txt
│   ├── R/               # R scripts for modeling
│   │   ├── 01_fit_pglS.R
│   │   └── 02_sensitivity.R
│   ├── 01_discover_data.py      # Phase 0: Identify Dryad/AnAge IDs
│   ├── 02_ingest_data.py        # FR-001: Download and parse
│   ├── 03_clean_merge.py        # FR-002, FR-003: Standardize units, merge
│   ├── 04_model_pglS.py         # FR-004, FR-005: Call R scripts for PGLS
│   ├── 05_visualize.py          # FR-007: Forest plot, scatter plot
│   ├── utils.py                 # Shared helpers (logging, checksum, state update)
│   └── run_pipeline.sh          # Orchestration script
├── results/
│   ├── association_forest.png
│   ├── moderator_plot.png
│   ├── model_summary.csv
│   └── sensitivity_log.csv
├── logs/
│   ├── missing_data_log.csv
│   └── unconvertible_units.csv
├── contracts/             # Explicitly included for artifact validation
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tests/
    ├── test_ingest.py
    ├── test_clean.py
    └── test_model.py
```

**Structure Decision**: Single project structure chosen to maintain tight coupling between data ingestion, modeling, and visualization. The separation of `raw` and `processed` data ensures Data Hygiene (Principle III). R scripts are isolated in `code/R/` to satisfy Constitution Principle VII. The `contracts/` directory is included in the root to ensure schemas are treated as executable validation targets.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| R (phylolm/lme4) via rpy2 | Required by Constitution Principle VII (Statistical Modeling Transparency) which mandates R/lme4. Python-only PGLS (statsmodels) is invalid for this project because it cannot iteratively estimate Pagel's lambda without a pre-computed, fixed covariance matrix. | Python-only `statsmodels` PGLS does not meet the constitutional requirement for R tooling and lacks iterative lambda estimation. |
| Species-Level Aggregation | Telomere length is highly variable; species-mean is the standard unit for cross-specpecies comparative analysis. | Individual-level analysis without phylogenetic correction at the individual level is not feasible with available data structure. |
| LOOCV/Jackknife | Required by FR-006 to ensure robustness against single-study dominance. | Omitting sensitivity analysis would leave the results vulnerable to outliers, failing the reproducibility and rigor standards. |
| Unit Conversion Logic | Required by FR-002 and US-1 to handle mixed qPCR/TRF units. | Assuming uniform units would introduce massive measurement error and bias, invalidating the statistical conclusions. |
| Early-Life Filter | Required to control for age-dependent attrition (scientific soundness). | Including mixed-age data would confound the predictor with sampling age, invalidating the association with maximum lifespan. |

## Versioning and Hashing

To satisfy Constitution Principle V:
1.  **Checksumming**: Every file written to `data/`, `results/`, and `logs/` is checksummed using `sha256`.
2.  **State Update**: The `utils.py` script reads these checksums and updates `state/projects/PROJ-055-investigating-the-impact-of-telomere-len.yaml` in the `artifact_hashes` map.
3.  **Validation**: The `run_pipeline.sh` script verifies that input hashes match expected values before proceeding.
4.  **Implementation**: `utils.py` will contain functions `generate_checksum(file_path)` and `update_state_file(hash_map)`.

## Data Flow and Order

1.  **Phase 0: Data Discovery**: `01_discover_data.py` queries Dryad API for specific dataset IDs. **Halt if 0 results**.
2.  **Phase 1: Ingestion**: `02_ingest_data.py` downloads raw CSVs (checksummed).
3.  **Phase 2: Cleaning**: `03_clean_merge.py` filters for juvenile/early-life, converts units, merges with AnAge.
4.  **Phase 3: Species List Extraction**: Extract unique species names from the merged dataset.
5.  **Phase 4: Phylogeny Fetch**: Download tree from `rotl` matching the specific species list from Phase 3. **Tree must match data exactly**.
6.  **Phase 5: Modeling**: `04_model_pglS.py` calls R scripts (`01_fit_pglS.R`) for PGLS (iterative lambda estimation).
7.  **Phase 6: Sensitivity**: `05_visualize.py` (or `04_sensitivity.py` if separate) runs LOOCV.
8.  **Phase 7: Visualization**: Generate plots.

## Compute Feasibility

*   **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, 6h limit).
*   **Strategy**:
    *   **No GPU**: All operations are CPU-based.
    *   **Memory**: Data subset to < 2 GB. PGLS matrix operations on < 500 species are trivial for 7 GB RAM.
    *   **Libraries**: Use `rpy2` to call R (`phylolm`, `ape`, `rotl`). Avoid heavy deep learning libraries.
    *   **Timeout**: The pipeline is linear and lightweight; expected runtime < 30 minutes.
    *   **Tree Fetching**: The tree is downloaded from `rotl` *after* species list is known (Phase 4), ensuring the covariance matrix is valid and avoiding circular dependencies.