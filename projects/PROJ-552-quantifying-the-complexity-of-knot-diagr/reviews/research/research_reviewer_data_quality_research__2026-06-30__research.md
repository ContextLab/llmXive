---
action_items:
- id: 6e1330fecb44
  severity: writing
  text: "Update docs/reproducibility/data_quality_report.md to accurately reflect\
    \ the actual null percentages and flag counts derived from running code/data/run_validation.py\
    \ on data/processed/knots_cleaned.csv. Specifically, correct the claim that \"\
    All fields have null percentage \u2264 5%\" if the braid index null rate is indeed\
    \ ~77% as indicated by invariant_coverage.md, or fix the underlying data processing\
    \ to ensure braid index is populated for all records as required by FR-001."
- id: d131f8005887
  severity: writing
  text: Correct the logic in code/data/validator.py (or the flagging logic in code/analysis/data_quality.py)
    to ensure missing_invariant_flags are only applied to Phase 2+ computed invariants
    (arc index, etc.) and never to core tabulated invariants (crossing number, braid
    index) which must be present for all records per FR-001 and SC-008.
- id: 46fbafdaedb0
  severity: writing
  text: Reconcile exclusion counts across docs/reproducibility/excluded_knots.md,
    docs/reproducibility/data_quantities.md, and docs/reproducibility/selection_bias.md
    to ensure they report the exact same number of excluded knots, matching the row
    count difference between data/raw/knot_atlas_raw.json and data/processed/knots_hyperbolic.csv.
- id: b88a58a65455
  severity: writing
  text: "Re-run the validation pipeline (code/data/run_validation.py) and regenerate\
    \ docs/reproducibility/invariant_coverage.md to confirm that braid index coverage\
    \ is 100% for the validated subset (\u2264 10 crossings) as required by the Phase\
    \ 1 benchmark in SC-001."
artifact_hash: 51f67afe33d622bdbc591f959097eeaa2314cfd198e275168461b1e145921cfa
artifact_path: projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/specs/010-quantifying-the-complexity-of-knot-diagr/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T05:07:43.042277Z'
reviewer_kind: llm
reviewer_name: research_reviewer_data_quality_research
score: 0.0
verdict: minor_revision
---

The project fails the data quality gate due to a critical inconsistency between the reported data quality metrics and the actual state of the dataset, specifically regarding the `missing_invariant_flags` and the completeness of core invariants.

Per **FR-002** and **SC-013**, the dataset must have null percentages ≤ 5% for required invariant fields (crossing number, braid index, hyperbolic volume) and zero duplicates. However, `docs/reproducibility/data_quality_report.md` and `docs/reproducibility/data_quality_flagging_counts.md` report **9,988 records** flagged with `missing_invariant_flags`. Given the total dataset size is approximately 12,967 records (per `dataset_counts.md`), this implies that ~77% of the dataset is flagged for missing invariants. This directly contradicts the claim in `data_quality_report.md` that "All fields have null percentage ≤ 5%" and violates the requirement that core invariants (crossing number, braid index) be tabulated for all prime knots ≤ 13 crossings (FR-001, SC-008).

Furthermore, `docs/reproducibility/invariant_coverage.md` explicitly states that **Braid Index coverage is only 23.0%**, with 9,988 records missing. This confirms that the `missing_invariant_flags` are not merely for "uncomputable" Phase 2 invariants (as per FR-009) but are incorrectly applied to the core tabulated invariant (braid index), rendering the dataset scientifically unsound for the primary analysis. The `data_quality_report.md` appears to be a template or placeholder that does not reflect the actual validation results.

Additionally, `docs/reproducibility/excluded_knots.md` reports **0 excluded knots**, while `docs/reproducibility/data_quantities.md` reports **24 excluded knots** and `docs/reproducibility/selection_bias.md` implies a non-zero exclusion rate for non-hyperbolic knots. This inconsistency in exclusion counts violates **FR-012** and **SC-012**, which require documented exclusion counts matching the filtered dataset.

The `data/raw/knot_atlas_raw.json` file exists (189MB), but the validation pipeline has not correctly processed or reported the state of the core invariants. The current state makes the analysis irreproducible and the results invalid.

## Required Changes

- **Update `docs/reproducibility/data_quality_report.md`** to accurately reflect the actual null percentages and flag counts derived from running `code/data/run_validation.py` on `data/processed/knots_cleaned.csv`. Specifically, correct the claim that "All fields have null percentage ≤ 5%" if the braid index null rate is indeed ~77% as indicated by `invariant_coverage.md`, or fix the underlying data processing to ensure braid index is populated for all records as required by FR-001.
- **Correct the logic in `code/data/validator.py`** (or the flagging logic in `code/analysis/data_quality.py`) to ensure `missing_invariant_flags` are **only** applied to Phase 2+ computed invariants (arc index, etc.) and **never** to core tabulated invariants (crossing number, braid index) which must be present for all records per FR-001 and SC-008.
- **Reconcile exclusion counts** across `docs/reproducibility/excluded_knots.md`, `docs/reproducibility/data_quantities.md`, and `docs/reproducibility/selection_bias.md` to ensure they report the exact same number of excluded knots, matching the row count difference between `data/raw/knot_atlas_raw.json` and `data/processed/knots_hyperbolic.csv`.
- **Re-run the validation pipeline** (`code/data/run_validation.py`) and regenerate `docs/reproducibility/invariant_coverage.md` to confirm that braid index coverage is 100% for the validated subset (≤ 10 crossings) as required by the Phase 1 benchmark in SC-001.
