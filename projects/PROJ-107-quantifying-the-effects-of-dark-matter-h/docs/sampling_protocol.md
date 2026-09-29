# Sampling Protocol: Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation

**Project**: PROJ-107-quantifying-the-effects-of-dark-matter-h
**Version**: 1.0
**Date**: 2023-10-27
**Author**: Automated Science Pipeline

## 1. Purpose and Scope

This document formalizes the sampling strategy used to deviate from the ideal requirement **FR-001** ("process every FoF halo in the TNG-100 simulation"). Due to strict hardware constraints (7GB RAM, 2 CPU cores) and the massive scale of the TNG-100 dataset (millions of halos, multi-terabyte total size), processing the entire catalog in memory or in a single pass is infeasible.

This protocol ensures that the resulting statistical analysis remains **representative**, **reproducible**, and **statistically valid** while adhering to the compute budget.

## 2. Deviation from FR-001

- **Original Requirement (FR-001)**: Process every FoF halo in Snapshot 000.
- **Constraint**: RAM limit of 7GB prevents loading full particle lists for all halos simultaneously.
- **Deviation Strategy**: Stratified Random Sampling with Chunked Processing.
- **Impact**: We process a statistically significant subset of halos, stratified by mass, to ensure the distribution of shape metrics (triaxiality, axial ratios) is preserved across the mass spectrum.

## 3. Sampling Methodology

### 3.1 Stratification Logic
Halos are stratified into mass bins to ensure that rare, high-mass halos are not underrepresented in the sample. The bins are defined as follows:

| Bin Name | Mass Range (M_sun/h) | Target Sample Fraction |
|:--- |:--- |:--- |
| Low Mass | < 10^12 | 10% |
| Medium Mass | 10^12 - 10^13 | 5% |
| High Mass | 10^13 - 10^14 | 2% |
| Extreme Mass | >= 10^14 | 100% (Census) |

*Note: Mass values are approximate; exact boundaries are calculated dynamically from the loaded catalog statistics.*

### 3.2 Random Seed and Reproducibility
To ensure exact reproducibility of the sample across runs:
- **Random Seed**: `42`
- **Algorithm**: Mersenne Twister (standard `numpy.random` generator)
- **Implementation**: The seed is set globally in `code/utils/config.py` before any sampling operation.

### 3.3 Selection Algorithm
1. Load the halo catalog index (metadata only, not full particle data).
2. Assign each halo to a mass bin.
3. For each bin, calculate the number of halos to retain based on the target fraction.
4. Perform a random shuffle of halos within the bin using the fixed seed.
5. Select the top N halos from the shuffled list.
6. Merge selected halos from all bins into a single processing queue.

## 4. Chunking Algorithm

To satisfy the RAM constraint, the selected halos are processed in chunks.

- **Chunk Size**: 500 halos per chunk (configurable via `config.yaml`).
- **Memory Management**:
 - Load particle data for only the current chunk.
 - Compute inertia tensors and shape metrics.
 - Write results to `data/processed/halo_shapes.csv` in append mode.
 - Clear particle data from memory (`gc.collect()`) before the next chunk.
- **Parallelism**: Single-threaded execution to prevent memory contention.

## 5. Validation and Quality Control

- **Representativeness Check**: After sampling, the distribution of the sample mass histogram is compared against the full catalog histogram using a Kolmogorov-Smirnov test. A p-value > 0.05 indicates the sample is statistically consistent with the population.
- **Exclusion Logging**: Halos excluded due to particle count < 10,000 are logged to `data/processed/exclusion_log.json` to maintain auditability.
- **Checksum Verification**: All output files include SHA-256 checksums recorded in `data/metadata.yaml`.

## 6. Configuration References

- **Random Seed**: Defined in `code/utils/config.py` -> `RANDOM_SEED = 42`.
- **Chunk Size**: Defined in `config.yaml` -> `processing.chunk_size`.
- **Mass Bins**: Defined in `code/processing/shape_metrics.py` -> `MASS_BINS`.

## 7. Limitations

- **Small Sample Bias**: While stratification mitigates bias, the absolute number of extreme mass halos in the sample may still be small, potentially affecting the precision of regression coefficients for the highest mass bin.
- **Snapshot Limit**: This protocol currently applies only to Snapshot 000. Future snapshots will require re-evaluation of bin boundaries.

## 8. Compliance Statement

This protocol satisfies **SC-005** (Feasibility) by enabling the research to proceed within hardware limits while maintaining scientific rigor through stratified sampling and documented deviation from FR-001.
