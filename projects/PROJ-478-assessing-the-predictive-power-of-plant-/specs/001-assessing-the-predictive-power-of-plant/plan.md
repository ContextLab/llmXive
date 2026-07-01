# Implementation Plan: Assessing the Predictive Power of Plant Functional Traits for Species Distribution Models

**Branch**: `feat-assess-plant-traits` | **Date**: 2026-06-25 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/feat-assess-plant-traits/spec.md`

## Summary

This feature implements a computational workflow to assess whether plant functional traits (Specific Leaf Area, Seed Mass, Plant Height) add predictive value to climate‑only Species Distribution Models (SDMs) for Asteraceae species. The approach involves downloading GBIF occurrences via the global GBIF API, WorldClim v2.1 climate layers, and TRY trait data (Handbook 2013‑verified where available). Random Forest classifiers are trained under a strict Leave‑One‑Species‑Out (LOSO) cross‑validation design, and performance is compared with a paired two‑sided t‑test (Bonferroni‑corrected) as required by the specification. No trait imputation is performed; the LOSO cycle uses the *known* trait values of the held‑out species.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `scikit-learn==1.5.0`, `pandas==2.2.2`, `geopandas==0.14.4`, `rasterio==1.3.9`, `numpy==1.26.4`, `pyyaml`, `requests`.
**Storage**: Local filesystem (`data/raw`, `data/processed`, `results/`). No external database.
**Testing**: `pytest` with strict assertions on schema compliance and statistical output formats.
**Target Platform**: Linux (GitHub Actions free‑tier: 2 CPU, 7 GB RAM, ≤ 6 h runtime).
**Constraints**: CPU‑only; Random Forest `n_estimators=100`, `max_depth=10`. Spatial thinning defaults to 10 km with fallback logic (see below).
**Scale/Scope**: A diverse set of Asteraceae species; ~ climate variables; 3 traits; up to ~1 M occurrence records after cleaning.

## Constitution Check

| Principle | Status | Evidence in Plan |
|:--- |:--- |:--- |
| **I. Reproducibility** | **PASS** | Random seeds (`random_state=42`) pinned; `requirements.txt` version‑locked; data fetched from canonical URLs with version tags; checksums recorded. |
| **II. Verified Accuracy** | **PASS** | Only verified dataset URLs are cited; version numbers for WorldClim and TRY are recorded. |
| **III. Data Hygiene** | **PASS** | Raw data preserved; each transformation writes a new file with provenance metadata; no PII present. |
| **IV. Single Source of Truth** | **PASS** | All metrics trace back to rows in `results/` JSON/CSV and the exact code that generated them. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked in project state; `updated_at` timestamps updated on each artifact change. |
| **VI. Ecological Data Provenance** | **PASS** | GBIF queries use a global taxon filter for Asteraceae; WorldClim version and download date logged; TRY source field verified against “Handbook 2013”. |
| **VII. Model Evaluation Transparency** | **PASS** | Hyperparameters, seeds, CV splits, and statistical test parameters are explicitly documented in code and reported in `results/`. |

## Project Structure

### Documentation (this feature)

```text
specs/feat-assess-plant-traits/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│ ├── occurrence.schema.yaml
│ ├── trait.schema.yaml
│ ├── climate.schema.yaml
│ ├── result.schema.yaml
│ ├── model_result_schema.schema.yaml
│ └── statistical_summary_schema.schema.yaml
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── data/
│ ├── download_gbif.py
│ ├── download_worldclim.py
│ ├── download_try.py
│ └── preprocess.py
├── modeling/
│ ├── train_climate_only.py
│ ├── train_climate_trait.py
│ └── metrics.py
├── analysis/
│ ├── statistical_tests.py
│ └── sensitivity_analysis.py
├── utils/
│ ├── config.py
│ └── logging.py
└── cli/
 └── main.py
