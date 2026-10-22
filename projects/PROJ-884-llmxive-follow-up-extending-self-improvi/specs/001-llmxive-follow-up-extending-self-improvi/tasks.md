# Tasks: Symbolic backward-step substitution in Bidirectional Evolutionary Search

**Input**: `specs/001-symbolic-bes/spec.md`, `plan.md`, `data-model.md`, `contracts/`
**Re-plan note**: Consolidates the prior task list (which contained duplicate IDs T024d-neural-run, T025–T029 and non-substantive directory/venv tasks) into a bounded set of research tasks. Research scripts never write to `state/` or `.github/`; the platform owns project state. No synthetic/mock data fallbacks are permitted anywhere — a failed real fetch or generation step must raise.

## Phase 0: Design and documentation (traceability for plan items)

- [X] T012 [US1] Finalize Dataset Strategy – document the generation methodology, complexity scaling, and provenance metadata in `specs/001-llmxive-follow-up-extending-self-improvi/design_dataset.md`.  
  Observable check: the markdown file exists and includes sections for puzzle types, scaling plan, and seed management.

- [X] T013 [US2] Define Statistical Analysis Plan – specify TOST bounds, alpha level, power analysis, and effect‑size targets in `specs/001-llmxive-follow-up-extending-self-improvi/stat_analysis_plan.md`.  
  Observable check: file exists and contains numeric values for delta, alpha, and required sample size.

- [X] T014 [US3] Select Baseline Architecture – choose the small CPU‑only LLM (e.g., `distilbert-base-uncased`), record the exact HuggingFace commit hash and fallback options in `specs/001-llmxive-follow-up-extending-self-improvi/baseline_architecture.md`.  
  Observable check: file lists model identifier, commit hash, and device settings.

- [X] T015 [US4] Validate Contracts – generate and place the contract schemas `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` (already present) and ensure they are syntactically valid.  
  Observable check: `python -c "import yaml, sys; yaml.safe_load(open('contracts/dataset.schema.yaml'))"` runs without error.

- [ ] T016 [US5] Create Quickstart Documentation – author `specs/001-llmxive-follow-up-extending-self-improvi/quickstart.md` with a reproducible command chain that runs the pilot end‑to‑end experiment and points to the expected output locations.  
  Observable check: quickstart.md exists and the command `python -m code.main --pilot` executes without error on a clean repo.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [US1] Implement the puzzle dataset generator and deterministic verifier in `code/dataset/generator.py` and `code/dataset/verifier.py`, with the formal constraint grammar in `code/dataset/grammar.py`, satisfying FR‑001.  
  - Generator creates 4x4‑Sudoku and grid‑pathfinding instances with all required fields and raises on any generation/grammar failure.  
  - Verifier returns `(is_valid: bool, error_code: str)` per puzzle type, executes in **< 100 ms** per solution, and raises `VerifierError` on internal failures.  
  - Tests in `code/tests/test_verifier.py`, `code/tests/test_generator.py` verify correctness **and** include a pytest‑benchmark test asserting `runtime < 0.1` seconds.  
  - Validate generated instances against `contracts/dataset.schema.yaml`.  
  - Observable check: `pytest code/tests/test_*.py` passes and the benchmark test succeeds.

- [ ] T002 [US2] Implement the symbolic planner and exclusion logging in `code/symbolic/parser.py`, `code/symbolic/planner.py`, and `code/symbolic/exclusion_logger.py`, satisfying FR‑002 and FR‑006.  
  - Parser converts constraint strings to objects; planner produces sub‑goal sequences and emits `CONTRADICTION_DETECTED` / `PARSE_FAILURE` codes.  
  - Exclusion logger writes excluded puzzle IDs and reasons to `data/processed/exclusions.json` (one‑writer per run).  
  - Tests in `code/tests/test_symbolic_planner.py` cover contradictory, unparsable, and well‑formed instances.  
  - Observable check: `pytest code/tests/test_symbolic_planner.py` passes.

