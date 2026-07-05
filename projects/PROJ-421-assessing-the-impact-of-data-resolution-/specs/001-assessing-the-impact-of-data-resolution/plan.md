# Implementation Plan: Assessing the Impact of Data Resolution on Statistical Power in Publicly Available Spatial Datasets

**Branch**: `001-assess-resolution-power` | **Date**: 2026-06-26 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-assess-resolution-power/spec.md`

## Summary

This project implements a computational pipeline to quantify how spatial data resolution affects the statistical power to detect spatial autocorrelation (Moran's I). The approach involves ingesting high-resolution (30m) National Land Cover Database (NLCD) data, aggregating it to coarser resolutions (60m–480m) using nearest-neighbor resampling, transforming categorical data into binary indicators, and running permutation-based hypothesis tests and power simulations across the resolution spectrum. The pipeline identifies the resolution threshold where statistical power drops below an acceptable level.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `rasterio`, `geopandas`, `pysal` (specifically `esda.moran`), `numpy`, `scipy`, `matplotlib`, `pandas`, `libpysal`
**Storage**: Local file system (raster `.tif` files, CSV results)
**Testing**: `pytest` (unit tests for resampling logic, integration tests for pipeline execution)
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, ~7 GB RAM)
**Project Type**: Data analysis pipeline / CLI tool
**Performance Goals**: Complete full pipeline (30m to 480m, 2000 simulations per level) within 6 hours on CPU-only runner.
**Constraints**: CPU-only (no CUDA/GPU), memory usage < 7 GB, disk usage < 14 GB.
**Scale/Scope**: Single state region (Colorado), resolution levels, A substantial number of statistical tests per level.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| **I. Reproducibility** | **Compliant** | All random seeds (numpy, pysal) will be pinned in `code/`. External NLCD data fetched from verified HuggingFace URLs. |
| **II. Verified Accuracy** | **Compliant** | Citations to NLCD sources restricted to the verified URLs provided in the input block. **Phase 4 includes explicit step to run Reference-Validator Agent.** |
| **III. Data Hygiene** | **Compliant** | Raw data (30m NLCD) preserved in `data/raw/`. Aggregated rasters saved as new files in `data/derived/`. Checksums recorded in `state/`. |
| **IV. Single Source of Truth** | **Compliant** | Power curves and threshold reports generated programmatically from `data/derived/` results; no hand-typed numbers. |
| **V. Versioning Discipline** | **Compliant** | Artifacts (rasters, CSVs) will be hashed. `state/` updated on artifact change. |
| **VI. Spatial Statistical Validity** | **Compliant** | Pipeline explicitly implements a sufficient number of permutations for H0 and simulations for H1 to ensure statistical robustness. **Benjamini-Hochberg correction** applied for multiple classes. Power < 0.80 reported as inferential limit. |
| **VII. Categorical Data Integrity** | **Compliant** | Resampling strictly uses `rasterio.warp.resampling.nearest` to preserve integer categories. |

## Memory Management Strategy

The full high-resolution NLCD for Colorado (large-scale grid) exceeds the 7GB RAM limit if loaded entirely into a NumPy array. The implementation MUST:
1. **Memory-Mapped I/O**: Use `rasterio` windowed reads to process the raster in tiles (e.g., 2000x2000 pixels) rather than loading the whole file.
2. **Lazy Evaluation**: Utilize `dask` or generator-based pipelines for the permutation steps where possible to avoid materializing full permutation matrices.
3. **Chunked Analysis**: Process each resolution level sequentially, clearing memory between levels.
4. **Sampling for Calibration**: If the calibration phase (Phase 0) requires heavy computation, use a representative [deferred] random sample of the 30m grid to estimate parameters, then apply to the full grid for the sweep.

## Project Structure

### Documentation (this feature)

```text
specs/001-assess-resolution-power/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/
├── __init__.py
├── main.py # CLI entry point
├── config.py # Configuration (resolutions, seeds, paths)
├── data_ingestion.py # NLCD download and subsetting
├── resampling.py # Nearest-neighbor aggregation logic
├── calibration.py # Lambda estimation (MLE) from 30m data
├── analysis.py # Moran's I, permutations, power simulation (Gibbs)
├── visualization.py # Power curve generation
└── utils.py # Logging, checksumming, memory-mapped I/O

projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/
├── raw/ # Downloaded NLCD (30m)
├── derived/ # Aggregated rasters (60m, 120m, etc.)
└── results/ # CSVs of Moran's I and Power

projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/
├── test_resampling.py
├── test_analysis.py
└── test_integration.py
```

**Structure Decision**: Single project structure selected to maintain tight coupling between data processing and statistical analysis, minimizing I/O overhead on the limited runner environment.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **None** | The complexity is minimal (linear pipeline). No architectural over-engineering is required. | N/A |

## Implementation Phases & FR/SC Mapping

### Phase 0: Calibration & Parameter Estimation
*Addresses: Methodology Rigor, Scientific Soundness*
1. **Estimate Lambda**: Load a representative subset of the 30m binary map.
 * **Method**: Use Maximum Likelihood Estimation (MLE) or GMM to estimate the spatial lag parameter ($\lambda$) that best fits the observed spatial autocorrelation in the 30m data.
 * **Output**: A single, fixed $\lambda$ value to be used for all H1 simulations.
2. **Validate Model Fit**: Ensure the estimated $\lambda$ produces a synthetic dataset with Moran's I statistically indistinguishable from the observed 30m data (within 5% error).
 * *Rationale*: This ensures H1 represents the "true" underlying structure of the specific dataset, avoiding arbitrary parameter injection.

### Phase 1: Data Ingestion and Resolution Aggregation
*Addresses: FR-001, FR-002, SC-003, Constitution Principle VII*
1. **Download**: Fetch NLCD 30m subset for Colorado from the verified URL: `. Validate checksum.
2. **Aggregate**: Generate multiple raster resolutions at varying scales. using nearest-neighbor resampling.
 * *Constraint*: Ensure categorical integrity (no interpolation artifacts).
 * *Memory*: Use chunked processing to stay within 7GB RAM.
3. **Validate**: Verify file existence and metadata for all resolution levels.

### Phase 2: Spatial Autocorrelation & Power Simulation
*Addresses: FR-003, FR-004, FR-005, SC-001, SC-002, Constitution Principle VI*
1. **Transform**: Convert categorical rasters to binary indicators (e.g., Forest=1, Others=0).
2. **H0 Simulation**: Run a sufficient number of random permutations for each resolution to build a null distribution.
3. **H1 Simulation**: Generate a substantial number of synthetic datasets for each resolution using a **Gibbs Sampler** (binary spatial autoregressive process) with the fixed $\lambda$ derived in Phase 0.
 * *Rationale*: Replaces linear lag injection to ensure construct validity for binary data.
4. **Calculate**: Compute observed Moran's I and p-values.
5. **Validate H1 Structure**: Compare the spatial autocorrelation of the synthetic H1 data against the observed 30m data to ensure the simulation mimics the true signal.
6. **Power**: Calculate power as the proportion of H1 simulations where p < 0.05 (or equivalent rejection rate).
 * *Correction*: Apply **Benjamini-Hochberg** correction for multiple testing if multiple classes are analyzed.

### Phase 3: Threshold Identification & Visualization
*Addresses: FR-006, FR-007, SC-001, SC-004*
1. **Plot**: Generate Power-vs-Resolution curve.
2. **Identify**: Locate resolution where power < 0.80.
3. **Calculate Type II Error Delta**: Compute the percentage point increase in Type II error (1 - power) relative to the 30m baseline. (Addresses SC-002).
4. **Sensitivity Analysis (Mandatory)**: Sweep the resolution aggregation factor by ±10% around the identified inflection point. Verify the threshold does not vary by more than one resolution step. (Addresses SC-004).
5. **Multi-Class Sensitivity**: Repeat the analysis for at least one other distinct land cover class (e.g., Urban) to ensure results are not artifacts of a single binary threshold. (Addresses Scientific Soundness).
6. **Report**: Output specific resolution threshold and delta metrics.

### Phase 4: Integration & Verification
*Addresses: SC-003, Edge Cases, Constitution Principle II*
1. **Retry Logic**: Implement exponential backoff for API failures (FR-001 edge case).
2. **Bounds Check**: Skip resolutions that exceed dataset bounds.
3. **End-to-End**: Run full pipeline on GitHub Actions runner to verify < 6h runtime and < 7GB RAM.
4. **Verified Accuracy Gate**: Execute the Reference-Validator Agent to confirm all citations (NLCD URLs) are reachable and match the primary source before marking `research_complete`.

## Compute Feasibility Plan

- **Environment**: GitHub Actions free-tier (2 CPU, 7 GB RAM).
- **Strategy**:
 - Use `pysal` (pure Python/Cython) which is CPU-native.
 - **Memory**: Strictly use `rasterio` windowed reads and chunked processing.
 - **Calibration**: Limit MLE estimation to a [deferred] random sample of the 30m grid.
 - **Simulations**: A sufficient number of permutations/simulations per level. If runtime exceeds a significant duration, reduce to a representative sample size for the final sweep (documented as a limitation).
 - Pin `numpy` and `scipy` versions to ensure CPU-wheel compatibility.
 - No GPU/CUDA dependencies.