# Deviation Record: JPEG2000 1D-to-2D Folding

## 1. Original Constraint
Standard JPEG2000 is a 2D image compression algorithm. Gravitational wave strain data is inherently 1D time-series data.

## 2. Deviation Description
To utilize JPEG2000 for 1D GW data, we implement a **1D-to-2D folding** step prior to compression.
- **Algorithm**: Hilbert Curve (Space-Filling Curve).
- **Process**: The 1D strain array is mapped onto a 2D grid (e.g., 2048x1024) following a Hilbert space-filling curve. This preserves local correlation in the 1D signal within the 2D spatial domain, which is critical for JPEG2000's wavelet-based compression efficiency.
- **Decompression**: The inverse Hilbert mapping is applied to the decompressed 2D image to reconstruct the 1D time series.

## 3. Rationale
- **Hilbert vs. Row-Major**: Row-major folding introduces discontinuities at row boundaries, creating high-frequency artifacts that degrade compression efficiency and introduce reconstruction noise. The Hilbert curve minimizes these boundary jumps, maintaining signal continuity.
- **Necessity**: This transformation is required to adapt existing, optimized 2D JPEG2000 libraries (via `pillow` or `openjpeg`) to 1D scientific data without writing a custom 1D JPEG2000 encoder.

## 4. Artifact Tagging Rules
- Any data file processed through this pipeline must be tagged with `Transformation: Hilbert_Fold`.
- Compression artifacts are classified as `Transformation+Compression`.
- Reconstruction error metrics must explicitly account for the folding/unfolding overhead.

## 5. Implementation Reference
- **Module**: `code/src/compression/lossy.py` (Function: `fold_hilbert`, `unfold_hilbert`).
- **Spec Reference**: FR-003.
- **Constitution**: Amended under Constitution Principle VII (Modified) for technical feasibility.