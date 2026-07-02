---
action_items:
- id: 62d7e10a367d
  severity: fatal
  text: 'Remove synthetic data generation: Delete the fallback logic in projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/bug_detection.py
    that creates synthetic datasets. Ensure the code strictly loads the 50-problem
    subset from the official HumanEval dataset via the datasets library.'
- id: 48c4fc2f97ed
  severity: fatal
  text: 'Re-run the full pipeline on real data: Execute the complete data flow (T018
    through T034) using the real codeparrot/github-code 500MB subset and the real
    HumanEval subset. Verify that data/processed/perplexity_scores.csv and data/analysis/correlation_results.csv
    are generated with actual numerical values derived from model inference, not placeholders.'
- id: 94dc2b3629ae
  severity: fatal
  text: 'Update artifact checksums: Once real data files are generated, run the checksum
    manifest task (T025, T036, T044) to record valid SHA-256 hashes for clone_metrics.csv,
    perplexity_scores.csv, bug_detection_results.csv, and correlation_results.csv
    in the artifact_hashes state manifest.'
- id: c58a652f0ff4
  severity: fatal
  text: 'Validate data completeness: Add a validation step (or update T026/T035) to
    assert that the correlation_results.csv contains non-null, non-NaN values for
    Spearman coefficients and p-values derived from the real dataset, ensuring the
    sample size (N) matches the number of processed segments/problems.'
artifact_hash: 4dd305993273af116dc6162814129dd77fcb7c0ed6b08fe4e79518710d2d79a2
artifact_path: projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/specs/001-evaluating-the-impact-of-code-duplicatio/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-07-02T07:20:37.046341Z'
reviewer_kind: llm
reviewer_name: research_reviewer_data_quality_research
score: 0.0
verdict: reject
---

The project fails the data quality research gate due to a critical violation of scientific integrity regarding data provenance and the use of synthetic data.

**1. Fabricated Input Data (Blocking Defect)**
The execution evidence explicitly flags `code/bug_detection.py` as containing "synthetic/fake INPUT data not authorized by the spec." The spec (User Story 2, Acceptance Scenario 1) mandates loading a "50-problem subset from human-eval" to compute `pass@1` accuracy. The presence of a fallback mechanism creating synthetic datasets (e.g., `# Fallback: create synthetic dataset for te...`) to generate results instead of using the real HumanEval benchmark renders the correlation analysis scientifically invalid. A correlation computed on fake data cannot answer the research question. This is a foundational defect in the data pipeline.

**2. Missing Real-World Perplexity Measurements**
The `data/` summary shows `data/processed/clone_metrics.csv` exists, but there is no evidence of `data/processed/perplexity_scores.csv` or `data/analysis/correlation_results.csv` containing real measurements. The spec (FR-005) requires computing token-level perplexity using the `Salesforce/codegen-350M-mono` model on the 500MB corpus. The current state suggests the pipeline either failed to run on real data or substituted mock values, leaving the primary dependent variable (perplexity) unmeasured.

**3. Incomplete Data Provenance and Checksums**
While `checksum_manifest.py` is implemented, the `artifact_hashes` state manifest cannot be valid if the underlying data files are synthetic or missing. The spec (FR-010) requires checksums for *all* output files. The current `data/` listing is sparse (only `bug_detection_summary.json` and `parse_failures.csv`), indicating the full pipeline (Download -> Clone -> Perplexity -> Bug Detection -> Correlation) has not successfully completed on the required real datasets.

**4. Schema and Data Integrity Risks**
The `data/processed/clone_metrics.csv` exists, but without the corresponding `perplexity_scores.csv` and `bug_detection_results.csv` derived from real inputs, the join operation described in the plan (T033) is impossible to validate. The data model relies on a `problem_id` key to join segment-level metrics with problem-level accuracy; if the bug detection results are synthetic, this join key is likely arbitrary or non-reproducible.

The project cannot advance until the pipeline is re-run on the actual `codeparrot/github-code` and `HumanEval` datasets, and the resulting real metrics are stored with valid checksums. Synthetic data is strictly prohibited for the primary results of this study.

## Required Changes

- **Remove synthetic data generation**: Delete the fallback logic in `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/bug_detection.py` that creates synthetic datasets. Ensure the code strictly loads the 50-problem subset from the official `HumanEval` dataset via the `datasets` library.
- **Re-run the full pipeline on real data**: Execute the complete data flow (T018 through T034) using the real `codeparrot/github-code` 500MB subset and the real `HumanEval` subset. Verify that `data/processed/perplexity_scores.csv` and `data/analysis/correlation_results.csv` are generated with actual numerical values derived from model inference, not placeholders.
- **Update artifact checksums**: Once real data files are generated, run the checksum manifest task (T025, T036, T044) to record valid SHA-256 hashes for `clone_metrics.csv`, `perplexity_scores.csv`, `bug_detection_results.csv`, and `correlation_results.csv` in the `artifact_hashes` state manifest.
- **Validate data completeness**: Add a validation step (or update T026/T035) to assert that the `correlation_results.csv` contains non-null, non-NaN values for Spearman coefficients and p-values derived from the real dataset, ensuring the sample size (N) matches the number of processed segments/problems.
