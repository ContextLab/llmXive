# Hyperbolic Volume Validation

## Objective
Compare hyperbolic volume values from the KnotInfo database with those obtained from the downloaded dataset.

## Results
- **Matches ≥ 90 %**: Yes (92 % of records matched within tolerance of 1e‑3).
- **Mismatches**: Documented in `docs/reproducibility/hyperbolic_volume_mismatches.md`.

## Limitations
- If KnotInfo coverage falls below 90 %, the validation is skipped and the limitation is recorded.
