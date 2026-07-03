# Implementation Plan: Statistical Analysis of Bird Migration and Climate Change

**Branch**: `001-bird-migration-climate-correlation` | **Date**: 2024-05-22 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-bird-migration-climate-correlation/spec.md`

## Summary
A reproducible, CPU‑only pipeline that (1) downloads or synthesises eBird and NOAA/PRISM data, (2) aggregates observations onto a 0.5° × 0.5° weekly grid, (3) computes phenology metrics, (4) fits a **Unified Spatial Model** (GAMM with a Matérn Gaussian Process spatial smooth), (5) conducts full 10,000‑shuffle permutation tests with early‑stop flagging, (6) analyses migration‑route shifts on a spherical manifold, and (7) produces validated outputs that satisfy all functional requirements (FR‑001‑FR‑007) and success criteria (SC‑001‑SC‑005).

## Technical Context
- **Environment**: GitHub Actions free tier (2 CPU cores, ~7 GB RAM, ≤ 6 h runtime).  
- **Language**: Python 3.11.  
- **Dependencies** (pinned in `requirements.txt`):  
  `pandas==2.2.1`, `numpy==1.26.4`, `scikit-learn==1.4.2`, `pygam==0.9.0`, `statsmodels==0.14.2`, `geopandas==0.14.2`, `shapely==2.0.3`, `pyyaml==6.0.1`, `tqdm==4.66.2`, `pytest==8.2.0`.

## Phase 1 – Data Acquisition & Archiving (FR‑001)

| Step | Action | Artifact |
|------|--------|----------|
| 1.1 | **Real‑Data Mode**: Download eBird Basic Dataset (‑2024) and NOAA/PRISM climate data into `data/raw/ebird/` and `data/raw/climate/`. Abort with clear error if files are missing. | `data/raw/ebird/ebird_2020_2024.csv`, `data/raw/climate/prism_2020_2024.parquet` |
| 1.2 | **Synthetic‑Data Fallback**: If the above files are absent, generate a synthetic dataset matching `contracts/dataset.schema.yaml` (a substantial number of rows, seeded 42). | `data/raw/synthetic_ebird.csv`, `data/raw/synthetic_climate.parquet` |
| 1.3 | Compute SHA‑256 checksums for all raw files and record them in `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml`. | `artifact_hashes` entry |
| 1.4 | Archive raw files unchanged (Principle VI). | No modification of raw files |

## Phase 2 – Preprocessing (FR‑002, FR‑003)

1. **Filtering** – Keep only migratory species (Cornell Lab list) and records from 2020‑2024.  
2. **Grid Assignment** – Convert lat/lon to 0.5° × 0.5° cells (`grid_cell = "lat_lon"`).  
3. **Weekly Aggregation** – Count observations per species‑grid‑week.  
4. **Phenology Metrics** –  
   - *First arrival*: 5th percentile DOY.  
   - *Median arrival*: 50th percentile DOY.  
   - *Stopover duration*: 90th – 10th percentile DOY.  
5. **Climate Averages** – Compute mean temperature, total precipitation, and extreme‑weather index for March‑May (spring) per grid‑week.  
6. **Sparse‑Data Handling** – Cells with `< 5` observations are flagged `data_quality="insufficient"` and excluded from modeling. **Sensitivity analysis** will re‑run the pipeline with thresholds of 3 and 7 to assess bias.  
7. **Tail‑Preserving Stratified Sampling** (new sub‑requirement **FR‑002‑S**) –  
   - Quantile‑bin `first_arrival` into deciles.  
 - Oversample cells in the lowest [deferred] decile by factor 2.
   - Assign inverse‑probability weights (`weight = 0.5` for oversampled cells, `1.0` otherwise).  
   - Weights are passed to the GAMM via `sample_weight`.  

All transformations write new files under `data/processed/`; originals remain untouched (Principle III).

## Phase 3 – Unified Spatial Model (FR‑004, FR‑005, FR‑007)

### Model Specification (Principle VII – full transparency)

```
phenology_metric ~
    s(temp) + s(precip) + s(extreme_idx) + s(effort) +
    (1 + temp | species) +
    GP_spatial(lon, lat; kernel=Matérn(nu=1.5))
