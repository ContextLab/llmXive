# Tasks: Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based Reinforcement Learning

**Input**: Design documents from `/specs/663-reproduce-cherrl/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project – adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory tree:
  - `projects/PROJ-663-https-arxiv-org-abs-2606-04923/`
  - Sub‑directories: `external/CHERRL/`, `scripts/`, `tests/`, `outputs/logs/`, `outputs/reports/`, `docs/`
  - Add placeholder files: `.gitignore`, `README.md`
- [X] T002 Create `requirements.txt` with exact CPU‑only dependencies:
  ```
  torch==2.3.0+cpu
  transformers==4.45.0
  datasets==2.20.0
  pandas==2.2.2
  scikit-learn==1.5.0
  pytest==8.3.2
  ```
- [X] T003 Create `.pre-commit-config.yaml` containing hooks for `black`, `isort`, and `flake8`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T004 Setup `external/CHERRL` as a git submodule and verify data integrity in `external/CHERRL/data/healthbench_train.parquet` (FR‑001)
- [X] T005 Implement environment sanity check script `scripts/setup_env.py` that loads Qwen1.5‑1.8B in float16 on CPU and loads one sample from the dataset (FR‑002)
- [X] T006 Implement OOM detection in `scripts/utils/memory_monitor.py` that aborts when memory usage exceeds available RAM (~7 GB) as defined by the Abort Policy (Plan)
- [X] T007 Create configuration loader `scripts/config_loader.py` for `bias_config.yaml` and `detection_thresholds.yaml`
- [X] T008 Configure structured JSONL logging in `scripts/logging_utils.py`
- [X] T009 Verify that `external/CHERRL/data/healthbench_train.parquet` exists; if missing, fail fast with a clear error message (no external download) (aligns with Spec Data Availability)

**Checkpoint**: Foundations ready – user story implementation can now begin.

---

## Phase 3: User Story 1 – Environment Setup and Sanity Execution (Priority: P1)

**Goal**: Validate that the environment is functional via a minimal, non‑training script.

### Tests (created before implementation)

- [X] T010 Create unit test `tests/test_data_load.py` that asserts the parquet file can be read (fails until implementation exists)
- [X] T011 Create unit test `tests/test_model_init.py` that asserts the Qwen1.5‑1.8B model loads in float16 on CPU (fails until implementation exists)

### Implementation

- [X] T012 Implement `scripts/setup_env.py` to install dependencies (via `pip install -r requirements.txt`) and run the sanity check (FR‑002)
- [X] T013 Implement `scripts/fetch_data.py` that simply checks for the presence of `healthbench_train.parquet` and raises an error if absent (used by sanity check)
- [X] T014 Add OOM detection usage in `scripts/setup_env.py` (calls `memory_monitor.check()`), aborting on memory pressure per Abort Policy (no hard‑coded byte limit)
- [X] T015 Add graceful error handling in `scripts/setup_env.py` for missing submodule data (clear message, exit code 1)

**Checkpoint**: US‑1 can be validated by running `python scripts/setup_env.py` and confirming exit code 0 and a “Success” log.

---

## Phase 4: User Story 2 – Controlled Bias Injection and Reward Divergence (Priority: P2)

**Goal**: Run short training episodes with injected biases and record reward divergence.

### Tests

- [X] T016 Create contract test `tests/test_bias_config.py` that validates the schema of `bias_config.yaml`
- [X] T017 Create integration test `tests/test_reward_divergence.py` that runs a single‑step bias experiment and checks that a reward increase is logged (fails until implementation)

### Implementation

- [X] T018 Create bias configuration file `external/CHERRL/configs/bias_config.yaml` with keys `self_praise`, `lexical`, `tone`; each defines the trigger phrase(s) and weighting parameters (YAML schema documented)
- [X] T019 Implement `scripts/run_bias_experiment.py`:
  - Loads bias config
  - Executes multiple seeds per bias plus multiple baseline seeds
  - Runs ≤ 500 steps per seed
  - Logs per‑step rewards, generated tokens, and bias‑trigger flags to `outputs/logs/<run_id>.jsonl`
- [X] T020 Ensure per‑step logging uses `logging_utils` to produce structured JSONL (FR‑004)
- [X] T021 (Supplemental – requires spec FR‑007) Implement `scripts/score_quality.py` that loads an unbiased rubric (`unbiased_rubric.json`) and writes a JSONL file `outputs/quality_scores.jsonl` with fields `sample_id` and `quality_score`.
- [X] T022 (Supplemental – requires spec FR‑008) Extend `scripts/analyze_results.py` to compute `divergence = mean(biased_rewards) - mean(ground_truth_scores)` and write `outputs/reports/divergence_metrics.json`.
- [X] T023 Add statistical significance testing (Mann‑Whitney U with Bonferroni correction) in `scripts/analyze_results.py` and output a summary `outputs/reports/stat_test.txt`.

**Checkpoint**: US‑2 is considered successful when the analysis reports a statistically significant reward increase for biased runs and logs the bias‑trigger tokens.

---

## Phase 5: User Story 3 – Hacking Onset Detection and Threshold Sensitivity (Priority: P3)

**Goal**: Run the RHDA detection agent on logs, identify hacking onset, and produce a threshold‑sensitivity report.

### Tests

- [X] T024 Create unit test `tests/test_rhda_agent.py` that validates the wrapper returns a detection step for a mock log.
- [X] T025 Create integration test `tests/test_sensitivity_report.py` that runs the full detection sweep on a small synthetic log and checks that `threshold_grid.csv` is produced with expected columns.

### Implementation

- [X] T026 Implement `scripts/run_detection.py` that wraps the vendored RHDA agent, loads a log file, and outputs the detected onset step.
- [X] T027 Add threshold sweep logic to `run_detection.py` for thresholds `{0.01, 0.05, 0.1}` and write results to `outputs/reports/threshold_grid.csv` (columns: `threshold,tpr,fpr`).
- [X] T028 Ensure `threshold_grid.csv` is generated in the specified location with the exact schema (executability‑66ec1b04 fixed).
- [X] T029 Implement `scripts/validate_onset.py` that compares the detected onset step against the known injection step recorded by `run_bias_experiment.py` and writes a validation summary `outputs/reports/onset_validation.txt`.
- [X] T030 Ensure all detection and validation reports include associational framing language per FR‑006.

**Checkpoint**: US‑3 passes when `threshold_grid.csv` exists with three rows and the onset validation report shows detection within ±5 steps of the ground‑truth injection point.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements affecting multiple user stories.

- [X] T031 Create `docs/reproduction_guide.md` containing:
  1. Environment setup instructions (T001‑T005)
  2. Sanity check usage (US‑1)
  3. Bias injection workflow (US‑2)
  4. Detection and sensitivity analysis steps (US‑3)
  5. Expected outputs and how to interpret them
- [X] T032 Refactor and clean up all scripts in `scripts/` for readability and reuse.
- [X] T033 Validate `quickstart.md` against the actual commands and update if necessary.
- [X] T034 Execute the full pipeline on a 2‑CPU/7 GB runner, record total runtime in `outputs/reports/feasibility_report.txt`; if runtime > 6 h, flag an error for further optimization.

---

## Dependencies & Execution Order Summary

- **Phase 1** → **Phase 2** → **Phase 3** (US‑1) → **Phase 4** (US‑2) → **Phase 5** (US‑3) → **Phase 6**.
- Within each phase, tasks marked `[P]` can run concurrently; all others respect the producer‑consumer ordering described above.
- All tasks are designed to run on a CPU‑only GitHub Actions runner (2 vCPU, 7 GB RAM) without GPU or CUDA dependencies.
