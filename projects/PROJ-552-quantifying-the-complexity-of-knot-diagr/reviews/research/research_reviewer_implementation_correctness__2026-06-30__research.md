---
action_items:
- id: c331e6ba9675
  severity: writing
  text: 'File: code/data/validator.py'
- id: 4efb4dd0f221
  severity: writing
  text: 'File: code/analysis/data_quality.py'
- id: 0e251fccdf1a
  severity: writing
  text: 'File: docs/reproducibility/data_quality_report.md'
- id: 4d7ea19aa4ef
  severity: writing
  text: 'File: docs/reproducibility/invariant_coverage.md'
artifact_hash: 51f67afe33d622bdbc591f959097eeaa2314cfd198e275168461b1e145921cfa
artifact_path: projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/specs/010-quantifying-the-complexity-of-knot-diagr/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T05:06:55.529041Z'
reviewer_kind: llm
reviewer_name: research_reviewer_implementation_correctness
score: 0.0
verdict: minor_revision
---

The implementation largely follows the design, but a critical **data quality logic error** violates FR-009 and SC-001. The `missing_invariant_flags` are being applied to **core tabulated invariants** (specifically `braid_index`), which contradicts the specification that this flag is reserved *only* for invariants that cannot be computed from diagram representations (Phase 2+).

Per `docs/reproducibility/data_quality_flagging_counts.md` and `docs/reproducibility/invariant_coverage.md`, the system reports **9,988 records** flagged with `missing_invariant_flags` for `braid_index`. However, `braid_index` is a core invariant tabulated from Knot Atlas (FR-001, FR-003), not a computed invariant. The spec explicitly states: "Core invariants (crossing number, braid index) are TABULATED... Algorithm validation applies only to additional invariants."

This misapplication of flags:
1.  **Violates FR-009**: `missing_invariant_flags` must only be set when invariants cannot be *computed* from representations. Tabulated data should not trigger this flag.
2.  **Violates SC-001**: The dataset completeness check requires null percentages ≤ 5% for required fields. If 9,988 records (approx. 77% of the dataset) are flagged as "missing" a core invariant, the dataset fails the completeness benchmark, yet the `data_quality_report.md` claims "All fields have null percentage ≤ 5%". This is a direct contradiction in the implementation logic.
3.  **Breaks downstream analysis**: The regression and correlation modules likely treat these flagged records as invalid or missing, potentially skewing the "census" analysis or causing silent data exclusion.

The `code/data/validator.py` and `code/analysis/data_quality.py` logic must be corrected to distinguish between "tabulated but missing" (which should trigger `data_quality_flags` or a specific `tabulation_missing` flag, not `missing_invariant_flags`) and "uncomputable" (which triggers `missing_invariant_flags`).

## Required Changes

- **File**: `code/data/validator.py`
  **Change**: Refactor the flagging logic to ensure `missing_invariant_flags` are **only** set for invariants defined as "computed" in Phase 2+ (e.g., arc index, Seifert circle count). For core tabulated invariants (`crossing_number`, `braid_index`, `hyperbolic_volume`), if data is missing, set `data_quality_flags` with a specific reason code (e.g., `tabulation_missing`) instead of `missing_invariant_flags`.

- **File**: `code/analysis/data_quality.py`
  **Change**: Update the report generation logic to correctly count and report `data_quality_flags` vs. `missing_invariant_flags`. Ensure the `data_quality_report.md` accurately reflects that the 9,988 records flagged previously were due to a logic error, and re-run the validation to confirm the null percentage for `braid_index` is actually 0% (or the true missing rate) and not artificially inflated by the misapplied flag.

- **File**: `docs/reproducibility/data_quality_report.md`
  **Change**: Regenerate this report after fixing the validator logic. The current report claims "All fields have null percentage ≤ 5%" while simultaneously listing 9,988 `missing_invariant_flags` for `braid_index`. This contradiction must be resolved by correcting the underlying data and the report.

- **File**: `docs/reproducibility/invariant_coverage.md`
  **Change**: Update the coverage statistics to reflect the corrected flagging logic. The current report states "Braid Index: 23.0% coverage" due to the misapplied flags. This must be corrected to show the true tabulation coverage (expected ~100% for core invariants).
