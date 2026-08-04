# Tasks: llmXive Geometry Extension

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-on-the-geome/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The spec requests statistical‑test validation and CI‑resource validation. Contract‑style tests are added for schema compliance and for key utility functions.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description (file path)`

- **[P]**: Can run in parallel (different files, no dependencies)  
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)  

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory layout as described in `plan.md` (root, `src/`, `tests/`, `data/`, `results/`, `contracts/`)  
- [ ] T001a [P] Add a test that asserts the expected directories (`src/`, `tests/`, `data/`, `results/`, `contracts/`) exist after execution (file: `tests/integration/test_project_layout.py`)  
- [ ] T002 Initialize a Python 3.11 project with `poetry init` and add required dependencies (see plan) – `requirements.txt` generated (file: `requirements.txt`)  
- [ ] T002a [P] Add a contract test for `requirements.txt` presence and content correctness (file: `tests/contract/test_requirements_schema.py`)  
- [ ] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools (file: `.ruff.toml`, `pyproject.toml`)  
- [ ] T003a [P] Add linting configuration validation test (file: `tests/contract/test_linting_config.py`)  
- [ ] T004 [P] Add a GitHub Actions CI workflow that installs dependencies, caches the `datasets` download, and sets a timeout of several hours (file: `.github/workflows/ci.yml`)  
- [ ] T004a [P] Add CI workflow schema validation (file: `tests/contract/test_ci_workflow.py`)  
- [ ] T005 [P] Create a top‑level `README.md` with quick‑start instructions (file: `README.md`)  
- [ ] T005a [P] Add README content verification test (file: `tests/contract/test_readme.py`)  

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before any user story can be implemented  

- [ ] T006 Implement a deterministic RNG helper that sets seeds for `numpy`, `torch`, and Python's `random` (file: `src/utils/random_seed.py`)  
- [ ] T006a [P] Add unit test for RNG seeding correctness (file: `tests/unit/test_random_seed.py`)  
- [ ] T007 [P] Implement a logging utility that writes JSON‑line logs with timestamps (file: `src/utils/logging.py`)  
- [ ] T007a [P] Add contract test for logging output schema (file: `tests/contract/test_logging_schema.py`)  
- [ ] T007b [P] Add verification test that each log entry includes a valid ISO‑8601 timestamp (file: `tests/contract/test_logging_timestamp.py`)  
- [ ] T008 [P] Implement a resource‑monitoring module that records peak VmRSS and wall‑clock time for any script (file: `src/utils/resource_monitor.py`) – used by all experiments (FR‑007)  
- [ ] T008a [P] Add unit test for resource monitor accuracy (file: `tests/unit/test_resource_monitor.py`)  
- [ ] T008b [P] Add contract test that the monitor raises an error if RAM > 7 GB or wall‑clock > 360 min for a single run (file: `tests/contract/test_resource_limits.py`)  
- [ ] T045 [P] Add unit test that verifies each experimental run’s resource‑monitor log respects the 7 GB RAM and 360 min wall‑clock limits (file: `tests/contract/test_per_run_resource_limits.py`)  
- [ ] T045a [P] Extend the per‑run test to assert failure when limits are exceeded, ensuring per‑run compliance (file: `tests/contract/test_per_run_resource_limits_failure.py`)  
- [ ] T009 [P] Implement a dataset‑download script that streams the GSM8K splits via `datasets.load_dataset("gsm8k", split=..., streaming=True)` and caches them under `data/gsm8k/` (file: `src/data/download_gsm8k.py`) – satisfies FR‑001  
- [ ] T009a [P] Add integration test for dataset download integrity and checksum validation (file: `tests/integration/test_download_gsm8k.py`)  
- [ ] T009b [P] US1/US2 Implement the data splitting logic to partition GSM8K into training, evaluation, and a **held-out generalization subset** (stratified by difficulty) and persist these splits to `data/gsm8k/splits/` (file: `src/data/split_gsm8k.py`) – satisfies US-1, US-2 acceptance scenarios  
- [ ] T009c [P] Add unit test for stratified splitting correctness and reproducibility (file: `tests/unit/test_split_gsm8k.py`)  
- [ ] T041 Compute and record SHA‑256 checksums for all GSM8K files under `data/gsm8k/` and validate them before any downstream use (file: `data/checksums.txt`) – satisfies Constitution Principle III  
- [ ] T041a [P] Add contract test that checksum file matches actual file hashes and that validation fails on mismatch (file: `tests/contract/test_checksums.py`)  
- [ ] T044 [P] Extend the dataset‑download script to verify the recorded SHA‑256 checksums before returning data, aborting on mismatch (file: `src/data/download_gsm8k.py`) – ensures checksum validation is enforced at load time  
- [ ] T044a [P] Add integration test that the checksum validation step is executed and raises on corrupted files (file: `tests/integration/test_checksum_validation.py`)  
- [ ] T010 [P] Implement a model‑loader that loads a TinyLlama variant in 4‑bit GGML format using `llama_cpp_python`. (file: `src/model/load_model.py`) – ensures RAM ≤ 7 GB (FR‑002)  
- [ ] T010a [P] Add test that loading TinyLlama‑1.1B in 4‑bit stays ≤ 7 GB RAM (file: `tests/unit/test_load_model.py`)  
- [ ] T011 [P] Create a binary‑mask utility that can generate, save, and load per‑layer masks (file: `src/model/mask.py`) – core for FR‑004, FR‑005  
- [ ] T011a [P] Extend mask utility tests to verify binary nature and dimensionality (file: `tests/unit/test_mask_binary.py`)  
- [ ] T012 [P] Add a contract test that validates `src/model/mask.py` produces a mask with the correct shape for each layer (file: `tests/contract/test_mask_schema.py`)  
- [ ] T012a [P] Extend mask schema test to assert per‑layer dimensions match model architecture (file: `tests/contract/test_mask_schema_extended.py`)  

**Checkpoint**: All foundational modules are in place; user‑story implementation can now begin.

---

## Phase 3: User Story 1 – Subspace Sufficiency Verification (Priority: P1) 🎯

**Goal**: Demonstrate that the OPD‑identified low‑dimensional subspace is sufficient to recover full‑parameter performance.

**Independent Test**: Run a set of seeds of the Frozen‑Subspace OPD protocol and compare against a comparable set of seeds of the Full‑Parameter OPD baseline. using a paired TOST equivalence test (δ = 0.02, α = 0.05). Verify power ≥ 0.80; otherwise flag “inconclusive”.

### Tests for User Story 1 (contract / schema)

- [ ] T013 [P] US1 Contract test that `results/experiment_summary.csv` contains the required columns defined in `contracts/experiment.schema.yaml` (file: `tests/contract/test_experiment_schema.py`)  
- [ ] T013a [P] Enhance test to assert column presence and correct data types.  
- [ ] T014 [P] US1 Integration test that a single seed run of `src/train/frozen_subspace_opd.py` produces a CSV row with non‑null `accuracy` and `peak_ram_gb` fields (file: `tests/integration/test_frozen_subspace_opd.py`)  
- [ ] T014a [P] Extend integration test to assert reasonable ranges for `accuracy` and `peak_ram_gb`.  

### Implementation for User Story 1

- [ ] T015 [P] US1 Implement Full‑Parameter OPD baseline script that trains TinyLlama for several epochs, logs loss and accuracy per epoch, and writes per‑layer weight deltas for the first 3 epochs (file: `src/train/opd_baseline.py`) – satisfies FR‑002  
- [ ] T015a [P] US1 Implement logic to **persist per-layer weight deltas** to `data/baseline_deltas/` and compute SHA‑256 checksums for each seed's deltas to satisfy Constitution Principle III (file: `src/data/persist_deltas.py`) – ensures data hygiene before SVD consumption  
- [ ] T015b [P] US1 Implement **Seed Loop Orchestrator** for the OPD baseline that iterates T015 over **N=30 independent seeds**, manages the RNG state for each seed, and aggregates the output deltas into `data/baseline_deltas/` (file: `src/pipeline/orchestrate_baseline_seeds.py`) – satisfies FR-006, US-1 N=30 requirement  
- [ ] T015c [P] Add verification that baseline script outputs per‑layer weight deltas (file: `tests/unit/test_opd_baseline_deltas.py`)  
- [ ] T016 [P] US1 Implement SVD computation script that reads the per‑layer deltas from the baseline run, performs a layer‑wise randomized SVD, and determines the minimal *k* achieving ≥ 95% cumulative variance (file: `src/data/svd_compute.py`) – satisfies FR‑003, FR‑008  
- [ ] T016a [P] Add unit test that cumulative variance ≥ 95% (file: `tests/unit/test_svd_variance.py`)  
- [ ] T016b [P] US1 Implement **Seed-Specific SVD Orchestrator** that iterates T016 over the 30 baseline seeds, generating multiple distinct `mask_opd_{seed}.pt` files (file: `src/pipeline/orchestrate_svd_seeds.py`) – ensures 30 seed-specific masks for paired tests  
- [ ] T017 [P] US1 Extend `src/data/svd_compute.py` to run a sensitivity sweep over variance thresholds covering low, medium, and high levels and output a summary CSV (file: `results/svd_sensitivity.csv`) – FR‑008  
- [ ] T017a [P] Add test that summary CSV includes entries for all thresholds (file: `tests/unit/test_svd_sweep.csv`)  
- [ ] T018 [P] US1 Implement mask generation that creates a binary mask from the top‑k singular vectors per layer and saves it (`mask_opd_{seed}.pt`) (file: `src/model/mask.py`) – FR‑004  
- [ ] T018a [P] Add test that mask files are correctly named per seed (file: `tests/unit/test_mask_naming.py`)  
- [ ] T019 [P] US1 Implement Frozen‑Subspace OPD training script that loads the OPD mask, freezes all other parameters, and trains for several epochs (file: `src/train/frozen_subspace_opd.py`) – FR‑001 & FR‑004  
- [ ] T019a [P] Add test that training respects mask and logs required fields (file: `tests/unit/test_frozen_opd_mask.py`)  
- [ ] T019b [P] US1 Implement **Seed Loop Orchestrator** for Frozen‑Subspace OPD that iterates T019 over **N=30 independent seeds** using the corresponding masks, manages RNG, and aggregates results (file: `src/pipeline/orchestrate_frozen_opd_seeds.py`) – satisfies FR-006, US-1 N=30 requirement  
- [ ] T020 [P] US1 Implement evaluation script that computes GSM8K held‑out generalization accuracy for any run and writes results to `results/frozen_opd_accuracy.csv` (file: `src/eval/evaluate.py`) – FR‑006  
- [ ] T020a [P] Add test for evaluation CSV format (file: `tests/unit/test_evaluate_output.py`)  
- [ ] T021 [P] US1 Implement statistical analysis module that (a) performs a pre‑test power analysis (≥ 0.80) using `statsmodels.stats.power.TTestPower`, (b) runs the paired TOST equivalence test on the Multiple‑seed accuracy vectors, and (c) records the achieved power and “equivalent”/“inconclusive” flag (file: `src/eval/stats.py`) – FR‑009, FR‑006, FR‑011  
- [ ] T021a [P] Add unit tests for power analysis and TOST correctness (file: `tests/unit/test_stats_analysis.py`)  
- [ ] T021b [P] US1 Implement **Sensitivity Aggregation** task that aggregates TOST results from the sensitivity sweep (T017) across all 30 seeds and variance thresholds into the final `results/experiment_summary.csv` to satisfy SC-006 (file: `src/pipeline/aggregate_sensitivity.py`)  
- [ ] T022 [P] US1 Add a script `src/pipeline/run_us1.py` that orchestrates steps T015b‑T021b for all seeds, logs resource usage via `resource_monitor`, and produces a final summary CSV (`results/us1_summary.csv`) – end‑to‑end execution, including aggregation of multiple seeds for TOST  
- [ ] T022a [P] Add end‑to‑end test that `run_us1.py` produces a complete summary CSV (file: `tests/integration/test_run_us1.py`)  

**Checkpoint**: After running `run_us1.py`, the summary CSV must contain the TOST result, power, and resource metrics; the contract test T013 should pass.

---

## Phase 4: User Story 2 – Comparative Geometric Distinctness (Priority: P2)

**Goal**: Show that the OPD‑derived subspace benefits OPD but not generic SFT, and that a random subspace harms SFT performance.

**Independent Test**: Run multiple seeds of Frozen‑Subspace SFT with the OPD mask and multiple seeds with a random mask; compare mean accuracy drops against the Full‑Parameter OPD baseline using a two‑sample t‑test (α = 0.05) and verify the stipulated drop thresholds.

### Tests for User Story 2

- [ ] T023 [P] US2 Contract test that `results/us2_summary.csv` contains columns `mask_type`, `mean_accuracy_drop`, `t_stat`, `p_value` (file: `tests/contract/test_us2_schema.py`)  
- [ ] T023a [P] Extend contract test to verify column types.  
- [ ] T024 [P] US2 Integration test that a single seed run of `src/train/frozen_subspace_sft.py` completes without OOM and writes a row to `results/frozen_sft_accuracy.csv` (file: `tests/integration/test_frozen_subspace_sft.py`)  
- [ ] T024a [P] Add assertions for OOM absence and CSV entry correctness.  

### Implementation for User Story 2

- [ ] T025 [P] US2 Implement a random‑mask generator that creates a binary mask of the same dimensionality as the OPD mask (seeded for reproducibility) (file: `src/model/mask.py`) – FR‑005  
- [ ] T025a [P] Add test that random mask is reproducible given a seed (file: `tests/unit/test_random_mask.py`)  
- [ ] T026 [P] US2 Implement Frozen‑Subspace SFT training script that loads a given mask (OPD or random), trains with the standard SFT objective for multiple epochs, and logs loss/accuracy (file: `src/train/frozen_subspace_sft.py`) – FR‑005  
- [ ] T026a [P] Add test that mask is correctly applied during SFT (file: `tests/unit/test_sft_mask_application.py`)  
- [ ] T026b [P] US2 Implement **Seed Loop Orchestrator** for Frozen‑Subspace SFT that iterates T026 over **N=30 independent seeds** for both OPD and random masks, manages RNG, and aggregates results (file: `src/pipeline/orchestrate_sft_seeds.py`) – satisfies FR-006, US-2 N=30 requirement  
- [ ] T027 [P] US2 Implement Frozen‑Subspace Random training script that re‑uses `frozen_subspace_sft.py` with the random mask (file: `src/train/frozen_subspace_random.py`) – FR‑005  
- [ ] T027a [P] Verify reuse of SFT script for random mask (file: `tests/unit/test_random_reuse.py`)  
- [ ] T028 [P] Extend `src/eval/evaluate.py` to compute accuracy for SFT runs and append to `results/frozen_sft_accuracy.csv` (file: same) – FR‑006  
- [ ] T028a [P] Add test for correct CSV appending behavior (file: `tests/unit/test_evaluate_sft_append.py`)  
- [ ] T029 [P] Extend `src/eval/stats.py` to (a) compute mean accuracy drop vs. baseline, (b) run the independent two‑sample t‑test for OPD‑mask vs. baseline and random‑mask vs. baseline, (c) detect loss plateau (Δloss < 0.001 over two epochs) and record epoch of plateau – FR‑010, FR‑006  
- [ ] T029a [P] Add unit test for loss‑plateau detection logic (file: `tests/unit/test_plateau_detection.py`)  
- [ ] T030 [P] US2 Add a driver script `src/pipeline/run_us2.py` that orchestrates mask generation, SFT runs, random runs, evaluation, and statistical reporting, producing `results/us2_summary.csv` – end‑to‑end  
- [ ] T030a [P] Add end‑to‑end test that `run_us2.py` yields expected summary schema (file: `tests/integration/test_run_us2.py`)  

**Checkpoint**: After `run_us2.py`, the summary must show (i) OPD‑mask SFT mean drop < 3 pp with non‑significant t‑test, (ii) random‑mask drop ≥ 3 pp with significant t-test, and loss‑plateau epochs as specified.

---

## Phase 5: User Story 3 – Resource Feasibility & Reproducibility (Priority: P3)

**Goal**: Verify that the entire experimental pipeline runs on a CPU‑only GitHub Actions runner within the 7 GB RAM / 6 h wall‑clock limits.

**Independent Test**: CI job completes with exit code 0, logs show peak RAM ≤ 7 GB and total runtime ≤ 360 min.

### Tests for User Story 3

- [ ] T031 [P] US3 CI sanity test that the workflow `ci.yml` finishes without timeout and publishes an artifact `ci_metrics.json` containing `peak_ram_gb` and `wall_clock_min` (file: `tests/ci/test_ci_limits.py`)  
- [ ] T031a [P] Extend CI sanity test to parse `ci_metrics.json` and assert per‑run RAM ≤ 7 GB and wall‑clock ≤ 360 min.  

### Implementation for User Story 3

- [ ] T033 [P] US3 Extend `src/utils/resource_monitor.py` to write a JSON summary (`ci_metrics.json`) at the end of the full pipeline (peak RAM, total wall‑clock) – FR‑007  
- [ ] T033a [P] Add contract test that `ci_metrics.json` respects `{ "peak_ram_gb": number, "wall_clock_min": number }` schema (file: `tests/contract/test_ci_metrics_schema.py`)  
- [ ] T042 [P] Add per‑run RAM assertion in `resource_monitor.py` that raises an error if peak RAM exceeds 7 GB (integrated with scripts) – satisfies SC‑003 and executability-48242675  
- [ ] T043 [P] Add per‑run wall‑clock assertion in `resource_monitor.py` that raises an error if runtime exceeds 360 min – satisfies SC‑004 and executability-93c351c7  
- [ ] T032 [P] US3 Create a top‑level pipeline script `src/pipeline/run_all.py` that sequentially calls `run_us1.py`, `run_us2.py`, and aggregates all result CSVs into `results/experiment_summary.csv` (file: `src/pipeline/run_all.py`) – FR‑007  
- [ ] T032b [P] US3 Implement **Unified Summary Generator** within `run_all.py` (or as a separate module) that explicitly merges US1, US2, and US3 CSVs into the single `results/experiment_summary.csv` with full schema compliance as per SC-001/SC-002 (file: `src/pipeline/generate_unified_summary.py`) – satisfies Constitution Principle IV  
- [ ] T032a [P] Add end‑to‑end test for `run_all.py` aggregation correctness (file: `tests/integration/test_run_all.py`)  
- [ ] T034 [P] US3 Update the GitHub Actions workflow to invoke `python -m src.pipeline.run_all` and to upload `ci_metrics.json` as an artifact (file: `.github/workflows/ci.yml`) – ensures SC‑003 & SC‑004 are exercised  
- [ ] T034a [P] Add CI workflow schema validation test (file: `tests/contract/test_ci_workflow_schema.py`)  
- [ ] T035 [P] US3 Add a contract test that `ci_metrics.json` respects the schema `{ "peak_ram_gb": number, "wall_clock_min": number }` (file: `tests/contract/test_ci_metrics_schema.py`)  

**Checkpoint**: After a CI run, the artifact `ci_metrics.json` must show `peak_ram_gb ≤ 7.0` and `wall_clock_min ≤ 360`. All contract tests pass.

---

## Phase 6: Polish & Cross‑Cutting Concerns

- [ ] T036 [P] Update documentation in `docs/` to describe how to reproduce each user story, including seed selection and mask files (file: `docs/REPRODUCTION.md`)  
- [ ] T036a [P] Verify REPRODUCTION.md matches actual scripts and seed usage (file: `tests/contract/test_reproduction_md.py`)  
- [ ] T037 [P] Code cleanup: apply `ruff` autofixes, ensure all modules have type hints, and run `mypy --strict` (no errors) (files: all `src/` modules)  
- [ ] T037a [P] Add CI step that runs `mypy --strict` and fails on any error (file: CI config)  
- [ ] T038 [P] Add additional unit tests for utility functions (`random_seed`, `resource_monitor`) (files: `tests/unit/`)  
- [ ] T038a [P] Ensure edge‑case coverage for utilities (invalid seeds, missing files) (file: `tests/unit/test_resource_monitor_edge.py`)  
- [ ] T039 [P] Run the full test suite with `pytest -q` in CI and enforce The pass rate is expected to be maximal. (CI step added)  
- [ ] T039a [P] Enforce CI to fail on any test failure (already covered by CI config)  
- [ ] T040 Security hardening: ensure no secrets are hard‑coded, add `.gitignore` entries for caches, and pin dependency hashes in `poetry.lock` (files: `.gitignore`, `poetry.lock`)  
- [ ] T040a [P] Add secret‑scan test and verify `.gitignore` excludes cache directories (file: `tests/security/test_secret_scan.py`)  

---

## Phase Dependencies

### Phase Dependencies
- **Setup (Phase 1)**: No dependencies – can start immediately.  
- **Foundational (Phase 2)**: Depends on Setup completion – **BLOCKS** all user stories.  
- **User Stories (Phases 3‑5)**: All depend on Foundational; within each story, tasks are ordered as listed; tasks marked `[P]` may run in parallel.  
- **Polish (Phase 6)**: Depends on completion of all user‑story phases.

### User Story Dependencies
- **US1 (P1)**: Starts after Foundational; independent of US2/US3.  
- **US2 (P2)**: Starts after Foundational; may reuse masks generated in US1 but the mask generation script is part of US2 to ensure reproducibility.  
- **US3 (P3)**: Starts after Foundational; orchestrates the full pipeline including US1 and US2 runs.

### Within Each User Story
- Write failing contract tests first (tasks T013‑T014, T023‑T024, T031).  
- Implement core scripts (model loading, dataset download, resource monitor) before training scripts.  
- Training scripts before evaluation scripts.  
- Evaluation before statistical analysis.  
- Driver/orchestration script last.  

### Parallel Opportunities
- All `[P]` tasks within a phase can be executed concurrently on separate cores or by different developers.  
- After Foundational is done, US1, US2, and US3 can be worked on in parallel (different team members).