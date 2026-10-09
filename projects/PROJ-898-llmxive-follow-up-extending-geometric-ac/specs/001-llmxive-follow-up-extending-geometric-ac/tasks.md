# Tasks: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-geometric-ac/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL – only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] description with exact artifact paths`

- **[P]**: Can run in parallel (different files, no dependencies)  
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)  
- Include exact file paths in descriptions  

## Phase 1: Setup and first end‑to‑end analysis

**Goal**: Run an executable analysis on valid, small real inputs early.  

- [X] T001a-reqs [P] Create `requirements.txt` with pinned dependencies: `pybullet`, `torch==2.0.0+cpu --index-url https://download.pytorch.org/whl/cpu`, `cvxpy`, `diff-taichi`, `scipy`, `pandas`, `numpy`, `pytest`.  
  - **Verification**: Add a test `tests/integration/test_requirements_exist.py` that asserts the file exists and contains all listed packages.  

- [ ] T001a-gitignore [P] Create `.gitignore` file excluding `data/`, `__pycache__/`, `*.pyc`, and environment files.  
  - **Verification**: `tests/integration/test_gitignore_exists.py` checks file existence and required patterns.  

- [X] T001a-init [P] Create `code/__init__.py` and `tests/__init__.py`.  
  - **Verification**: `tests/integration/test_init_files.py` asserts both files exist and are importable.  

- [X] T001b [P] Create the three top‑level directories `code/`, `data/`, and `tests/`.  
  - **Verification**: `tests/integration/test_directories_exist.py` asserts the directories exist.  

- [X] T001c [P] Add a `.gitkeep` file to each of `data/raw/`, `data/generated/`, and `data/results/` so the directories exist in version control.  
  - **Verification**: `tests/integration/test_gitkeep_files.py` checks the three `.gitkeep` files exist.  

### Phase 1 – Shared infrastructure (blocking prerequisites)

- [ ] T002 (`requirements.txt`: pybullet, torch (cpu, `--index-url https://download.pytorch.org/whl/cpu`), cvxpy, diff-taichi, scipy, pandas, numpy, pytest)  
- [X] T003 [P] Create `ruff.toml` and `.pre-commit-config.yaml` for linting and formatting.  
  - **Verification**: `tests/integration/test_lint_config.py` runs `ruff --quiet` and ensures a successful exit.  

- [ ] T004 Setup data directory structure (`data/raw`, `data/generated`, `data/results`) and `.gitkeep` files.  
- [ ] T005 [P] Implement `code/utils.py` with logging, deterministic seeding (numpy/torch), and SHA‑256 hashing utilities.  
  - **Verification**: `tests/unit/test_utils.py` imports the module and checks each utility function runs without error.  

- [ ] T007a [P] Create `code/config.yaml` defining experiment parameters (e.g., `topology_counts`, `timeout_limits`, `seed`, `trial_count`, `sim_fps`, `max_attempts`, `stiffness_range`, `target_zone`, `baseline_model_url`, `MAX_TASKS`).  
  - **Verification**: `tests/unit/test_config_schema.py` validates the YAML against a schema.  

- [~] T007b [P] Implement `code/config.py` loader that parses `code/config.yaml` into a typed configuration object.  
  - **Verification**: `tests/unit/test_config_loader.py` loads a sample config and checks attribute types.  

- [ ] T005-baseline-fetch [P] Fetch and validate `data/raw/gfm_baseline.pt` according to `code/config.yaml`. Abort with a clear error if the file cannot be obtained. No synthetic weights may be generated.   <!-- FAILED-IN-EXECUTION: code/fetch_baseline.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/fetch_baseline.py exit=1 --> <!-- FAILED: unspecified -->
  - **Depends on** T007a  
  - **Verification**: `tests/integration/test_baseline_fetch.py` asserts the file exists and matches a known checksum.  

