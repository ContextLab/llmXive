# Revision Specification: Research Revision (writing) — PROJ-552-quantifying-the-complexity-of-knot-diagr round 3

**Generated**: 2026-06-24T15:08:00.620820+00:00
**Kind**: research_writing
**Project**: PROJ-552-quantifying-the-complexity-of-knot-diagr
**Round**: 3

## Input

Address the following reviewer-raised action items:

- **[08ad1e98e920] (severity: writing)** Correct the dataset size reporting: Ensure that data/processed/knots_cleaned.csv (and any derived CSV/Parquet files) contain *all* prime knots with crossing number ≤ 13 (≈ 9 988 records). Update docs/reproducibility/dataset_counts.md, docs/reproducibility/data_quantities.md, and docs/reproducibility/methodology_appendix.md to reflect the exact, consistent record count.
- **[56ac5e538416] (severity: writing)** Achieve ≤ 5 % null rate for hyperbolic volume (or explicitly document a justified exemption). If the raw source lacks volume for certain knots, either obtain the missing values from an independent source (e.g., KnotInfo) or adjust the scope to exclude those knots and update all success criteria (SC‑001, SC‑013) accordingly.
- **[ca386d70c920] (severity: writing)** Populate concrete flag statistics: Replace placeholder “TBD” and “PLACEHOLDER_TOTAL” entries in data_quality_report.md, data_quality_flagging_counts.md, and invariant_coverage.md with the actual numbers derived from the validation run. Ensure the counts match the contents of processed/validation_flags.json.
- **[fcbb5bc23ef8] (severity: writing)** Align schema validation output: Verify that the schema validator actually runs against the processed dataset and that the pass/fail status in validation_status.md reflects the true outcome. If any schema violations exist, fix the data or the schema and re‑run validation.
- **[7878f4eb6912] (severity: writing)** Synchronize all reproducibility documents: After fixing the dataset and validation outputs, regenerate the automatically produced docs (validation_status.md, quickstart_validation.md, seed_verification.md, etc.) to eliminate any remaining inconsistencies.


## Success Criterion

After the implementer applies this revision, the project returns to
``research_review`` and the per-specialist re-review protocol confirms
each of the 5 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
