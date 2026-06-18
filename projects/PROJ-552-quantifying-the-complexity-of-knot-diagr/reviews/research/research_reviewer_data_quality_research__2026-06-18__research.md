---
action_items:
- id: b06a9b8fe49f
  severity: writing
  text: Provenance & Licensing
- id: 8848392465c4
  severity: writing
  text: The project records provenance in provenance.yaml and in multiple reproducibility
    documents (e.g., docs/reproducibility/knot_atlas_data_license.md).
- id: ec9ea7f023f6
  severity: writing
  text: "Licensing for the source code (MIT) and the Knot Atlas data (CC\u2011BY\u2011\
    4.0) is clearly stated."
- id: b9eea2935a70
  severity: writing
  text: "Recommendation (non\u2011blocking): Consolidate provenance information into\
    \ a single, version\u2011controlled file (e.g., PROVENANCE.md) and reference it\
    \ from all other docs to avoid duplication."
- id: f77dc36be1cc
  severity: writing
  text: Schema Definition & Validation
- id: be2b296a6bc4
  severity: writing
  text: JSON/YAML schemas for KnotRecord, InvariantsDataset, and RegressionModel are
    present under specs/001-knot-complexity-analysis/contracts/.
- id: 2e49d960b41b
  severity: writing
  text: Contract tests (tests/contract/test_schemas.py) are listed, indicating schema
    conformance is verified.
- id: 6a457c45ea91
  severity: writing
  text: 'Issue (blocking): The schema files are not listed in the reproducibility
    manifest, and there is no explicit version tag on the schemas. Adding a schema
    version field and including the schemas in the checksum manifest would satisfy
    Constitution Principle III.'
- id: 137ff3bd11f9
  severity: writing
  text: "Missing\u2011Data Handling"
- id: 1fb5bab4d90b
  severity: writing
  text: "The system distinguishes data_quality_flags (general quality issues) from\
    \ missing_invariant_flags (uncomputable invariants) as required by FR\u2011002\
    \ and FR\u2011009."
- id: 99cead546cdb
  severity: writing
  text: Flagging logic is implemented in code/data/validator.py and exercised by unit
    tests.
- id: 3d2de06d1c04
  severity: writing
  text: "The data\u2011quality report (docs/reproducibility/data_quality_report.md)\
    \ documents null\u2011percentage \u2264 5 % and format\u2011pass \u2265 99 %,\
    \ satisfying SC\u2011013."
- id: c0e2c028859a
  severity: writing
  text: "Recommendation (non\u2011blocking): The duplicate\u2011record check is currently\
    \ deferred (\u201Cduplicate records = 0 ([deferred])\u201D). For a research\u2011\
    stage artifact this should be resolved; a simple duplicate\u2011ID scan can be\
    \ added to the validator and the result recorded."
- id: 75577e829571
  severity: writing
  text: Version Control & Checksums
- id: 2254a7103ecb
  severity: writing
  text: "SHA\u2011256 checksums are generated (data/checksums.json, checksums.sha256)\
    \ and documented in many docs/reproducibility/*.md files."
artifact_hash: 7baa44b59cd32c7fda7ee82e82eeaf53dd34c3f18b9a974e3b4792da9f1598ca
artifact_path: projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/specs/010-quantifying-the-complexity-of-knot-diagr/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-06-18T15:32:54.707564Z'
reviewer_kind: llm
reviewer_name: research_reviewer_data_quality_research
score: 0.0
verdict: minor_revision
---

**Data‑Quality Assessment (Provenance, License, Schema, Missing‑Data Handling, Version Control, Sample‑Size Adequacy)**  

1. **Provenance & Licensing**  
   - The project records provenance in `provenance.yaml` and in multiple reproducibility documents (e.g., `docs/reproducibility/knot_atlas_data_license.md`).  
   - Licensing for the source code (MIT) and the Knot Atlas data (CC‑BY‑4.0) is clearly stated.  
   - **Recommendation (non‑blocking):** Consolidate provenance information into a single, version‑controlled file (e.g., `PROVENANCE.md`) and reference it from all other docs to avoid duplication.