- [~] T006-frozen [P] Implement `code/gfm_wrapper.py` (Frozen Inference Mode) to load frozen GFM weights from `data/raw/gfm_weights.pt` (CPU‑only, `eval()` mode) and expose `encode`/`decode` methods. Autograd must be disabled.  
  - **Depends on** T046-fetch-gfm-weights  
  - **Verification**: `tests/unit/test_gfm_frozen.py` loads the wrapper and asserts `requires_grad=False` for all parameters.  

- [~] T006-diff [P] Implement `code/gfm_wrapper.py` (Differentiable Gradient‑Check Mode) that loads the same weights but **enables** autograd on inputs for finite‑difference verification.  
  - **Depends on** T046-fetch-gfm-weights  
  - **Verification**: `tests/unit/test_gfm_diff.py` checks that gradients flow through inputs but not through weights.  

- [~] T008 [P] Add a GitHub Actions workflow `.github/workflows/ci.yml` that runs on a 2‑core x86_64 runner with no GPU, enforces the 6‑hour timeout, and installs `requirements.txt`.  
  - **Verification**: The CI run itself serves as verification; include a badge in README that asserts the workflow passes.  

- [ ] T009a-fetch-stats [US1] [Depends on T007b] Generate or fetch `data/raw/gam_reference_stats.json` (mean/covariance of training latents). Abort if unavailable.   <!-- FAILED-IN-EXECUTION: code/statistical_reference.py exit=1 --> <!-- FAILED-IN-EXECUTION: scripts/compute_reference_stats.py exit=1 -->
  - **Verification**: `tests/integration/test_gam_stats_fetch.py` checks file existence and JSON schema.  

- [ ] T040-contract-create [P] Generate `contracts/trial_log.schema.yaml` defining the single source of truth for trial logs. Validate against a JSON‑Schema validator.  
  - **Verification**: `tests/unit/test_contract_schema.py` runs a validator on the created schema.  

- [ ] T041-data-model-define [P] Author `data-model.md` documenting all data entities (simulation states, latent trajectories, trial logs) and their relationships.  
  - **Verification**: `tests/integration/test_data_model_exists.py` asserts file presence.  

- [ ] T042-quickstart-write [P] Write `quickstart.md` with step‑by‑step instructions to run the full pipeline on a fresh runner.  
  - **Verification**: `tests/integration/test_quickstart_exists.py` checks file existence and that all referenced scripts are reachable.  

- [ ] T043-citation-validate [P] Invoke the Reference‑Validator Agent to check every external citation in `spec.md`, `plan.md`, and `research.md`. Fail the CI if any citation is invalid.  
  - **Verification**: The CI step `run-citation-validator` returns non‑zero on failure.  

## Phase 2: User Story 1 – Synthetic Topology‑Shift Test Set Generation (Priority P1)

**Goal**: Produce ≥ 100 novel manipulation tasks (kinematic chains & deformable objects) using PyBullet, with zero overlap against `training-topology-manifest.json`.  

- [ ] T008‑manifest‑gen [US1] [Depends on T009a-fetch-stats] Generate or load `data/raw/training-topology-manifest.json`. If no real manifest exists, abort (do **not** create a dummy).  
  - **Verification**: `tests/integration/test_manifest_exists.py` ensures the manifest file is present and non‑empty.  

- [ ] T008‑drift‑calib [US1] [Depends on T009a-fetch-stats] Compute reference mean/covariance for latent‑drift detection and store as `data/raw/latent_drift_stats.json`.  
  - **Verification**: `tests/unit/test_drift_calib.py` validates JSON structure.  

- [ ] T008‑latent‑validity [US1] [Depends on T006-frozen, T035-drift-detection] Run a quick sanity check: encode a few novel topologies, verify latent dimensionality, and log any Mahalanobis‑distance outliers to `data/results/latent_validity_log.json`.  
  - **Verification**: `tests/unit/test_latent_validity.py` checks that the log file is created and contains expected fields.  

- [ ] T009‑gen‑impl [US1] [Depends on T007a, T007b] Implement `code/data/generator.py` that builds random kinematic chains (variable hinge count) and soft‑body objects (rope/cloth) in PyBullet and records full simulation states.  
  - **Verification**: `tests/unit/test_generator.py` runs the generator for a single trial and asserts a valid PyBullet world is created.  

