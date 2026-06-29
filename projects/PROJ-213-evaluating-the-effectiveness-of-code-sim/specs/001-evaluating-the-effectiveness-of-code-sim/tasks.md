# Tasks: Evaluating the Effectiveness of Code Simplification on LLM Performance

**Input**: Design documents from `/specs/[001-eval-code-simplification]/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL – include them only if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 0: Research Preparations (Pre‑Foundational)

- [ ] T049 Conduct power/sample‑size analysis per FR‑010 (minimum detectable effect for **≥200** benchmark problems at power ≥ 0.8) and document results in `research.md`. This analysis must be completed before any benchmarking begins.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure with concrete paths and placeholder files:
  ```
  projects/PROJ-213-evaluating-the-effectiveness-of-code-sim/
  ├─ data/
  │   ├─ raw/
  │   ├─ processed/
  │   └─ logs/
  ├─ code/
  │   └─ __init__.py
  ├─ tests/
  │   ├─ unit/
  │   ├─ integration/
  │   └─ contract/
  ├─ requirements.txt
  ├─ README.md
  └─ .gitignore
  ```
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (`datasets`, `transformers`, `llama-cpp-python`, `scipy`, `matplotlib`, `pandas`, `ruff`, `black`).
- [ ] T003 [P] Configure linting and formatting tools (ruff, black) in `code/` and add pre‑commit hooks.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [ ] T004 [US1] Reference the power analysis results from Phase 0 (T049) and ensure the chosen sample size meets the **≥200** requirement.
- [ ] T005 Create data model definitions in `data-model.md` (HumanEvalProblem, SimplifiedProblem, InferenceResult entities).
- [ ] T006 [P] Define JSON schema contracts in `contracts/` for parsed data, results CSVs, and logs.
- [ ] T007 [P] Create `quickstart.md` with setup instructions and CLI usage examples.
- [ ] T008 Create environment configuration files:
  - `.env.example` with `MODEL_PATH`, `TIMEOUT=30`, `DATASET_VERSION`, etc.
  - `config.yaml` with matching schema and defaults.

**Checkpoint**: Foundation ready – user story implementation can now begin.

---

## Phase 3: User Story 1 – Benchmark Comparison (Priority: P1) 🎯 MVP

**Goal**: Run HumanEval benchmark on the code LLM using both original and AST‑simplified snippets, producing two result tables for direct comparison of pass@1 accuracy and inference latency.

**Independent Test**: Execute the full end‑to‑end pipeline on HumanEval (or the combined ≥200‑problem dataset) and verify two CSV files are produced (raw and simplified), each containing `problem_id`, `pass@1`, `token_count`, `inference_time_ms`.

### Implementation

- [ ] T011 [US1] Implement `download.py` in `code/` to fetch HumanEval from HuggingFace Datasets (FR‑001) and store under `data/raw/`.
- [ ] T012 [US1] Implement core AST preprocessing in `simplify.py` (dead‑code removal, boolean reduction) (FR‑002).
- [ ] T013 [US1] Add error handling to `simplify.py` for unparsable code; log failures to `parse_failures.log` (FR‑007).
- [ ] T014 [US1] Add semantic‑change detection to `simplify.py`; run reference test harness and write flagged snippets to `flagged_snippets.csv` (FR‑008).
- [ ] T015 [US1] Implement CPU‑only inference in `inference.py` using 4‑bit StarCoder‑1.3B via `llama.cpp` (FR‑003).
- [ ] T016 [US1] Add per‑sample timeout (30 s) to `inference.py`; on timeout log event and set `inference_time_ms = 30000` with failure flag (FR‑009).
- [ ] T017 [US1] Implement `main.py` CLI to orchestrate benchmark runs for raw and simplified subsets (accepts flags `--mode raw|simplified`).
- [ ] T018 [US1] Verify that `raw_results.csv` and `simplified_results.csv` are generated with matching `problem_id`s (US‑1 acceptance scenario 2).

### Tests (optional, written **after** implementation)

- [ ] T009 [P] [US1] Contract test for HumanEval dataset schema in `tests/contract/test_humaneval_schema.py`.
- [ ] T010 [P] [US1] Integration test for end‑to‑end benchmark pipeline in `tests/integration/test_benchmark_pipeline.py`.

---

## Phase 4: User Story 2 – Metric Logging & Token Accounting (Priority: P2)

**Goal**: Record precise token counts and wall‑clock inference time for every sample in `metrics_raw.csv` and `metrics_simplified.csv`.

**Independent Test**: After a benchmark run, open the generated CSV and confirm each row contains non‑negative integer `token_count` and numeric `inference_time_ms`.

### Implementation

- [ ] T021 Implement metric recording in `inference.py`: capture total token count of the input for each call (FR‑004). *(sequential – must precede T022)*
- [ ] T022 Implement metric recording in `inference.py`: capture wall‑clock inference time in milliseconds for each call (FR‑004).
- [ ] T023 Implement CSV writers to output `metrics_raw.csv` and `metrics_simplified.csv` with columns `problem_id`, `pass@1`, `token_count`, `inference_time_ms`, `status` (FR‑004).
- [ ] T024 Verify each row contains non‑negative integer `token_count` and numeric `inference_time_ms` (US‑2 acceptance scenario 1).

### Tests (optional, written **after** implementation)

- [ ] T019 [P] [US2] Contract test for metrics CSV schema in `tests/contract/test_metrics_schema.py`.
- [ ] T020 [P] [US2] Integration test for metric logging accuracy in `tests/integration/test_metric_logging.py`.

---

## Phase 5: User Story 3 – Statistical Analysis & Visualization (Priority: P3)

**Goal**: Generate reproducible statistical report with paired Wilcoxon signed‑rank tests, Bonferroni correction for two hypotheses, and Matplotlib visualizations comparing raw vs simplified results.

**Independent Test**: Run the analysis script and produce `analysis_report.pdf` containing test statistic, p‑value, effect size, and side‑by‑side bar charts for accuracy and latency.

### Implementation

- [ ] T050 **Gating task** – Verify that median token‑count reduction meets a predefined threshold (e.g., ≥5 % reduction). If the threshold is not met, log a warning and abort accuracy/latency analysis (enforces SC‑003 gating).
- [ ] T027 [US3] Implement paired Wilcoxon signed‑rank test on pass@1 scores (FR‑005, SC‑001).
- [ ] T028 [US3] Implement paired Wilcoxon signed‑rank test on inference times (FR‑005, SC‑002).
- [ ] T029 [US3] Apply Bonferroni correction for **two** hypotheses (accuracy and latency) (FR‑005, SC‑001/002).
- [ ] T030 [US3] Compute effect sizes (Cohen’s d for accuracy, rank‑biserial correlation for latency) (FR‑006).
- [ ] T031 [US3] Compute token‑count ratio (simplified/raw) for all problems (descriptive metric) (SC‑003).
- [ ] T032 [US3] Create Matplotlib visualizations: side‑by‑side bar charts for accuracy and latency comparison (FR‑006).
- [ ] T033 [US3] Generate PDF report `analysis_report.pdf` containing all statistics, corrected p‑values, effect sizes, and figures (FR‑006, SC‑004).
- [ ] T034 [US3] Calculate and report drop rate from parse failures + semantic‑change warnings (SC‑005).
- [ ] T035 Create a test runner script `run_contract_tests.sh` that aggregates and executes all contract tests under `tests/contract/`.

### Tests (optional, written **after** implementation)

- [ ] T025 [P] [US3] Contract test for analysis report schema in `tests/contract/test_analysis_report_schema.py`.
- [ ] T026 [P] [US3] Integration test for statistical analysis correctness in `tests/integration/test_statistical_analysis.py`.

---

## Phase 6: Validation & Testing (Priority: P1)

**Purpose**: Ensure all components work correctly and meet acceptance criteria

- [ ] T036 [P] Write unit tests for `simplify.py` AST transformations in `tests/unit/test_simplify.py`.
- [ ] T037 [P] Write unit tests for `analyze.py` statistical functions in `tests/unit/test_analyze.py`.
- [ ] T038 [P] Write unit tests for `inference.py` timeout handling in `tests/unit/test_inference.py`.
- [ ] T039 Write contract tests for all data schemas in `tests/contract/`:
  - `test_humaneval_schema.py`
  - `test_metrics_schema.py`
  - `test_analysis_report_schema.py`
- [ ] T040 Run end‑to‑end integration test on a HumanEval subset (≤100 problems) to verify pipeline correctness.
- [ ] T041 Create `fr_coverage_matrix.md` documenting mapping of FR‑001 through FR‑010 to implementation tasks (e.g., T011‑T018, T021‑T023, T027‑T034, etc.).
- [ ] T042 [P] Update `README.md` with comprehensive setup, usage, and troubleshooting instructions.
- [ ] T043 [P] Code cleanup: run `ruff --fix` and `black --check`; ensure zero violations before merge.
- [ ] T044 Verify pipeline completes within the 6‑hour CI limit on the full ≥200‑problem dataset (≤7 GB RAM, ≤14 GB disk).
- [ ] T045 Write edge‑case unit tests for inference timeout and crash handling in `tests/unit/test_inference_edge_cases.py`.
- [ ] T046 [P] Verify CPU‑only feasibility: confirm no CUDA/GPU dependencies, memory usage ≤7 GB, disk usage ≤14 GB.
- [ ] T047 Run `quickstart.md` validation to ensure all instructions work end‑to‑end.
- [ ] T048 [P] Add CI workflow configuration for GitHub Actions (Linux, CPU‑only runner).

---

## Phase 7: Cross‑Cutting Concerns

- [ ] T051 Verify StarCoder‑1.3B GGUF model source citation complies with Constitution Principle II; record verification status in `state/verification.md`.
- [ ] T052 Combine HumanEval with MBPP (or another open‑source code benchmark) to achieve **≥200** problems; update data model and documentation accordingly.

---

### Dependencies & Execution Order Summary

- **Phase 0** must finish before any benchmarking (provides power analysis).
- **Phase 1** → **Phase 2** (foundational) must be complete before any user‑story work.
- **User Story 1** (T011‑T018) can run in parallel with **User Story 2** (T021‑T024) once foundational work is done.
- **User Story 3** depends on outputs of US 1 and US 2 and on gating task T050.
- All test tasks are placed **after** the code they validate.
- Parallel‑safe tasks are explicitly marked `[P]`; all others are sequential to avoid merge conflicts.
- Model source verification (T051) and dataset augmentation (T052) ensure constitutional compliance before execution.
