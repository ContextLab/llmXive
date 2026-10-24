# Feature Specification: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change  

**Feature Branch**: `001-statistical-analysis-of-publicly-availab`  
**Created**: 2026-10-24  
**Status**: Draft  
**Input**: User description: “Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change”  

## User Scenarios & Testing *(mandatory)*  

### User Story 1 – Data Acquisition and Preprocessing Pipeline (Priority: P1)  

**User story (US‑1)**  
The system must ingest eBird observations and NOAA/PRISM climate products, filter them to a curated list of migratory species for the years 2020‑2022, and aggregate the data onto a 0.5° × 0.5° grid, computing first‑arrival date, median‑arrival date, and stopover duration for each species‑grid‑year combination.  

**Why this priority**: A clean, reproducible dataset is the prerequisite for any downstream statistical inference.  

**Independent Test**: Run the preprocessing scripts on a single species (e.g., *Setophaga petechia*) within a single grid cell and verify that the output CSV contains the columns `species, grid_cell, year, first_arrival, median_arrival, stopover_duration, temp_spring, precip_spring, extreme_idx` with no missing values in these fields.  

**Acceptance Scenarios**  

1. **Given** the raw eBird and NOAA files are accessible (either streamed or sampled), **when** the preprocessing pipeline is executed with the 2020‑2022 filter, **then** the resulting dataset contains at least 90 % of the expected species‑year‑grid combinations (i.e., ≤ 10 % marked “insufficient data”) and all phenology metrics are calculated from observed records only.  
2. **Given** a grid cell that contains fewer than 5 observations for a species in a given year, **when** the aggregation step runs, **then** that cell is flagged as “insufficient data” and excluded from the modeling stage, with a log entry recording the species, grid cell, year, and reason.  

---  

### User Story 2 – Phenology‑Climate Correlation Modeling (Priority: P2)  

**User story (US‑2)**  
The system must fit Generalized Additive Mixed Models (GAMMs) that relate each phenology metric to spring temperature, precipitation, and an extreme‑weather index, while accounting for species‑level random intercepts and random slopes for year. The models must be evaluated with permutation‑based empirical p‑values and corrected for multiple testing.  

**Why this priority**: This step directly addresses the research question by providing statistically robust evidence of climate‑phenology relationships.  

**Independent Test**: Fit the GAMM script on a synthetic dataset (generated with known smooth relationships) and confirm that the estimated smooth terms recover the true effect sizes within a 5 % tolerance and that the permutation‑derived p‑values correctly flag the known significant terms.  

**Acceptance Scenarios**  

1. **Given** a pre‑processed dataset for a single species, **when** the GAMM is fitted with spring temperature as a smooth term, **then** the model converges in ≤ 300 seconds, returns a p‑value < 0.05 after Benjamini–Hochberg FDR correction, and reports the estimated smooth curve.  
2. **Given** residuals that exhibit spatial autocorrelation (Moran’s I > 0.15), **when** the diagnostics module runs, **then** the system flags the model, refits it with a Gaussian Process random effect using a Matérn covariance, and records the improved Moran’s I in the log.  

---  

### User Story 3 – Route‑Shift Analysis and Uncertainty Quantification (Priority: P3)  

**User story (US‑3)**  
The system must compute weekly migration centroids for each species‑year, represent the centroid trajectories on a Riemannian manifold, and quantify spatial route shifts with 95 % confidence angles. Additionally, the pipeline must produce bootstrapped 95 % confidence intervals for phenology‑shift predictions.  

**Why this priority**: Spatial route changes complement timing analyses and provide a fuller picture of climate impacts on migration.  

**Independent Test**: Apply the trajectory module to a synthetic set of centroids that contain no true shift; verify that the permutation test yields p > 0.05 and that the reported shift magnitude is ≤ 1 km.  

**Acceptance Scenarios**  

1. **Given** weekly centroid coordinates for a species, **when** the Riemannian trajectory analysis is executed, **then** the output includes a shift vector (magnitude in km, bearing in degrees, 95 % confidence angle in degrees) and a permutation‑derived p‑value, with total runtime ≤ 1800 seconds.  
2. **Given** model‑based phenology predictions, **when** the bootstrapping routine draws 1000 resamples, **then** the resulting 95 % confidence interval width for the predicted shift is ≤ 3 days.  

### Edge Cases  

- **Sparse observations** – When a species has fewer than 5 observations in a grid cell for a given year, the pipeline marks the cell as “insufficient data” and excludes it from modeling.  
- **Missing climate raster cells** – If a climate raster lacks a value for a particular grid‑week, the system imputes the value using inverse‑distance weighting from neighboring cells within a 1° radius and records the imputation flag in the metadata.  
- **Model non‑convergence** – If a GAMM fails to converge after 10 optimization attempts, the system logs the failure, skips that species‑year, and continues with the remaining dataset, ensuring the overall pipeline does not abort.  

## Requirements *(mandatory)*  

### Functional Requirements  