- [ ] T009‑gen‑unified [US1] [Depends on T008‑manifest‑gen, T009‑gen‑impl, T034] Execute a loop that generates unique topologies until **≥ 100** distinct entries are collected (or until `max_attempts` is reached). Abort with error if the target count is not met. Output to `data/generated/physics_states.json`.  
  - **Verification**: `tests/integration/test_gen_unified_count.py` checks that at least 100 unique topologies are generated.  

- [ ] T009‑verify‑overlap [US1] [Depends on T008‑manifest‑gen, T009‑gen‑unified, T034] Verify that none of the generated topology hashes appear in `training-topology-manifest.json`. Abort on any overlap. Write verified IDs to `data/generated/unique_topology_ids.json`.  
  - **Verification**: `tests/unit/test_overlap_check.py` asserts no overlap and file creation.  

- [ ] T009‑serialize [US1] [Depends on T009‑verify‑overlap] Serialize the full simulation histories (including per‑timestep vertex positions for deformable objects) to `data/generated/physics_states.json` **and** a CSV of latent trajectories to `data/generated/latent_trajectory.csv`.  
  - **Verification**: `tests/integration/test_serialization.py` checks both files exist and conform to schemas.  

- [ ] T010a [US1] [Depends on T009‑serialize] Extract and store per‑timestep joint angles, vertex data, and object types in `data/generated/physics_states.json` using the schema `{object_type, vertex_data, joint_angles}`.  
  - **Verification**: `tests/unit/test_extraction_schema.py` validates JSON against the schema.  

- [ ] T011 [US1] Implement robust error handling in `code/data/generator.py`: on PyBullet load or simulation failures, retry with exponential back‑off (max 5 attempts), log to `data/results/errors.log`, and skip the trial if unrecoverable. Include a unit test `tests/unit/test_crash_recovery.py`.  
  - **Verification**: `tests/unit/test_error_handling.py` forces a failure and checks retry logic and logging.  

- [ ] T013 [US1] Create `scripts/generate_test_set.py` as a thin CLI wrapper that runs the generator with a configurable random seed.  
  - **Verification**: `tests/integration/test_generate_cli.py` runs the script and asserts successful exit and file creation.  

- [ ] T009b‑gt‑traj [US1] [Depends on T009‑serialize] Run high‑fidelity PyBullet simulations (no decoder) for a subset of generated topologies to produce ground‑truth trajectories. Store in `data/generated/ground_truth_traj.json`.  
  - **Verification**: `tests/unit/test_ground_truth_traj.py` checks file creation and basic content.  

- [ ] T009b‑gt‑decoder [US1] [Depends on T009‑serialize] Produce ground‑truth states for decoder validation and store in `data/generated/ground_truth_decoder.json`.  
  - **Verification**: `tests/unit/test_ground_truth_decoder.py` validates file.  

- [ ] T009‑mock [US1] [P] Generate a minimal mock dataset (5 entries) conforming to `contracts/trial_log.schema.yaml` with valid topology hashes. Store in `data/generated/mock_topology_data.json` for early solver development.  
  - **Verification**: `tests/unit/test_mock_dataset.py` checks schema compliance.  

## Phase 3: User Story 2 – Symbolic Latent Planner Execution (Priority P2)

**Goal**: Run the frozen GFM encoder/decoder together with a differentiable symbolic solver on CPU, enforce geometric constraints, and verify constraint‑satisfaction ≥ 95 % while keeping reconstruction error ≤ 1.5× baseline.  

- [ ] T014‑solver‑impl [US2] [Depends on T006-diff, T009‑mock] Implement `code/models/symbolic_solver.py` using DiffTaichi. The solver optimises latent variables but validates constraints **after decoding** to 3‑D space (non‑penetration, joint limits).  
  - **Verification**: `tests/unit/test_solver_feasibility.py` runs the solver on a known feasible problem and asserts a solution is returned.  

