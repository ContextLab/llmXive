# Implementation Plan: Predicting Avian Foraging Guilds from Public eBird Data and Land Cover Maps

**Branch**: `001-avian-foraging-land-cover` | **Date**: 2025-01-15 | **Spec**: `specs/001-avian-foraging-land-cover/spec.md`
**Input**: Feature specification from `specs/001-avian-foraging-land-cover/spec.md`

## Summary

This project implements a reproducible machine learning pipeline to predict avian foraging guilds (ground, canopy, aerial) using public eBird Basic Dataset (EBD) occurrence records and NLCD 2019 land cover data. The approach involves extracting the top 25 species by record count, aggregating land cover proportions to the species level, and training a Random Forest classifier. To validate signal beyond species identity, a **Random Guild Permutation Test** (permuting guild labels across species) is performed. The entire pipeline is designed to run on CPU-only GitHub Actions free-tier runners within 6 hours.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, geopandas, rasterio, scikit-learn, requests, numpy, matplotlib, seaborn, pyyaml, jupyter  
**Storage**: Local filesystem (CSV, GeoJSON, PNG artifacts)  
**Testing**: pytest (contract tests, unit tests for data processing)  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: data-science-pipeline  
**Performance Goals**: Complete pipeline execution ≤ 6 hours on 2 CPU cores, ≤ 7 GB RAM  
**Constraints**: No GPU/CUDA, no large model training, dataset must fit in RAM after filtering to top 25 species with ≥50 observations  
**Scale/Scope**: ~25 species, variable observation counts (filtered ≥50), Multiple land cover classes (derived from NLCD), multiple foraging guilds. Estimated raw EBD size on the order of hundreds of millions of records; filtered dataset with approximately five million records (estimated < 2GB RAM).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: **SATISFIED**. Plan mandates pinned `random_state` in `code/`, fixed dataset sources from verified URLs, and a `requirements.txt` for dependency pinning located at `projects/<PROJ-ID>/code/requirements.txt`.
- **II. Verified Accuracy**: **SATISFIED**. Plan restricts dataset sources to the `# Verified datasets` block in the user prompt. All citations in `research.md` will reference these specific URLs or primary literature for foraging guild definitions.
- **III. Data Hygiene**: **SATISFIED**. Plan requires raw data checksums in `data/metadata.yaml`. Intermediate derived files (merged datasets) will be new files, never overwriting raw inputs.
- **IV. Single Source of Truth**: **SATISFIED**. A final analysis notebook (`code/notebooks/01_analysis.ipynb`) will serve as the SSoT, programmatically generating all figures and statistics from `data/` artifacts.
- **V. Versioning Discipline**: **SATISFIED**. A `generate_hashes.py` script will be executed during the data download phase to generate content hashes for all artifacts, recorded in the project state file.
- **VI. Habitat Data Provenance**: **SATISFIED**. Plan explicitly requires downloading NLCD from the verified USGS EarthExplorer source and embedding provenance fields (source URL, coordinates, timestamp) in the merged dataset.
- **VII. Model Evaluation Transparency**: **SATISFIED**. Plan mandates a sufficient number of permutation iterations (across species) to ensure statistical robustness., with logging of balanced accuracy, F scores, and the specific random seed used for the Random Forest in the final notebook.

## Project Structure

### Documentation (this feature)

