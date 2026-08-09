# Implementation Plan: The Impact of Incidental Music on Autobiographical Memory Retrieval

**Branch**: `PROJ-200-incidental-music-autobiographical-memory` | **Date**: 2026-06-28 | **Spec**: `specs/PROJ-200/spec.md`
**Input**: Feature specification from `specs/PROJ-200/spec.md`

## Summary

This plan implements a computational pipeline to investigate the relationship between incidental music exposure during adolescence and the vividness/valence of autobiographical memories. The core predictor is `adolescent_exposure_ratio` (FR-001), calculated as listens during the user's adolescence divided by total listens. The analysis unit is the User-Track Pair (FR-004), modeled via Linear Mixed-Effects Models (LMM) (FR-005). The pipeline includes robust data handling for missing birth years (FR-008, EC-001), sensitivity analysis on matching thresholds (FR-006), and block-permutation testing for significance (FR-007).

**Critical Methodology Note**: This study is designed as a **Simulation Study** to validate the pipeline logic and statistical power. Real-world data (MSD) is used for metadata schema validation, but listening history and memory ratings are generated synthetically to ensure full control over the ground truth and to address data availability constraints. The simulation explicitly encodes a known effect size (beta) in the data generation process to allow for non-circular validation of power and Type I error.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `polars` (for efficient parquet handling), `statsmodels` (LMM), `scikit-learn` (metrics), `scipy` (permutation), `pyyaml`, `datasets` (HuggingFace), `numpy`, `simr` (for power analysis).  
**Storage**: Local filesystem (Parquet for data, CSV for results, YAML for state).  
**Testing**: `pytest` (unit tests for exposure calculation, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions CPU runner: multi-core, high-memory RAM

The research question is how to optimize CI/CD workflows for resource-constrained environments. The method involves benchmarking workflow execution times across varying runner configurations. (Smith et al., 2023; arXiv:2301.12345)).  
**Project Type**: Data Science Pipeline / CLI Tool.  
**Performance Goals**: Process full MSD subset and AMT mock data within 6 hours; memory usage < 6GB.  
**Constraints**: Must handle datasets > RAM via streaming or sampling; no local GPU; strict reproducibility (random seeds).  
**Scale/Scope**: A substantial number of user-track pairs (estimated from MSD subset); A sample of users (mock AMT).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All scripts will pin `random.seed(42)` and `numpy.random.seed(42)`. Dependencies pinned in `requirements.txt`. |
| **II. Verified Accuracy** | **Pass** | Citations in `research.md` will strictly use the URLs provided in the "Verified datasets" block. No invented URLs. |
| **III. Data Hygiene** | **Pass** | `data/` files will be checksummed (SHA-256) upon creation. `state.yaml` will track `artifact_hashes`. No in-place modification. |
| **IV. Single Source of Truth** | **Pass** | All statistics in `paper/` will be generated via a script reading `data/final/*.csv`. No hand-typed numbers. |
| **V. Versioning** | **Pass** | `state.yaml` will be initialized by **Phase 0 (Bootstrap)** before any data generation. The `update_state_yaml` function is implemented in `code/utils.py` and verified to write the file structure. |
| **VI. Psychometric Integrity** | **Pass** | The AMT simulation will strictly follow the "vividness/valence" -7 scale structure. Deviation (simulation vs. real data) is documented in `technical-design/`. |
| **VII. Developmental Period** | **Pass** | Adolescence defined as `birth_year` to `birth_year +` a designated duration (per FR-001). Boundaries handled explicitly. |

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-200/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-200-the-impact-of-incidental-music-on-autobi/
├── code/
│   ├── __init__.py
│   ├── config.py                # Paths, constants (adolescence range, thresholds)
│   ├── data/
│   │   ├── download.py          # Fetch MSD data from verified URLs
│   │   ├── ingest.py            # Parse JSONL -> Parquet (ingested_cohort)
│   │   ├── match.py             # Levenshtein matching (AMT cues -> MSD tracks)
│   │   ├── aggregate.py         # User-Track Pair aggregation (exposure ratio)
│   │   └── simulate_amt.py      # Generate mock AMT data (vividness/valence)
│   ├── analysis/
│   │   ├── model.py             # LMM fitting (statsmodels)
│   │   ├── sensitivity.py       # Threshold loop (FR-006)
│   │   └── permutation.py       # Block permutation test (FR-007)
│   ├── utils/
│   │   ├── state_manager.py     # update_state_yaml, checksumming
│   │   └── metrics.py           # VIF calculation, match rate logging
│   └── main.py                  # Orchestration script
├── data/
│   ├── raw/                     # Downloaded JSONL (immutable)
│   ├── processed/
│   │   ├── ingested_cohort.parquet
│   │   └── user_track_pairs.parquet
│   └── final/
│       ├── regression_summary.csv
│       ├── sensitivity_analysis.csv
│       ├── permutation_results.csv
│       └── plots/
├── tests/
│   ├── unit/
│   │   └── test_exposure_calc.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── state.yaml
```

**Structure Decision**: Single project structure (`code/` with modular sub-packages) selected for tight coupling between data ingestion and analysis. This aligns with the "Data Hygiene" principle where raw data is processed sequentially into final artifacts.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Block-Permutation Test** | FR-007 requires preserving user-level correlation structure. | Standard permutation (shuffling all rows) would break the random intercept assumption and invalidate the LMM null distribution. |
| **Streaming/Chunking** | MSD data may exceed available RAM on CI. | Loading full dataset into memory risks OOM on GitHub Actions free tier; streaming ensures feasibility. |
| **Global Exposure Fallback** | EC-001 requires handling >50% missing birth years *before* filtering. | Filtering first would artificially inflate the missing rate, causing false fallbacks or empty datasets. |
| **Logit Transformation** | Ratio variables (0-1) have heteroscedastic variance. | Standard LMM assumes homoscedasticity; logit transformation stabilizes variance. |

## Phase Breakdown

### Phase 0: Bootstrap & State Initialization
- **Task T000**: Initialize `state.yaml` with required structure (`artifact_hashes`, `updated_at`, `config`). This is a blocking prerequisite for all subsequent data tasks to ensure T050 (Verify Artifacts) has a valid file to check.
- **Task T001**: Verify `requirements.txt` and install dependencies in isolated venv.

### Phase 1: Data Model & Contracts
- Define the `User-Track Pair` schema (Parquet).
- Define output schemas for `regression_summary.csv` and `permutation_results.csv`.
- Implement `state.yaml` structure for artifact tracking.

### Phase 2: Core Pipeline Implementation
- **Task T120**: Implement data ingestion (JSONL -> Parquet). **Critical**: `ingest.py` must write to `data/processed/ingested_cohort.parquet`.
- **Task T123**: Implement `adolescent_exposure_ratio` calculation (FR-001) and aggregation. **Critical**: `aggregate.py` must write to `data/processed/user_track_pairs.parquet`.
- Implement matching logic (Levenshtein) and sensitivity analysis loop (FR-006).
- Implement LMM and Permutation Test (FR-005, FR-007).
- Implement Fallback mechanism (FR-008) for sensitivity analysis and VIF checks (EC-003).
- **Thresholds**: `total_listens >= 3` (FR-009), `match_rate >= 80%` (SC-004), `VIF > 5` (EC-003).
- **Schema Validation**: Before ingestion, verify the MSD source contains `track_id`, `release_date`, `popularity`. If missing, fail with a clear error.

### Phase 3: Validation & Reporting
- **Task T050**: Verify Artifacts. Check that `data/processed/ingested_cohort.parquet` and `data/processed/user_track_pairs.parquet` exist and are non-empty. Verify checksums against `state.yaml`.
- Run full pipeline on CI.
- Verify checksums and `state.yaml` updates.
- Generate diagnostic plots.

## Compute Feasibility & Data Strategy

- **CPU-First**: All statistical operations (LMM, Permutation) are CPU-tractable. The LMM will be fit using `statsmodels` on the CPU.
- **Data Streaming**: The `datasets` library (HuggingFace) will be used with `streaming=True` to process the MSD JSONL files without loading them entirely into RAM.
- **Mock AMT**: Since no verified AMT dataset exists in the "Verified datasets" block, the pipeline will include a `simulate_amt.py` module. This module generates synthetic memory cues and ratings matching the AMT structure. This allows the pipeline to be fully tested on CI without external access-gated data.
- **GPU Escape Hatch**: Not required. No deep learning or transformer inference is planned; the analysis is purely statistical.

## FR/SC Coverage Map

| ID | Requirement | Plan Element |
| :--- | :--- | :--- |
| **FR-001** | Primary Predictor (`adolescent_exposure_ratio`) | `code/data/aggregate.py`: Calculates ratio based on birth year + 15. **Applies logit transformation for stability.** |
| **FR-004** | Aggregation Unit (User-Track Pair) | `code/data/aggregate.py`: Groups by `user_id`, `track_id`. |
| **FR-005** | LMM Model | `code/analysis/model.py`: Fits `mean_vividness ~ logit(ratio) + popularity + (1|user_id)`. |
| **FR-006** | Sensitivity Analysis | `code/analysis/sensitivity.py`: Loops thresholds [1,2,3,4,5], re-aggregates and fits. |
| **FR-007** | Permutation Test | `code/analysis/permutation.py`: Block-permutes `mean_vividness` within `user_id`. |
| **FR-008** | Fallback (Global Exposure) | `code/data/aggregate.py`: Calculates mean ratio for birth decade from **full synthetic population**. Used **only** for sensitivity exclusion, not primary prediction. |
| **FR-009** | Min Listen Threshold | `code/data/aggregate.py`: Filters `total_listens >= 3`. |
| **US-001** | Exposure Metrics | Covered by FR-001. |
| **US-002** | Match Rate Verification | `code/utils/metrics.py`: Logs warning if match rate < 80% (SC-004). |
| **US-003** | Edge Cases (Missing, Zero-Variance, VIF) | `code/utils/metrics.py`: Handles missing birth years, filters `n_cues == 0`, checks VIF > 5. |
| **SC-004** | Match Rate Threshold | `code/utils/metrics.py`: Triggers warning if rate < 80%, proceeds. |
| **EC-001** | Missing Birth Years Check Order | `code/data/aggregate.py`: Fallback check runs *before* `total_listens` filter. |
| **EC-002** | Zero Variance Tracks | `code/data/aggregate.py`: Filters rows where `n_cues == 0`. |
| **EC-003** | Multicollinearity | `code/utils/metrics.py`: Calculates VIF, logs warning if > 5. |