- [ ] T014b‑fd‑verify [US2] [Depends on T014‑solver‑impl, T006-diff] Perform a finite‑difference check: perturb solver inputs by ε = 1e‑6, compute change in constraint‑violation loss, and assert non‑zero gradients for solver inputs while gradients w.r.t. frozen GFM weights remain zero. Output `data/results/finite_diff_verification.json`.  
  - **Verification**: `tests/unit/test_finite_diff.py` checks the JSON for non‑zero gradient entries.  

- [ ] T016 [US2] [Depends on T006-frozen, T014‑solver‑impl] Integrate `code/gfm_wrapper.py` (frozen mode) with `code/models/symbolic_solver.py` to form the full inference pipeline (encode → solve → decode).  
  - **Verification**: `tests/integration/test_full_pipeline.py` runs a single end‑to‑end trial and asserts no exceptions.  

- [ ] T017 [US2] [Depends on T007a, T007b] Implement a per‑step timeout (configurable via `config.yaml`) inside the solver loop; on timeout, record `timeout=true` and `timeout_reason` in `data/results/trial_log.csv`.  
  - **Verification**: `tests/unit/test_timeout_handler.py` forces a timeout and checks log entry.  

- [ ] T018 [US2] [Depends on T014‑solver‑impl, T007a, T007b] Implement an “infeasible” flag: if the solver cannot find a solution within the timeout or constraints are contradictory, record `infeasible=true` in the trial log.  
  - **Verification**: `tests/unit/test_infeasible_flag.py` supplies an unsolvable problem and asserts the flag is set.  

- [ ] T019‑decoder‑control [US2] [Depends on T006-frozen, T009‑serialize] Measure decoder reconstruction error **without** the solver (encode → decode) on a subset of test cases; write results to `data/results/decoder_control_log.json`.  
  - **Verification**: `tests/unit/test_decoder_control.py` checks JSON content.  

- [ ] T019b‑symbolic‑mse [US2] [Depends on T006-frozen, T009b‑gt‑decoder, T020‑trial‑exec] Decode symbolic latent actions, compare to ground‑truth from `ground_truth_decoder.json`, and store MSE in `data/results/symbolic_decoder_mse.json`.  
  - **Verification**: `tests/unit/test_symbolic_mse.py` validates MSE calculation.  

- [ ] T022b‑baseline‑mse [US2] [Depends on T006-frozen, T009b‑gt‑decoder, T022a] Compute baseline decoder MSE analogously and store in `data/results/baseline_decoder_mse.json`.  
  - **Verification**: `tests/unit/test_baseline_mse.py` validates.  

- [ ] T019c [US2] [Depends on T019b‑symbolic‑mse, T022b‑baseline‑mse] Verify that `symbolic_mse ≤ 1.5 × baseline_mse`. Write `data/results/decoder_ratio_check.json` with `ratio` and pass/fail flag.  
  - **Verification**: `tests/unit/test_decoder_ratio.py` asserts the condition.  

- [ ] T019d‑constraint‑sat [US2] [Depends on T020‑trial‑exec] Compute the overall constraint‑satisfaction rate across all symbolic trials; store in `data/results/constraint_satisfaction_log.json`.  
  - **Verification**: `tests/unit/test_constraint_satisfaction.py` checks the rate calculation.  

- [ ] T019e‑combined‑verification [US2] [Depends on T019c, T019d‑constraint‑sat] Combine the two SC‑003 checks (MSE ratio & satisfaction rate) into `data/results/sc003_combined_verification.json`.  
  - **Verification**: `tests/unit/test_combined_verification.py` validates both metrics present.  

- [ ] T023‑feasibility‑pilot [US3] [Depends on T021c] Run a small pilot (e.g., 5 trials) of the symbolic pipeline, measure total runtime, extrapolate to full experiment, and write `ci_time_limit_exceeded` flag to `data/results/feasibility_status.json`.  
  - **Verification**: `tests/unit/test_feasibility_pilot.py` asserts flag is correctly set based on runtime.  

