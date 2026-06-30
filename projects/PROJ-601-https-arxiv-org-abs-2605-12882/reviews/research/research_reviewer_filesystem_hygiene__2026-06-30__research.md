---
action_items:
- id: 8b13eb96ab74
  severity: writing
  text: Create the docs/reproducibility/ directory and add data_quality_report.md
    detailing the dataset validation process, including the count of skipped records
    and reasons, as required by spec.md (FR-005) and plan.md.
- id: 3ad640d4e064
  severity: writing
  text: Create the outputs/ directory and ensure the pipeline generates outputs/infer_results.jsonl,
    outputs/evaluation_report.json, and outputs/validation_log.json instead of placing
    them in data/.
- id: a5ff1e41de1e
  severity: writing
  text: 'Reorganize the source code to match plan.md: move citevqa_cpu_adaptation.py
    logic into infer/run.py and eval/run.py (or create these files), create data/validate_dataset.py,
    and establish the external/CiteVQA/ submodule structure.'
- id: 51c19e18ab4c
  severity: writing
  text: Update README.md to reflect the new directory structure, including instructions
    for initializing the external/CiteVQA submodule and running the pipeline from
    the root.
artifact_hash: 3bc58d267beba9781004e1504dd10ce4d5392a1219ff46841f44df44f7e74495
artifact_path: projects/PROJ-601-https-arxiv-org-abs-2605-12882/specs/001-https-arxiv-org-abs-2605-12882/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T12:16:33.907763Z'
reviewer_kind: llm
reviewer_name: research_reviewer_filesystem_hygiene
score: 0.0
verdict: minor_revision
---

The project exhibits significant filesystem hygiene issues that violate the structural expectations defined in `plan.md` and `spec.md`, rendering the artifact layout inconsistent with the research design.

1.  **Missing Documentation Directory**: The `plan.md` explicitly defines a `docs/reproducibility/` directory structure (e.g., `docs/reproducibility/hyperbolic_volume_validation.md` is implied by the pattern, though the specific file name in the plan is `docs/reproducibility/data_quality_report.md` or similar). The current `docs summary` reports "(no files found)". The `spec.md` requires logging skipped records to `outputs/validation_log.json` and generating a final report, but there is no documentation describing the data validation process or the SAA calculation methodology. This makes the work irreproducible without reading the code.

2.  **Incorrect Artifact Locations**:
    *   **Inference Results**: `spec.md` and `plan.md` mandate that raw prediction artifacts be generated at `outputs/infer_results.jsonl`. The execution evidence shows artifacts at `data/results.csv` and `data/summary.csv`. This violates the defined data flow where `infer/run.py` outputs to `outputs/`.
    *   **Evaluation Report**: `spec.md` requires `outputs/evaluation_report.json`. The current artifacts are `data/summary.csv`.
    *   **Validation Log**: `plan.md` requires `outputs/validation_log.json`. No such file exists in the `outputs/` directory (which appears to be missing entirely based on the tree listing).

3.  **Missing Source Code Structure**: The `plan.md` and `tasks.md` define a specific source structure: `external/CiteVQA/`, `data/validate_dataset.py`, `infer/run.py`, `eval/run.py`, and `tests/`. The current `code summary` only lists `citevqa_cpu_adaptation.py` and `requirements.txt` at the root. The modular structure (`infer/`, `eval/`, `data/`, `tests/`) is absent, and the `external/` submodule is not visible in the listing. This suggests the implementation has not followed the planned directory layout, making the project difficult to navigate and maintain.

4.  **Missing `README.md` Content**: While `README.md` exists (1410 bytes), it likely lacks the necessary instructions for setting up the `external/CiteVQA` submodule and running the specific pipeline steps (`infer/run.py`, `eval/run.py`) as defined in the plan, given the structural deviations.

## Required Changes

- Create the `docs/reproducibility/` directory and add `data_quality_report.md` detailing the dataset validation process, including the count of skipped records and reasons, as required by `spec.md` (FR-005) and `plan.md`.
- Create the `outputs/` directory and ensure the pipeline generates `outputs/infer_results.jsonl`, `outputs/evaluation_report.json`, and `outputs/validation_log.json` instead of placing them in `data/`.
- Reorganize the source code to match `plan.md`: move `citevqa_cpu_adaptation.py` logic into `infer/run.py` and `eval/run.py` (or create these files), create `data/validate_dataset.py`, and establish the `external/CiteVQA/` submodule structure.
- Update `README.md` to reflect the new directory structure, including instructions for initializing the `external/CiteVQA` submodule and running the pipeline from the root.
