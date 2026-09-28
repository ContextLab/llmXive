# Implementation Plan: Predicting Avian Foraging Guilds from Public eBird Data and Land Cover Maps

**Branch**: `001-avian-foraging-land-cover` | **Date**: 2025-01-15 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-avian-foraging-land-cover/spec.md`

## Summary

This project implements a data science pipeline to predict avian foraging guilds (ground, canopy, aerial) using land cover composition derived from NLCD 2021 and occurrence records from the eBird Basic Dataset (EBD). The approach involves dynamically extracting the top-ranked species by observation count, merging them with A buffer land cover data analysis will be conducted. Research Question: How does land cover within a defined proximity buffer influence the observed ecological patterns? Method: Spatial analysis of land cover datasets using a fixed-distance buffer approach. References: [Citation preserved as in original context]., applying a Centered Log-Ratio (CLR) transformation to handle compositional data, and training a Regularized Logistic Regression classifier (L2). The model is validated via an Across-Species Permutation Test (operating on aggregated species-level data) to assess whether land cover predicts guild assignment better than chance. The pipeline is designed for CPU-only execution on GitHub Actions free-tier runners (limited CPU, constrained memory).

**Note on Spec Gaps**: The Spec (FR-004) mandates a Random Forest classifier, and Principle VI mandates NLCD 2019 via USGS. Due to statistical constraints (N=25) and data availability (verified NLCD 2021 source only), this plan uses Logistic Regression and NLCD 2021. These deviations are flagged for Spec amendment.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, geopandas, scikit-learn, rasterio, numpy, datasets (HuggingFace), requests  
**Storage**: Local file system (CSV, GeoJSON, Pickle, NumPy)  
**Testing**: pytest (contract tests, integration tests)  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: data-science-pipeline  
**Performance Goals**: Runtime < 145 minutes (per verified fact), Memory < 7 GB, Disk < 14 GB  
**Constraints**: CPU-only (no GPU), strict data provenance, no manual data curation steps in automated pipeline  
**Scale/Scope**: Top 25 species (dynamically selected), filtered to ≥50 observations each, ~100k-500k records depending on filtering  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: **PASS**. Plan mandates pinned random seeds, canonical dataset sources (HuggingFace verified URLs), and deterministic data flows. Dynamic species selection ensures reproducibility of the "top 25" set.
- **II. Verified Accuracy**: **PASS**. All citations to datasets and literature will be validated against the `# Verified datasets` block. Guild mapping uses a dynamic lookup against the top-25 list, validated against the cited literature source.
- **III. Data Hygiene**: **PASS**. Plan includes checksumming steps for raw data and distinct filenames for derived data (e.g., `merged_observations.csv` vs `species_profiles.csv`).
- **IV. Single Source of Truth**: **PASS**. All outputs (metrics, plots) will be generated programmatically from `data/` artifacts; no manual entry.
- **V. Versioning**: **PASS**. Artifacts will carry content hashes; `state/` files updated upon artifact generation.
- **VI. Habitat Data Provenance**: **PASS (with Spec Gap)**. Plan uses NLCD 2021 via HuggingFace as the *only* verified available source. The Spec's requirement for NLCD 2019 via USGS is flagged as a gap because the required source is unavailable/verified.
- **VII. Model Evaluation Transparency**: **PASS**. Plan mandates `logistic_regression.pkl`, `training_metrics.json`, and `null_distribution.npy` with logged seeds and metrics.
- **Spec Gap Note**: FR-004 mandates Random Forest, but N=25 makes it statistically unsound. Plan uses Logistic Regression. This is a deliberate deviation to ensure scientific validity, flagged for Spec amendment.

## Project Structure

### Documentation (this feature)

```text
specs/001-avian-foraging-land-cover/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── download_ebd.py            # (T001 - Data extraction wrapper)
│   ├── download_guild_source.py   # (T008a - Fetches guild metadata)
│   ├── generate_guild_mapping.py  # (T008b - Creates mapping CSV from dynamic list)
│   ├── load_and_count.py          # (T012.5a - Counts records, identifies top 25)
│   ├── select_top_species.py      # (T012.5b - Filters EBD to top 25)
│   ├── calculate_100m_buffers.py  # (T039b - Raster extraction + 100m validation)
│   ├── join_guild_labels.py       # (T039c - Merges data)
│   ├── write_merged_observations.py # (T039d - Final raw dataset)
│   ├── aggregate.py               # (T040 - Species-level aggregation)
│   └── transform_clr.py           # (T040b - CLR transformation for compositional data)
├── models/
│   ├── train.py                   # (T041 - Logistic Regression training)
│   └── stratified_permutation.py  # (T059 - Across-Species Permutation Test)
├── viz/
│   └── generate_plots.py          # (T042c, T044 - Visualization)
├── tests/
│   ├── contract/
│   │   └── test_data_contract.py  # (T010 - Validates schema)
│   └── integration/
│       └── test_pipeline.py
└── lib/
    └── utils.py
```

**Structure Decision**: Single-project structure chosen for data science workflows. `code/` contains modular scripts for each pipeline stage, `data/` for intermediate artifacts, and `models/` for trained artifacts. This aligns with the "Reproducibility" and "Data Hygiene" principles.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Across-Species Permutation | Spec FR-005 requires controlling for species identity. "Within-species" shuffling is impossible (guilds are static per species). | Standard permutation (random shuffle) fails to control for species-specific habitat preferences, introducing confounding bias. |
| Fixed 100m Buffer | Spec FR-002 mandates 100m. Multi-scale testing rejected due to 145-minute runtime limit. | Varying scales would require multi-resolution raster processing, exceeding the 145-minute limit. |
| CLR Transformation | Land cover proportions sum to 1.0 (compositional data). Raw proportions induce spurious correlations. | Using raw proportions without transformation leads to unstable feature importance rankings in compositional contexts. |
| Logistic Regression (L2) | N=25 species is too small for Random Forest (high variance). | Random Forest on N=25 would overfit and produce unreliable feature importance. Logistic Regression with L2 is statistically sound for low-N. |
| Dynamic Species Selection | Spec FR-001 requires "top-ranked species" (dynamic). | Hardcoding the top 25 would violate the requirement to extract based on current record counts. |


## Computational Task Ordering

The pipeline strictly orders phases to ensure data availability:
1.  **Data Download**: `download_ebd.py`, `download_guild_source.py` (T001, T008a).
2.  **Species Selection**: `load_and_count.py` (T012.5a) -> `select_top_species.py` (T012.5b). *Critical: Top 25 list generated dynamically. T012.5b depends on T012.5a output.*
3.  **Buffer & Merge**: `calculate_100m_buffers.py` (with 100m validation & logging) -> `join_guild_labels.py` -> `write_merged_observations.py` (T039b -> T039c -> T039d).
4.  **Aggregation & Transform**: `aggregate.py` (T040) -> `transform_clr.py` (T040b). *Output: species_profiles.csv.*
5.  **Model Training**: `train.py` (T041) on `species_profiles.csv` (CLR transformed).
6.  **Validation**: `stratified_permutation.py` (T059) on `species_profiles.csv` (Across-Species Permutation). *Note: T059 operates on aggregated data to match training input.*
7.  **Visualization**: `generate_plots.py` (T042c).
8.  **Literature Check**: T028.1 (Compare feature importance against domain literature). *Depends on T044 (feature importance) and the dynamic literature table.*