- [ ] T020‑trial‑exec [US2] [Depends on T014‑solver‑impl, T016, T009‑serialize, T017, T018] Execute the full set of symbolic and baseline trials; output per‑trial JSONL records to `data/results/trial_logs.jsonl`.  
  - **Verification**: `tests/integration/test_trial_execution.py` checks that the JSONL file exists, conforms to `contracts/trial_log.schema.yaml`, and contains required fields.  

- [ ] T020b [US2] [SC‑005] Validate per‑step latency on a subset of symbolic trials; ensure `< 300 ms` per step and projected total < 6 h. Write `data/results/latency_validation.json`.  
  - **Verification**: `tests/unit/test_latency_validation.py` asserts latency thresholds.  

- [ ] T021 Add logging for inference latency (ms) and success/failure status for each trial (implemented inside `code/evaluation/runner.py`).  
  - **Verification**: `tests/unit/test_logging.py` confirms log files contain required columns.  

- [ ] T021c [US2] [P] Implement `calculate_success` in `code/evaluation/metrics.py` (collision = 0 AND distance < 5 cm for ≥ 1 s).  
  - **Verification**: `tests/unit/test_success_metric.py` runs on known success/failure cases.  

- [ ] T021b [US2] [SC‑001] Using `calculate_success`, produce `data/results/symbolic_results.csv` with columns `trial_id, approach, success, latency_ms, timeout, infeasible, timestamp`.  
  - **Verification**: `tests/unit/test_symbolic_results_csv.py` validates schema compliance.  

- [ ] T022a [US3] [Depends on T005‑baseline‑fetch, T009‑serialize] Run the baseline GAM (`code/baseline_runner.py`) on the generated test set; write results to `data/results/baseline_results.csv`.  
  - **Verification**: `tests/unit/test_baseline_results_csv.py` checks file and schema.  

- [ ] T023b‑ci‑time‑verify [US3] [Depends on T020‑trial‑exec] Record the final wall‑clock runtime and write `data/results/ci_time_limit_status.json`.  
  - **Verification**: `tests/unit/test_ci_time_status.py` asserts runtime recorded and flag set correctly.  

## Phase 4: User Story 3 – Comparative Statistical Analysis (Priority P3)

**Goal**: Statistically compare symbolic vs. baseline on success rate (McNemar) and latency (Wilcoxon / paired t) and produce a reproducible report.  

- [ ] T023 [P] [US3] [Depends on T021c, T022a] Implement `code/analysis.py` to load `symbolic_results.csv` and `baseline_results.csv`.  
  - **Verification**: `tests/integration/test_analysis_load.py` asserts successful loading.  

- [ ] T024a‑load [US3] [Depends on T023] Add schema verification and data‑loading utilities inside `code/analysis.py`.  
  - **Verification**: `tests/unit/test_schema_verification.py` checks validation passes.  

- [ ] T024a‑detect‑censor [US3] [Depends on T021c, T022a] Scan both result CSVs for `timeout=true` or `infeasible=true`; output `data/results/censoring_status.json` (`symbolic_censored`, `baseline_censored`, `any_censored`).  
  - **Verification**: `tests/unit/test_censor_detection.py` validates JSON.  

- [ ] T024a‑select [US3] [Depends on T024a‑load, T024a‑detect‑censor]  
  * Build two datasets:  
    1. `dataset_success` – all trials (censored trials counted as failures) for McNemar.  
    2. `dataset_latency` – only trials without `timeout=true` for latency testing.  
  * Run Shapiro‑Wilk on latency differences; choose Wilcoxon if p < 0.05, else paired t‑test. Write the chosen test and rationale to `data/results/stat_test_selection.json`.  
  - **Verification**: `tests/unit/test_test_selection.py` asserts correct test choice logic.  

- [ ] T024a‑report [US3] [Depends on T024a‑select] Generate `data/results/analysis_report.md` containing a markdown table: Metric, Symbolic, Baseline, Difference, p‑value, 95 % CI, Effect Size.  
  - **Verification**: `tests/unit/test_report_contents.py` checks for presence of all required fields.  