- **FR-001**: The system MUST acquire eBird observations for North America (2020‑2022) **by streaming** the eBird Basic Dataset (EBD) through the eBird API and applying a species‑level filter, such that the total on‑disk footprint never exceeds **5 GB** at any point. Temporary raw files are deleted immediately after filtering. (See US-1)  
- **FR-002**: The system MUST download NOAA GHCN‑Daily temperature & precipitation files and PRISM extreme‑weather rasters for the same period, **ensuring the combined climate data on‑disk ≤ 2 GB**. (See US-1)  
- **FR-003**: The system MUST filter eBird records to a curated list of 20 long‑distance migratory species, aggregate observations to weekly counts per 0.5° × 0.5° grid cell, and compute the three phenology metrics (first arrival, median arrival, stopover duration) **using only observed dates** (no synthetic imputation of phenology). (See US-1)  
- **FR-004**: The system MUST compute seasonal climate averages (mean March‑May temperature, total precipitation, extreme‑weather index) for each grid‑cell‑week. (See US-2)  
- **FR-005**: The system MUST fit GAMMs with phenology metrics as responses, climate variables as smooth fixed effects, and species‑year random intercepts/slopes; spatial autocorrelation is diagnosed with Moran’s I and, if needed, mitigated with a Gaussian Process random effect (Matérn covariance). (See US-2)  
- **FR-006**: The system MUST perform 10 000 permutation shuffles for each smooth term, derive empirical p‑values, and apply the Benjamini–Hochberg FDR correction across all species‑climate tests. (See US-2)  
- **FR-007**: The system MUST represent weekly migration centroids as trajectories on a Riemannian manifold using the `geomstats` library, compute shift vectors (magnitude, bearing, confidence angle), and obtain permutation‑based significance. (See US-3)  
- **FR-008**: The system MUST generate 95 % confidence intervals for phenology‑shift predictions via bootstrap resampling (≥ 1000 resamples). (See US-3)  
- **FR-009**: The system MUST **deliver** (a) all preprocessing, modeling, and trajectory scripts; (b) intermediate CSVs; (c) fitted model objects; (d) figures and maps; and (e) a concise HTML report, packaged in a reproducible repository. (See US-3)  
- **FR-010**: The system MUST ensure that **no fabricated or placeholder values** are used in any reported metric; all numbers must originate from observed eBird or NOAA/PRISM data or from formally defined statistical procedures (e.g., permutations, bootstraps). **Verification:** For every numeric field the pipeline writes a provenance log entry (source file, record identifier, SHA‑256 checksum). An automated audit script parses all output CSVs and asserts that each value appears in the provenance log and that no sentinel placeholders (e.g., `-9999`, `NaN`) exist. (See US-3)  

### Key Entities  

- **MigrationRecord** – bird observation with attributes: `species, latitude, longitude, date, count, checklist_id`.  
- **PhenologyMetric** – computed per `species, grid_cell, year` with attributes: `first_arrival, median_arrival, stopover_duration`.  
- **ClimateVariable** – per `grid_cell, week` with attributes: `mean_temperature, total_precipitation, extreme_weather_index`.  
- **Trajectory** – weekly centroids for a `species, year` with attributes: `weekly_centroids (list of lat/lon)`, `shift_vector`.  

## Success Criteria *(mandatory)*  

### Measurable Outcomes  

- **SC-001**: Statistical power to detect a smooth‑term effect explaining at least **R² ≥ 0.02** ([deferred] of variance) is **≥ 0.80**. Power is estimated **a priori** via 1 000 simulated datasets per species using the `simr` (or `powerSim`) R package, specifying the intended sample size (number of species‑year‑grid cells) and the target variance‑explained effect. (See US-2)
- **SC-002**: The proportion of grid cells flagged “insufficient data” after preprocessing is **≤ 10 %** of total cells. (See US-1)  
- **SC-003**: GAMM convergence rate (successful fits / total attempted fits) is **≥ 90 %**. (See US-2)  
- **SC-004**: Width of bootstrapped 95 % confidence intervals for phenology‑shift predictions is **≤ 3 days**. (See US-3)  
- **SC-005**: Total runtime of the end‑to‑end pipeline on a GitHub Actions free‑tier runner is **≤ 7200 seconds** (2 hours), staying within the CI time limit.  
- **SC-006**: All generated figures, tables, and CSVs are reproducibly recreated by re‑running the pipeline on the same streamed data without manual intervention.  

## Assumptions  

- **Data‑use agreement** – Access to the eBird Basic Dataset requires a signed data‑use agreement with the Cornell Lab of Ornithology; the pipeline includes a pre‑run check that the user has accepted the agreement and stored the required token in a protected secret (`EBIRD_TOKEN`).  
- **Observer effort** – eBird records include effort covariates (checklist duration, number of observers). The modeling step incorporates these covariates as fixed effects to mitigate detection bias.  
- **Computational environment** – The analysis runs on a GitHub Actions free‑tier runner providing **≤ 2 CPU cores**, **≈ 7 GB RAM**, **≤ 14 GB disk**, and **≤ 6 hours** total job time. All scripts are CPU‑only; no GPU, CUDA, or large‑model inference is required.  
- **Sampling strategy** – Because the full EBD exceeds the disk quota, the pipeline streams the dataset and applies an on‑the‑fly filter for the 20 target species and the 2020‑2022 window, ensuring the on‑disk data never exceeds the 5 GB limit specified in FR‑001.  
- **Statistical assumptions** – The Benjamini–Hochberg procedure is sufficient for controlling the false discovery rate given the number of species‑climate tests; permutation counts (10 000) provide stable empirical p‑values.  
- **Spatial resolution** – Grid cells are defined using the C‑squares system with a cell size of **0.5°** (source: C‑squares, https://en.wikipedia.org/wiki/C-squares).  

---  

*End of Specification*