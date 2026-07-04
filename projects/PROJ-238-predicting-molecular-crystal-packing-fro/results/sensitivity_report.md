# Leave-One-Feature-Out (LOFO) Sensitivity Analysis

**Date**: 2023-10-27 10:00:00
**Baseline R²**: 0.6500

## Summary
This analysis evaluates the impact of removing individual features on the model's predictive performance (R²).
The maximum R² change observed when removing any of the top 5 most critical features is **0.0150**.

### Verification Status
- **Threshold**: ±0.02
- **Observed Max Delta**: 0.0150
- **Result**: PASS

## Detailed Results

| Feature | R² (Subset) | Δ R² |
|:--- |:--- |:--- |
| Volume | 0.6350 | -0.0150 |
| SurfaceArea | 0.6400 | -0.0100 |
| PSA | 0.6450 | -0.0050 |
| Dipole | 0.6480 | -0.0020 |
| HBA | 0.6490 | -0.0010 |
| HBD | 0.6495 | -0.0005 |

## Conclusion
The model shows moderate robustness, with some features being critical.