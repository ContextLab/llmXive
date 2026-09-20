# Assumptions and Methodology Notes

## Data Preprocessing
- LOD Handling: Values below Limit of Detection (LOD) were imputed as 0.5 * LOD_VALUE.
- Normalization: Microbiome data normalized to relative abundance (sum=1).
- Diversity: Shannon index calculated on normalized data.
- Transformation: Centered Log-Ratio (CLR) applied with pseudo-count for zeros.

## Correlation Analysis
Methodology Note: Spearman rank correlation with Benjamini-Hochberg correction is used as the primary method per Spec FR-004. This overrides the Plan's initial mention of permutation testing.