```

**Structure Decision**: A single, modular project layout keeps the pipeline lightweight for the CI environment while preserving testability.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **LOSO Design** | Required by FR‑004 to evaluate predictive utility when a species’ occurrences are unseen. | Simple k‑fold CV would not test generalization to new taxa. |
| **Fallback Thinning** | FR‑001 demands ≥ 80 % record retention; dynamic reduction avoids data loss on sparse species. | Fixed thinning distance often discards too many records. |
| **Trait Flagging** | FR‑010 requires flagging unverified protocol traits rather than exclusion. | Automatic exclusion would bias the trait‑augmented analysis. |

## Detailed Methodology

### 1. Data Acquisition

| Data | Source | Access Method | Version / Date |
|------|--------|---------------|----------------|
| GBIF Occurrences | GBIF API (`) | `requests` + pagination | Query: taxonKey for *Asteraceae* (family), worldwide, ≥ 100 records per species |
| WorldClim | WorldClim (bioclim layers) | `rasterio` + HTTP download | Release 2023‑08‑01 |
| TRY Traits | TRY public subset (v2022‑07) | `requests` to TRY API | Includes `source` metadata field |

### 2. Pre‑processing

1. **Occurrence cleaning (FR‑001)**
 - Remove exact duplicate coordinates.
 - Apply spatial thinning at 10 km using `spatial‑thin` library.
 - **Fallback algorithm**: If retained records < 80 % of raw, reduce thinning distance by 1 km steps (10 km → 9 km → … → 1 km) until the 80 % threshold is met or the minimum distance (1 km) is reached. If still insufficient, flag species as `insufficient_data` and skip further analysis.

2. **Climate raster extraction (FR‑002)**
 - Compute convex hull of cleaned occurrences per species.
 - Download the WorldClim layers covering the hull.
 - Align rasters to WGS84; extract raster values at each occurrence point.

3. **Trait retrieval (FR‑003, FR‑010)**
 - Query TRY for SLA, seed mass, height.
 - Check `trait_source` field; set `is_verified = true` only if source matches “Handbook 2013”. Otherwise flag as `unverified_protocol`.
 - If any of the three traits are missing, set `exclusion_reason = "missing_trait"` and exclude the species from the trait‑augmented branch (FR‑006). Unverified traits are retained with `is_verified = false` and flagged in downstream reports.

### 3. Modeling (FR‑004)

- **LOSO Cycle** (N = number of species with complete trait data):
 - **Training set**: N‑1 species (climate + traits).
 - **Test set**: 1 held‑out species.
 - **Climate‑only model**: Random Forest on 19 climate predictors.
 - **Climate + traits model**: Random Forest on 19 climate + 3 trait predictors; uses the *known* trait values of the held‑out species (no imputation).
 - Hyperparameter tuning via inner 5‑fold CV on the training set only.
 - Record AUC and TSS for each fold; compute VIF for the full predictor set; if any VIF > 5, set `collinearity_flag = true` (FR‑011).

### 4. Statistical Analysis (FR‑005, FR‑008, FR‑009)

1. **Paired two‑sided t‑test** on per‑species AUC (and separately on TSS) comparing climate‑only vs. climate + traits across all LOSO folds.
2. **Bonferroni correction** for the two metrics (AUC, TSS) (FR‑008).
3. **Effect size**: Cohen’s d.
4. **Sensitivity sweep**: Compute ΔAUC for thresholds {0.01, 0.02, 0.05}; generate a table showing the proportion of species with ΔAUC > threshold; success criterion ≥ 67 % (≥ 2 of 3 thresholds) (FR‑009).

### 5. Reporting & Disclaimer (FR‑007)

- All statements about predictive improvement are framed as *associative* (predictive value given known traits), not causal.
- Include a disclaimer that the approach does not evaluate performance when trait values are unknown for a new species.

## Compute Feasibility & Constraints

- **Memory**: Process species sequentially; each species’ raster stack and occurrence set fit < 200 MB.
- **Runtime**: Estimated ≤ 4 h for 50 species on 2‑core CI runner.
- **CPU**: All libraries are CPU‑native; no GPU dependencies.

## Decision Rationale

- **Why known traits?** FR‑004 explicitly requires using the *known* trait values of the held‑out species. This design tests whether traits are *associated* with distribution patterns beyond climate, which aligns with the spec’s requirement while remaining feasible on the CI platform.
- **Why paired t‑test?** The spec mandates a paired two‑sided t‑test with Bonferroni correction. A LMM would be unnecessary and would deviate from the contractual requirement. The t‑test directly compares the two model configurations across the same species, satisfying FR‑005 and FR‑008.