```text
specs/001-avian-foraging-land-cover/
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
projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/
├── data/
│   ├── download_ebd.py          # Downloads and checksums EBD (Official + Fallback)
│   ├── download_nlcd.py         # Downloads and checksums NLCD 2019 (USGS)
│   ├── merge_and_buffer.py      # Merges data, calculates buffers of varying radii to assess spatial influence.
│   └── aggregate.py             # Aggregates observations to species-level profiles
├── models/
│   ├── train.py                 # Random Forest training on aggregated data
│   └── evaluate.py              # Permutation tests, metrics
├── viz/
│   ├── plot_confusion.py        # Confusion matrix
│   ├── plot_importance.py       # Feature importance bar chart
│   └── map_habitat.py           # Spatial map generation
├── notebooks/
│   └── 01_analysis.ipynb        # Final SSoT notebook (orchestrates pipeline + logs)
├── utils/
│   ├── config.py                # Paths, seeds, constants
│   └── provenance.py            # Metadata logging
├── tests/
│   ├── test_data_contract.py    # Validates schema compliance
│   └── test_metrics.py          # Validates metric calculations
├── requirements.txt
└── run_pipeline.sh              # Orchestration script

projects/PROJ-397-predicting-avian-foraging-behavior-from-/data/
├── raw/
│   ├── ebd_train.csv            # Raw EBD (or parquet)
│   └── nlcd_2019.zip            # Raw NLCD
├── processed/
│   ├── merged_observations.csv  # Filtered, buffered, labeled
│   └── species_profiles.csv     # Aggregated species-level data
└── metadata.yaml                # Checksums and provenance

projects/PROJ-397-predicting-avian-foraging-behavior-from-/docs/
└── results/
    ├── confusion_matrix.png
    ├── feature_importance.png
    └── habitat_map.png
```

**Structure Decision**: Single project structure selected (`code/` subdirectories). This minimizes complexity for a data-science pipeline, keeping data processing, modeling, and visualization in a unified environment suitable for a single-runner execution. The final notebook serves as the SSoT for transparency.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Species-Level Aggregation | Required because guild labels are static per species. Training on raw observations would conflate species identity with land cover. Aggregation ensures the model learns habitat-guild relationships, not species-habitat preferences. | Training on raw observations would fail to distinguish between 'guild predicts habitat' and 'species predicts habitat', violating the research question. |
| Random Guild Permutation (Across Species) | Required to test if land cover predicts guild assignment better than chance. Permuting within species is impossible (constant labels). Permuting across species breaks the species-guild link, creating a valid null distribution. | Standard stratified permutation (by species) is mathematically invalid for constant labels. |
| 100m Buffering | Required by FR-002 to capture local habitat context at the observation scale before aggregation. | Using a single global land cover proportion would obscure local habitat heterogeneity critical to foraging behavior. |
| Top 25 Species Filter | Required by FR-001 to balance statistical power with computational feasibility on free-tier CI. | Using all species would exceed RAM limits and runtime constraints; using fewer than 25 might reduce guild representation. |

## FR/SC Coverage Matrix

| ID | Requirement | Plan Element Addressing It |
|----|-------------|---------------------------|
| FR-001 | Extract top 25 species | `data/download_ebd.py` (filtering logic) |
| FR-002 | NLCD 100m buffers | `data/download_nlcd.py`, `data/merge_and_buffer.py` |
| FR-003 | Filter ≥50 obs/species | `data/preprocess.py` (filtering logic) |
| FR-004 | Random Forest -fold CV | `models/train.py` (aggregated data) |
| FR-005 | Stratified Permutation Test | `models/evaluate.py` (redefined as Across-Species Permutation) |
| FR-006 | Balanced Accuracy / F1 | `models/evaluate.py` (metrics calculation) |
| FR-007 | Visualizations | `viz/*.py` scripts |
| FR-008 | Control for species identity | Aggregation step + Across-Species Permutation |
| SC-001 | Balanced Accuracy vs Chance | `models/evaluate.py` (null distribution comparison) |
| SC-002 | Permutation p < 0.05 | `models/evaluate.py` (p-value calculation) |
| SC-003 | Feature Importance vs Lit | `viz/plot_importance.py` + `notebooks/01_analysis.ipynb` |
| SC-004 | Runtime ≤ 6h | CPU-tractable methods, aggregated data |

## Risks & Mitigations

- **Risk**: Official EBD download exceeds 6-hour CI limit.
  - *Mitigation*: Pipeline checks if official download is feasible. If not, it automatically switches to a verified, pre-filtered S3 subset (simulating the full EBD) to ensure CI completion.
- **Risk**: NLCD raster is missing for specific coordinates.
  - *Mitigation*: Filter out observations where NLCD data is invalid or missing. Log count of dropped points.
- **Risk**: Foraging guild data missing for a top 25 species.
  - *Mitigation*: Drop species from the final training set if guild is unknown. Log the species.