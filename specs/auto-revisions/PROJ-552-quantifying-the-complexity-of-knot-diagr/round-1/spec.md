# Revision Specification: Research Revision (writing) — PROJ-552-quantifying-the-complexity-of-knot-diagr round 1

**Generated**: 2026-06-30T04:54:01.422524+00:00
**Kind**: research_writing
**Project**: PROJ-552-quantifying-the-complexity-of-knot-diagr
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[63ea8ffe8818] (severity: writing)** Refactor code/analysis/model_fitting.py and code/analysis/regression.py: Merge overlapping logic into a single, well-structured module (e.g., code/analysis/regression_models.py) that clearly separates model fitting, metric calculation, and residual analysis. Ensure the file size is under 2,000 lines and follows the PEP 8 style guide.
- **[33c5d92de38a] (severity: writing)** Consolidate code/analysis/hyperbolic_volume_validation.py: Split this 15KB file into distinct modules: code/analysis/validation/hyperbolic_volume_loader.py (data loading), code/analysis/validation/hyperbolic_volume_checker.py (logic), and code/analysis/validation/hyperbolic_volume_report.py (reporting).
- **[bb12654fb5c7] (severity: writing)** Eliminate redundant composite metric files: Review code/analysis/composite_metric*.py files. Select the single canonical implementation (likely composite_metric.py or composite_metric_linear.py) and delete the others. Update all imports and documentation to reference the single canonical file.
- **[8fedd536d4cc] (severity: writing)** Consolidate docs/reproducibility/checksums*.md: Merge all checksums*.md files into a single docs/reproducibility/checksums.md that contains the authoritative policy, location, and generation instructions. Delete the redundant "guidance", "location", "policy", and "version control" variants.
- **[837b8c69396e] (severity: writing)** Refactor code/reproducibility/validation_status_generator.py: Split this large file (19KB) into code/reproducibility/validation_status_logic.py (core logic) and code/reproducibility/validation_status_report.py (report generation).
- **[41f72b5ef4c4] (severity: writing)** Add PEP 484 type hints: Ensure all public functions in code/analysis/ and code/reproducibility/ have complete type hints. Run mypy and fix all errors.
- **[546bb68ea46e] (severity: writing)** Add unit tests: Create tests/unit/test_regression_models.py, tests/unit/test_validation_logic.py, and tests/unit/test_checksums.py to cover the core logic of the refactored modules. Ensure test coverage is > 80% for these critical paths.
- **[2d5e13d8b2ea] (severity: writing)** Fix code/download/knot_atlas_loader.py and code/data/parser.py: Implement and verify the explicit request for the braid_index column and the fallback lookup to KnotInfo. Re-run the pipeline to ensure docs/reproducibility/invariant_coverage.md reports Braid Index coverage ≥ 95% (nulls ≤ 5%).
- **[acdb853f55db] (severity: writing)** Correct code/data/validator.py: Refactor the logic for missing_invariant_flags so that it is only set for invariants that are algorithmically computed (Phase 2+) and fail. Ensure that missing *tabulated* core invariants (Crossing Number, Braid Index) trigger data_quality_flags or a specific "missing_tabulated" flag, not missing_invariant_flags. Re-run validation to ensure docs/reproducibility/data_quality_flagging_counts.md reflects this distinction (e.g., missing_invariant_flags should be 0 or
- **[096e16433f4d] (severity: writing)** Update docs/reproducibility/data_quality_report.md and docs/reproducibility/invariant_coverage.md: Regenerate these reports after the data fixes to accurately reflect the new null percentages (≤ 5%) and correct flag counts.
- **[e034dcadff2d] (severity: writing)** Update tasks.md: Replace the placeholder <SHA-256 hash of tasks.md required> in the review record (or the tasks.md file itself if it contains the placeholder) with the actual SHA-256 hash of the current tasks.md file.
- **[1eeb573aba5b] (severity: writing)** Consolidate all checksum-related documentation (checksums.md, checksums_guidance.md, checksums_location.md, checksums_location_notice.md, checksums_location_update.md, checksums_policy.md, checksums_single_manifest.md, checksums_version_control.md, checksums_version_control_guidelines.md, checksums_version_control_notice.md) into a single file docs/reproducibility/checksums.md and delete the others.
- **[c908d50df24f] (severity: writing)** Consolidate all licensing-related documentation (LICENSE_AND_DATA_*.md, Licensing_Statement.md, license_and_data_*.md, license_summary.md, LICENSES_SUMMARY.md) into a single file docs/reproducibility/LICENSE_AND_DATA.md and delete the others.
- **[64bad3aae056] (severity: writing)** Consolidate all braid index precision documentation (braid_index_precision*.md) into a single file docs/reproducibility/braid_index_precision_validation.md and delete the others.
- **[fd53f80fe766] (severity: writing)** Consolidate all log location and operation log documentation (LOGS_LOCATION*.md, operation_logs*.md) into a single file docs/reproducibility/operation_logs.md and delete the others.
- **[27d9dbdc8512] (severity: writing)** Remove docs/reproducibility/validation_status_update.md as it is marked deprecated; ensure docs/reproducibility/validation_status.md is the sole source of truth.
- **[8997805f28d0] (severity: writing)** Consolidate quickstart documentation (quickstart.md, quickstart_instructions.md, quickstart_validation.md, quickstart_entrypoints.md) into a single docs/reproducibility/quickstart.md (or quickstart_guide.md) and delete the others.
- **[97f07d91ef44] (severity: writing)** Consolidate derivation notes documentation (derivation_notes.md, derivation_notes_validator.md, derivation_validator.md) into a single docs/reproducibility/derivation_notes.md and delete the others.
- **[737168e04524] (severity: writing)** Move all log files currently in data/ (data/logs.json, data/logs.jsonl, data/operation_logs.jsonl, data/reproducibility.log) to docs/reproducibility/logs/ (creating the directory if needed) and delete the originals from data/ to align with the plan.md structure.
- **[ba9fc8ded3cf] (severity: writing)** Ensure data/checksums.json is the only checksum manifest in data/ and remove data/checksums.csv and data/checksums.sha256 if they exist (per checksums_policy.md content).


## Success Criterion

After the implementer applies this revision, the project returns to
``research_review`` and the per-specialist re-review protocol confirms
each of the 20 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
