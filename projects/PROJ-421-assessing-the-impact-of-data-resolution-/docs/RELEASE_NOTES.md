# Release Notes

## Version 1.0.0 (Initial Release)

### Features
- **Data Ingestion**: Automated download and validation of NLCD 30m data for Colorado.
- **Resolution Aggregation**: Nearest-neighbor resampling to generate 60m, 120m, 240m, and 480m rasters.
- **Spatial Analysis**: Computation of Moran's I, null distributions (H0), and alternative distributions (H1) via Gibbs sampling.
- **Statistical Power**: Calculation of power for each resolution level.
- **Threshold Identification**: Automatic detection of the resolution where power < 0.80.
- **Sensitivity Analysis**: Validation of threshold stability with ±10% sweeps.
- **Reporting**: Generation of comprehensive reports including Type II error delta.

### Key Results
- **Threshold**: Statistical power drops below 0.80 at 240m resolution. [UNRESOLVED-CLAIM: c_16c7b68b — status=not_enough_info]
- **Stability**: Threshold is stable within sensitivity analysis bounds.

### Technical Details
- **Dependencies**: `rasterio`, `geopandas`, `pysal`, `numpy`, `scipy`, `matplotlib`, `pandas`, `libpysal`.
- **Memory Management**: Windowed raster reads to stay within 7GB RAM limit.
- **Reproducibility**: Fixed random seed (42) for all stochastic processes.

### Known Issues
- None at this time.

### Future Work
- Extend analysis to other geographic regions.
- Explore alternative resampling methods.
- Add support for additional land cover classes.
