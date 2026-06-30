# Revision Specification: Research Revision (writing) — PROJ-552-quantifying-the-complexity-of-knot-diagr round 3

**Generated**: 2026-06-30T17:07:26.879230+00:00
**Kind**: research_writing
**Project**: PROJ-552-quantifying-the-complexity-of-knot-diagr
**Round**: 3

## Input

Address the following reviewer-raised action items:

- **[0cf5284e66b8] (severity: writing)** Split code/analysis/model_fitting.py into code/analysis/model_fitting.py (core fitting logic), code/analysis/residual_analysis.py (residual calculation and family identification), and code/analysis/model_reporting.py (metrics calculation and reporting). Ensure each file is under 200 lines.
- **[1e4543aadb1a] (severity: writing)** Refactor code/reproducibility/validation_status_generator.py by separating the status generation logic into code/reproducibility/status_generator.py and the report formatting/output logic into code/reproducibility/status_reporting.py.
- **[ecf1cab508a8] (severity: writing)** Consolidate redundant validation status files (validation_status.py, validation_status_gen.py, validation_status_generator.py) into a single, well-structured module per the plan's Phase N+2 requirements.
- **[86d409d4285b] (severity: writing)** Split code/analysis/precision.py into code/analysis/precision.py (calculation logic) and code/analysis/precision_reporting.py (report generation).
- **[2fa29777afbd] (severity: writing)** Split code/reproducibility/hashing.py into code/reproducibility/hashing.py (hash computation) and code/reproducibility/hashing_reporting.py (manifest generation and logging).
- **[3339caa28263] (severity: writing)** docs/reproducibility/data_quality_report.md: Regenerate this report to accurately reflect the state of data/processed/knots_cleaned.csv. Specifically, correct the missing_invariant_flags count to reflect only records where invariants are truly uncomputable (Phase 2+), not the entire dataset. Ensure the null percentage calculation aligns with the actual record count in the cleaned CSV.
- **[2c339f43e970] (severity: writing)** docs/reproducibility/invariant_coverage.md: Resolve the contradiction between the 23% coverage claim and the 0% null percentage claim in data_quantities.md. Verify the dataset size (476 vs 9,988 vs 12,967) and ensure the coverage report matches the actual data in data/processed/knots_cleaned.csv.
- **[578958f823a2] (severity: writing)** docs/reproducibility/hyperbolic_volume_validation.md: Add a specific section documenting the source independence assessment between Knot Atlas and KnotInfo, explicitly stating whether they share underlying data sources (e.g., HTW enumeration) and how this affects the interpretation of the ≥90% match rate.
- **[0e843d9a12c8] (severity: writing)** code/data/validator.py: Review the logic for setting missing_invariant_flags to ensure it does not flag records where core invariants (crossing number, braid index) are successfully tabulated from Knot Atlas. The current logic appears to be flagging the entire dataset or a mismatched subset.
- **[c485ec01db81] (severity: writing)** docs/reproducibility/dataset_counts.md: Verify the total prime knot count (9,988 vs 12,967) against OEIS A002863 and correct the report to reflect the accurate count for crossing number ≤ 13.
- **[978cfd5e1336] (severity: writing)** Consolidate Checksum Manifests: Delete data/checksums.csv and data/checksums.sha256 if they exist. Ensure data/checksums.json is the only checksum manifest file in the data/ directory. Update docs/reproducibility/checksums.md to reflect that only checksums.json is used.
- **[cf2e55a01d70] (severity: writing)** Consolidate Reproducibility Documentation: Merge the redundant documentation files into single, authoritative documents.
- **[0e276713d81c] (severity: writing)** Merge all LICENSE_* and knot_atlas_data_license* files into a single docs/reproducibility/LICENSE_AND_DATA.md.
- **[2c82664bc781] (severity: writing)** Merge all checksums_* files into a single docs/reproducibility/checksums.md (or update the existing one to be comprehensive and delete the others).
- **[d55b267d17ce] (severity: writing)** Merge all braid_index_precision* files into a single docs/reproducibility/braid_index_precision.md.
- **[3df8b2424f7b] (severity: writing)** Merge all composite_metric* and novel_composite_metric* files into a single docs/reproducibility/composite_metrics.md.
- **[45574a375e6a] (severity: writing)** Apply a consistent naming convention (e.g., <topic>.md) to all remaining files in docs/reproducibility/.
- **[29009203a1a9] (severity: writing)** Clean Up Log Artifacts: Delete all log files from data/ (e.g., data/logs/, data/logs.jsonl, data/operation_logs.jsonl) and the repository root (e.g., reproducibility.log, logs.jsonl). Ensure all logs are exclusively located in docs/reproducibility/logs/ as per FR-007. Update docs/reproducibility/operation_logs.md to confirm the canonical location and removal of legacy files.
- **[fee37f44ddeb] (severity: writing)** Standardize File Naming: Rename files in docs/reproducibility/ to follow a consistent pattern (e.g., <topic>.md). Specifically, rename validation_status_generator.md to validation_status.md (if it contains the report) or remove it if it's a script. Ensure quickstart.md is the primary guide and quickstart_validation.md is the report.
- **[099a90425ac9] (severity: writing)** code/analysis/residual_analysis.py: Implement logic to classify knots into specific families (specifically "pretzel" and "hyperbolic non-alternating") and re-run the deviation check using the ≥ 2 standard deviations threshold as mandated by FR-005 and SC-011. Update the output to explicitly list any identified families and their specific knot identifiers.
- **[9e49dfb6124f] (severity: writing)** docs/reproducibility/residual_analysis.md: Regenerate this report to reflect the corrected analysis. If no families deviate at the 2-sigma level, the report must explicitly state that the 2-sigma check was performed and passed, rather than implying a 3-sigma check was the only one run.
- **[868e20353924] (severity: writing)** code/data/validator.py: Refactor the flagging logic to ensure missing_invariant_flags are not set for core invariants (crossing number, braid index) that are tabulated from Knot Atlas. These flags should only apply to Phase 2+ computed invariants where diagram representations are missing. Regenerate docs/reproducibility/data_quality_report.md to reflect the corrected flag counts (expected: 0 for core invariants).


## Success Criterion

After the implementer applies this revision, the project returns to
``research_review`` and the per-specialist re-review protocol confirms
each of the 22 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
