# Design Documentation: Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation

## Overview
This document outlines the architectural design and implementation strategy for the project `PROJ-107`. The goal is to quantify the relationship between dark matter halo shapes (triaxiality, axial ratios) and galaxy formation properties (star formation rate, size) using cosmological simulation data.

## Architecture
The pipeline follows a modular, chunked-processing architecture designed to operate within strict hardware constraints (7GB RAM, CPU-only).

### Directory Structure
- `code/`: Source code modules
 - `ingestion/`: Data loaders (TNG-100, Millennium-II)
 - `processing/`: Core physics calculations (Inertia tensors, shape metrics, alignment)
 - `analysis/`: Statistical tests, correlation analysis, report generation
 - `utils/`: Configuration, I/O utilities, logging
 - `tests/`: Unit and integration tests
- `data/`: Data storage
 - `raw/`: Downloaded simulation snapshots (HDF5)
 - `processed/`: Derived datasets (CSVs for halo shapes, statistical results)
- `docs/`: Documentation (this file, API specs)
- `paper/`: Research report templates and final outputs

### Data Flow
1. **Ingestion**: `tng_loader.py` fetches metadata and HDF5 files from the TNG API.
2. **Processing**: `pipeline_runner.py` iterates over haloes in chunks.
 - Computes reduced inertia tensors (`inertia_tensor.py`).
 - Derives shape metrics: axial ratios ($b/a, c/a$) and triaxiality ($T$) (`shape_metrics.py`).
 - Filters haloes with $N < 10,000$ particles.
3. **Analysis**: `run_statistical_analysis.py` and `correlation_analysis.py` perform:
 - Mass-matching (Nearest Neighbor) to control for confounding.
 - Non-parametric tests (Kruskal-Wallis, Mann-Whitney U, KS).
 - Linear regression with mass control.
 - Bonferroni correction for multiple comparisons.
4. **Robustness**: `sensitivity.py` sweeps binning thresholds to verify stability.
5. **Alignment**: `alignment.py` computes spin-spin and major-major misalignment angles.

### Key Design Decisions
- **Chunked Processing**: To respect the 7GB RAM limit, data is processed in configurable chunks rather than loading entire snapshots.
- **Associational Only**: All output datasets include `associational_only=true` to reflect the correlational nature of the study.
- **Fail-Loudly Data Fetching**: Loaders do not fall back to synthetic data. If a real source is unreachable, the pipeline halts to prevent fabrication.
- **Mass-Matching**: Instead of propensity score stratification, nearest-neighbor matching is used for mass control as per project constraints.

## Constraints & Deviations
- **Hardware**: 7GB RAM, CPU-only. This necessitates sampling or chunking, deviating from the theoretical "every halo" requirement (FR-001) to satisfy feasibility (SC-005).
- **Data Availability**: If Millennium-II or WDM variants are not publicly accessible via verified URLs, the pipeline logs the gap, marks SC-004 as 'Not Measurable', and proceeds with TNG-100.

## Success Criteria
- SC-001: Compute axial ratios and triaxiality for valid haloes.
- SC-002: Detect statistical correlations with p < 0.01 (Bonferroni corrected).
- SC-003: Sensitivity analysis shows p-value variance ≤ 0.001 across thresholds.
- SC-005: Pipeline executes successfully within resource constraints.
