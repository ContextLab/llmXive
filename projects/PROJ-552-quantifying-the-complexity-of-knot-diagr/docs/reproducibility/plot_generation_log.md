# Plot Generation Log: Crossing Number vs Braid Index

**Task**: T024 - Save plots to data/plots/crossing_vs_braid.png with resolution 1200x900 pixels
**User Story**: US2 - Establish Measurement Precision for Core Invariants
**Generated**: 2026-01-15
**Script**: `code/analysis/save_crossing_braid_plot.py`

## Plot Specifications

| Parameter | Value |
|-----------|-------|
| Output File | `data/plots/crossing_vs_braid.png` |
| Resolution | 1200 × 900 pixels |
| DPI | 100 |
| Figure Size | 12 × 9 inches |
| File Format | PNG |

## Data Source

- **Input File**: `data/processed/knots_cleaned.csv`
- **Dataset**: Hyperbolic prime knots with crossing number ≤ 13
- **Stratification**: Alternating vs Non-alternating classification

## Plot Description

The crossing number vs braid index scatter plot visualizes the relationship
between these two core knot invariants. Points are stratified by alternating
classification to reveal any systematic differences in the relationship.

**Expected Pattern**: Due to the mathematical constraint that braid index ≤ crossing
number, all points should lie on or below the diagonal line y = x.

**Analysis Value**: This visualization supports the precision validation work
in User Story 2 by providing a visual check of the crossing number vs braid
index relationship across different knot classes.

## Reproducibility

To regenerate this plot:

```bash
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr
python code/analysis/save_crossing_braid_plot.py
```

The operation is logged by the reproducibility logging framework with
parameters including width, height, DPI, and total knot count.

## Verification

After generation, verify:
1. File exists at `data/plots/crossing_vs_braid.png`
2. File resolution is 1200 × 900 pixels (check with `identify` or similar tool)
3. File is valid PNG format
4. Plot contains data points for both alternating and non-alternating knots
5. All points satisfy braid_index ≤ crossing_number constraint

## Related Artifacts

- `code/analysis/exploratory.py` - Plot generation functions
- `data/processed/knots_cleaned.csv` - Source data
- `docs/reproducibility/data_quality_report.md` - Data quality metrics
- `docs/reproducibility/mathematical_constraints.md` - Braid index ≤ crossing number constraint