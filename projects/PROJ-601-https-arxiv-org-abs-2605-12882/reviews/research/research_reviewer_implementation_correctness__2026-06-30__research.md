---
action_items:
- id: eda0336ea947
  severity: writing
  text: 'Refactor citevqa_cpu_adaptation.py into the modular structure defined in
    plan.md: create infer/run.py for inference, eval/run.py for scoring, and data/validate_dataset.py
    for pre-checks.'
- id: 4a46799a401b
  severity: writing
  text: Replace data/results.csv and data/summary.csv with outputs/infer_results.jsonl
    (containing question, predicted_answer, predicted_bbox) and outputs/evaluation_report.json
    (containing saa_score, attribution_hallucination_rate, skipped_count).
- id: 722416960fde
  severity: writing
  text: Implement the dataset validation logic in data/validate_dataset.py to explicitly
    check for ground_truth_bbox and image_path fields, logging skipped records to
    outputs/validation_log.json as per FR-005 and SC-005.
- id: 49c77feb8df4
  severity: writing
  text: Ensure eval/run.py calculates and reports the attribution_hallucination_rate
    (correct answer + wrong region) to satisfy the Phase 6 bias mitigation requirements.
artifact_hash: 3bc58d267beba9781004e1504dd10ce4d5392a1219ff46841f44df44f7e74495
artifact_path: projects/PROJ-601-https-arxiv-org-abs-2605-12882/specs/001-https-arxiv-org-abs-2605-12882/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T12:15:22.234657Z'
reviewer_kind: llm
reviewer_name: research_reviewer_implementation_correctness
score: 0.0
verdict: minor_revision
---

The implementation deviates significantly from the design specifications regarding file structure, artifact generation, and pipeline logic. The spec and plan explicitly define a modular architecture with specific entry points (`infer/run.py`, `eval/run.py`, `data/validate_dataset.py`) and output artifacts (`outputs/infer_results.jsonl`, `outputs/evaluation_report.json`).

However, the current code summary shows a monolithic `citevqa_cpu_adaptation.py` (11KB) and data artifacts in `data/results.csv` and `data/summary.csv`. This indicates the implementation did not follow the planned directory structure or the specified output formats. The spec requires JSONL for inference results to support streaming and JSON for the evaluation report to ensure machine-readability of the SAA breakdown; CSV outputs suggest a different, un-specified data flow.

Furthermore, the plan mandates a validation phase (`data/validate_dataset.py`) to check for `ground_truth_bbox` and `image_path` before inference (FR-005). The current artifacts (`results.csv`) do not demonstrate that this validation step occurred or that skipped records were logged as required by SC-005. The "WYSIATI" bias mitigation (Phase 6) requires specific metrics (`attribution_hallucination_rate`) in the report, which cannot be verified in a generic `summary.csv` without the defined schema.

The execution gate passed, but it likely validated a different script or a simplified version that does not match the `tasks.md` requirements for the CiteVQA reproduction pipeline. The implementation must be restructured to match the spec's modular design and output contracts.

## Required Changes
- Refactor `citevqa_cpu_adaptation.py` into the modular structure defined in `plan.md`: create `infer/run.py` for inference, `eval/run.py` for scoring, and `data/validate_dataset.py` for pre-checks.
- Replace `data/results.csv` and `data/summary.csv` with `outputs/infer_results.jsonl` (containing `question`, `predicted_answer`, `predicted_bbox`) and `outputs/evaluation_report.json` (containing `saa_score`, `attribution_hallucination_rate`, `skipped_count`).
- Implement the dataset validation logic in `data/validate_dataset.py` to explicitly check for `ground_truth_bbox` and `image_path` fields, logging skipped records to `outputs/validation_log.json` as per FR-005 and SC-005.
- Ensure `eval/run.py` calculates and reports the `attribution_hallucination_rate` (correct answer + wrong region) to satisfy the Phase 6 bias mitigation requirements.
