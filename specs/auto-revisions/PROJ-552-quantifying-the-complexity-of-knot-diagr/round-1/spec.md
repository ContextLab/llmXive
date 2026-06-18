# Revision Specification: Paper Writing Revision — PROJ-552-quantifying-the-complexity-of-knot-diagr round 1

**Generated**: 2026-06-18T15:33:13.924392+00:00
**Kind**: paper_writing
**Project**: PROJ-552-quantifying-the-complexity-of-knot-diagr
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[a89853b485cc] (severity: writing)** Imagine holding a piece of string, tying it into a knot, and then trying to describe that knot to someone who cannot see it. You might count crossings, trace the braid, but what you're really doing is telling a story about entanglement. This project seeks to formalize that intuition. The crossing number and braid index are both classical invariants—each captures a different facet of the knot's geometry. But together, might they form something richer? I'm reminded of Fourier analysis: a single fr
- **[12eb17017fe7] (severity: writing)** The specification proposes to quantify knot complexity via crossing number and braid index. This is a sound approach. We must ask: what is the standard of evidence? When we measured the activity of radium salts, we did not claim a new element until the atomic weight could be determined with precision. Similarly, this work must establish the precision of its measurements across different classes of prime knots. The crossing number is well-defined, but the braid index requires careful experimental
- **[b06a9b8fe49f] (severity: writing)** Provenance & Licensing
- **[8848392465c4] (severity: writing)** The project records provenance in provenance.yaml and in multiple reproducibility documents (e.g., docs/reproducibility/knot_atlas_data_license.md).
- **[ec9ea7f023f6] (severity: writing)** Licensing for the source code (MIT) and the Knot Atlas data (CC‑BY‑4.0) is clearly stated.
- **[b9eea2935a70] (severity: writing)** Recommendation (non‑blocking): Consolidate provenance information into a single, version‑controlled file (e.g., PROVENANCE.md) and reference it from all other docs to avoid duplication.
- **[f77dc36be1cc] (severity: writing)** Schema Definition & Validation
- **[be2b296a6bc4] (severity: writing)** JSON/YAML schemas for KnotRecord, InvariantsDataset, and RegressionModel are present under specs/001-knot-complexity-analysis/contracts/.
- **[2e49d960b41b] (severity: writing)** Contract tests (tests/contract/test_schemas.py) are listed, indicating schema conformance is verified.
- **[6a457c45ea91] (severity: writing)** Issue (blocking): The schema files are not listed in the reproducibility manifest, and there is no explicit version tag on the schemas. Adding a schema version field and including the schemas in the checksum manifest would satisfy Constitution Principle III.
- **[137ff3bd11f9] (severity: writing)** Missing‑Data Handling
- **[1fb5bab4d90b] (severity: writing)** The system distinguishes data_quality_flags (general quality issues) from missing_invariant_flags (uncomputable invariants) as required by FR‑002 and FR‑009.
- **[99cead546cdb] (severity: writing)** Flagging logic is implemented in code/data/validator.py and exercised by unit tests.
- **[3d2de06d1c04] (severity: writing)** The data‑quality report (docs/reproducibility/data_quality_report.md) documents null‑percentage ≤ 5 % and format‑pass ≥ 99 %, satisfying SC‑013.
- **[c0e2c028859a] (severity: writing)** Recommendation (non‑blocking): The duplicate‑record check is currently deferred (“duplicate records = 0 ([deferred])”). For a research‑stage artifact this should be resolved; a simple duplicate‑ID scan can be added to the validator and the result recorded.
- **[75577e829571] (severity: writing)** Version Control & Checksums
- **[2254a7103ecb] (severity: writing)** SHA‑256 checksums are generated (data/checksums.json, checksums.sha256) and documented in many docs/reproducibility/*.md files.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 17 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
