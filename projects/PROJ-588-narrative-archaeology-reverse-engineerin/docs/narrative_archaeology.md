# Narrative Archaeology Analysis Strategy

## Primary Analysis: Early vs. Late Event Stability

Per the fallback authorization in FR-003 and FR-004, the "Encoding vs. Recognition" comparison is implemented as **"Early vs. Late Event Stability"**.

### Methodology
1. **Segmentation**: Events are segmented into "Early" (first half of story) and "Late" (second half) phases.
2. **RSA**: Dissimilarity matrices are computed for each phase.
3. **Comparison**: We test if Early-Late dissimilarity is significantly higher than Early-Early or Late-Late, indicating pattern reconfiguration.

## Secondary Analysis: Narrative Element Decoding

Linear classifiers (Ridge Regression) are trained to predict narrative elements (plot, character, theme) from neural patterns.

### Validation
- **Chance Baseline**: Accuracy is compared against `1/N_actual` where `N_actual` is the number of unique labels in the test fold.
- **Null Model**: Label shuffling is used to generate null distributions.

## Statistical Correction
- **FDR**: Benjamini-Hochberg correction is applied across ROIs and categories (q < 0.05).
- **Permutation Testing**: Used to establish significance of RSA differences.