# Tasks: llmXive follow‑up: extending “Agents’ Last Exam”

**Input**: Design documents from `/specs/001-llmxive-ale-extension/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data‑model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL – only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by research phase and by user story to enable independent implementation and verification.

---

## Phase 1 – Setup & Quick‑start (already completed)

- [X] T001 Create project directory structure for `code/`, `tests/`, `data/`, `docs/` as defined in `specs/001-llmxive-ale-extension/plan.md`.  
- [X] T002 Initialize Python project with `llama-cpp-python`, `datasets`, `scikit-learn`, `pandas`, `pyyaml`, `pytest`, `statsmodels` in `requirements.txt`.  
- [X] T003 [P] Configure linting (ruff) and formatting tools in `pyproject.toml`.  

---

## Phase 2 – Foundational Infrastructure (blocking prerequisites)

- [X] T004 Implement deterministic seed‑pinning utility in `code/utils/seeds.py` (FR‑008).  
  *Verification:* unit test `tests/unit/test_seeds.py` asserts `seeds.get_seed(task_id)` returns a consistent integer and that the file exists.  

- [X] T004b Create `code/utils/verify_seed_pinning.py` script that scans the codebase for prohibited `random.seed`, `np.random.seed`, etc., and ensures they call `seeds.get_seed(task_id)`.  
  *Verification:* run script in CI; exit code 0 indicates compliance.  

- [X] T005 [P] Implement configuration loader in `code/utils/config.py` (model paths, checkpoint intervals).  
  *Verification:* unit test `tests/unit/test_config_loader.py` loads a sample YAML config and checks expected keys (`model_path`, `checkpoint_interval`).  

- [ ] T006 Create base data structures for ExecutionTrace and FailureLabel in `code/data/generator.py`.  
  *Verification:* unit test `tests/unit/test_data_structures.py` validates instances against `contracts/dataset.schema.yaml`.  

- [ ] T007 Setup logging infrastructure to capture timeouts and memory usage in `code/utils/logging_config.py`.  
  *Verification:* integration test `tests/integration/test_logging.py` runs a dummy process, checks that `logs/run.log` is created and contains a timestamp entry.  

- [X] T008 [P] Verify seed‑pinning compliance across the codebase (`code/utils/verify_seed_pinning.py`).  
  *Verification:* execute the script; CI asserts exit code 0 (no violations).  

- [X] T015a [US1] Define data‑generation logic in `code/data/generator_logic.py`.  
  *Creates deterministic functions that encode the ten prescribed scenarios (5 State Persistence Errors, 5 Reasoning Deficits).*  
  *Verification:* unit test `tests/unit/test_generator_logic.py` checks that the logic returns exactly ten scenarios with correct labels.  

- [~] T015b [US1] Implement data‑generator script `code/data/generator.py` that **imports** `generator_logic.py` and writes the ten scenario traces to **`data/raw/golden_fixture.json`**.
  *CLI entry point:* `python -m code.data.generator --output data/raw/golden_fixture.json`.  
  *Verification (indented):*  
    - The script must exit with status 0.  
    - The output file must exist, be non‑empty, and contain exactly ten JSON objects matching the schema in `contracts/dataset.schema.yaml`.  
    - Generate SHA‑256 checksum saved to `data/processed/golden_fixture_checksum.txt`.  

- [~] T015c [US1] Execute the generator and verify the artifact.  
  *Command:* `python -m code.data.generator --output data/raw/golden_fixture.json`.  
  *Verification (indented):*  
    - Confirm `data/raw/golden_fixture.json` exists.  
    - Parse the file and assert each record’s `ground_truth_label` is one of `["State Persistence Error","Reasoning Deficit","Pass"]`.  
    - Assert the label distribution is **5** State Persistence Errors and **5** Reasoning Deficits.  
    - Compute and record a SHA‑256 checksum in `data/processed/golden_fixture_checksum.txt`.  

- [ ] T015d Update spec.md for FR‑009 (ground‑truth proxy) – already completed.  

- [ ] T008b [Cross‑Cutting] Create `code/utils/verify_seed_pinning.py` to scan the codebase for prohibited `random.seed`, `np.random.seed`, etc., and ensure they call `seeds.get_seed(task_id)`. *(moved before T008 for correct ordering)*  

---

## Phase 3 – User Story 1: Failure‑Mode Classification (P1)

### Parsing & Normalization

- [ ] T011 [US1] Implement Normalization Protocol in `code/classification/heuristics.py`.  
  *Features:* float tolerance 1e‑6, timestamp/ID stripping, canonical hash of object content.  
  *Verification:* unit tests in `tests/unit/test_heuristics.py` must pass.  

- [ ] T010 [US1] Implement ALE log parser in `code/classification/parser.py`.  
  *Consumes* `data/raw/golden_fixture.json`; *produces* `data/processed/parsed_traces.json`.  
  *Depends* on T015c and T011.  
  *Verification:* integration test `tests/integration/test_parser.py` validates correct extraction of `step_id`, `action`, and `environment_state`.  

### Validation & Goal Extraction

- [ ] T013 [US1] Implement State‑Reconstruction validator in `code/classification/state_validator.py`.  
  *Inputs:* parsed traces; *outputs:* `data/processed/reconstruction_report.json` with `accuracy` field.  
  *Gate:* If accuracy < 0.95, exit with code 1.  

- [ ] T012 [US1] Implement deterministic Task‑Goal validator in `code/classification/goal_validator.py` (regex‑based, FR‑007).  
  *Outputs:* `data/processed/static_constraints.json`.  
  *Verification:* unit test `tests/unit/test_goal_validator.py` ensures correct extraction of the five template constraints.  

### LLM‑Based Classification

- [ ] T014 [US1] Implement Local LLM classifier in `code/classification/semantic_classifier.py` using `llama‑cpp‑python` (quantized Q4_K_M, temperature 0, seed‑pinned).  
  *Consumes* parsed traces and static constraints; *produces* `data/processed/classification_raw.json`.  
  *Depends* on T013, T012, and T015c.  
  *Verification:* unit test `tests/unit/test_classification_output.py` validates output against `contracts/classification.schema.yaml`.  

- [ ] T013c [US1] Validate classification accuracy against the golden fixture.  
  *Compares* `classification_raw.json` with ground‑truth labels in `data/raw/golden_fixture.json`.  
  *Outputs* `data/processed/classification_validation.json` containing `accuracy`, `precision`, `recall`, `f1`.  
  *Verification:* test `tests/integration/test_classification_accuracy.py` must assert `accuracy ≥ 0.90`.  

- [ ] T016 [US1] Generate summary report `data/processed/classification_report.json` with counts of each failure type, overall `state_persistence_proportion`, and average confidence scores.  
  *Depends* on T014 and T013c.  
  *Verification:* generate checksum `data/processed/classification_report_checksum.txt` and test its existence.  

---

## Phase 4 – User Story 2: Context Checkpointing Intervention (P2)

- [ ] T019 [US2] Implement Context‑Checkpointing wrapper in `code/intervention/wrapper.py` (FR‑003).  
  *Configurable* `checkpoint_interval` N; injects a deterministic state summary before each step.  
  *Verification:* integration test `tests/integration/test_checkpoint_wrapper.py` ensures summaries are injected at the correct interval.  

- [ ] T020 [US2] Implement summary‑compression heuristic in the same module (deterministic truncation, no LLM fallback) to respect the model’s context window (FR‑004).  
  *Verification:* unit test `tests/unit/test_compression_heuristic.py` checks that given inputs the truncated summary length matches expectations.  

- [ ] T021 [US2] Implement CPU‑only task runner in `code/intervention/runner.py` using `llama‑cpp‑python` with Q4_K_M quantization (FR‑004).  
  *Handles* baseline (`checkpoint_interval=None`) and intervention runs.  
  *Verification:* unit test `tests/unit/test_runner_resource_limits.py` asserts peak memory < 7 GB and runtime < 6 h.  

- [ ] T022 [US2] Add memory‑monitoring and timeout logging to the runner (ensure < 7 GB RAM, < 6 h per job).  
  *Verification:* unit test `tests/unit/test_memory_monitor.py` forces a memory spike and checks that the monitor logs a warning and aborts execution.  

- [ ] T023a [US2] Input validation script `code/utils/validate_inputs.py` – verifies existence and non‑emptiness of `data/raw/golden_fixture.json`.  
  *Verification:* unit test `tests/unit/test_input_validation.py` that fails when the file is missing or empty.  

- [ ] T023 [US2] Execute **baseline** runs (no checkpointing).  
  *Command example:* `python -m code.intervention.runner --input data/raw/golden_fixture.json --seeds 42-51 --reps 10 --checkpoint-interval none`.  
  *Outputs:* `data/processed/baseline_results.json` (list of per‑step results adhering to `experiment.schema.yaml`).  
  *Verification:* unit test `tests/unit/test_baseline_results.py` validates schema and generates checksum `data/processed/baseline_checksum.txt`.  

- [ ] T028 [US2] Run **sensitivity experiments** for N = 1, 3, 5 (merged into a single parametrized task).  
  *Command template:* `python -m code.intervention.runner --input data/raw/golden_fixture.json --seeds 42-51 --reps 10 --checkpoint-interval {N}`.  
  *Produces* three files:  
    - `data/processed/sensitivity_N1.json`  
    - `data/processed/sensitivity_N3.json`  
    - `data/processed/sensitivity_N5.json`.  
  *Verification:* integration test `tests/integration/test_sensitivity_outputs.py` checks all three files exist and conform to `experiment.schema.yaml`.  

- [ ] T023b [US3] Verify strict pairing of baseline and intervention results (uses `verify_pairing` from T004).  
  *Input:* `baseline_results.json` and `sensitivity_N3.json`.  
  *Output:* `data/processed/pairing_verification_report.json` with `status` = `PASS`/`FAIL`.  

---

## Phase 5 – User Story 3: Statistical Significance & Reporting (P3)

- [ ] T026b [Cross‑Cutting] Update `plan.md` to replace “Mixed‑Effects Logistic Regression” with “McNemar’s test” (FR‑005).  
  *Verification:* CI step runs `git diff` ensuring `plan.md` contains the string “McNemar” and no reference to Mixed‑Effects.  

- [ ] T026a [US3] Implement McNemar’s test in `code/analysis/stats.py`.  
  *Inputs:* baseline and N = 3 intervention results (validated by T023b).  
  *Outputs:* `data/processed/mcnemar_result.json` containing `p_value`, `contingency_table`, and computed statistical power (flag if < 0.80).  
  *Verification:* unit test `tests/unit/test_mcnemar_output.py` validates schema and required fields.  

- [ ] T027 [US3] Implement multiple‑comparison correction (Bonferroni/FDR) within `stats.py` if more than one hypothesis is tested.  
  *Verification:* unit test `tests/unit/test_multiple_correction.py` checks that corrected p‑values are written to `data/processed/mcnemar_result.json`.  

- [ ] T028d [US3] Aggregate sensitivity results (from N = 1, 3, 5) into `data/processed/sensitivity_analysis.json` and compute pass‑rate deltas per FR‑006.  
  *Verification:* unit test `tests/unit/test_aggregated_sensitivity.py` validates the aggregated JSON against a custom schema.  

- [ ] T026c [US3] Combine statistical outputs into a single summary `data/processed/statistical_summary.json` (keys: `p_value`, `power`, `sensitivity_delta`, `significance_flag`).  
  *Verification:* unit test `tests/unit/test_statistical_summary.py` ensures all required keys are present and non‑null.  

- [ ] T029 [US3] Generate final report `docs/report.md` that includes:  
   * McNemar’s p‑value and power,  
   * Sensitivity‑analysis deltas,  
   * Memory‑footprint analysis (≤ 7 GB),  
   * State‑reconstruction accuracy,  
   * `state_persistence_proportion` from T016,  
   * All tables/figures directly derived from the JSON artifacts.  
  *Verification:* script `scripts/verify_report.sh` builds the markdown with pandoc and checks for required sections; CI fails if any are missing.  

---

## Phase 6 – Polish & Cross‑Cutting Concerns

- [ ] T031 [P] Documentation updates in `docs/` (including `quickstart.md`).  
  *Verification:* markdown lint CI step ensures no syntax errors.  

- [ ] T032 Refactor `code/classification/heuristics.py` to move magic numbers into the config file.  
  *Verification:* unit test `tests/unit/test_refactor_magic_numbers.py` asserts config‑driven values match previous behavior.  

- [ ] T033 Refactor `code/intervention/wrapper.py` to enforce explicit context‑window limits.  
  *Verification:* integration test `tests/integration/test_wrapper_context_limits.py` confirms the wrapper never exceeds the configured context size.  

- [ ] T034 [P] Additional unit tests for edge cases (incomplete logs, context overflow) in `tests/unit/`.  

- [ ] T035 Run `quickstart.md` validation to ensure the full pipeline executes cleanly in a fresh environment.  
  *Verification:* CI executes the quick‑start script and asserts exit code 0 and presence of a success banner.  

- [ ] T036 Implement checksum‑verification script `code/utils/verify_checksums.py` (reads manifest, compares SHA‑256, exits 0/1).  
  *Verification:* unit test `tests/unit/test_checksum_verifier.py` deliberately mismatches a checksum and expects a non‑zero exit status.  

- [ ] T042 [Cross‑Cutting] Update `plan.md` to replace the mandatory large‑scale model statement with a lightweight‑model requirement (≤ 7 GB RAM) consistent with Constitution VII.  
  *Verification:* CI step runs a diff check confirming the removal of the large‑scale clause and presence of the lightweight clause.  

- [ ] T043 [Cross‑Cutting] Amend `spec.md` to add explicit numeric thresholds for evaluation metrics (e.g., reconstruction accuracy ≥ 0.95, classification accuracy ≥ 0.90, pass‑rate ≥ 0.80).  
  *Verification:* CI step parses `spec.md` and asserts the thresholds are present; fails otherwise.  

---

## Dependencies & Execution Order (summary)

| Phase | Task IDs (order) |
|------|-------------------|
| **Setup** | T001 → T002 → T003 |
| **Foundational** | T004 → T004b → T005 → T006 → T015a → T015b → T015c → T015d → T007 → T008 |
| **US 1** | T011 → T010 → T013 → T012 → T014 → T013c → T016 |
| **US 2** | T019 → T020 → T021 → T022 → T023a → T023 → T028 (N=1/3/5) → T023b |
| **US 3** | T026b → T026a → T027 → T028d → T026c → T029 |
| **Polish** | T031 → T032 → T033 → T034 → T035 → T036 → T042 → T043 |

All tasks that produce files write to project‑owned paths under `code/`, `data/`, or `docs/`. No task writes outside these directories.  

--- 

*End of `tasks.md`.*  