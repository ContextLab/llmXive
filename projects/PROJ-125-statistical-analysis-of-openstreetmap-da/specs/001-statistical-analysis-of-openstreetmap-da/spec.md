# Specification: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Overview
This project implements a statistical pipeline to analyze the relationship between OpenStreetMap (OSM) derived urban features and Land Surface Temperature (LST) to quantify Urban Heat Island (UHI) effects.

## Functional Requirements

### FR-001: Data Ingestion
The system must ingest raw vector data from OpenStreetMap (OSM) including buildings, land-use, trees, and roads.

### FR-002: Satellite Thermal Data
The system must ingest satellite thermal data (MODIS/Landsat) for the most recent 5-year period.

### FR-003: Rasterization
All data must be reprojected to a common CRS (EPSG:3857 or Local UTM) and resampled to a standardized 30m resolution.

### FR-004: Exploratory Analysis
The system must compute correlation matrices and spatial autocorrelation metrics (Moran's I).

### FR-005: Spatial Regression Modeling
The system must fit OLS, SAR, and GWR models.

**Memory Constraint Fallback Strategy (Governing Rule):**
If memory constraints prevent fitting all three models (OLS, SAR, GWR) simultaneously or if spatial block sampling fails to reduce the dataset size below the threshold (N < 500k), the system **MUST** degrade gracefully to an **OLS-only** execution path.

- **Trigger**: Memory safety check (T026a) indicates >5GB usage OR spatial sampling (T026b) fails to reduce N sufficiently.
- **Action**: Skip SAR (T028) and GWR (T029) model fitting.
- **Execution**: Proceed only with OLS Baseline (T027) using the sampled or full dataset.
- **Logging**: The system must log `model_type: OLS_DEGRADED` in `data/results/metrics.csv` and stdout.
- **Integrity**: This fallback is the governing rule for memory constraints and supersedes the requirement for three models when resources are insufficient. The pipeline must not crash; it must complete with the degraded model set.

### FR-006: Spatial Cross-Validation
The system must implement 5-fold spatial cross-validation to prevent data leakage.

### FR-007: Model Evaluation
The system must calculate RMSE, MAE, and R² for all fitted models.

### FR-008: Multiple-Comparison Correction
The system must apply Permutation-based FDR with Meff adjustment for p-values.

### FR-009: Sensitivity Analysis
The system must perform a GWR bandwidth sweep to assess model stability.

### FR-010: Proxy Validity
The system must calculate the "Unexplained Variance Gap" by comparing observed R² against literature-derived upper bounds.

## Non-Functional Requirements

### SC-001: Reproducibility
All results must be reproducible with documented random seeds and data versions.

### SC-002: Data Integrity
No synthetic data generation is allowed for input datasets. All data must be fetched from real sources.

### SC-003: Traceability
All metrics must include the `correction_method` string in output CSVs.

### SC-004: Reporting
Sensitivity reports must visualize stability of R² across bandwidths.

### SC-005: Memory Safety
The system must not exceed 6GB RAM usage during execution.

## Data Model
- **CityBoundary**: Name, BBox, CRS
- **RasterCovariate**: Path, Resolution, CRS, Variable Name
- **TemperatureRaster**: Path, Resolution, CRS, Time Range

## Execution Flow
1. Ingest OSM and Satellite Data (T012, T013)
2. Align and Rasterize (T014, T015)
3. Exploratory Analysis (T019, T020)
4. Memory Check & Sampling (T026a, T026b)
5. Model Fitting (T027, T028, T029) - *Subject to FR-005 Fallback*
6. Cross-Validation & Metrics (T030, T031)
7. Sensitivity & Proxy Validity (T034, T032)
8. Export Results (T033)