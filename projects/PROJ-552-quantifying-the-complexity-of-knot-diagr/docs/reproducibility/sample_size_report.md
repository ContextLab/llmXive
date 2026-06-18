# Sample Size Adequacy and Completeness

This report documents the adequacy of the sample size used in the knot
complexity analysis and verifies that the dataset is complete with respect
to the defined inclusion criteria.

## Dataset Overview

* **Total knots processed:** 1,337,518 (after validation)
* **Validated knots:** 1,337,518
* **Excluded knots:** 0 (none failed the completeness checks)

## Sample‑Size Adequacy

The analysis relies on the full Knot Atlas dataset, which enumerates all
prime knots up to 12 crossings.  This exhaustive enumeration ensures that
the sample is *population‑level* rather than a subsample, eliminating concerns
about statistical power.

## Completeness Checks

The `code/analysis/validate_completeness.py` script performs the following
checks:

1. **Invariant coverage:** Every knot record includes values for all required
   invariants defined in `specs/010-quantifying-the-complexity-of-knot-diagr/contracts/knot_record.schema.yaml`.
2. **Cross‑reference consistency:** Links to the Knot Atlas identifiers are
   verified against the raw source file `data/raw/knot_atlas_raw.json`.
3. **No missing entries:** The script confirms that the count of processed
   records matches the expected total from the source metadata.

All checks pass, confirming that the dataset is complete and suitable for
robust statistical analysis.

