# Deviation Record: JPEG2000 1D-to-2D Folding

## 1. Original Requirement
**FR-003**: JPEG2000 compression MUST be implemented directly on 1D strain data.

## 2. Deviation Description
JPEG2000 is inherently a 2D image compression standard. To apply it to 1D gravitational wave strain time series, a **1D-to-2D folding transformation** is required. This deviation records the use of the **Hilbert curve algorithm** for this transformation.

## 3. Algorithm Description
### Hilbert Curve Folding
1. **Input**: 1D strain time series of length N (where N = 2^k for some integer k).
2. **Folding**: Map the 1D index `i` to 2D coordinates `(x, y)` using the Hilbert curve algorithm.
 - The Hilbert curve is a space-filling curve that preserves locality: adjacent points in 1D map to adjacent points in 2D.
 - This minimizes the disruption of temporal correlations during compression.
3. **Reshaping**: Reshape the folded data into a 2D array (e.g., 2048x1024 for 2M samples).
4. **Compression**: Apply JPEG2000 compression to the 2D array using `Pillow` or a dedicated JPEG2000 library.
5. **Decompression**: Decompress the 2D array.
6. **Unfolding**: Map the 2D coordinates back to 1D indices using the inverse Hilbert curve.
7. **Output**: Reconstructed 1D strain time series.

## 4. Rationale
- **Locality Preservation**: The Hilbert curve preserves spatial locality better than row-major or column-major folding, which is critical for maintaining the temporal structure of GW signals.
- **Standard Compliance**: JPEG2000 requires 2D input; folding is the only practical way to adapt it to 1D data.
- **Reproducibility**: The Hilbert curve is deterministic and reversible, ensuring that the transformation artifact can be isolated from compression artifacts.

## 5. Artifact Tagging Rules
All artifacts produced by this process MUST be tagged with:
- **Type**: `Transformation+Compression`
- **Method**: `JPEG2000_Hilbert`
- **Dimensions**: e.g., `2048x1024`
- **Quality**: JPEG2000 quality parameter (e.g., `Q=50`)

## 6. Validation
To ensure the transformation does not invalidate MSE/SNR comparisons:
1. Compare the original 1D data with the "folded-unfolded" (no compression) version.
2. Verify that MSE ≈ 0 and SNR degradation ≈ 0 dB for this step.
3. Only after confirming the transformation is lossless, compute error metrics for the compressed version.

## 7. Implementation Details
- **Library**: `pillow` (with `openjpeg` support) or `glymur`
- **Target Dimensions**: 2048x1024 (for 2M samples)
- **Hilbert Implementation**: Use a verified Hilbert curve library (e.g., `hilbert` package or custom implementation with unit tests).

## 8. References
- ISO/IEC 15444-1: JPEG2000 Image Coding System
- Sagan, H. (1994). Space-Filling Curves. Springer.
- https://en.wikipedia.org/wiki/Hilbert_curve

## 9. Approval
- **Date**: 2024-01-15
- **Author**: llmXive Pipeline
- **Status**: Approved under Constitution Principle VII (Modified) and Plan Complexity Tracking.

## 10. Related Artifacts
- `code/compression/lossy.py` (implementation of JPEG2000 folding)
- `data/interim/compressed/jpeg2000/` (output directory)
- `spec.md` (amended FR-003)
