# Implementation Plan: Predicting Avian Song Variation with Climatic and Geographic Factors

**Branch**: `001-predict-avian-song-variation` | **Date**: 2026-10-15 | **Spec**: `specs/001-predict-avian-song-variation/spec.md`  
**Input**: Feature specification from `/specs/001-predict-avian-song-variation/spec.md`

## Summary
The pipeline will (1) obtain a **verified, pre‑merged** `AnalysisDataset` (song metrics + climate variables) from an open HuggingFace repository, (2) validate its schema, (3) perform exploratory data analysis (correlation matrix, summary statistics, VIF diagnostics), (4) fit multiple linear regression models for each song metric, (5) apply Benjamini‑Hochberg false‑discovery‑rate control across *all* hypotheses, and (6) run a sensitivity analysis by sweeping the p‑value significance threshold `{0.01, 0.05, 0.10}`. All steps run on the GitHub Actions free‑tier CPU runner; no GPU is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `pyproj`, `geopandas`, `rasterio` (for optional raster handling)  
- **Storage**: CSV/Parquet files under `data/`  
- **Testing**: `pytest` (unit tests for ingestion, EDA, modeling)  
- **Target Platform**: Linux (GitHub Actions free‑tier runner)  
- **Project Type**: Research‑pipeline CLI (`code/main.py`)  
- **Performance Goals**: End‑to‑end runtime < 1 hour, RAM ≤ 6 GB  
- **Constraints**: CPU‑only, observational (associational) analysis, strict reproducibility (pinned seeds, checksums)  

## Constitution Check
| Principle | Status | Verification |
|-----------|--------|--------------|
| **I. Reproducibility** | PASS | `requirements.txt` pins exact versions; `random_state=42` used everywhere; checksums recorded in `data/checksums.txt`. |
| **II. Verified Accuracy** | PASS | Only the **AnalysisDataset** parquet files are cited (verified URLs). No unverified external sources are used for primary analysis. |
| **III. Data Hygiene** | PASS | Raw parquet files are immutable; all transformations write new files; no PII present. |
| **IV. Single Source of Truth** | PASS | Every statistic, figure, and table is generated programmatically from the `AnalysisDataset`. |
| **V. Versioning Discipline** | PASS | Content hashes stored in `state/projects/PROJ-334-...yaml`; timestamps updated on artifact change. |

## Project Structure
```text
specs/001-predict-avian-song-variation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── analysis_dataset.schema.yaml
    ├── analysis_output.schema.yaml
    ├── song_record.schema.yaml
    ├── climate_snapshot.schema.yaml
    └── aggregated_pvalues.schema.yaml
```

```text
projects/PROJ-334-predicting-avian-song-variation-with-cli/
├── data/
│   ├── raw/                # Verified parquet files downloaded from HuggingFace
│   ├── processed/
│   │   └── analysis_dataset.parquet   # Produced by ingestion (copy of raw)
│   └── checksums.txt
├── code/
│   ├── __init__.py
│   ├── ingestion.py        # Load + schema validation + optional CRS reprojection
│   ├── eda.py              # Correlation, summary stats, VIF, flag report
│   ├── modeling.py         # OLS, aggregated p‑values, Benjamini‑Hochberg, sensitivity
│   ├── utils.py            # Helper utilities (seed, checksum, logging)
│   └── main.py             # Orchestrates the pipeline
├── tests/
│   ├── test_ingestion.py
│   ├── test_eda.py
│   └── test_modeling.py
├── requirements.txt
└── README.md
```

**Structure Decision**: A single‑project layout minimises overhead for a linear research pipeline while keeping code modular.

## Phase / Task Mapping (covers every FR & SC)

| Phase | Tasks (IDs) | FR / SC addressed | Description |
|------|--------------|-------------------|-------------|
| **0 Data Acquisition & Validation** | T001 – Download verified `AnalysisDataset` parquet files.<br> T002 – Record SHA‑256 checksums in `data/checksums.txt`.<br> T003 – Validate schema against `contracts/analysis_dataset.schema.yaml`.<br> T004 – (Optional) If raw climate raster is present, reproject to EPSG:4326 using `pyproj` (fulfills FR‑001 CRS requirement). | FR‑001, SC‑001 | Guarantees reproducible, checksum‑verified input. |
| **1 Exploratory Data Analysis** | T010 – Compute summary statistics (mean, std, range).<br> T011 – Generate Pearson correlation matrix (song metrics ↔ climate predictors).<br> T012 – Verify matrix symmetry & diagonal = 1.0.<br> T013 – Compute VIF for all predictors; flag any **pair** whose VIF > 5 (per‑variable VIF > 5 ⇒ identify highest‑correlated partner).<br> T014 – Produce EDA JSON report (`outputs/eda_report.json`). | FR‑002, FR‑005, SC‑004 | Provides data‑quality diagnostics and multicollinearity flags. |
| **2 Modeling & Hypothesis Testing** | T020 – Fit OLS model for `song_metric_1` (Model A: climate only).<br> T021 – Fit OLS model for `song_metric_2` (Model A).<br> T022 – Fit expanded Model B (climate + geo).<br> T023 – Compute R² and adjusted R²; compare to null model (intercept‑only) → satisfies SC‑002.<br> T024 – Aggregate all predictor p‑values across both outcomes into a table (`aggregated_pvalues.parquet`).<br> T025 – Apply Benjamini‑Hochberg FDR correction **globally** across the aggregated list (fulfills FR‑006).<br> T026 – Generate model summary CSV (`outputs/model_summary.csv`) validated by `contracts/analysis_output.schema.yaml`. | FR‑003, FR‑006, SC‑002 | Delivers primary associational results with proper multiple‑testing control. |
| **3 Sensitivity Analysis** | T030 – Sweep significance threshold `{0.01, 0.05, 0.10}`; for each threshold recompute significant predictor set and R².<br> T031 – Compute Jaccard index of predictor sets between thresholds (reports per‑threshold stability).<br> T032 – Assemble `sensitivity_report.json` containing threshold, #significant predictors, R², Jaccard indices (fulfills SC‑003). | FR‑004, SC‑003 | Demonstrates robustness of variable selection. |
| **4 Reporting & Artifacts** | T040 – Export figures (correlation heatmap, VIF bar, R² vs. threshold plot) to `outputs/figures/`.<br> T041 – Log total runtime; enforce SC‑005 (< 6 h). | SC‑005 | Guarantees compute‑budget compliance. |

All phases are ordered so that data is downloaded **before** any consumption, models are fitted **before** evaluation, and figures are generated **before** they are referenced in downstream reports.

## Compute Feasibility
- All heavy lifting uses `statsmodels` OLS (CPU‑only).  
- Memory usage stays < 5 GB (parquet loading with `dtype` optimisation).  
- Expected wall‑time: ≈ 30 min on 2‑core GitHub Actions runner. No GPU required.

## Risk Mitigation & Open Issues
- **Raw SongRecord / ClimateSnapshot sources**: No open, verified raw files exist. The plan therefore uses the **verified merged** `AnalysisDataset` (HuggingFace) as the canonical input, satisfying reproducibility while acknowledging the limitation (no separate raw‑merge step).  
- **CRS handling**: If a user supplies an external raster, `ingestion.py` will detect its CRS via `rasterio` and reproject to EPSG:4326; otherwise the step is a no‑op (dataset already in WGS84).  
- **Power analysis**: `modeling.py` will compute Cohen’s f² and report achieved power; if < 0.80, results are flagged as preliminary (no claim of “no effect”).  

---
