# Revision Specification: Research Revision (writing) — PROJ-552-quantifying-the-complexity-of-knot-diagr round 3

**Generated**: 2026-06-24T14:15:46.753079+00:00
**Kind**: research_writing
**Project**: PROJ-552-quantifying-the-complexity-of-knot-diagr
**Round**: 3

## Input

Address the following reviewer-raised action items:

- **[561cf4344ef7] (severity: writing)** Replace the VIF placeholders in docs/reproducibility/multicollinearity_assessment.md with the actual VIF values computed for crossing number and braid index.
- **[6271e9dc0a7a] (severity: writing)** Insert the true excluded‑knot count in docs/reproducibility/excluded_knots.md (replace PLACEHOLDER_EXCLUDED_COUNT).
- **[4bcfaf52277e] (severity: writing)** Fill in concrete coverage numbers in docs/reproducibility/invariant_coverage.md (replace PLACEHOLDER_TOTAL and PLACEHOLDER_COVERAGE).
- **[25ed4717cba0] (severity: writing)** Update docs/reproducibility/data_quality_report.md to list the exact number of records flagged with missing_invariant_flags and report the format‑pass rate (must be ≥ 99 %).
- **[f9884b262e98] (severity: writing)** Consolidate checksum documentation to a single authoritative manifest (retain data/checksums.json only) and adjust all related policy/notice files to reflect this change.
- **[2ed374e1d199] (severity: writing)** Compute the SHA‑256 hash of specs/001-knot-complexity-analysis/tasks.md and supply it in the review metadata (artifact_hash).


## Success Criterion

After the implementer applies this revision, the project returns to
``research_review`` and the per-specialist re-review protocol confirms
each of the 6 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
