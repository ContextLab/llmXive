# Data Processing Assumptions

## Task T020a: CLR Transformation

### Pseudo-count Selection for Zero Handling

**Decision**: A pseudo-count of `1e-6` (0.000001) is used to replace zero values before applying the Centered Log-Ratio (CLR) transformation.

**Rationale**:
- The CLR transformation requires taking the logarithm of abundances, which is undefined for zero values.
- Adding a small pseudo-count allows the transformation to proceed without discarding valuable data points.
- The value `1e-6` is sufficiently small to minimize distortion of the relative abundance structure while being large enough to avoid numerical instability in the log calculation.
- This choice is consistent with common practices in microbiome data analysis (e.g., as implemented in the `scikit-bio` and `gneiss` packages).

**Configuration**:
- The pseudo-count value is parameterized in `code/utils/config.py` via the `get_pseudocount()` function.
- Default value: `1e-6`
- This parameter can be adjusted if sensitivity analysis suggests a different value is more appropriate for the specific dataset.

**Impact on Downstream Analysis**:
- The CLR-transformed data will be used for correlation analysis (Task T032) and predictive modeling (Task T034d).
- The choice of pseudo-count may influence the magnitude of the CLR values but should not substantially alter the ranking of taxa in correlation analysis.
- Sensitivity analysis (Task T020b, if implemented) could explore the impact of different pseudo-count values on results.

### Alternative Approaches Considered
- **Zero Replacement via Bayesian Methods**: More complex methods exist (e.g., `cmultRepl` in `zCompositions` R package) but were deemed unnecessary given the small magnitude of zeros expected in relative abundance data after normalization.
- **Exclusion of Zero-Heavy Taxa**: Removing taxa with many zeros could reduce dimensionality but might also discard biologically relevant signals. The current approach retains all taxa.

**Reference**:
- Gloor, G. B., et al. (2017). "Microbiome Datasets Are Compositional: And This Is Not Optional." Frontiers in Microbiology.
- Quinn, T. P., et al. (2018). "A Field Guide to the Compositional Analysis of Microbiome Data." Frontiers in Microbiology.
