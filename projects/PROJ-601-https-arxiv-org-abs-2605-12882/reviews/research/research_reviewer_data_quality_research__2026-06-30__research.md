---
action_items:
- id: 7e7082abdcb8
  severity: writing
  text: 'Create/Update outputs/evaluation_report.json: Generate the machine-readable
    JSON report as specified in FR-004. It must contain the saa_score, total_samples,
    skipped_count, and a breakdown of error types (e.g., answer_only_correct, region_only_correct,
    both_correct).'
- id: 957a0841e0f8
  severity: writing
  text: 'Create/Update outputs/infer_results.jsonl: Ensure the raw prediction artifacts
    are generated and saved in JSONL format, containing question, predicted_answer,
    and predicted_bbox for every processed record, as required by FR-001.'
- id: 9baa9dd041f0
  severity: writing
  text: 'Update data/results.csv or replace with outputs/validation_log.json: If data/results.csv
    is intended to be the validation log, it must be renamed to outputs/validation_log.json
    and populated with the list of skipped record IDs and the specific reasons (e.g.,
    "missing_bbox", "missing_image") as required by FR-005 and SC-005.'
- id: ca99b0afc2a1
  severity: writing
  text: 'Verify Schema Compliance: Ensure all generated data artifacts (CSV/JSON)
    include the mandatory columns/fields: question, answer, ground_truth_bbox, predicted_bbox,
    and image_path (or image_id) to allow for independent verification of the SAA
    calculation.'
artifact_hash: 3bc58d267beba9781004e1504dd10ce4d5392a1219ff46841f44df44f7e74495
artifact_path: projects/PROJ-601-https-arxiv-org-abs-2605-12882/specs/001-https-arxiv-org-abs-2605-12882/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T12:16:16.291590Z'
reviewer_kind: llm
reviewer_name: research_reviewer_data_quality_research
score: 0.0
verdict: minor_revision
---

The project fails to meet the data quality standards required for a research-stage artifact because the primary data artifacts do not conform to the schema and provenance requirements defined in `spec.md` and `plan.md`.

**1. Schema Mismatch and Missing Critical Fields**
The specification (FR-005, US-3) and plan explicitly require the validation and processing of records containing `question`, `answer`, `ground_truth_bbox`, and `image_path`. The current output artifact `data/results.csv` (3244 bytes) appears to be a simple tabular summary. It lacks the granular, record-level data necessary to verify the "Strict Attributed Accuracy" (SAA) calculation. Specifically:
- There is no evidence of `ground_truth_bbox` or `predicted_bbox` columns in the provided CSV, which are mandatory for the IoU calculation described in `plan.md` (Phase 2).
- The artifact `data/summary.csv` (108 bytes) is too small to contain the detailed breakdown of "Attribution Hallucination" cases (correct answer, wrong region) required by FR-004 and US-2.
- The required machine-readable report `outputs/evaluation_report.json` (FR-004) is missing from the artifact list; the project only produced `figures/saa_distribution.png`, which is a visualization, not the raw data artifact required for reproducibility.

**2. Provenance and Reproducibility Gap**
The `spec.md` mandates that the system must generate `outputs/infer_results.jsonl` (raw predictions) and `outputs/evaluation_report.json` (metrics). The current execution produced `data/results.csv` and `data/summary.csv`. This deviation suggests the pipeline either:
- Did not execute the `eval/run.py` script as planned, or
- Implemented a custom, undocumented data transformation that bypasses the required schema.
Without the intermediate `infer_results.jsonl` and the final `evaluation_report.json`, it is impossible to verify the SAA calculation logic or reproduce the specific "Attribution Hallucination" counts. The current CSVs do not provide the necessary audit trail.

**3. Data Integrity Verification**
The plan requires a `data/validate_dataset.py` script to log skipped records to `outputs/validation_log.json` (Phase 0). No such log file is present in the artifact list. Consequently, the "missing data handling" requirement (FR-005) cannot be verified. We cannot confirm if records were skipped due to missing bounding boxes or images, nor can we verify the count of skipped records as required by SC-005.

**4. Advisory Alignment**
The advisory from `daniel-kahneman-simulated` warns against "WYSIATI" (What You See Is All There Is) and the risk of rewarding coherence over truth. The current data artifacts (simple CSVs) obscure the distinction between "Answer Correct" and "Region Correct." Without the granular data showing *which* records had correct answers but wrong bounding boxes, the project fails to address the specific bias concern raised. The data quality is insufficient to support the scientific claim of validating SAA.

## Required Changes

- **Create/Update `outputs/evaluation_report.json`**: Generate the machine-readable JSON report as specified in FR-004. It must contain the `saa_score`, `total_samples`, `skipped_count`, and a breakdown of error types (e.g., `answer_only_correct`, `region_only_correct`, `both_correct`).
- **Create/Update `outputs/infer_results.jsonl`**: Ensure the raw prediction artifacts are generated and saved in JSONL format, containing `question`, `predicted_answer`, and `predicted_bbox` for every processed record, as required by FR-001.
- **Update `data/results.csv` or replace with `outputs/validation_log.json`**: If `data/results.csv` is intended to be the validation log, it must be renamed to `outputs/validation_log.json` and populated with the list of skipped record IDs and the specific reasons (e.g., "missing_bbox", "missing_image") as required by FR-005 and SC-005.
- **Verify Schema Compliance**: Ensure all generated data artifacts (CSV/JSON) include the mandatory columns/fields: `question`, `answer`, `ground_truth_bbox`, `predicted_bbox`, and `image_path` (or `image_id`) to allow for independent verification of the SAA calculation.
