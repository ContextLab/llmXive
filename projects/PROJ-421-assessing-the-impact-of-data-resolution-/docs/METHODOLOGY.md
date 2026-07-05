# Methodology

## Research Question

How does the resolution of spatial data affect the statistical power to detect spatial autocorrelation in land cover patterns?

## Hypotheses

- **H0 (Null)**: Spatial patterns are random (no autocorrelation).
- **H1 (Alternative)**: Spatial patterns exhibit significant autocorrelation (modeled via Gibbs Sampler).

## Data Source

- **Dataset**: National Land Cover Database (NLCD) 2019.
- **Region**: Colorado, USA.
- **Resolution**: 30m (original), aggregated to 60m, 120m, 240m, 480m.

## Methodology Steps

### 1. Data Ingestion
- Download high-resolution NLCD data.
- Validate integrity via checksums.

### 2. Resolution Aggregation
- Use nearest-neighbor resampling to generate coarser rasters.
- Preserve categorical integrity (no interpolation).

### 3. Binary Indicator Map
- Convert land cover to binary: Forest (Class 41, 42, 43) = 1, Others = 0.

### 4. Spatial Autocorrelation
- Compute Moran's I for each resolution.
- Generate null distribution (H0) via 1,000 random permutations.
- Simulate alternative distribution (H1) via Gibbs Sampler using a calibrated λ parameter.

### 5. Statistical Power
- Calculate power as the proportion of H1 simulations where p < 0.05.

### 6. Threshold Identification
- Identify the resolution where power drops below 0.80.
- Perform sensitivity analysis (±10% sweep) to validate stability.

### 7. Reporting
- Generate power curves, threshold reports, and final analysis.

## Statistical Models

### Moran's I
$$ I = \frac{n}{\sum_i \sum_j w_{ij}} \frac{\sum_i \sum_j w_{ij}(x_i - \bar{x})(x_j - \bar{x})}{\sum_i (x_i - \bar{x})^2} $$

### Gibbs Sampler (H1)
- Binary spatial autoregressive process.
- Calibrated λ from 30m data.

## Validation

- **Checksumming**: All downloaded and generated files validated.
- **Reproducibility**: Fixed random seed (42).
- **Memory Constraints**: Windowed I/O to stay within 7GB RAM.

## Limitations

- Analysis limited to Colorado region.
- Binary indicator map simplifies land cover complexity.
- Nearest-neighbor resampling may introduce artifacts at boundaries.