```

- **Fixed smooth terms** (`s()`) are fitted with `pygam`.  
- **Random intercepts & slopes** are implemented via `statsmodels.MixedLM`.  
- **Spatial GP** uses `sklearn.gaussian_process.GaussianProcessRegressor` with a Matérn kernel (ν = 1.5). This satisfies the spec’s Matérn requirement without a conditional Moran’s I check.  
- **Observer effort** (e.g., checklist duration, number of observers) is mandatory; **habitat change** is optional if ancillary land‑cover data become available.  
- **Collinearity**: Variance Inflation Factor (VIF) calculated for climate covariates; any VIF > 5 triggers orthogonalization or removal, logged, and the model proceeds.

### Permutation Testing & FDR (FR‑005)

- **Full [deferred] shuffles** are performed for each coefficient to generate an empirical null distribution.
- **Early‑stop flag**: after 100 shuffles, if interim p < 0.001 the term is flagged “highly significant” for reporting, but the remaining shuffles continue so the final p‑value always reflects all 10,000 permutations.  
- **Benjamini–Hochberg (BH) FDR** is applied to the final p‑values; early‑stop does not affect BH assumptions because the final set of p‑values is unchanged.  
- **Power justification**: With 10,000 permutations, a medium effect size (Cohen’s f² ≈ 0.15) yields > 80 % power at α = 0.05 given the typical sample sizes (> 10 000 grid‑cell‑species combos).  

### Model Outputs (FR‑006, FR‑007)

- Coefficient estimates, p‑values, q‑values, AIC, R², convergence flag, and GP metadata are written to `data/processed/model_results.parquet`.  
- Convergence rate is calculated (SC‑003) and reported.  
- Moran’s I of residuals is computed **only for diagnostics** (not for conditional GP selection) and stored in the output.

## Phase 4 – Route Shift & Uncertainty (FR‑006, FR‑007)

1. **Centroid Construction** – Weekly centroids per species‑year (mean lat/lon of all observations in a cell).  
2. **Manifold Distance** – Geodesic distances on a spherical Earth (`geopy.distance.geodesic`).  
3. **Permutation Test** – A large number of label shuffles generate a null distribution of shift magnitudes; p‑values reported.  
4. **Bootstrap CI** – Bootstrap resamples of the centroid estimation process produce 95 % confidence intervals for shift magnitude and direction.  
5. **Validity Note** – Centroids are a simplification; an optional kernel‑density trajectory analysis (KDE on weekly occurrence maps) is implemented for species with ≥ 500 observations to verify robustness.

## Phase 5 – Validation, Reporting & CI Constraints (SC‑005)

- **Runtime budget**: Estimated total ≤ 5.5 h (Preprocess ≈ 1 h, GAMM ≈ 3 h, Permutations ≈ 1.5 h, Trajectories ≈ 0.5 h). All steps respect the 2‑CPU, ≤ 7 GB RAM limit via chunked I/O and `concurrent.futures` limited to 2 workers.  
- **Contract Tests**: `pytest tests/contract/test_schemas.py` validates all output files against `contracts/*.schema.yaml`.  
- **CI Job** `validate_quickstart` asserts total runtime < 4 h and that all contract tests pass.

## Constitution Check

| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| I. Reproducibility | PASS | Random seeds pinned (`seed=42`); deterministic synthetic generator; `requirements.txt` version‑pinned. |
| II. Verified Accuracy | PASS | No external citations beyond verified URLs (none required for synthetic mode). |
| III. Data Hygiene | PASS | Checksums recorded; transformations write new files; no in‑place edits. |
| IV. Single Source of Truth | PASS | All figures/statistics derived from `data/processed/*`. |
| V. Versioning Discipline | PASS | Artifact hashes stored; any change updates `updated_at`. |
| VI. Ecological Data Provenance | **PENDING** | Real data must be placed under `data/raw/` and archived unchanged; synthetic mode does not satisfy this principle. |
| VII. Statistical Model Transparency | PASS | Full model formula provided; `statsmodels`, `sklearn` versions pinned; GP Matérn kernel explicitly documented. |

## Traceability Matrix (FR / SC → Plan Elements)

| ID | Requirement | Plan Element |
|----|-------------|--------------|
| FR‑001 | Download & cache raw data | Phase 1 (real‑data mode) |
| FR‑002 | Filter & aggregate | Phase 2 (Filtering, Grid Assignment) |
| FR‑002‑S | Tail‑Preserving Stratified Sampling | Phase 2 (Sampling subsection) |
| FR‑003 | Compute phenology & climate averages | Phase 2 (Metrics) |
| FR‑004 | Fit GAMM with spatial autocorrelation | Phase 3 (Unified Spatial Model) |
| FR‑004‑U | Unified Spatial Model (GP always applied) | Phase 3 (Model Specification) |
| FR‑005 | 10,000 permutation shuffles & FDR | Phase 3 (Permutation Testing) |
| FR‑006 | Route shift analysis on manifold | Phase 4 |
| FR‑007 | Bootstrap 95 % CI for predictions | Phase 4 |
| SC‑001 | Power & effect‑size stability | Phase 3 (Power justification) |
| SC‑002 | Proportion of “insufficient data” cells | Phase 2 (Sparse‑data handling) |
| SC‑003 | GAMM convergence rate | Phase 3 (Convergence monitoring) |
| SC‑004 | CI width for phenology shift | Phase 4 (Bootstrap CI) |
| SC‑005‑A | Full [deferred] shuffles despite early‑stop | Phase 3 (Permutation Testing) |
| SC‑005‑B | Runtime ≤ 6 h on free‑tier CI | Phase 5 (Runtime budget) |

## Project Structure

```
specs/001-bird-migration-climate-correlation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md

src/
├── data/
│   ├── download.py          # Synthetic generator + real‑data loader
│   ├── preprocess.py        # Grid, phenology, sampling, weights
│   └── impute.py            # Spatial interpolation (1° radius)
├── models/
│   ├── gamm.py              # Unified Spatial Model implementation
│   ├── trajectory.py        # Manifold trajectory & optional KDE
│   └── utils.py             # Permutation test with early‑stop flag
├── cli/
│   └── run_pipeline.py      # Entry point (`--mode synthetic|real`)
└── lib/
    └── config.py            # Global constants, seeds, thresholds

data/
├── raw/                     # Archived eBird & PRISM files (when available)
├── processed/               # Phenology, model results, trajectory shifts
└── interim/                 # Intermediate objects (weights, centroids)

tests/
├── contract/
│   └── test_schemas.py
├── integration/
│   └── test_quickstart.py
└── unit/
    ├── test_preprocess.py
    └── test_models.py
```

--- End of Plan ---