- [ ] T024a‑validate [US3] [Depends on T024a‑report] Verify that the report includes success‑rate validation (≥ 1 s success window) and that all required p‑values are present.  
  - **Verification**: `tests/unit/test_report_validation.py` asserts these conditions.  

- [ ] T025‑validate‑experiment [US3] [Depends on T019e‑combined‑verification, T019d‑constraint‑sat] Load constraint‑satisfaction rate and combined verification; write overall pass/fail to `data/results/experiment_validation.json`.  
  - **Verification**: `tests/unit/test_experiment_validation.py` checks pass/fail flag.  

## Phase N: Polish & Cross‑Cutting Concerns

- [ ] T029 [P] Update `README.md` with CLI usage instructions, project structure, and quick‑start example.  
  - **Verification**: `tests/integration/test_readme_links.py` ensures no broken links.  

- [ ] T030 Code cleanup and refactoring of all modules under `code/` (PEP‑8 compliance, type hints, docstrings).  
  - **Verification**: `ruff check` passes with zero errors; `mypy` passes.  

- [ ] [X] T032 [P] Add additional unit tests for solver constraints and latent‑drift detection in `tests/unit/`.  
  - **Verification**: `pytest -q` reports >90% coverage.  

- [ ] T033 [P] Run `scripts/validate_quickstart.sh` (or equivalent) to ensure end‑to‑end reproducibility; generate `data/results/quickstart_validation.json` with pass/fail status.  
  - **Verification**: CI step asserts the JSON flag is true.  

## Phase Revision: Addressing Analyze Findings (edge‑case & robustness tasks)

- [ ] T034 [P] **Robust Topology Hashing** – Implement `code/utils/topology_hasher.py` that deterministically hashes kinematic chain specifications and soft‑body mesh parameters (links, joint types, material properties, vertex count). Used by T009‑gen‑unified and T009‑verify‑overlap.  
  - **Verification**: `tests/unit/test_topology_hasher.py` checks deterministic output across runs.  

- [ ] T035 [P] **Mahalanobis‑Distance Drift Detection** – In `code/evaluation/runner.py`, compute Mahalanobis distance between each latent vector and the reference stats (`latent_drift_stats.json`). If distance > threshold, record `drift_flag=true` in `trial_logs.jsonl` and log to `data/results/drift_events.json`.  
  - **Verification**: `tests/unit/test_drift_detection.py` forces a high‑distance vector and checks flag.  

- [ ] T036 [P] **Solver Timeout Handler** – Wrap the DiffTaichi solver call in `code/models/symbolic_solver.py` with a cross‑platform timeout (using `signal.alarm` on Unix or `threading.Timer` elsewhere). On timeout, set `timeout=true` in the trial log and return a `"timeout"` status.  
  - **Verification**: `tests/unit/test_cross_platform_timeout.py` runs on both platforms (mocked) and asserts proper flag.  

- [ ] T037 [P] **Censor‑Aware Statistical Analysis** – Extend `code/analysis.py` to treat `timeout` and `infeasible` flags as failures for McNemar’s test while excluding them from latency distributions, as required by the specification.  
  - **Verification**: `tests/unit/test_censor_logic.py` validates correct inclusion/exclusion.  

- [ ] T038 [P] **Deformable Material Parameterisation** – Extend `code/data/generator.py` to expose soft‑body parameters (Young’s modulus, Poisson’s ratio) and store them in `data/generated/physics_states.json`.  
  - **Verification**: `tests/unit/test_deformable_params.py` checks new fields appear.  

- [ ] T039 [P] **Differentiable Constraint Validation** – Ensure the constraint‑violation loss in `code/models/symbolic_solver.py` is fully differentiable w.r.t. latent variables; add a verification step that calls `torch.autograd.grad` and writes `data/results/gradient_flow_check.json`.  
  - **Verification**: `tests/unit/test_gradient_flow.py` asserts non‑zero gradients.  

