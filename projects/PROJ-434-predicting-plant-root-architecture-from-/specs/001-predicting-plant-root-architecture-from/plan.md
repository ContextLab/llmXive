# Implementation Plan: Predicting Plant Root Architecture from Soil Nutrient Profiles

**Branch**: `001-predict-root-architecture` | **Date**: 2024-05-21 | **Spec**: `specs/001-predict-root-architecture/spec.md`

## Summary

This feature implements a computational pipeline to predict plant root architecture (depth and branching density) from soil nutrient profiles (N, P, K, pH). The approach involves ingesting public geospatial soil data and tabular root trait data, merging them via geocoding, and training Random Forest models. The plan strictly adheres to the observational nature of the data, framing results as associational. Crucially, the validation strategy distinguishes between a "Soil-Only" model (testing generalization) and a "Soil+Species" model (testing species-specific effects), and employs rigorous nested permutation tests for significance.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `pandas`, `numpy`, `rasterio`, `geopandas`, `requests`, `pyyaml`, `pytest`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `artifacts`)  
**Testing**: `pytest` (unit, integration, contract validation)  
**Target Platform**: GitHub Actions Free Tier (Linux, 2 vCPU, ~7 GB RAM)  
**Project Type**: Data Science / Computational Biology Pipeline  
**Performance Goals**: Pipeline completion < 6 hours; Model training < 30 minutes on CPU.  
**Constraints**: CPU-only execution for modeling; No local GPU; Data must be streamed or sampled to fit memory.  
**Scale/Scope**: Global soil rasters (streamed/subset); Tabular root traits (large-scale datasets).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; External datasets fetched from canonical sources (HuggingFace/Zenodo) on every run. Synthetic data used *only* for pipeline testing, not scientific results. |
| **II. Verified Accuracy** | PASS | All citations in `research.md` limited to the "Verified datasets" block provided in the prompt. No URL fabrication. Synthetic data clearly flagged as non-scientific. |
| **III. Data Hygiene** | PASS | Raw data preserved in `data/raw` with checksums; Derivations in `data/processed` with new filenames. |
| **IV. Single Source of Truth** | PASS | All figures/stats in the final report trace to `data/processed` and `code/`. |
| **V. Versioning Discipline** | PASS | Artifacts tracked via content hash in `state/`. |
| **VI. Geospatial Data Alignment** | PASS | Soil rasters reprojected/resampled to common CRS before extraction; Geocoding logged with API version. |
| **VII. Cross-Species Generalization** | PASS | **Primary**: Stratified k-Fold CV (stratified by Species). **Secondary**: LOSO. This satisfies the 5-fold requirement while maintaining species stratification. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-root-architecture/
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
projects/PROJ-434-predicting-plant-root-architecture-from-/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── soil_data.py       # SoilGrids extraction (streamed)
│   │   └── trait_data.py      # Root trait loading
│   ├── modeling/
│   │   ├── __init__.py
│   │   ├── train.py           # RF training + CV + Permutation Tests
│   │   └── sensitivity.py     # Threshold sweep
│   ├── utils/
│   │   ├── geocoding.py       # Location alignment
│   │   └── stats.py           # Permutation tests, metrics
│   └── main.py                # Pipeline orchestrator
├── data/
│   ├── raw/                   # Downloaded rasters (if cached) / trait CSVs
│   └── processed/             # Merged CSVs, model artifacts
└── tests/
    ├── contract/              # Schema validation tests
    ├── integration/           # End-to-end pipeline tests
    └── unit/                  # Unit tests for ingestion/modeling
