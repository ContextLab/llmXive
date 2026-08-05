---
description: "Task list template for feature implementation"
---

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
- [X] T001a [P] Add a test that asserts the expected directories (`src/`, `tests/`, `data/`, `results/`, `contracts/`) exist after execution (file: `tests/integration/test_project_layout.py`)
- [X] T002 Initialize a Python 3.11 project with `poetry init` and add required dependencies (see plan) – `requirements.txt` generated (file: `requirements.txt`)
- [X] T002a [P] Add contract test for `requirements.txt` presence and content correctness (file: `tests/contract/test_requirements_schema.py`)
- [X] T003 Create linting configuration file `.ruff.toml` (file: `.ruff.toml`) **(completed)**
- [X] T003a [P] Add linting configuration validation test (file: `tests/contract/test_linting_config.py`)
- [X] T004 Add a GitHub Actions CI workflow that installs dependencies, caches the `datasets` download, and sets a timeout of several hours (file: `.github/workflows/ci.yml`) **(completed)**
- [X] T004a [P] Add CI workflow schema validation (file: `tests/contract/test_ci_workflow.py`)
- [X] T005 Create a top‑level `README.md` with quick‑start instructions (file: `README.md`) **(completed)**
- [X] T005a [P] Add README content verification test (file: `tests/contract/test_readme.py`)
- [ ] T050 Run the Reference‑Validator Agent on all citations in the spec and plan to ensure Principle II compliance (file: `scripts/run_reference_validator.sh`)
- [X] T050a [P] Add contract test that verifies the reference‑validator output contains no failures (file: `tests/contract/test_reference_validation.py`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before any user story can be implemented

- [X] T006 Implement a deterministic RNG helper that sets seeds for `numpy`, `torch`, and Python's `random` (file: `src/utils/random_seed.py`)
- [X] T006a [P] Add unit test for RNG seeding correctness (file: `tests/unit/test_random_seed.py`)
- [ ] T007 Implement a logging utility that writes JSON‑line logs with timestamps (file: `src/utils/logging.py`)
- [X] T007a [P] Add contract test for logging output schema (file: `tests/contract/test_logging_schema.py`)
- [X] T007b [P] Add verification test that each log entry includes a valid ISO‑8601 timestamp (file: `tests/contract/test_logging_timestamp.py`)
- [ ] T008 Implement a resource‑monitoring module that records peak VmRSS and wall‑clock time for any script (file: `src/utils/resource_monitor.py`) – used by all experiments (FR‑007)
- [X] T008a [P] Add unit test for resource monitor accuracy (file: `tests/unit/test_resource_monitor.py`)
- [X] T008b [P] Add contract test that the monitor raises an error if RAM > 7 GB or wall‑clock > 360 min for a single run (file: `tests/contract/test_resource_limits.py`)
- [X] T045 [P] Add unit test that verifies each experimental run’s resource‑monitor log respects the 7 GB RAM and 360 min wall‑clock limits (file: `tests/contract/test_per_run_resource_limits.py`)
- [X] T045a [P] Extend the per‑run test to assert failure when limits are exceeded, ensuring per‑run compliance (file: `tests/contract/test_per_run_resource_limits_failure.py`)
- [ ] T009 Implement a dataset‑download script that streams the GSM8K splits via `datasets.load_dataset("gsm8k", split=..., streaming=True)` and caches them under `data/gsm8k/` (file: `src/data/download_gsm8k.py`) – satisfies FR‑001
- [X] T009a [P] Add integration test for dataset download integrity and checksum validation (file: `tests/integration/test_download_gsm8k.py`)
- [X] T009b [P] US1/US2 Implement the data splitting logic to partition GSM8K into training, evaluation, and a **held‑out generalization subset** (stratified by difficulty) and persist these splits to `data/gsm8k/splits/` (file: `src/data/split_gsm8k.py`) – satisfies US‑1, US‑2 acceptance scenarios
- [X] T009c [P] Add unit test for stratified splitting correctness and reproducibility (file: `tests/unit/test_split_gsm8k.py`)
- [ ] T009d [P] Add integration test that running the download script a second time hits the local cache (no network request) (file: `tests/integration/test_gsm8k_cache.py`)
- [X] T041 Compute and record SHA‑256 checksums for all GSM8K files under `data/gsm8k/` (file: `data/checksums.txt`) **(completed)**
- [X] T041a [P] Add contract test that `data/checksums.txt` exists and contains an entry for each downloaded file (file: `tests/contract/test_checksums_generation.py`)
- [X] T044 Extend the dataset‑download script to verify the recorded SHA‑256 checksums before returning data, aborting on mismatch – ensures data‑hygiene enforcement **(completed)**
- [X] T044a [P] Add integration test that checksum validation is executed and raises on corrupted files (file: `tests/integration/test_checksum_validation.py`)

---

## Phase 3: User Story 1 – Subspace Sufficiency Verification (Priority: P1) 🎯

**Goal**: Demonstrate that the OPD‑identified low‑dimensional subspace is sufficient to recover full‑parameter performance.

**Independent Test**: Run a set of seeds of the Frozen‑Subspace OPD protocol and compare against a comparable set of seeds of the Full‑Parameter OPD baseline using a paired TOST equivalence test (δ = 0.02, α = 0.05). Verify power ≥ 0.80; otherwise flag “inconclusive”.

### Implementation for User Story 1

- [ ] T015 Implement Full‑Parameter OPD baseline script that trains TinyLlama for several epochs, logs loss and accuracy per epoch, and writes per‑layer weight deltas for the initial epochs (file: `src/train/opd_baseline.py`) – satisfies FR‑002
- [ ] T015a Implement logic to **persist per‑layer weight deltas** to `data/baseline_deltas/` and compute SHA‑256 checksums for each seed's deltas (file: `src/data/persist_deltas.py`) – ensures data hygiene before SVD consumption
- [ ] T015b Implement **Seed Loop Orchestrator** for the OPD baseline that iterates T015 over **N=30 independent seeds**, manages the RNG state for each seed, and aggregates the output deltas into `data/baseline_deltas/` (file: `src/pipeline/orchestrate_baseline_seeds.py`) – satisfies FR‑006, US‑1 N=30 requirement
- [ ] T015c Add verification that baseline script outputs per‑layer weight deltas (file: `tests/unit/test_opd_baseline_deltas.py`)
- [ ] T016 Implement SVD computation script that reads the per‑layer deltas from the baseline run, performs a layer‑wise randomized SVD, and determines the minimal *k* achieving ≥ 95% cumulative variance (file: `src/data/svd_compute.py`) – satisfies FR‑003, FR‑008
- [ ] T016a Add unit test that cumulative variance ≥ 95% (file: `tests/unit/test_svd_variance.py`)
- [ ] T016b Implement **Seed‑Specific SVD Orchestrator** that iterates T016 over the 30 baseline seeds, generating distinct `mask_opd_{seed}.pt` files (file: `src/pipeline/orchestrate_svd_seeds.py`) – ensures 30 seed‑specific masks for paired tests
- [ ] T017 Extend `src/data/svd_compute.py` to run a sensitivity sweep over variance thresholds covering low, medium, and high levels and output a summary CSV (file: `results/svd_sensitivity.csv`) – FR‑008
- [ ] T017a Add test that summary CSV includes entries for all thresholds (file: `tests/unit/test_svd_sweep.csv`)
- [ ] T018 Implement mask generation that creates a binary mask from the top‑k singular vectors per layer and saves it (`mask_opd_{seed}.pt`) (file: `src/model/mask.py`) – FR‑004
- [ ] T018a Add test that mask files are correctly named per seed (file: `tests/unit/test_mask_naming.py`)
- [ ] T019 Implement Frozen‑Subspace OPD training script that loads the OPD mask, freezes all other parameters, and trains for several epochs (file: `src/train/frozen_subspace_opd.py`) – FR‑001 & FR‑004
- [ ] T019a Add test that training respects mask and logs required fields (file: `tests/unit/test_frozen_opd_mask.py`)
- [ ] T019b Implement **Seed Loop Orchestrator** for Frozen‑Subspace OPD that iterates T019 over **N=30 independent seeds** using the corresponding masks, manages RNG, and aggregates results (file: `src/pipeline/orchestrate_frozen_opd_seeds.py`) – satisfies FR‑006, US‑1 N=30 requirement
- [ ] T020 Implement evaluation script that computes GSM8K held‑out generalization accuracy for any run and writes results to `results/frozen_opd_accuracy.csv` (file: `src/eval/evaluate.py`) – FR‑006
- [ ] T020a Add test for evaluation CSV format (file: `tests/unit/test_evaluate_output.py`)
- [ ] T021 Implement statistical analysis module that (a) performs a pre‑test power analysis (≥ 0.80) using `statsmodels.stats.power.TTestPower`, (b) runs the paired TOST equivalence test on the multiple‑seed accuracy vectors, and (c) records the achieved power and “equivalent”/“inconclusive” flag (file: `src/eval/stats.py`) – FR‑009, FR‑006, FR‑011
- [ ] T021a Add unit tests for power analysis and TOST correctness (file: `tests/unit/test_stats_analysis.py`)
- [ ] T021b Implement **Sensitivity Aggregation** task that aggregates TOST results from the sensitivity sweep (T017) across all 30 seeds and variance thresholds into the final `results/experiment_summary.csv` to satisfy SC‑006 (file: `src/pipeline/aggregate_sensitivity.py`)
- [ ] T022 Implement a script `src/pipeline/run_us1.py` that orchestrates steps T015b‑T021b for all seeds, logs resource usage via `resource_monitor`, and produces a final summary CSV (`results/us1_summary.csv`) – end‑to‑end execution, including aggregation of multiple seeds for TOST
- [ ] T022a Add end‑to‑end test that `run_us1.py` produces a complete summary CSV (file: `tests/integration/test_run_us1.py`)

### Tests for User Story 1 (contract / schema)

- T013 US1 Contract test that `results/experiment_summary.csv` contains the required columns defined in `contracts/experiment.schema.yaml` (file: `tests/contract/test_experiment_schema.py`)
- T013a Enhance test to assert column presence and correct data types.
- T014 US1 Integration test that a single seed run of `src/train/frozen_subspace_opd.py` produces a CSV row with non‑null `accuracy` and `peak_ram_gb` fields (file: `tests/integration/test_frozen_subspace_opd.py`)
- T014a Extend integration test to assert reasonable ranges for `accuracy` and `peak_ram_gb`.

---

## Phase 4: User Story 2 – Comparative Geometric Distinctness (Priority: P2)

**Goal**: Show that the OPD‑derived subspace benefits OPD but not generic SFT, and that a random subspace harms SFT performance.

**Independent Test**: Run multiple seeds of Frozen‑Subspace SFT with the OPD mask and multiple seeds with a random mask; compare mean accuracy drops against the Full‑Parameter OPD baseline using a two‑sample t‑test (α = 0.05) and verify the stipulated drop thresholds.

### Implementation for User Story 2

- [ ] T025 Implement a random‑mask generator that creates a binary mask of the same dimensionality as the OPD mask (seeded for reproducibility) (file: `src/model/mask.py`) – FR‑005
- [ ] T025a Add test that random mask is reproducible given a seed (file: `tests/unit/test_random_mask.py`)
- [ ] T026 Implement Frozen‑Subspace SFT training script that loads a given mask (OPD or random), trains with the standard SFT objective for multiple epochs, and logs loss/accuracy (file: `src/train/frozen_subspace_sft.py`) – FR‑005
- [ ] T026a Add test that mask is correctly applied during SFT (file: `tests/unit/test_sft_mask_application.py`)
- [ ] T026b Implement **Seed Loop Orchestrator** for Frozen‑Subspace SFT that iterates T026 over **N=30 independent seeds** for both OPD and random masks, manages RNG, and aggregates results (file: `src/pipeline/orchestrate_sft_seeds.py`) – satisfies FR‑006, US‑2 N=30 requirement
- [ ] T027 Implement Frozen‑Subspace Random training script that re‑uses `frozen_subspace_sft.py` with the random mask (file: `src/train/frozen_subspace_random.py`) – FR‑005
- [ ] T027a Verify reuse of SFT script for random mask (file: `tests/unit/test_random_reuse.py`)
- [ ] T028 Extend `src/eval/evaluate.py` to compute accuracy for SFT runs and append to `results/frozen_sft_accuracy.csv` (file: same) – FR‑006
- [ ] T028a Add test for correct CSV appending behavior (file: `tests/unit/test_evaluate_sft_append.py`)
- [ ] T029 Extend `src/eval/stats.py` to (a) compute mean accuracy drop vs. baseline, (b) run the independent two‑sample t‑test for OPD‑mask vs. baseline and random‑mask vs. baseline, (c) detect loss plateau (Δloss < 0.001 over two epochs) and record plateau epoch – FR‑010, FR‑006
- [ ] T029a Add unit test for loss‑plateau detection logic (file: `tests/unit/test_plateau_detection.py`)
- [ ] T030 Add a driver script `src/pipeline/run_us2.py` that orchestrates mask generation, SFT runs, random runs, evaluation, and statistical reporting, producing `results/us2_summary.csv` – end‑to‑end
- [ ] T030a Add end‑to‑end test that `run_us2.py` yields expected summary schema (file: `tests/integration/test_run_us2.py`)

### Tests for User Story 2

- T023 US2 Contract test that `results/us2_summary.csv` contains columns `mask_type`, `mean_accuracy_drop`, `t_stat`, `p_value` (file: `tests/contract/test_us2_schema.py`)
- T023a Extend contract test to verify column types.
- T024 US2 Integration test that a single seed run of `src/train/frozen_subspace_sft.py` completes without OOM and writes a row to `results/frozen_sft_accuracy.csv` (file: `tests/integration/test_frozen_subspace_sft.py`)
- T024a Add assertions for OOM absence and CSV entry correctness.

---

## Phase 5: User Story 3 – Resource Feasibility & Reproducibility (Priority: P3)

**Goal**: Verify that the entire experimental pipeline runs on a CPU‑only GitHub Actions runner within the allocated RAM budget and appropriate wall‑clock time limits.

### Implementation for User Story 3

- [X] T033 Extend `src/utils/resource_monitor.py` to write a JSON summary (`ci_metrics.json`) at the end of the full pipeline (peak RAM, total wall‑clock) – FR‑007
- [X] T033a [P] Add contract test that `ci_metrics.json` respects `{ "peak_ram_gb": number, "wall_clock_min": number }` schema (file: `tests/contract/test_ci_metrics_schema.py`)
- [X] T042 [P] Add per‑run RAM assertion in `resource_monitor.py` that raises an error if peak RAM exceeds 7 GB – satisfies SC‑003 and executability‑48242675
- [X] T043 [P] Add per‑run wall‑clock assertion in `resource_monitor.py` that raises an error if runtime exceeds 360 min – satisfies SC‑004 and executability‑93c351c7
- [X] T032 Create a top‑level pipeline script `src/pipeline/run_all.py` that sequentially calls `run_us1.py`, `run_us2.py`, and aggregates all result CSVs into `results/experiment_summary.csv` (file: `src/pipeline/run_all.py`) – FR‑007
- [X] T032b Implement **Unified Summary Generator** within `run_all.py` (or as a separate module) that explicitly merges US1, US2, and US3 CSVs into the single `results/experiment_summary.csv` with full schema compliance (file: `src/pipeline/generate_unified_summary.py`) – satisfies Constitution Principle IV
- [X] T032a [P] Add end‑to‑end test for `run_all.py` aggregation correctness (file: `tests/integration/test_run_all.py`)
- [X] T032b-schema [P] Add contract test that the unified `results/experiment_summary.csv` conforms to `contracts/experiment.schema.yaml` (file: `tests/contract/test_unified_summary_schema.py`)
- [X] T034 Update the GitHub Actions workflow to invoke `python -m src.pipeline.run_all` and to upload `ci_metrics.json` as an artifact (file: `.github/workflows/ci.yml`) – ensures SC‑003 & SC‑004 are exercised
- [X] T034a [P] Add CI workflow schema validation test (file: `tests/contract/test_ci_workflow_schema.py`)
- [X] T031 CI sanity test that the workflow `ci.yml` finishes without timeout and publishes an artifact `ci_metrics.json` containing `peak_ram_gb` and `wall_clock_min` (file: `tests/ci/test_ci_limits.py`)
- [X] T031a Extend CI sanity test to parse `ci_metrics.json` and assert per‑run RAM ≤ 7 GB and wall‑clock ≤ 360 min.

---

## Phase 6: Polish & Cross‑Cutting Concerns

- [ ] T036 Update documentation in `docs/` to describe how to reproduce each user story, including seed selection and mask files (file: `docs/REPRODUCTION.md`)
- [ ] T036a Verify REPRODUCTION.md matches actual scripts and seed usage (file: `tests/contract/test_reproduction_md.py`)
- [ ] T037-ruff Apply `ruff` autofixes across the codebase (file: `src/` modules)
- [ ] T037-type-hints Add type hints to all modules and run `mypy --strict` (files: all `src/` modules)
- [ ] T037-mypy Add CI step that runs `mypy --strict` and fails on any error (file: CI config)
- [ ] T037a [P] Add CI step that runs `ruff` and fails on lint errors (file: CI config)
- [ ] T038 Add additional unit tests for utility functions (`random_seed` and `resource_monitor`) with explicit test files `tests/unit/test_random_seed.py` and `tests/unit/test_resource_monitor_edge.py`
- [ ] T038a Ensure edge‑case coverage for utilities (invalid seeds, missing files) (file: `tests/unit/test_resource_monitor_edge.py`)
- [ ] T039 Run the full test suite with `pytest -q` in CI and enforce a maximal pass rate
- [ ] T039-threshold Enforce that the overall test pass rate is ≥ 100 % (or a defined minimum) and add a contract test verifying this threshold (file: `tests/contract/test_pass_rate_threshold.py`)
- [ ] T040-secret-scan Add secret‑scan test and verify `.gitignore` excludes cache directories (file: `tests/security/test_secret_scan.py`)
- [ ] T040-gitignore Add `.gitignore` entries for caches, model checkpoints, and other large artifacts (file: `.gitignore`)
- [ ] T040-poetry-lock Pin dependency hashes in `poetry.lock` and verify integrity (file: `poetry.lock`)
- [ ] T040a [P] Add contract test that verifies `.gitignore` correctly excludes specified directories (file: `tests/contract/test_gitignore.py`)
- [ ] T051 Refine SC‑002 into a single measurable predicate: compute both the mean drop and the t‑test p‑value; the test passes if (mean < 3 pp && p > 0.05) OR (mean ≥ 3 pp && p < 0.05). Add contract test to enforce this logic (file: `tests/contract/test_sc002_predicate.py`)

---

## Phase Dependencies

### Phase Dependencies
- **Setup (Phase 1)**: No dependencies – can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion – **BLOCKS** all user stories.
- **User Stories (Phases 3‑5)**: All depend on Foundational; within each story, tasks are ordered as listed; tasks marked `[P]` may run in parallel where safe.
- **Polish (Final Phase)**: Depends on completion of all user‑story phases.

### User Story Dependencies
- **US1 (P1)**: Starts after Foundational; independent of US2/US3.
- **US2 (P2)**: Starts after Foundational; reuses masks generated in US1 via explicit dependency on T018.
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
- All tests for a user story marked `[P]` can run in parallel.
- Models within a story marked `[P]` can run in parallel.
- Different user stories can be worked on in parallel by different team members.