# Tasks: llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts in `specs/001-virtual-tactile-adaptation/contracts/`
**Revision note**: Consolidated from the prior 60-task list into substantive research tasks. All FR-001–FR-011 and SC-001–SC-006 requirements are preserved. Removed platform-owned work (directory creation, `state/...` hash writes, CI configuration, citation-validation scaffolding) per stage-ownership rules. Object count corrected to **10** per FR-003 (the prior list's 25 conflicted with the spec). T030 documentation was rejected by verification and is retained as an unchecked redo.

<!-- ID Mapping: Task IDs in this file (T001‑T030 plus added T014‑T025) are authoritative. Plan IDs (e.g., T015a) are superseded by the tasks below. -->

## Phase 0: Specification Amendments

- [X] T017 [US1 US2] **Amendment Proposal** – Create `amendment_proposal.md` documenting the addition of a paired‑t‑test analysis (aligned with Constitution Principle VII) and version it. This fulfills the original plan’s Phase 0 task T000.

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [US1 US2 US3] Establish the code layout and fetch the real DragMesh-2 data with fail‑loud semantics in `code/data_loader.py`. <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 -->
  - Implement `load_dragmesh_manifest()` using `datasets.load_dataset` or `hf_hub_download` against the DragMesh‑2 dataset referenced in `plan.md`, writing the trajectory manifest to `data/raw/dragmesh_manifest.jsonl`. On any fetch failure the loader MUST raise (no synthetic/mock fallback).
  - Set global seeds (`numpy`, `random`, `torch` if used) to 42 in `code/seed_config.py` for reproducibility (Constitution Principle I).
  - Enforce CPU‑only: PyBullet `DIRECT` mode, `torch` CPU build; a unit test in `code/tests/test_cpu_only.py` scans `code/` for `torch.cuda` / `device="cuda"` and fails if found (FR-004).
  - Document the runnable fetch command in `specs/001-virtual-tactile-adaptation/quickstart.md`.
  - **Verification**: `python code/data_loader.py` produces a non‑empty `data/raw/dragmesh_manifest.jsonl` on the real source; the CPU‑only test passes.

- [ ] T016 [US1 US2 US3] **Requirements Pinning** – Create a `requirements.txt` at `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/requirements.txt` that pins exact versions of all Python dependencies used in the project (e.g., `pybullet==3.25.0`, `torch==2.2.0+cpu`, `numpy`, `pandas`, `scipy`, `statsmodels`, `psutil`, etc.). This satisfies Constitution Principle I.

- [ ] T002 [US1 US2] Implement the `VirtualTactileEstimator` in `code/estimators/virtual_tactile.py`.
  - Compute $k_{\text{norm}} = \frac{|\Delta \tau_{\text{hand}}|}{\max(|\Delta v_{\text{object}}|,\;\epsilon)\;N}$ each timestep (FR-001), using $\epsilon = 10^{-4}$.
  - Apply a moving‑average filter (window = 5) to the torque derivative before computing the ratio (FR-006); clamp output to $[1\times10^{-4}, 10]$ (FR-007).
  - **Verification**: Unit tests in `code/tests/test_estimator.py` will be executed **after** real simulation data is available (see T022). The estimator must emit a JSON object conforming to the amended `estimator_output.schema.yaml` (epsilon_clamped and is_valid are booleans, not const‑true).

- [ ] T003 [US1] Implement the `AdaptiveRewardScheduler` in `code/policies/adaptive_pica.py`.
  - Map the percentile position of $k_{\text{norm}}$ within the **training‑distribution** (collected by T021) to reward multipliers: > 90th percentile ⇒ increase $r_{\text{detach}}$ by ≥ 20 %; < 10th percentile ⇒ decrease by ≥ 15 % (FR-002, FR‑011).
  - **Verification**: `pytest code/tests/test_scheduler.py` passes.

- [ ] T021 [US1] **Training‑distribution Baseline Collection** – Run a short sweep on objects whose friction coefficients are sampled uniformly from 0.2–0.6 (the training range). Log $k_{\text{norm}}$ values to `data/results/training_baseline.csv`. These statistics will be used by the AdaptiveRewardScheduler to compute percentiles during adaptive runs.

- [ ] T023 [US1 US3] **Environment Setup** – Implement `code/environment/drag_mesh_env.py`:
  - PyBullet `DIRECT`‑mode physics engine for dexterous hand manipulation.
  - Log per‑timestep `torque_hand`, `velocity_object`, and `normal_force` to `data/logs/simulation_run_<run_id>.csv`.
  - **Crucially**, invoke `VirtualTactileEstimator` **online** each timestep to compute `k_norm` and feed it to the reward scheduler (addresses FR‑001 real‑time requirement).

- [ ] T024 [US1] **Novel Object Generator** – Implement `code/environment/articulated_object_gen.py`:
  - Generate **exactly 10** novel articulated objects with friction coefficients **≥ 0.8** or **≤ 0.1** (FR‑010, FR‑003).
  - Write each manifest to `data/generated/novel_objects/<object_id>.json` conforming to `contracts/dataset.schema.yaml`.

- [ ] T025 [US1] **Smoke Pipeline** – `code/main.py --mode smoke` runs a minimal end‑to‑end pass:
  - Uses the environment (T023) and generator (T024) for **2** objects, executes three policies (`static`, `adaptive`, `ablation_random`) for a few episodes each.
  - Writes trial rows to `data/results/sweep.csv` (conforms to `contracts/sweep_output.schema.yaml`).
  - **Verification**: The command completes on CPU and produces real rows.

## Phase 2: Complete the study and validate its evidence

- [ ] T005 [US1] **Full Policy Comparison** – `code/main.py --mode full` evaluates all 10 objects across all three policies, re‑using the same objects and initial conditions for each policy. The adaptive policy now receives live `k_norm` values from the estimator (via T023). **Before starting the full run, truncate or delete `data/results/sweep.csv` to ensure only full‑run trials are present.** Results are streamed to `data/results/sweep.csv` (append mode). Runtime and memory are logged for each trial.

- [ ] T006 [US2] **Correlation‑Validation Experiment** – `code/analysis/correlation_experiment.py`:
  - Run ≥ 30 trials with known ground‑truth friction values spanning 0.0–2.5.
  - Compute $k_{\text{norm}}$ using the online estimator.
  - Perform **partial correlation** controlling for normal force `N`.
  - Write `data/results/correlation_report.json` with `pearson_r`, `n_trials`, and a pass flag (`r ≥ 0.8`).

- [ ] T007 [US1] **Statistical Analyses** – `code/analysis/statistical_test.py`:
  - Fit a GLMM (logit link) on `data/results/sweep.csv` with `policy_type` fixed effect and `object_id` random intercept; output `glmm_summary.json` (p‑value, odds ratio).
  - Perform a paired‑t‑test on per‑object success rates (adaptive vs. static); output `t_test_summary.json`.
  - Conduct a power analysis; if predicted power < 0.8, trigger **spec amendment** task T018 to formally relax FR‑003 (see below).

- [ ] T008 [US1] **Reward‑Threshold Sensitivity** – `code/analysis/sensitivity.py`:
  - Re‑evaluate adaptive policy under alternative percentile thresholds (80/20, 85/15) on the same dataset.
  - Report results to `data/results/sensitivity_report.json` and select the most robust setting.

- [ ] T009 [US3] **Resource & Correctness Checks** – Integration test `code/tests/test_cpu_pipeline.py`:
  - Run the smoke pipeline, asserting wall‑clock time ≤ 6 h and **peak RSS memory ≤ 7 GB** (using `psutil`).
  - Verify no CUDA imports via static code scan.
  - **Verification**: `pytest code/tests/test_cpu_pipeline.py` passes.

- [ ] T010 [US1 US2] **Result Summarization & PASS/FAIL Flag** – `code/analysis/make_figures.py`:
  - Produce success‑rate tables, $k_{\text{norm}}$ vs. friction scatter plot, and sensitivity comparison figures under `figures/`.
  - Write `data/logs/experiment_summary.json` containing:
    - `adaptive_success_rate`, `static_success_rate`, `improvement_pct` (computed as `(adaptive‑static)*100`),
    - `p_value` (GLMM), `t_test_p`, `correlation_r`,
    - `conclusion` set to `"PASS"` **iff** both improvement thresholds (≥ 15 % for high‑friction, ≥ 10 % for low‑friction) from the acceptance scenarios are met **and** `p_value < 0.05` and `correlation_r ≥ 0.8`. This ties the flag to concrete, documented numbers rather than the deferred SC placeholders.

- [ ] T014 [US2] **Estimator Schema Amendment** – Edit `specs/001-virtual-tactile-adaptation/contracts/estimator_output.schema.yaml`:
  - Change `epsilon_clamped` and `is_valid` from `const: true` to `"type": "boolean"` (no constant), allowing `false` where appropriate.

- [ ] T018 [US1] **Spec Amendment for Object‑Count Escalation** – If the power analysis in T007 reports insufficient power, create `spec_amendment_object_count.md` that formally updates FR‑003 to allow up to 20 objects for the study, while preserving the original “exactly 10” as the default. This keeps the change traceable and complies with Constitution VII.

- [ ] T020 [US3] **Sweep Schema Path Alignment** – Edit `specs/001-virtual-tactile-adaptation/contracts/sweep_output.schema.yaml` description to reference `data/results/sweep.csv` (the actual file location).

- [ ] T022 [US2] **Estimator Real‑Trace Validation** – After running T025 (full pipeline), execute `code/tests/test_estimator_real.py` which loads `data/logs/simulation_run_*.csv` and verifies that the estimator outputs conform to the amended schema on real data.

## Phase 3: Reproducible results and paper handoff

- [ ] T011 Write a concise methods/results account in `specs/001-virtual-tactile-adaptation/research.md`, linking every claim to concrete artifacts (`experiment_summary.json`, figures, statistical JSONs).

- [ ] T012 (REDO) Populate the documentation with actual content.
  - Write non‑empty `docs/README.md` and `docs/CHANGELOG.md` (and the project root `README.md`) with Installation, Running the pipeline, Results, and Reproducibility sections, concrete CLI examples, and a list of expected output artifacts.

- [ ] T013 Re‑run the documented workflow end‑to‑end from a clean state and record the exact commands, runtime, and handoff details in `specs/001-virtual-tactile-adaptation/quickstart.md`.

- [ ] T019 **Data‑Model Friction Constraint Alignment** – Amend `specs/001-virtual-tactile-adaptation/data-model.md` to change the friction constraint from “> 0.0” to “≥ 0.0”, matching FR‑010 and `dataset.schema.yaml`.

- [ ] **T015 Coverage Mapping Document** – Create `docs/coverage_mapping.md` that enumerates the correspondence between plan task IDs (e.g., T015a, T020) and the current tasks IDs (T001‑T025). This document resolves the disjoint ID spaces and clarifies that tasks.md supersedes plan IDs for execution.