- [ ] T040 [P] **Effect‑Size Calculation** – In `code/analysis.py`, compute Cohen’s h for success‑rate differences and Cohen’s d for latency differences; include these values in `analysis_report.md`.  
  - **Verification**: `tests/unit/test_effect_size_in_report.py` checks the markdown includes both metrics.  

- [ ] T041‑verify‑requirements [P] Verify `requirements.txt` contains exactly the pinned dependencies listed in T001a-reqs.  
  - **Verification**: `tests/unit/test_requirements_pinned.py`.  

- [ ] T042‑verify‑gitignore [P] Verify `.gitignore` contains the required patterns.  
  - **Verification**: `tests/unit/test_gitignore_patterns.py`.  

- [ ] T043‑verify‑init [P] Verify `code/__init__.py` and `tests/__init__.py` are importable.  
  - **Verification**: `tests/unit/test_init_importable.py`.  

- [ ] T044‑verify‑directories [P] Verify the existence of `code/`, `data/`, and `tests/`.  
  - **Verification**: `tests/unit/test_top_level_dirs.py`.  

- [ ] T045‑verify‑gitkeep [P] Verify `.gitkeep` files exist in each `data/*/` subdirectory.  
  - **Verification**: `tests/unit/test_gitkeep_presence.py`.  

- [ ] T046‑fetch-gfm-weights [P] Fetch the frozen GFM weights `data/raw/gfm_weights.pt` from the canonical model repository (e.g., a public URL). Abort with error if unavailable.  
  - **Verification**: `tests/integration/test_gfm_weights_fetch.py` checks file existence and checksum.  

- [ ] T047‑verify‑ruff-config [P] Run `ruff` against the repository; ensure no linting errors.  
  - **Verification**: CI step `ruff check .` must exit zero.  

- [ ] T048‑verify‑pre‑commit [P] Execute `pre-commit run --all-files`; ensure all hooks pass.  
  - **Verification**: CI step `pre-commit run --all-files` must exit zero.  

- [ ] T049‑verify‑config‑schema [P] Validate `code/config.yaml` against a predefined schema.  
  - **Verification**: `tests/unit/test_config_schema_validation.py`.  

- [ ] T050‑verify‑gfm‑wrapper‑frozen [P] Load `code/gfm_wrapper.py` in frozen mode and assert all parameters have `requires_grad=False`.  
  - **Verification**: `tests/unit/test_gfm_wrapper_frozen_grad.py`.  

- [ ] T051‑verify‑gfm‑wrapper‑diff [P] Load `code/gfm_wrapper.py` in diff mode and assert inputs are differentiable while weights remain frozen.  
  - **Verification**: `tests/unit/test_gfm_wrapper_diff_grad.py`.  

- [ ] T052‑verify‑solver‑gradient [P] Confirm that gradients flow from the constraint‑violation loss to latent variables but not through the decoder.  
  - **Verification**: `tests/unit/test_solver_gradient_flow.py`.  

- [ ] T053‑verify‑timeout‑behavior [P] Run the solver with a deliberately low timeout and ensure `timeout=true` is recorded.  
  - **Verification**: `tests/unit/test_timeout_behavior.py`.  

- [ ] T054‑verify‑infeasible‑flag [P] Supply an unsolvable constraint set and verify `infeasible=true` appears in trial logs.  
  - **Verification**: `tests/unit/test_infeasible_flag_behavior.py`.  

- [ ] T055‑verify‑latency‑threshold [P] Measure per‑step latency on a sample trial and assert it is below 300 ms.  
  - **Verification**: `tests/unit/test_latency_threshold.py`.  

- [ ] T056‑verify‑trial‑log‑schema [P] Validate that each line in `trial_logs.jsonl` conforms to `contracts/trial_log.schema.yaml`.  
  - **Verification**: `tests/unit/test_trial_log_schema.py`.  

- [ ] T057‑verify‑analysis‑report‑effect‑sizes [P] Ensure `analysis_report.md` includes both Cohen’s h and Cohen’s d values.  
  - **Verification**: `tests/unit/test_report_effect_sizes_present.py`.  