# Spec Override: SC-001 Correction

## Rejection of Original Specification

The original specification SC-001 defined the measurement target as "CLR-transformed alpha diversity". This is mathematically invalid and scientifically unsound for the following reasons:

1. **Alpha diversity metrics (e.g., Shannon Index) are scalar summary statistics** calculated from raw count data. They represent the diversity of a single sample.
2. **Centered Log-Ratio (CLR) transformation** is a compositional data technique designed for high-dimensional relative abundance vectors (taxa matrices), not for scalar diversity indices.
3. Applying CLR to a scalar value is undefined and renders the metric meaningless.
4. The statistical properties of Shannon Index (non-negative, bounded by sample richness) are incompatible with the log-ratio assumptions of CLR.

## Corrected Requirement

**SC-001: The correlation coefficient and p-value between **Raw Shannon Index** and fluid intelligence are measured against the Spearman rank correlation test results.**

### Implementation Details

- **Input Data**: The `shannon_index` column in the processed dataset must be derived directly from **raw OTU/ASV counts** using `scikit-bio`'s `diversity.alpha.shannon` function.
- **Transformation**: No CLR transformation is applied to the `shannon_index` column.
- **Statistical Test**: Spearman rank correlation (`scipy.stats.spearmanr`) is used to measure the monotonic relationship between `shannon_index` and `fluid_intelligence`.
- **Output**: The correlation coefficient (`r_value`) and p-value (`p_value`) are recorded in `data/processed/correlation_results.csv`.

### Validation

This override ensures that the analysis pipeline adheres to ecological statistical best practices by:
1. Preserving the interpretability of the Shannon Index.
2. Preventing the application of invalid mathematical transformations.
3. Ensuring the correlation analysis reflects the true relationship between gut diversity and cognitive performance.

## Dependencies

- **T056**: Spec override documentation framework established.
- **T045**: Related override for FR-003 (CLR on Alpha Diversity rejection) established.

## Status

**REJECTED**: Original SC-001 (CLR-transformed alpha diversity) is invalid.
**APPROVED**: Corrected SC-001 (Raw Shannon Index) is the mandatory measurement target.