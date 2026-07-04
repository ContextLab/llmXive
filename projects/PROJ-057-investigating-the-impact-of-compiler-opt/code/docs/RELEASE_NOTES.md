# Release Notes

## Version 0.1.0 (Current)

### Highlights
- First public release of the compiler optimization benchmark suite.
- Complete pipeline from data generation to Pareto frontier analysis.
- Robust handling of numerical stability and memory constraints.

### New Features
- **Deterministic Data**: Fixed-seed tensor generation.
- **High-Precision Reference**: 512-bit decimal arithmetic.
- **Dynamic Compilation**: Support for multiple optimization flags.
- **Statistical Rigor**: Welch's t-test for independent samples.
- **Visualization**: Pareto frontier plots with stability markers.

### Bug Fixes
- Fixed memory pressure handling to auto-downsample tensors.
- Corrected statistical method from paired t-test to Welch's t-test.
- Improved NaN detection and exclusion logic.

### Known Issues
- None at this time.

### Upgrade Notes
- This is the initial release. No upgrade path exists.

### Deprecation Notes
- None.

### Security Notes
- Ensure compiler binaries are trusted before execution.
- Validate input configurations to prevent injection attacks.

### Contact
For support, contact [Email Address].
