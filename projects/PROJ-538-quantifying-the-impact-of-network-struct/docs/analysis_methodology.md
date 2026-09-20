# Analysis Methodology

## Overview

This document describes the methodological approach for quantifying the impact of network structure on heat transport in disordered alloys.

## Data Sources

### Real Data
- **OpenKim API**: Queries for Cu-Ni and Au-Ag molecular dynamics snapshots
- **Materials Cloud API**: Additional snapshot data for validation

### Synthetic Data
When real data is unavailable, synthetic snapshots are generated using:
- Lennard-Jones potentials via ASE (Atomic Simulation Environment)
- NVT thermalization with VelocityVerlet integrator
- Unique random seeds (0-49) for statistical independence

## Network Construction

### Defect Graph Definition
- **Nodes**: Individual atomic sites
- **Edges**: Connections between nearest-neighbor atoms of mismatched species
- **Method**: Voronoi tessellation with periodic boundary conditions (PBC)

### Voronoi Neighbor Detection
- Uses `pymatgen.analysis.sites.VoronoiNN(pbc=True)` or equivalent
- Handles periodic boundary conditions explicitly
- Fallback to distance-cutoff with warning if PBC data missing

## Topological Metrics

### Calculated Descriptors
1. **Clustering Coefficient**: Measures local connectivity
2. **Mean Degree**: Average number of connections per node
3. **Degree Distribution Moments**: Mean and variance of degree distribution
4. **Percolation Threshold**: Critical point for network connectivity

### Edge Cases
- Disconnected graphs: Metrics calculated on largest component
- Undefined metrics: Assigned NaN with warning logged to audit log

## Statistical Analysis

### Correlation Methods
- **Pearson Correlation**: Linear relationships
- **Spearman Correlation**: Monotonic relationships
- **Bonferroni Correction**: Multiple comparison adjustment

### Power Analysis
- Uses `statsmodels.stats.power.FTestPower`
- Reports minimum detectable effect size
- Flags when sample size N < 20

### Sensitivity Analysis
- Sweeps significance thresholds
- Verifies rank-order stability of correlation coefficients
- Ensures magnitude differences < 0.1

## Thermal Conductivity Estimation

### Callaway Model
- Estimates conductivity based on defect density and mass difference
- **Critical**: NOT derived from graph metrics to avoid tautology
- Based on phonon-scattering theory

## Validation

### Unit Tests
- Voronoi neighbor detection accuracy
- Metric calculation on known graph topologies
- Correlation calculation and p-value accuracy
- Edge case handling (N=1, missing metadata, NaN metrics)

### Integration Tests
- End-to-end pipeline execution
- Real vs. synthetic mode switching
- Output file generation and validation

## Reproducibility

### Random Seeds
- Synthetic generation uses seeds 0-49
- All random operations seeded for reproducibility

### Configuration Management
- All parameters stored in `code/config.py`
- Mode selection (REAL/SYNTHETIC) explicitly configurable

## Limitations

### Data Availability
- Real data fetch may fail; system switches to synthetic mode
- Synthetic data approximates real systems but may not capture all complexities

### Computational Constraints
- Large datasets processed in streaming mode
- Memory limitations handled via chunked processing

### Model Assumptions
- Lennard-Jones potentials approximate real interatomic forces
- Callaway model assumptions for thermal conductivity estimation
