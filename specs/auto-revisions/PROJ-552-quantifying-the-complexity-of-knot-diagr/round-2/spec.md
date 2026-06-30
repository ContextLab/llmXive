# Revision Specification: Research Revision (writing) — PROJ-552-quantifying-the-complexity-of-knot-diagr round 2

**Generated**: 2026-06-30T05:08:11.354668+00:00
**Kind**: research_writing
**Project**: PROJ-552-quantifying-the-complexity-of-knot-diagr
**Round**: 2

## Input

Address the following reviewer-raised action items:

- **[098a681b509f] (severity: writing)** Split code/analysis/model_fitting.py: Decompose into code/analysis/model_fitting.py (pure model fitting logic), code/analysis/residual_analysis.py (residual calculation and family identification), and code/analysis/plotting.py (all figure generation). Ensure each file is < 5,000 lines and has a single responsibility.
- **[dfdf101d3751] (severity: writing)** Split code/analysis/regression_models.py: Merge or refactor to remove redundancy with model_fitting.py. If distinct, ensure clear separation of concerns (e.g., model definition vs. model execution).
- **[bdfc10f29b46] (severity: writing)** Refactor code/reproducibility/hashing.py and seed_verifier.py: Break these into smaller, focused modules (e.g., code/reproducibility/hashing/core.py, code/reproducibility/hashing/verifier.py) to reduce complexity and improve testability.
- **[c10c234f8aa3] (severity: writing)** Consolidate Documentation Generation: Refactor the scripts generating the fragmented docs/reproducibility/ files (e.g., braid_index_precision_*.md) into a single, parameterized reporting module to reduce code duplication and improve maintainability.
- **[bc11939a9d7b] (severity: writing)** Add Type Hints and Unit Tests: Ensure all functions in code/analysis/model_fitting.py, code/download/knot_atlas_loader.py, and code/data/validator.py have complete PEP 484 type annotations. Add unit tests in tests/unit/ for regression fitting, residual analysis, and data validation logic to guarantee reproducibility.
- **[6e1330fecb44] (severity: writing)** Update docs/reproducibility/data_quality_report.md to accurately reflect the actual null percentages and flag counts derived from running code/data/run_validation.py on data/processed/knots_cleaned.csv. Specifically, correct the claim that "All fields have null percentage ≤ 5%" if the braid index null rate is indeed ~77% as indicated by invariant_coverage.md, or fix the underlying data processing to ensure braid index is populated for all records as required by FR-001.
- **[d131f8005887] (severity: writing)** Correct the logic in code/data/validator.py (or the flagging logic in code/analysis/data_quality.py) to ensure missing_invariant_flags are only applied to Phase 2+ computed invariants (arc index, etc.) and never to core tabulated invariants (crossing number, braid index) which must be present for all records per FR-001 and SC-008.
- **[46fbafdaedb0] (severity: writing)** Reconcile exclusion counts across docs/reproducibility/excluded_knots.md, docs/reproducibility/data_quantities.md, and docs/reproducibility/selection_bias.md to ensure they report the exact same number of excluded knots, matching the row count difference between data/raw/knot_atlas_raw.json and data/processed/knots_hyperbolic.csv.
- **[b88a58a65455] (severity: writing)** Re-run the validation pipeline (code/data/run_validation.py) and regenerate docs/reproducibility/invariant_coverage.md to confirm that braid index coverage is 100% for the validated subset (≤ 10 crossings) as required by the Phase 1 benchmark in SC-001.
- **[83476870b1c8] (severity: writing)** Consolidate Checksum Manifests: Delete data/checksums.sha256 and data/checksums.csv (if they exist). Ensure data/checksums.json is the only checksum manifest. Update docs/reproducibility/checksums.md to reference only data/checksums.json and remove all references to deprecated formats.
- **[68122630d545] (severity: writing)** Consolidate Redundant Documentation: Merge all redundant license, checksum, and braid-index precision files into single, authoritative documents.
- **[9b895cc52583] (severity: writing)** Delete: docs/reproducibility/LICENSE_AND_DATA_*.md (keep only docs/reproducibility/LICENSE_AND_DATA_STATEMENT.md or similar single file).
- **[3863eaab2a7b] (severity: writing)** Delete: docs/reproducibility/checksums_*.md (keep only docs/reproducibility/checksums.md).
- **[f75787491dee] (severity: writing)** Delete: docs/reproducibility/braid_index_precision_*.md (keep only docs/reproducibility/braid_index_precision.md or docs/reproducibility/core_invariants_tabulation.md if that covers it).
- **[b24edb32b3ee] (severity: writing)** Delete: docs/reproducibility/quickstart_instructions.md, docs/reproducibility/quickstart_validation.md (keep only docs/reproducibility/quickstart.md and docs/reproducibility/quickstart_validation.md if validation is a separate report, but ensure no duplication of content).
- **[2903c818c6a5] (severity: writing)** Standardize Log Locations: Move all operational logs to docs/reproducibility/logs/. Delete data/logs/ and root logs.jsonl / operation_logs.jsonl. Update docs/reproducibility/operation_logs.md to point to the single canonical location.
- **[a056dc9f5737] (severity: writing)** Update READMEs: Ensure README.md and docs/reproducibility/README.md clearly link to the single authoritative quickstart.md and data_quality_report.md files, removing references to the deleted redundant files.
- **[c331e6ba9675] (severity: writing)** File: code/data/validator.py
- **[4efb4dd0f221] (severity: writing)** File: code/analysis/data_quality.py
- **[0e251fccdf1a] (severity: writing)** File: docs/reproducibility/data_quality_report.md
- **[4d7ea19aa4ef] (severity: writing)** File: docs/reproducibility/invariant_coverage.md


## Success Criterion

After the implementer applies this revision, the project returns to
``research_review`` and the per-specialist re-review protocol confirms
each of the 21 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
