"""
Resampling module for generating coarser resolution rasters from high-resolution
spatial data using nearest-neighbor aggregation.

This module implements the core logic for the 'zoom out' operation on spatial
datasets, aggregating fine-resolution pixels into larger blocks while preserving
the categorical integrity of land cover classifications.

Nearest-neighbor aggregation is the preferred method for categorical data (such as
NLCD land cover classes) because it:
1. Preserves integer class values without interpolation artifacts.
2. Maintains the original distribution of categorical values.
3. Avoids the creation of non-existent intermediate classes.

The aggregation process works by dividing the input raster into non-overlapping
windows of size (factor x factor) and selecting the dominant (or first) pixel
value within each window for the output raster. This effectively reduces the
spatial resolution by the specified factor.

Key Functions:
- generate_resolution(input_path, factor): Generates a single coarser resolution
  raster using chunked processing to manage memory usage.
- CLI Interface: Supports command-line execution to process multiple resolution
  factors in a single run.

This module is a prerequisite for the statistical power analysis pipeline, as it
enables the comparison of spatial autocorrelation metrics across different
resolutions.
"""
pass