---
action_items:
- id: bc57b135f923
  severity: writing
  text: Create the directory structure infer/, eval/, data/, and tests/ as defined
    in plan.md.
- id: b72cf74b49ef
  severity: writing
  text: Implement infer/run.py to serve as the entry point for the inference pipeline,
    ensuring it generates outputs/infer_results.jsonl as specified in FR-001.
- id: 74cba55a5825
  severity: writing
  text: Implement eval/run.py to consume the inference results and generate outputs/evaluation_report.json
    containing the SAA metric, as specified in FR-003 and FR-004.
- id: dce37726176a
  severity: writing
  text: Create data/validate_dataset.py to perform the dataset integrity checks (FR-005)
    and generate outputs/validation_log.json.
- id: 7521979b9f82
  severity: writing
  text: Implement the test suite in tests/ (including contract/ and integration/ subdirectories)
    to verify the schemas and pipeline execution as per T010-T026.
- id: 455cd60d0eb3
  severity: writing
  text: Move or refactor the logic currently in citevqa_cpu_adaptation.py into the
    appropriate modular files (infer/, eval/, data/) to ensure the codebase matches
    the planned architecture.
- id: 35b0644de41a
  severity: writing
  text: Generate the required documentation files in docs/ and docs/reproducibility/
    as outlined in T036.
- id: 44b735d7bef5
  severity: writing
  text: Update the output generation logic to produce the JSON/JSONL artifacts specified
    in the spec, or update the spec to explicitly accept the CSV format if the scope
    has changed (but the latter requires a spec revision, not just a code change).
artifact_hash: 3bc58d267beba9781004e1504dd10ce4d5392a1219ff46841f44df44f7e74495
artifact_path: projects/PROJ-601-https-arxiv-org-abs-2605-12882/specs/001-https-arxiv-org-abs-2605-12882/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T12:15:39.497626Z'
reviewer_kind: llm
reviewer_name: research_reviewer_implementation_completeness
score: 0.0
verdict: minor_revision
---

The implementation is **incomplete** relative to the claimed scope defined in `spec.md` and `tasks.md`. While the execution gate passed and produced artifacts (`results.csv`, `summary.csv`, `saa_distribution.png`), the codebase structure and file inventory do not match the detailed implementation plan.

**Specific Defects:**

1.  **Missing Core Scripts**: The spec and `tasks.md` explicitly require `infer/run.py` (T013, T015) and `eval/run.py` (T022) as the primary entry points for the pipeline. The code summary only lists `citevqa_cpu_adaptation.py`. There is no evidence of the `infer/` or `eval/` directories or the specific runner scripts mandated by the architecture.
2.  **Missing Validation Utility**: `tasks.md` (T027) requires `data/validate_dataset.py` to verify dataset integrity (FR-005). This file is absent from the code summary.
3.  **Missing Test Suite**: The plan mandates a `tests/` directory with contract and integration tests (T010-T026). The code summary shows no `tests/` directory.
4.  **Missing Documentation**: The plan requires `docs/reproducibility/` and `docs/` (T036), but the documentation summary indicates "no files found".
5.  **Artifact Mismatch**: The spec requires `outputs/infer_results.jsonl` and `outputs/evaluation_report.json`. The actual artifacts are `data/results.csv` and `data/summary.csv`. While the execution passed, the output format deviates from the spec's defined schema, suggesting the implementation may be a simplified prototype rather than the full pipeline described in `tasks.md`.

The current state appears to be a single-file prototype (`citevqa_cpu_adaptation.py`) that bypasses the modular structure (inference/evaluation separation, validation layer, test suite) defined in the plan. To meet the research-stage bar for "complete implementation per spec," the project must be restructured to include the missing modules and scripts.

## Required Changes

- Create the directory structure `infer/`, `eval/`, `data/`, and `tests/` as defined in `plan.md`.
- Implement `infer/run.py` to serve as the entry point for the inference pipeline, ensuring it generates `outputs/infer_results.jsonl` as specified in FR-001.
- Implement `eval/run.py` to consume the inference results and generate `outputs/evaluation_report.json` containing the SAA metric, as specified in FR-003 and FR-004.
- Create `data/validate_dataset.py` to perform the dataset integrity checks (FR-005) and generate `outputs/validation_log.json`.
- Implement the test suite in `tests/` (including `contract/` and `integration/` subdirectories) to verify the schemas and pipeline execution as per T010-T026.
- Move or refactor the logic currently in `citevqa_cpu_adaptation.py` into the appropriate modular files (`infer/`, `eval/`, `data/`) to ensure the codebase matches the planned architecture.
- Generate the required documentation files in `docs/` and `docs/reproducibility/` as outlined in T036.
- Update the output generation logic to produce the JSON/JSONL artifacts specified in the spec, or update the spec to explicitly accept the CSV format if the scope has changed (but the latter requires a spec revision, not just a code change).
