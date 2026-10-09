# Tasks: Evaluating the Impact of Code Generation on Code Review Quality with LLM Assistance  

**Input**: `spec.md`, `plan.md`, and the research idea.  

The tasks below are organized by research phase and map directly to the functional
requirements (FR‑001 … FR‑017) in the specification.  Each task follows the
canonical format `- [ ] T### [P?] [USx?] description – `*file path*`.  
`[P]` marks tasks that can be executed in parallel (different files, no
data‑flow dependency).  `USx` links the task to the corresponding user story.  

---  

## Phase 1 – Project scaffolding & core utilities  

| Goal | Description |
|------|-------------|
| Establish a reproducible workspace and enforce coding standards. |  |

- [X] **T001** Create the required directory layout – `src/`, `src/utils/`, `data/raw/`, `data/derived/`, `data/annotations/`, `results/`, `tests/`, `specs/`, `contracts/`. **Verification:** assert that each directory exists after execution.  
- [X] **T002** Add `requirements.txt` (pinned versions of `datasets`, `transformers`, `scikit‑learn`, `scipy`, `pandas`, `pyyaml`, `pytest`, `numpy`) and a `config/settings.py` that defines hyper‑parameters, path constants, random seeds, and the list `TARGET_REPOS = ["microsoft/vscode", "pytorch/pytorch", "tensorflow/tensorflow"]`. **Verification:** check that both files exist and contain the expected entries.  
- [X] **T003** Add a `pyproject.toml` configuring **ruff** and **black** (including line‑length, exclude patterns) and a GitHub Actions workflow that runs `ruff check` and `black --check`. **Verification:** confirm `pyproject.toml` includes ruff/black sections and `.github/workflows/ci.yml` exists.  
- [ ] **T004** Implement utility modules in `src/utils/`:  
  - `timeout_wrapper.py` – enforces the global 6 h runtime limit, writes warnings to `logs/timeout.log`, and exits gracefully with code 143.  
  - `logger.py` – provides a structured logger (JSON lines) that records timestamps, task names, and runtime statistics. **Verification:** unit tests verify timeout exit code 143 and logger produces valid JSON lines.  
- [ ] **T005** Create the CLI entry point `src/cli/main.py` that wires the pipeline (extraction → detection → inference → analysis → reporting) and uses the timeout and logger utilities. **Verification:** running `python -m src.cli.main --config config/settings.py --run sample` succeeds on a small sample dataset.   <!-- FAILED-IN-EXECUTION: src/cli/main.py exit=1 -->

---  

## Phase 2 – Data extraction & ground‑truth construction  

| Goal | Description |
|------|-------------|
| Pull real PR data, preprocess it, and produce a triangulated ground truth. |  |

- [ ] **T006** Define data‑model dataclasses (`PullRequest`, `BugDetection`, `AlignmentResult`) in `src/extraction/schema.py`, `src/detection/schema.py`, `src/inference/schema.py`; generate matching YAML contracts `contracts/pr_schema.yaml`, `contracts/bug_detection_schema.yaml`, `contracts/alignment_result_schema.yaml`. **Verification:** schema files exist and can be imported without error.  
- [ ] **T007** Implement `src/extraction/fetch_prs.py` that reads `TARGET_REPOS` from `config/settings.py`, fetches up to 500 PRs per repo via the GitHub REST API, and writes the raw payload to `data/raw/prs.json`. Compute SHA‑256 checksums for each PR and store them in `data/raw/checksums.json`. **Verification:** both `prs.json` and `checksums.json` are created and contain entries for the expected number of PRs.   <!-- FAILED-IN-EXECUTION: code/src/extraction/fetch_prs.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/extraction/fetch_prs.py exit=-1 (TIMEOUT) -->
- [ ] **T008** Implement `src/extraction/preprocess_and_ground_truth.py` that:   <!-- FAILED-IN-EXECUTION: src/extraction/preprocess_and_ground_truth.py exit=1 -->
  1. Loads `data/raw/prs.json`.  
  2. Truncates diffs that exceed the LLM context window, logging a warning per PR to `logs/truncation.log` and setting `truncation_flag: true`.  
  3. Extracts human review comments and writes them to `data/annotations/raw_comments.json` conforming to `contracts/bug_detection_schema.yaml` (fields: `reviewer_id`, `comment_body`, `timestamp`, `is_confirmed`, `linked_pr_id`).  
  4. Applies the rubric from FR‑011 to identify confirmed bugs, producing `data/derived/human_confirmations.json`.  
  5. Generates the triangulated ground‑truth file `data/derived/human_baseline.json` (strict triangulation ≥ 2 reviewers or senior maintainer; falls back to “closed issue with bug label” when needed, marking `verification_method`).  
  6. Writes the processed PRs (with possible truncation) to `data/derived/prs_processed.json`.  
  **Verification:** all derived JSON files exist and validate against their respective YAML contracts.  

---  

## Phase 3 – LLM‑assisted bug detection (simulation)  

| Goal | Description |
|------|-------------|
| Detect LLM‑generated code, run the CPU‑tractable model, and store results. |  |

- [ ] **T009a** Implement `src/detection/detect_llm_code.py` that applies heuristics (e.g., “Generated by” headers, similarity to known model outputs) to each processed diff and writes flags to `data/derived/llm_code_flags.json`. **Verification:** unit test confirms that given a diff with a known header the flag is set correctly.  
- [ ] **T009** Implement `src/detection_and_inference.py` that performs the following steps in order:  
  1. **LLM‑code detection** – invoke `src/detection/detect_llm_code.py` and use its output `llm_code_flags.json`.  
  2. **Model loading** – load StarCoder2‑3B with `device_map="auto"` and `low_cpu_mem_usage=True` (ensuring ≤ 7 GB RAM, FR‑015).  
  3. **Memory watchdog** – monitor RAM via `psutil`; if usage exceeds 7 GB, log to `logs/memory_warning.log` and skip the offending PR.  
  4. **Prompt templating** – use `src/inference/prompt_templates.py` (standardized bug‑detection prompt with severity categories).  
  5. **Batch inference** – process PRs, retry up to 2 times on JSON‑formatting failures (1 s delay), enforce ≤ 5 min latency per PR (FR‑013), and write successful detections to `data/derived/llm_detections.json`.  
  6. **Error flagging** – for PRs where inference ultimately fails, add `llm_error_flag: true` in the output and exclude them from downstream metrics.  
  **Verification:** existence and schema‑validation of `llm_code_flags.json`, `llm_detections.json`, and presence of `memory_warning.log` when thresholds are breached.  

---  

## Phase 4 – Alignment, metrics, and statistical testing  

| Goal | Description |
|------|-------------|
| Align LLM and human bugs, compute quantitative metrics, and run statistical tests. |  |

- [ ] **T010** Implement `src/analysis/analysis.py` that:  
  1. Loads `data/derived/human_baseline.json` and `data/derived/llm_detections.json`.  
  2. Matches bugs using **strict Jaccard ≥ 0.5** on line sets (with ±5 line tolerance) **and** cosine‑similarity on description embeddings (default threshold 0.85, configurable).  Writes matches to `data/derived/alignment.json`.  
  3. Computes Precision, Recall, F1, and “LLM‑only recall” (FR‑017) and writes `data/derived/metrics.json`.  
  4. Performs **McNemar’s test** on detection rates and a **Chi‑square test** on severity‑distribution differences (FR‑005), adding p‑values and effect sizes (`odds_ratio`, `cramers_v`) to the same metrics file.  
  **Verification:** `alignment.json` and `metrics.json` contain the required fields and pass schema checks.  

- [ ] **T011** Implement `src/analysis/sensitivity.py` that sweeps the description‑similarity threshold over `{0.80, 0.85, 0.90}`, re‑runs the alignment/metric pipeline for each value, and stores the resulting F1‑scores (and variance) in `data/derived/sensitivity_analysis.json`.  
  **Verification:** JSON includes entries for all three thresholds.  

- [ ] **T016** Add a runtime‑monitoring task that aggregates per‑PR latency and memory usage recorded by `src/utils/logger.py`, computes total pipeline execution time, and writes `data/derived/runtime_report.json` containing total runtime, average latency, and a boolean flag indicating whether the target threshold (e.g., 6 h) was met.  
  **Verification:** `runtime_report.json` exists and the “threshold_met” field is evaluated.  

---  

## Phase 5 – Reporting & reproducibility  

| Goal | Description |
|------|-------------|
| Produce a final, reproducible research report and supporting artefacts. |  |

- [ ] **T012** Implement `src/reporting/generate_report.py` that reads `data/derived/metrics.json`, `data/derived/alignment.json`, `data/derived/sensitivity_analysis.json`, and `data/derived/runtime_report.json` and creates:  
  - `results/final_report.md` – markdown report containing tables of precision/recall/F1, p‑values, effect sizes, a paragraph that **states the impact “correlate with”** (FR‑014), and the exact alignment description: “alignment used strict Jaccard index (Jaccard ≥ 0.5) with line‑shift tolerance (±5 lines) and similarity threshold 0.85”.  
  - `results/metrics.json` – machine‑readable copy of the metrics with content‑hash footers for each `data/derived/*` file (Constitution IV).  
  **Verification:** both files exist, are non‑empty, and contain the expected sections.  

- [ ] **T013** Add a comprehensive test suite:  
  - Unit tests for each module under `tests/unit/` (e.g., `test_fetch_prs.py`, `test_preprocess.py`, `test_alignment.py`).  
  - Integration test `tests/integration/test_end_to_end.py` that runs the full pipeline on a **small, real** sample of 5 PRs (selected from `microsoft/vscode`) and asserts that `results/final_report.md` and `results/metrics.json` are produced and contain non‑empty metric fields.  
  - Contract tests `tests/contract/test_schema_validation.py` that validate every JSON output against the YAML schemas in `contracts/`.  
  **Verification:** `pytest -q` returns exit code 0 and all listed test files are present.  

- [ ] **T014** Write `quickstart.md` (and update `README.md`) with a step‑by‑step command‑line example:  
  ```bash
  python -m src.cli.main --config config/settings.py --run all
  ```  
  The guide must list required environment variables (GitHub token) and show how to reproduce the end‑to‑end run on the small sample. **Verification:** both markdown files contain the exact snippet above.  

---  

## Phase 6 – Verification checklist  

| Check | Expected artifact |
|-------|-------------------|
| Directory layout created | `src/`, `data/`, `results/`, `tests/`, `contracts/` |
| Dependencies installed | `requirements.txt` |
| Linting config present | `pyproject.toml` |
| Timeout & logger utilities | `src/utils/timeout_wrapper.py`, `src/utils/logger.py` |
| CLI orchestrator | `src/cli/main.py` |
| Schemas & contracts | `src/*/schema.py`, `contracts/*.yaml` |
| Raw PR data & checksums | `data/raw/prs.json`, `data/raw/checksums.json` |
| Processed PRs, comments, ground truth | `data/derived/prs_processed.json`, `data/annotations/raw_comments.json`, `data/derived/human_confirmations.json`, `data/derived/human_baseline.json` |
| LLM detection & inference output | `data/derived/llm_code_flags.json`, `data/derived/llm_detections.json` |
| Alignment & metric files | `data/derived/alignment.json`, `data/derived/metrics.json` |
| Sensitivity analysis | `data/derived/sensitivity_analysis.json` |
| Runtime report | `data/derived/runtime_report.json` |
| Final report & metrics copy | `results/final_report.md`, `results/metrics.json` |
| Test suite passing | `pytest -q` returns 0 |
| Quickstart documentation | `quickstart.md`, updated `README.md` |

---  

### Execution order  

1. **Phase 1** (T001‑T005) – sequential (no [P] tags).  
2. **Phase 2** (T006‑T008) – depends on completed Phase 1.  
3. **Phase 3** (T009a, T009) – requires output of Phase 2.  
4. **Phase 4** (T010‑T011, T016) – requires outputs of Phases 2 & 3.  
5. **Phase 5** (T012‑T014) – runs after Phase 4.  

All tasks remain unchecked (`- [ ]`) to indicate they still need implementation. When a task is completed, the corresponding checkbox should be marked `[X]` by the developer.  
