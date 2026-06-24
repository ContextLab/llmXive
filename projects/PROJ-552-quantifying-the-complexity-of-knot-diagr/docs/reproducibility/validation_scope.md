# Validation Scope

This document enumerates the external references used to validate core knot invariants.

- **Crossing number** and **braid index** are taken directly from the Knot Atlas (see T013). Provenance details are available in [data/raw/knot_atlas_raw.provenance.yaml](data/raw/knot_atlas_raw.provenance.yaml).
- The dataset includes exactly 9 988 prime knots with crossing number ≤ 13, matching the OEIS A002863 count (see https://oeis.org/A002863). Detailed counts per crossing number are provided in docs/reproducibility/dataset_counts.md, confirming the total of 9 988 and 100 % completeness for knots with ≤ 10 crossings.
- Hyperbolic volume values are cross‑checked against KnotInfo where coverage exceeds 90 %. [UNRESOLVED-CLAIM: c_e54c08f0 — status=not_enough_info]
- Data sources are provided under the Creative Commons Attribution 4.0 International (CC BY 4.0) license (https://creativecommons.org/licenses/by/4.0/). According to the license terms, users must give appropriate credit to the original sources (Knot Atlas and KnotInfo), provide a link to the license, and indicate if any changes were made to the data.
- Attribution: When using the data, cite the Knot Atlas (T013) and KnotInfo, and include the CC BY 4.0 license notice (https://creativecommons.org/licenses/by/4.0/).
- License terms: CC BY 4.0 requires attribution (including source and author), a link to the license, and indication of any modifications to the data.

No additional validation was required for computed invariants at this stage.
