# Implementation Plan: Predicting Plant Root Architecture from Soil Nutrient Availability

**Branch**: `001-predict-root-architecture` | **Date**: 2024-05-21 | **Spec**: `specs/001-predict-root-architecture/spec.md`
**Input**: Feature specification from `/specs/001-predict-root-architecture/spec.md`

## Summary

This feature implements a computational pipeline to quantify the associational relationship between soil nutrient availability (Phosphorus, Nitrogen) and plant root architecture traits (length, branching, surface area). The technical approach involves ingesting observational root phenotype data from PlantPheno (via Hugging Face), merging it with soil data (or handling the unavailability of ISRIC via a documented deviation), preprocessing with log-transforms and KNN imputation, and fitting Linear Mixed-Effects Models (LMM) and Random Forest baselines. The plan adheres to the project constitution by enforcing species-level stratified validation, logging all deviations from the spec (specifically regarding ISRIC data and KNN imputation fallbacks), and framing all results as associational.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `datasets` (Hugging Face), `pyyaml`  
**Storage**: Local `data/` directory (raw and processed CSV/Parquet), `artifacts/` for metrics/logs.  
**Testing**: `pytest` with contract tests against YAML schemas.  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM).  
**Project Type**: Computational Research Pipeline / CLI.  
**Performance Goals**: Complete data ingestion, modeling, and reporting within 6 hours on CPU.  
**Constraints**: No local GPU; strict memory limits (~7 GB); all results must be reproducible with pinned seeds; no causal claims.  
**Scale/Scope**: Single-species and multi-species observational analysis; dataset size depends on available PlantPheno records (estimated < 100k rows).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action/Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All scripts will pin random seeds. `requirements.txt` will be used. External datasets fetched via canonical HF IDs. |
| **II. Verified Accuracy** | **PASS** | Citations for literature ranges will be validated. If no verified source exists for nutrient ranges, the analysis will fail gracefully or use a documented fallback (see Research). |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/`. Processed data in `data/processed/`. Checksums recorded in state file. |
| **IV. Single Source of Truth** | **PASS** | All figures and stats generated programmatically. No manual entry in reports. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked for data and code. State file updated on artifact changes. |
| **VI. Cross-Species Stratified Validation** | **PASS** | Model splits will be performed by `species` column, not random rows. |
| **VII. Nutrient-Specific Metric Normalization** | **PASS** | Log-transforms for root metrics; Z-score for nutrients implemented as per spec. |

**Deviation Note**: The spec mandates merging with ISRIC (FR-002) and KNN imputation (FR-003). If ISRIC is unavailable (as indicated in Verified Datasets), the plan includes a formal deviation (AM-001) to proceed with root-only data or available soil proxies, and to replace KNN with exclusion or mean imputation if neighbors are insufficient. This deviation is logged explicitly to satisfy the "Spec Deviation" narrative.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-root-architecture/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── model_results.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-457-predicting-plant-root-architecture-from-/
├── code/
│   ├── requirements.txt
│   ├── __init__.py
│   ├── ingestion.py           # Data download and parsing
│   ├── preprocessing.py       # Cleaning, imputation, transformation
│   ├── modeling.py            # LMM and RF fitting
│   ├── visualization.py       # PDP plots and report generation
│   └── utils.py               # Logging, config, seed setting
├── data/
│   ├── raw/                   # Downloaded raw files
│   └── processed/             # Cleaned CSV/Parquet
├── artifacts/
│   ├── metrics.json           # R2, p-values, success criteria
│   ├── logs/                  # Execution logs
│   └── reports/               # Final PDF/MD report
├── tests/
│   ├── contract/
│   │   └── test_schemas.py    # Contract tests for YAML schemas
│   └── integration/
└── state/
    └── projects/PROJ-457-...yaml
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) is selected to minimize overhead for a computational research pipeline. This aligns with the "Single Source of Truth" principle by keeping all artifacts in one repository.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Deviation Handling (AM-001)** | Required because ISRIC is not a verified source in the dataset block. | Proceeding without a fallback would cause the pipeline to crash on data ingestion. |
| **KNN Fallback Logic** | Required because k=5 neighbors may not exist for sparse species. | Simple mean imputation alone fails to capture local structure; KNN is preferred but needs a safe fallback. |
| **Stratified Validation** | Required by Constitution Principle VI. | Random row splitting would leak species-specific variance, inflating R² and violating the spec. |