```

**Structure Decision**: Single Python package structure (`code/`) chosen to align with the "Data Science Pipeline" pattern. This keeps ingestion, modeling, and utility logic modular while maintaining a single entry point (`main.py`) for the CI runner.

## Phase Breakdown

### Phase 0: Data Ingestion & Geospatial Alignment (US-1)
*Goal: Produce a unified dataset of paired soil nutrients and root traits.*
1.  **Data Discovery**: Identify verified open sources for root trait data (Zenodo/Dryad) and SoilGrids access methods.
    *   *Constraint Check*: If no verified root trait URL exists in the prompt block, the pipeline will use a **synthetic proxy dataset** for **pipeline structure testing only**. No scientific results will be claimed from synthetic data.
    *   *Soil Data*: Use a verified HuggingFace mirror or Zenodo snapshot of SoilGrids layers (e.g., `soilgrids/soilgrids2017`).
2.  **Ingestion Script**:
    *   Download root trait tabular data (or load synthetic proxy).
    *   Stream/extract SoilGrids N, P, K, pH values at specific coordinates.
    *   **Handling Missing Data**: Records with "No Data" or negative values in soil layers are **excluded** from the primary analysis to avoid bias from global mean imputation. A sensitivity analysis will compare "Complete Cases" vs. "Species-Median Imputation" if sufficient data exists.
3.  **Geocoding**: Align coordinates to a common CRS.
4.  **Merge & Filter**: Join datasets. Filter for species with ≥10 valid observations.
5.  **Success Criterion Enforcement (SC-001)**: Calculate the proportion of root study locations successfully matched with soil nutrient data.
    *   **Action**: If match proportion < 90%, the pipeline raises a `DataQualityError` and halts execution, logging the specific failure reason.
6.  **Output**: `data/processed/merged_dataset.csv`.

### Phase 1: Predictive Modeling & Validation (US-2)
*Goal: Train RF models and evaluate via Stratified 5-Fold CV (Primary) and LOSO (Secondary).*
1.  **Preprocessing**: Encode 'Species' as categorical.
2.  **Model Strategy**:
    *   **Model A (Soil-Only)**: Predictors = [N, P, K, pH]. Targets = [Depth, Branching]. **Primary test for generalization.**
    *   **Model B (Soil + Species)**: Predictors = [N, P, K, pH, Species]. Targets = [Depth, Branching]. Tests the added value of species identity.
3.  **Validation Protocol**:
    *   **Primary**: Stratified -Fold Cross-Validation (stratified by Species) to satisfy Constitution Principle VII.
    *   **Secondary**: Leave-One-Species-Out (LOSO) CV to assess extreme generalization.
4.  **Statistical Significance (SC-002)**:
    *   **Null Baseline**: Mean prediction (R² = 0).
    *   **Null Distribution (Permutation Test)**:
        *   For Model A: Permute the target variable **within the training fold** multiple times. Re-train the model and evaluate on the held-out fold for *each* permutation.
        *   For Model B: Permute the **soil features** (N, P, K, pH) **within the training fold**, stratified by species, multiple times. Re-train and evaluate for *each* permutation.
        *   **p-value**: Proportion of permuted R² scores ≥ observed R².
    *   **Pass/Fail**: SC-002 is marked PASS only if ΔR² ≥ 0.05 **AND** permutation test p-value < 0.05.
5.  **Output**: `artifacts/model_metrics.json`, `artifacts/feature_importance.csv`.

### Phase 2: Sensitivity Analysis & Reporting (US-3)
*Goal: Validate robustness of feature importance.*
1.  **Feature Importance p-values**: For each feature, perform a sufficient number of permutations of that feature *within the training fold* to generate a null distribution of importance scores. Calculate the p-value as the proportion of permuted scores exceeding the observed score.
2.  **Threshold Sweep**: Evaluate stability of top-ranked feature rankings across a range of p-value thresholds.
3.  **Reporting**: Generate summary tables and plots.
    *   *Constraint*: All findings framed as associational (FR-006).
4.  **Output**: `artifacts/sensitivity_report.md`, `figures/`.

### Phase 3: Documentation & Contracts
*Goal: Finalize artifacts.*
1.  Generate `quickstart.md`.
2.  Define `contracts/` schemas.
3.  Verify all FR/SC coverage in the final report.

## Compute Feasibility Strategy

*   **CPU-First**: All modeling (Random Forest) is CPU-tractable. The dataset size (likely < 10k rows) fits easily in 7 GB RAM.
*   **Data Streaming**: SoilGrids rasters are large. The ingestion step will NOT download global rasters. Instead, it will request tiles for specific coordinates via the API or download only the relevant shards if using a pre-processed HF dataset.
*   **No GPU Needed**: No deep learning or large language models are involved. No "GPU escape hatch" is required.
*   **Time Budget**:
 * Ingestion: [deferred] (network dependent).
 * Modeling: < 10 mins for RF on <10k rows. Permutation tests (sufficient iterations) may extend this to a moderate duration, still well [deferred].
 * Total: Well [deferred].

## FR/SC Coverage Map

| ID | Requirement/Success Criteria | Plan Phase | Implementation Detail |
|----|------------------------------|------------|-----------------------|
| FR-001 | Download soil rasters | Phase 0 | `code/ingestion/soil_data.py` (API/Stream) |
| FR-002 | Merge & Filter (≥10 obs) | Phase 0 | `code/ingestion/trait_data.py` + Merge logic |
| FR-003 | Train RF (Species as feature) | Phase 1 | `code/modeling/train.py` (Model B only; Model A excludes Species) |
| FR-004 | LOSO Cross-Validation | Phase 1 | `code/modeling/train.py` (Secondary validation) |
| FR-005 | Feature Importance & Sensitivity | Phase 2 | `code/modeling/sensitivity.py` (p-value sweep) |
| FR-006 | Associational Framing | Phase 3 | Report generation logic |
| FR-007 | Exclude <10 obs summary | Phase 0 | `code/ingestion/trait_data.py` (logging) |
| SC-001 | Match proportion ≥90% | Phase 0 | **Hard Fail** if <90% (DataQualityError) |
| SC-002 | R² gain ≥0.05 + Permutation | Phase 1 | **Pass/Fail Logic**: ΔR² ≥ 0.05 AND p < 0.05 |
| SC-003 | LOSO R² SD | Phase 1 | Metric calculation in `main.py` |
| SC-004 | Feature ranking stability | Phase 2 | Sensitivity analysis output |
| SC-005 | <6h execution | Phase 0/1/2 | CPU-optimized RF, streaming data |