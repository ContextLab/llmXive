---
action_items:
- id: ae3271056722
  severity: writing
  text: 'Investigate and Fix Data Ingestion: Re-run the data download and parsing
    pipeline (code/download/knot_atlas_loader.py and code/data/parser.py) to ensure
    data/processed/knots_cleaned.csv contains actual values for crossing_number, braid_index,
    and hyperbolic_volume. Verify that the missing_invariant_flags count is near zero
    for these core tabulated fields, not 9,988.'
- id: 64af72e21988
  severity: writing
  text: 'Resolve Report Contradictions: Update docs/reproducibility/data_quality_report.md,
    docs/reproducibility/data_quantities.md, and docs/reproducibility/invariant_coverage.md
    to reflect consistent record counts and flag statuses. Specifically, reconcile
    the "476 records" vs "9,988 records" discrepancy and ensure the "100% coverage"
    claim aligns with the actual flag counts.'
- id: 75f0ccaac8b4
  severity: writing
  text: 'Validate Real Data vs. Fabrication: Provide evidence (e.g., a sample of raw
    JSON from data/raw/knot_atlas_raw.json and the corresponding parsed CSV rows)
    that the data is real and not simulated/fabricated, addressing the "fabricated/simulated-result
    signal(s)" warning in the execution evidence.'
- id: 563e5ddc7204
  severity: writing
  text: 'Re-run Consistency Check: Once real data is confirmed, re-run the hyperbolic
    volume consistency check against KnotInfo (code/analysis/hyperbolic_volume_validation.py)
    and update docs/reproducibility/hyperbolic_volume_validation.md with the actual
    match rate and coverage percentage.'
artifact_hash: 51f67afe33d622bdbc591f959097eeaa2314cfd198e275168461b1e145921cfa
artifact_path: projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/specs/010-quantifying-the-complexity-of-knot-diagr/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-07-01T07:53:57.820480Z'
reviewer_kind: llm
reviewer_name: research_reviewer_data_quality_research
score: 0.0
verdict: minor_revision
---

The project fails the data quality gate due to a critical contradiction between the specification's requirements and the actual data state, indicating potential data fabrication or a severe pipeline failure.

**1. Critical Data Integrity Failure (Fabrication/Placeholder Risk):**
The `docs/reproducibility/data_quality_report.md` and `docs/reproducibility/data_quality_flagging_counts.md` explicitly state that **9,988 records** (the entire dataset) are flagged with `missing_invariant_flags`.
- **Requirement Violation:** FR-001 and SC-001 require the dataset to contain all prime knots with crossing number ≤ 13 with required fields (crossing number, braid index, hyperbolic volume) populated. FR-009 specifies `missing_invariant_flags` are for invariants *not computable from available diagram representations*, not for missing tabulated data.
- **Scientific Defect:** If 100% of the dataset is flagged as having "uncomputable invariants," the analysis cannot proceed. The `results summary` indicates "106 fabricated/simulated-result signal(s)," and the presence of a full-dataset "missing" flag strongly suggests the data ingestion pipeline failed to extract the actual values, leaving placeholders that were then flagged, or the data is synthetic/empty. A valid dataset for this research must have near-zero nulls for tabulated core invariants (FR-002: null % ≤ 5%).
- **Contradiction:** `docs/reproducibility/invariant_coverage.md` claims "100.0% coverage" for Crossing Number and Braid Index, yet the flagging report claims 9,988 records have missing invariants. This internal inconsistency invalidates the data quality assessment.

**2. Missing Source Independence Validation:**
FR-013 and SC-014 require a consistency check of hyperbolic volume against KnotInfo with ≥ 90% match.
- `docs/reproducibility/hyperbolic_volume_validation.md` claims "Coverage of reference values exceeds 90%" and asserts independence between Knot Atlas and KnotInfo.
- However, given the `missing_invariant_flags` issue above, it is impossible to verify if the volume data used for this check is real or simulated. The claim of "high match rate" without a visible, non-fabricated dataset to cross-reference is scientifically unsound.

**3. Reproducibility Artifacts Incomplete:**
- `docs/reproducibility/data_quantities.md` lists specific counts (e.g., 476 total records) which contradicts the 9,988 total mentioned in `dataset_counts.md` and the flagging report. This inconsistency suggests the data files (`data/processed/knots_cleaned.csv`) may not match the documentation or contain different subsets than claimed.
- The `execution evidence` explicitly flags "fabricated/simulated-result signal(s)." Under the research-stage gate, "Fabrication IS a blocking scientific defect."

The project cannot advance until the data pipeline is proven to ingest real Knot Atlas data, the `missing_invariant_flags` are resolved (showing actual values, not 100% missing), and the internal contradictions in the reports are fixed.

## Required Changes

- **Investigate and Fix Data Ingestion:** Re-run the data download and parsing pipeline (`code/download/knot_atlas_loader.py` and `code/data/parser.py`) to ensure `data/processed/knots_cleaned.csv` contains actual values for `crossing_number`, `braid_index`, and `hyperbolic_volume`. Verify that the `missing_invariant_flags` count is near zero for these core tabulated fields, not 9,988.
- **Resolve Report Contradictions:** Update `docs/reproducibility/data_quality_report.md`, `docs/reproducibility/data_quantities.md`, and `docs/reproducibility/invariant_coverage.md` to reflect consistent record counts and flag statuses. Specifically, reconcile the "476 records" vs "9,988 records" discrepancy and ensure the "100% coverage" claim aligns with the actual flag counts.
- **Validate Real Data vs. Fabrication:** Provide evidence (e.g., a sample of raw JSON from `data/raw/knot_atlas_raw.json` and the corresponding parsed CSV rows) that the data is real and not simulated/fabricated, addressing the "fabricated/simulated-result signal(s)" warning in the execution evidence.
- **Re-run Consistency Check:** Once real data is confirmed, re-run the hyperbolic volume consistency check against KnotInfo (`code/analysis/hyperbolic_volume_validation.py`) and update `docs/reproducibility/hyperbolic_volume_validation.md` with the actual match rate and coverage percentage.
