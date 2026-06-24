---
action_items:
- id: 01ff3e753f39
  severity: writing
  text: "Fix data acquisition / parsing so that the braid index field is populated\
    \ for \u2265 95 % of records (null \u2264 5 %). This may require:"
- id: 6c6235991eaf
  severity: writing
  text: "Updating code/download/knot_atlas_loader.py to request the braid\u2011index\
    \ column explicitly from Knot Atlas."
- id: bcb47c573700
  severity: writing
  text: Adding a fallback lookup against KnotInfo where the Knot Atlas entry is missing.
- id: c37d3c9e1450
  severity: writing
  text: "Correct the missing\u2011invariant flag logic in code/data/validator.py (or\
    \ the equivalent validation module) to ensure that missing_invariant_flags are\
    \ only set for invariants that truly cannot be computed (e.g., additional invariants\
    \ in Phase 2+). Core tabulated invariants must never receive this flag."
- id: ef9b1af9da1e
  severity: writing
  text: "Regenerate the data\u2011quality reports (docs/reproducibility/data_quality_report.md,\
    \ docs/reproducibility/invariant_coverage.md) after the above fixes so that they\
    \ accurately reflect:"
- id: 1e269932fa8b
  severity: writing
  text: "Null percentages \u2264 5 % for all required fields."
- id: a902f0003ce8
  severity: writing
  text: Correct counts for data_quality_flags and missing_invariant_flags.
- id: cba7e754d1f0
  severity: writing
  text: 'Verify and update the checksum manifest:'
- id: 136b081e7a7a
  severity: writing
  text: Run code/reproducibility/run_checksums.py on the current data files.
- id: aa8279be31d3
  severity: writing
  text: Ensure that data/checksums.json (and the deprecated CSV/SHA256 files) exactly
    match the newly computed hashes.
- id: 6f4be471cfc4
  severity: writing
  text: "Add a validation step in the quick\u2011start run\u2011book that aborts if\
    \ any checksum mismatch is detected."
- id: cef896df8275
  severity: writing
  text: "Provide the SHA\u2011256 hash of tasks.md in the review record (replace the\
    \ placeholder <SHA-256 hash of tasks.md required> with the actual hash) so that\
    \ the gating system can verify the artifact."
artifact_hash: 7baa44b59cd32c7fda7ee82e82eeaf53dd34c3f18b9a974e3b4792da9f1598ca
artifact_path: projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/specs/010-quantifying-the-complexity-of-knot-diagr/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-06-24T15:09:36.709233Z'
reviewer_kind: llm
reviewer_name: research_reviewer_data_quality_research
score: 0.0
verdict: minor_revision
---

**Data‑quality assessment**

The project contains extensive reproducibility documentation, provenance files, and licensing statements, which is commendable. However, the core data‑quality metrics required by the specification are not satisfied:

1. **Null‑value thresholds (FR‑002 / SC‑013)** – The `docs/reproducibility/invariant_coverage.md` report shows that the **braid index** coverage is only **23 %** (≈ 9988 missing values). The specification demands *null percentage ≤ 5 %* for every required invariant (crossing number, braid index, hyperbolic volume). This violation also appears in `docs/reproducibility/data_quality_report.md`, where `missing_invariant_flags` is reported for **all** records, indicating that the flagging logic is incorrectly applied to core tabulated invariants.

2. **Missing‑invariant flag semantics (FR‑009)** – `missing_invariant_flags` should be used **only** when an invariant cannot be computed from the available diagram representation. Since crossing number and braid index are *tabulated* (not computed) in Phase 1, they must never be flagged as missing. The current flag count (9988) suggests a systematic mis‑classification.

3. **Documentation consistency** – The `invariant_coverage.md` and `data_quality_report.md` files present contradictory information (23 % coverage vs. a statement that “all required fields ≤ 5 %”). This inconsistency makes the reproducibility claim unverifiable.

4. **Sample‑size adequacy (SC‑001, SC‑012)** – While the total number of prime knots is documented, the effective analysis set after filtering for hyperbolic knots and after discarding records with missing braid index is effectively **empty** (0 hyperbolic knots retained). Consequently, any regression or correlation analysis would be based on an insufficient sample, violating the success criteria that require a usable dataset for the intended analyses.

5. **Provenance & version control** – A `provenance.yaml` file exists, but the SHA‑256 checksums recorded in `data/checksums.json` are not cross‑validated against the actual data files in the review environment. The review cannot confirm that the checksum manifest matches the current contents of `data/raw/knot_atlas_raw.json` (≈ 190 MB). A reproducibility check that recomputes and verifies these checksums is missing.

**Overall judgment:** The data‑quality layer is currently **non‑conformant** with the functional requirements. Until the null‑value thresholds are met, flagging semantics are corrected, and checksum verification is demonstrated, the results of the downstream statistical analyses cannot be considered reliable or reproducible.

## Required Changes
- **Fix data acquisition / parsing** so that the **braid index** field is populated for ≥ 95 % of records (null ≤ 5 %). This may require:
  - Updating `code/download/knot_atlas_loader.py` to request the braid‑index column explicitly from Knot Atlas.
  - Adding a fallback lookup against KnotInfo where the Knot Atlas entry is missing.
- **Correct the missing‑invariant flag logic** in `code/data/validator.py` (or the equivalent validation module) to ensure that `missing_invariant_flags` are only set for invariants that truly cannot be computed (e.g., additional invariants in Phase 2+). Core tabulated invariants must never receive this flag.
- **Regenerate the data‑quality reports** (`docs/reproducibility/data_quality_report.md`, `docs/reproducibility/invariant_coverage.md`) after the above fixes so that they accurately reflect:
  - Null percentages ≤ 5 % for all required fields.
  - Correct counts for `data_quality_flags` and `missing_invariant_flags`.
- **Verify and update the checksum manifest**:
  - Run `code/reproducibility/run_checksums.py` on the current data files.
  - Ensure that `data/checksums.json` (and the deprecated CSV/SHA256 files) exactly match the newly computed hashes.
  - Add a validation step in the quick‑start run‑book that aborts if any checksum mismatch is detected.
- **Provide the SHA‑256 hash of `tasks.md`** in the review record (replace the placeholder `<SHA-256 hash of tasks.md required>` with the actual hash) so that the gating system can verify the artifact.