- [ ] T003 [US2] Implement the BES evolutionary loop in `code/bes/` (population, forward step, backward step, fitness, termination), satisfying FR‑003.  
  - Forward step loads the small CPU LLM (`distilbert-base-uncased`) with `device='cpu'`; fetch failures raise.  
  - Backward step uses the symbolic planner; on planner errors returns `EXCLUDED` and logs via the exclusion logger.  
  - Fitness calls the deterministic verifier with a timeout; termination logs reason.  
  - Pilot run on N=10 puzzles produces logs under `data/processed/bes_runs/<run_id>/`.  
  - Observable check: `specs/001-llmxive-follow-up-extending-self-improvi/quickstart.md` command runs pilot and creates non‑empty `attempts.jsonl` and `evaluations.jsonl` with real `cost_time`.

## Phase 2: Complete the study and validate its evidence

- [ ] T004 [US1] Generate the full scaled dataset and validate its distribution, satisfying FR‑001 and SC‑005's data basis.  
  - Produce `data/raw/puzzles_N10.json`, `puzzles_N100.json`, `puzzles_N500.json`.  
  - Run `code/dataset/validate_distribution.py` against the schema and write `distribution_report.json` and `distribution_validation.json`.  
  - Observable check: files exist, schema validation passes, and the report contains counts per type and complexity bucket.

- [ ] T005 [US2] Implement and run the neural‑verifier baseline in `code/bes/neural_verifier.py` and `code/bes/neural_baseline_runner.py`, satisfying FR‑004.  
  - Record **wall‑clock time** **and** **energy consumption (Joules)** (estimated as `cpu_time * TDP_WATTS`).  
  - Output `data/processed/neural_baseline_results.json` with success, time, and energy fields matching `contracts/output.schema.yaml`.  
  - Observable check: result file contains real measured values (no placeholders).

- [ ] T006 [US2] Execute the full symbolic‑guided experiment across all complexity scales, satisfying FR‑003/FR‑004.  
  - Run symbolic BES on each puzzle set, aggregate via `code/bes/result_aggregator.py` into `data/processed/bes_results.json` conforming to `contracts/output.schema.yaml`.  
  - Observable check: file validates against the schema.

- [ ] T007 [US3] Implement and execute the statistical analysis in `code/analysis/stats.py` and `code/analysis/cost_calculator.py`, satisfying FR‑004, FR‑005, SC‑001‑SC‑004.  
  - Perform two‑proportion z‑test, TOST equivalence test, and t‑test on wall‑clock time.  
  **Add** explicit GPU‑hours estimation (using a documented conversion factor) and include `gpu_hours_estimate` in `statistical_report.json`.  
  - Unit test `code/tests/test_stats.py::test_z_test_significance` validates the statistical functions.  
  - Observable check: report JSON contains `p_value_z`, `p_value_t`, `significance`, and `gpu_hours_estimate`.

- [ ] T008 [US3] Implement and execute the scalability analysis in `code/analysis/complexity_empirical.py` and `code/analysis/complexity_theory.py`, satisfying SC‑005.  
  - Produce `complexity_report.json` and `sc005_validation.json`.  
  - **New** contracts: `contracts/complexity_report.schema.yaml` and `contracts/sc005_validation.schema.yaml` (created by tasks T017‑T018) define the expected structure; validation script checks conformity.  
  - Observable check: both JSON files exist and pass schema validation.

- [ ] T009 [US3] Generate result tables and figures in `code/analysis/report.py`, writing to `data/results/` and `figures/`.  
  - Tables/figures are programmatically derived from processed JSON files.  
  - Added verification test `code/tests/test_report_links.py` that asserts every table cell and figure data point maps to a source JSON value.  
  - Observable check: test suite passes and the output files are non‑empty.

- [ ] T010 [US3] Write the methods/results account in `specs/001-symbolic-bes/results.md`, linked to actual artifacts.  
  - All numbers cite the originating JSON files.

- [ ] T011 [All] Re‑run the documented workflow end‑to‑end from a clean `data/processed/` and record the paper‑stage handoff in `specs/001-symbolic-bes/handoff.md`.  
  - Verify reproducibility of all result files.

## Phase 3: Reproducible results and paper handoff (already covered by T010‑T011)

## Additional Contract Creation Tasks

- [ ] T017 [US4] Define JSON schema for `complexity_report.json` as `contracts/complexity_report.schema.yaml`.  
  - Schema captures fields: `run_id`, `method`, `complexity_class`, `empirical_R2`, `theoretical_class`, `discrepancy_flag`.

- [ ] T018 [US4] Define JSON schema for `sc005_validation.json` as `contracts/sc005_validation.schema.yaml`.  
  - Schema captures: `passed`, `complexity_class`, `notes`.
