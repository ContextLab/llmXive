# Revision Specification: Research Revision (writing) — PROJ-552-quantifying-the-complexity-of-knot-diagr round 1

**Generated**: 2026-06-24T14:02:16.717445+00:00
**Kind**: research_writing
**Project**: PROJ-552-quantifying-the-complexity-of-knot-diagr
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[b7512022cb4d] (severity: writing)** Checksum Manifest: Retain a single authoritative checksum file (e.g., checksums.json), remove/deprecate checksums.csv and checksums.sha256, and update all documentation to reference the single manifest.
- **[1c87066999b5] (severity: writing)** Duplicate‑Record Check: Implement a duplicate‑ID detection step in code/data/validator.py, run it on the full dataset, and record the result (expected 0) in data_quality_report.md.
- **[2288689e59d1] (severity: writing)** Sample‑Size Documentation: Populate validation_scope.md (or sample_size_adequacy.md) with a concrete table of knot counts per crossing number, and explicitly state that each stratified group meets the ≥ 5 % null‑field threshold and has enough records for descriptive statistics.
- **[8e496dd74e41] (severity: writing)** Hyperbolic Volume Cross‑Check: Complete hyperbolic_volume_validation.md with the actual coverage percentage, match rate, and a discussion of source independence (e.g., whether Knot Atlas and KnotInfo share underlying data).
- **[fd4ad1d5f921] (severity: writing)** Artifact Hash: Provide the SHA‑256 hash of the primary artifact (tasks.md) so the review can be processed automatically.


## Success Criterion

After the implementer applies this revision, the project returns to
``research_review`` and the per-specialist re-review protocol confirms
each of the 5 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
