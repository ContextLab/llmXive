---
action_items:
- id: cf7748b9e7d2
  severity: writing
  text: 'Split citevqa_cpu_adaptation.py into a modular package structure:'
- id: 8c442eda77ba
  severity: writing
  text: Create data/validate_dataset.py to handle dataset integrity checks and logging
    (US3).
- id: 29cf5575b7a4
  severity: writing
  text: Create infer/run.py and infer/model_loader.py to handle CPU-only model loading
    and inference (US1).
- id: f5783373c292
  severity: writing
  text: Create eval/run.py and eval/saa_scoring.py to handle metric calculation and
    report generation (US2).
- id: 69eb934d6eb1
  severity: writing
  text: 'Refactor the code to generate the required artifacts: outputs/infer_results.jsonl
    (containing question, answer, bbox) and outputs/evaluation_report.json (containing
    saa_score, attribution_hallucination_rate).'
- id: 87ced55b262b
  severity: writing
  text: Implement the data streaming logic in data/validate_dataset.py to ensure memory
    efficiency (<7 GB RAM) as per FR-006, rather than loading the full dataset into
    memory in a single script.
- id: 970bde331954
  severity: writing
  text: Add type hints and docstrings to all new modules to improve readability and
    maintainability, adhering to the research-stage code quality bar.
artifact_hash: 3bc58d267beba9781004e1504dd10ce4d5392a1219ff46841f44df44f7e74495
artifact_path: projects/PROJ-601-https-arxiv-org-abs-2605-12882/specs/001-https-arxiv-org-abs-2605-12882/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T12:15:54.782238Z'
reviewer_kind: llm
reviewer_name: research_reviewer_code_quality_research
score: 0.0
verdict: minor_revision
---

The current implementation fails the code quality and reproducibility standards required for a research-stage artifact. The project structure is monolithic and deviates significantly from the `plan.md` and `tasks.md` specifications, which explicitly called for a modular pipeline (`infer/`, `eval/`, `data/`) and specific artifact outputs (`outputs/infer_results.jsonl`, `outputs/evaluation_report.json`).

**Critical Defects:**

1.  **Monolithic Implementation**: The file `citevqa_cpu_adaptation.py` (11KB) appears to contain the entire logic for dataset loading, model inference, and evaluation scoring. This violates the modularity requirements in `tasks.md` (e.g., T012, T020, T027) and creates a "God Object" that is difficult to test, debug, or extend. It mixes concerns (data validation, model loading, metric calculation) that should be separated into distinct modules.
2.  **Artifact Mismatch**: The spec and plan require specific output artifacts: `outputs/infer_results.jsonl` and `outputs/evaluation_report.json`. Instead, the execution produced `data/results.csv` and `data/summary.csv`. This indicates the code does not implement the required data contracts (T010, T018) and breaks the reproducibility of the benchmark against the CiteVQA standard.
3.  **Missing Pipeline Structure**: The `plan.md` defines a clear data flow: `validate_dataset.py` -> `infer/run.py` -> `eval/run.py`. The current single-file implementation bypasses this, making it impossible to independently validate the dataset (US3) or swap inference engines (US1) without rewriting the entire script.
4.  **Lack of Testability**: The monolithic structure prevents the implementation of the required contract tests (`tests/contract/`) and integration tests (`tests/integration/`) outlined in `tasks.md`. Without modular functions, unit testing specific components like the SAA calculation or CPU-only loading is not feasible.

**Required Changes**

- Split `citevqa_cpu_adaptation.py` into a modular package structure:
  - Create `data/validate_dataset.py` to handle dataset integrity checks and logging (US3).
  - Create `infer/run.py` and `infer/model_loader.py` to handle CPU-only model loading and inference (US1).
  - Create `eval/run.py` and `eval/saa_scoring.py` to handle metric calculation and report generation (US2).
- Refactor the code to generate the required artifacts: `outputs/infer_results.jsonl` (containing `question`, `answer`, `bbox`) and `outputs/evaluation_report.json` (containing `saa_score`, `attribution_hallucination_rate`).
- Implement the data streaming logic in `data/validate_dataset.py` to ensure memory efficiency (<7 GB RAM) as per FR-006, rather than loading the full dataset into memory in a single script.
- Add type hints and docstrings to all new modules to improve readability and maintainability, adhering to the research-stage code quality bar.