2. **Schema Definition & Validation**  
   - JSON/YAML schemas for `KnotRecord`, `InvariantsDataset`, and `RegressionModel` are present under `specs/001-knot-complexity-analysis/contracts/`.  
   - Contract tests (`tests/contract/test_schemas.py`) are listed, indicating schema conformance is verified.  
   - **Issue (blocking):** The schema files are not listed in the reproducibility manifest, and there is no explicit version tag on the schemas. Adding a schema version field and including the schemas in the checksum manifest would satisfy Constitution Principle III.

3. **Missing‑Data Handling**  
   - The system distinguishes `data_quality_flags` (general quality issues) from `missing_invariant_flags` (uncomputable invariants) as required by FR‑002 and FR‑009.  
   - Flagging logic is implemented in `code/data/validator.py` and exercised by unit tests.  
   - The data‑quality report (`docs/reproducibility/data_quality_report.md`) documents null‑percentage ≤ 5 % and format‑pass ≥ 99 %, satisfying SC‑013.  
   - **Recommendation (non‑blocking):** The duplicate‑record check is currently deferred (“duplicate records = 0 ([deferred])”). For a research‑stage artifact this should be resolved; a simple duplicate‑ID scan can be added to the validator and the result recorded.

4. **Version Control & Checksums**  
   - SHA‑256 checksums are generated (`data/checksums.json`, `checksums.sha256`) and documented in many `docs/reproducibility/*.md` files.  
   - However, the repository contains **multiple, partially contradictory checksum manifests** (`checksums.csv`, `checksums.json`, `checksums.sha256`, plus several policy docs). Constitution Principle III requires a **single authoritative manifest** per directory.  
   - **Blocking defect:** The presence of three parallel manifests creates a risk of divergence. Choose one format (e.g., `checksums.json`) as the source of truth, deprecate the others, and update all references accordingly.

5. **Sample‑Size Adequacy**  
   - SC‑001 and SC‑012 require documentation of knot counts per crossing number and justification of the ≤ 10‑crossing validation benchmark. The file `docs/reproducibility/validation_scope.md` is mentioned, but the actual counts per crossing number are not shown in the provided excerpts.  
   - **Blocking defect:** Without explicit counts (e.g., “Crossing 10: 1 234 knots, 95 % have complete invariants”), reviewers cannot verify that stratified groups (alternating vs. non‑alternating) have sufficient size for descriptive reporting. The `sample_size_adequacy.md` file exists but its content is not confirmed; the review requires that it contain a table of counts and a brief adequacy discussion.

6. **Cross‑Reference Checks (Hyperbolic Volume)**  
   - FR‑013 mandates a ≥ 90 % match against KnotInfo where coverage ≥ 90 %. The document `hyperbolic_volume_validation.md` is only 372 bytes and appears to be a placeholder.  
   - **Blocking defect:** The validation results (match rate, coverage, source‑independence assessment) are not present, so the claim of data‑consistency cannot be verified.

### Summary of Required Changes (must be addressed before acceptance)

| Area | Required Action |
|------|-----------------|
| **Checksum Manifest** | Retain a single authoritative checksum file (e.g., `checksums.json`), remove/deprecate `checksums.csv` and `checksums.sha256`, and update all documentation to reference the single manifest. |
| **Duplicate‑Record Check** | Implement a duplicate‑ID detection step in `code/data/validator.py`, run it on the full dataset, and record the result (expected 0) in `data_quality_report.md`. |
| **Sample‑Size Documentation** | Populate `validation_scope.md` (or `sample_size_adequacy.md`) with a concrete table of knot counts per crossing number, and explicitly state that each stratified group meets the ≥ 5 % null‑field threshold and has enough records for descriptive statistics. |
| **Hyperbolic Volume Cross‑Check** | Complete `hyperbolic_volume_validation.md` with the actual coverage percentage, match rate, and a discussion of source independence (e.g., whether Knot Atlas and KnotInfo share underlying data). |
| **Artifact Hash** | Provide the SHA‑256 hash of the primary artifact (`tasks.md`) so the review can be processed automatically. |

Once these items are resolved, the data‑quality artifacts will fully satisfy the research‑stage requirements, and the reviewer can issue an **accept** verdict.
