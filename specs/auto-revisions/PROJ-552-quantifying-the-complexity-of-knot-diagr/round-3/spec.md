# Revision Specification: Research Revision (writing) — PROJ-552-quantifying-the-complexity-of-knot-diagr round 3

**Generated**: 2026-06-24T14:31:21.592110+00:00
**Kind**: research_writing
**Project**: PROJ-552-quantifying-the-complexity-of-knot-diagr
**Round**: 3

## Input

Address the following reviewer-raised action items:

- **[b808c4b2dbbd] (severity: writing)** The provenance of the raw Knot Atlas dump is recorded in data/raw/knot_atlas_raw.provenance.yaml, but the file is not referenced anywhere in the reproducibility documentation (e.g., docs/reproducibility/validation_scope.md does not cite it).
- **[1884e557d59f] (severity: writing)** License information for the external Knot Atlas data is duplicated across many markdown files, but the primary license statement (docs/reproducibility/knot_atlas_data_license.md) is missing from the repository tree. ### Schema & Validation
- **[b04c16b2a5ad] (severity: writing)** Schema files exist (specs/001-knot-complexity-analysis/contracts/*.yaml), yet the validation reports (docs/reproducibility/data_quality_report.md, docs/reproducibility/invariant_coverage.md) contain place‑holder text (PLACEHOLDER_TOTAL, TBD, *TBD*) and do not show concrete pass/fail numbers.
- **[44541df4bce6] (severity: writing)** The data‑quality report claims “null‑percentage ≤ 5 % and format‑pass ≥ 99 %” without presenting the actual percentages for each field. ### Missing‑Data Handling
- **[4df839a4542d] (severity: writing)** The flagging system (missing_invariant_flags, data_quality_flags) is described in the spec, but the concrete counts of flagged records are absent (*TBD* in the report).
- **[87fc684b2419] (severity: writing)** docs/reproducibility/ambiguous_classification_log.md states “No ambiguous records remain” but provides no evidence (e.g., a count or sample entries). ### Version Control & Reproducibility Artifacts
- **[505749289486] (severity: writing)** The SHA‑256 checksums are recorded (docs/reproducibility/checksums.md), yet the authoritative manifest (data/checksums.json) is not shown, and the documentation does not confirm that the manifest matches the current data files.
- **[5bb9f150e305] (severity: writing)** The quick‑start validation (docs/reproducibility/quickstart_validation.md) contains an unresolved claim (UNRESOLVED‑CLAIM: c_dfb35bbc) indicating that the validation status could not be fully verified. ### Sample‑Size Adequacy
- **[209e3910a28d] (severity: writing)** The core scientific claim (SC‑001) requires all prime knots with crossing number ≤ 13 (≈ 9 988 knots).
- **[e961ee743a9f] (severity: writing)** docs/reproducibility/data_quantities.md reports only 476 records, and docs/reproducibility/dataset_counts.md lists a total of 49 prime knots – both far short of the required census.
- **[a48b93273a98] (severity: writing)** Consequently, the dataset does not satisfy the completeness benchmark, and any statistical analysis is under‑powered and not representative of the intended population. ### Required Changes ## Required Changes
- **[7b73d52f6316] (severity: writing)** Provide a complete dataset: Download and retain the full set of prime knots with crossing number ≤ 13 (≈ 9 988 records) from Knot Atlas, ensuring that the raw file (data/raw/knot_atlas_raw.json) contains all entries and that data/processed/knots_cleaned.csv reflects this full census.
- **[35d33b33ef99] (severity: writing)** Update provenance documentation: Add a clear reference to data/raw/knot_atlas_raw.provenance.yaml in docs/reproducibility/validation_scope.md and any other reproducibility docs that discuss data sources.
- **[dd3d09400295] (severity: writing)** Consolidate and correct license statements: Keep a single authoritative license file for the Knot Atlas data (e.g., docs/reproducibility/knot_atlas_data_license.md) and remove duplicated or outdated license markdown files.
- **[004205a94ac2] (severity: writing)** Replace all placeholder text in reproducibility reports (data_quality_report.md, invariant_coverage.md, dataset_counts.md, data_quantities.md, etc.) with the actual computed numbers (null percentages, format‑pass rates, flag counts, coverage percentages, total record counts).


## Success Criterion

After the implementer applies this revision, the project returns to
``research_review`` and the per-specialist re-review protocol confirms
each of the 15 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
