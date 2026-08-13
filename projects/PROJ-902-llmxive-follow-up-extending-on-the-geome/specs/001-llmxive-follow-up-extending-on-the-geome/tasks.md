# Tasks: llmXive Geometry Extension

**Input**: Design documents from `/specs/001-llmxive-geometry-extension/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The spec requests statistical‑test validation and CI‑resource validation. Contract‑style tests are added for schema compliance and for key utility functions.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description (file path)`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

---

## Phase 0: Setup (Project Layout & Docs)

- [ ] T001 Create project directory layout as described in `plan.md` (root, `src/`, `tests/`, `data/`, `results/`, `contracts/`) (file: N/A)
- [X] T001a Add a test that asserts the expected directories (`src/`, `tests/`, `data/`, `results/`, `contracts/`) exist after execution (file: `tests/integration/test_project_layout.py`)
- [X] T002 Initialize a Python 3.11 project with `poetry init` and add required dependencies (see plan) – `requirements.txt` generated (file: `requirements.txt`)
- [X] T002a Add contract test for `requirements.txt` presence and content correctness (file: `tests/contract/test_requirements_schema.py`)
- [ ] T003 Create linting configuration file `.ruff.toml` (file: `.ruff.toml`)
- [X] T003a Add linting configuration validation test (file: `tests/contract/test_linting_config.py`)
- [ ] T004 Add a GitHub Actions CI workflow that installs dependencies, caches the `datasets` download, sets a timeout of several hours, and **explicitly implements matrix-splitting logic** (separate jobs per condition with ≤15 seeds) and failure-handling (archive logs, proceed) as mandated by FR-012 (file: `.github/workflows/ci.yml`)
- [X] T004a Add CI workflow schema validation (file: `tests/contract/test_ci_workflow.py`)
- [ ] T005 Create a top‑level `README.md` with quick‑start instructions (file: `README.md`)
- [X] T005a Add README content verification test (file: `tests/contract/test_readme.py`)
- [X] T036 Create `docs/REPRODUCTION.md` describing how to reproduce each user story (file: `docs/REPRODUCTION.md`)
- [ ] T036a Verify `REPRODUCTION.md` matches actual scripts and seed usage (file: `tests/contract/test_reproduction_md.py`)
- [ ] T037‑data‑model Create `data-model.md` documenting dataset splits, file formats, and checksum usage (file: `data-model.md`)
- [ ] T037‑data‑model‑test Add unit test validating `data-model.md` structure (file: `tests/unit/test_data_model.py`)
- [ ] T038‑contract‑exp Generate contract schemas `contracts/experiment.schema.yaml` and `contracts/experiment_results.schema.yaml` (file: `contracts/experiment.schema.yaml`)
- [ ] T038‑contract‑res Add tests ensuring contracts are syntactically valid (file: `tests/contract/test_contract_schema.py`)

---

## Phase 1: Shared Infrastructure (Foundational)

- [X] T006 Implement a deterministic RNG helper that sets seeds for `numpy`, `torch`, and Python's `random` (file: `src/utils/random_seed.py`)
- [X] T006a Add unit test for RNG seeding correctness (file: `tests/unit/test_random_seed.py`)
- [X] T007 Implement a logging utility that writes JSON‑line logs with timestamps, records peak RAM and wall‑clock time (file: `src/utils/logging.py`)
- [X] T007a Add contract test for logging output schema (file: `tests/contract/test_logging_schema.py`)
- [X] T007b Add verification test that each log entry includes a valid ISO‑8601 timestamp (file: `tests/contract/test_logging_timestamp.py`)
- [X] T008 Implement a resource‑monitoring module that records peak VmRSS and wall‑clock time for any script (file: `src/utils/resource_monitor.py`)
- [X] T008a Add unit test for resource monitor accuracy (file: `tests/unit/test_resource_monitor.py`)
- [X] T008b Add contract test that the monitor raises an error if RAM > 7 GB or wall‑clock > 360 min for a single run (file: `tests/contract/test_resource_limits.py`)
- [X] T009 Implement dataset‑download script `src/data/download_gsm8k.py` that streams GSM8K splits via `datasets.load_dataset(..., streaming=True)` and caches them under `data/gsm8k/` (file: `src/data/download_gsm8k.py`)
- [X] T009a Add integration test for dataset download integrity and checksum validation (file: `tests/integration/test_download_gsm8k.py`)
- [X] T009b Implement data splitting logic `src/data/split_gsm8k.py` to partition GSM8K into training, evaluation, and held‑out generalization subsets (stratified by difficulty) (file: `src/data/split_gsm8k.py`)
- [X] T009c Add unit test for stratified splitting correctness and reproducibility (file: `tests/unit/test_split_gsm8k.py`)
- [X] T009d Add integration test that running the download script a second time hits the local cache (file: `tests/integration/test_gsm8k_cache.py`)
- [ ] T041 Compute and record SHA‑256 checksums for **the final split files** generated by T009b under `data/gsm8k/` (file: `data/checksums.txt`)
- [X] T041a Add contract test that `data/checksums.txt` exists and contains an entry for each downloaded file (file: `tests/contract/test_checksums_generation.py`)
- [X] T044 Extend the dataset‑download script to verify the recorded SHA‑256 checksums before returning data, aborting on mismatch (file: `src/data/download_gsm8k.py`)
- [X] T044a Add integration test that checksum validation is executed and raises on corrupted files (file: `tests/integration/test_checksum_validation.py`)
- [X] T064 Create configuration module `src/config.py` defining `MASK_DERIVATION_SEEDS = list(range())`, `EVAL_SEEDS = list(range(START_SEED, START_SEED + N_SEEDS))

The specific value to remove/generalize: 'START_SEED'

Rewritten passage:`, and global hyper‑parameters (learning rate, batch size, epochs, etc.) (file: `src/config.py`)
- [X] T064a Add unit test that verifies the seed lists contain the correct number of seeds and are disjoint (file: `tests/unit/test_config_seeds.py`)
- [ ] T064b Add contract test that `src/config.py` defines required hyper‑parameter keys and that values fall within expected ranges (file: `tests/contract/test_config_hyperparams.py`)
- [X] T064c Add unit test that checks hyper‑parameter values are reasonable (e.g., 0 < learning_rate ≤ 1, batch_size > 0, epochs > 0) (file: `tests/unit/test_config_hyperparams_values.py`)
- [X] T070 Implement model loading for **TinyLlamaM** with 8‑bit CPU quantization using `bitsandbytes` (validated to fit available RAM resources) (file: `src/models/tinyllama.py`)
- [X] T070a Add unit test that the quantized model loads without CUDA errors and reports parameter count within RAM budget (file: `tests/unit/test_tinyllama_quantization.py`)
- [ ] T071 Implement mask utilities in `src/model/mask.py` exposing `load_mask(seed) -> torch.Tensor` and `apply_mask(model, mask)` (file: `src/model/mask.py`)
- [ ] T071a Add contract test that mask tensors contain only 0/1 values and have correct shape per layer (file: `tests/contract/test_mask_schema.py`)

---

## Phase 1.5: Baseline & SVD (Data Flow: Baseline -> SVD -> Mask)

- [ ] T015 Implement Full‑Parameter OPD baseline script that trains TinyLlama for **exactly 3 epochs**, logs loss and accuracy, and writes per‑layer weight deltas (file: `src/train/opd_baseline.py`)
- [X] T015a Implement logic to persist per‑layer weight deltas to `data/baseline_deltas/` and compute SHA‑256 checksums (file: `src/data/persist_deltas.py`)
- [X] T015b Implement Seed Loop Orchestrator for the OPD baseline over `EVAL_SEEDS` (file: `src/pipeline/orchestrate_baseline_seeds.py`)
- [X] T015c Add verification that baseline script outputs per‑layer weight deltas (file: `tests/unit/test_opd_baseline_deltas.py`)
- [ ] T016 Implement SVD computation script `src/data/svd_compute.py` that reads per‑layer deltas from the initial epochs, performs layer‑wise randomized SVD, and determines minimal *k* achieving ≥ 95 % cumulative variance (file: `src/data/svd_compute.py`)
- [ ] T016a Add unit test that cumulative variance ≥ 95 % (file: `tests/unit/test_svd_variance.py`)
- [ ] T016b Implement SVD orchestrator `src/pipeline/orchestrate_svd_seeds.py` iterating over mask‑derivation seeds to generate `mask_opd_{seed}.pt` (file: `src/pipeline/orchestrate_svd_seeds.py`)
- [ ] T016c **Implement aggregation logic** that combines multiple independent mask-derivation seeds into a **single binary mask** (e.g., via voting or averaging) as required by FR-006 and FR-020 (file: `src/model/mask.py`)
- [ ] T016d Add test that each generated mask file matches expected dimensionality (file: `tests/unit/test_mask_dimensionality.py`)
- [ ] T017 Extend `src/data/svd_compute.py` to run a sensitivity sweep over variance thresholds {90 %, 95 %, 99 %} and output `results/svd_sensitivity.csv` (file: `src/data/svd_compute.py`)
- [ ] T017a Add test that summary CSV includes entries for all thresholds (file: `tests/unit/test_svd_sweep.csv`)
- [ ] T018 Implement mask generation that creates a binary mask from top‑k singular vectors per layer and saves it (`mask_opd_{seed}.pt`) (file: `src/model/mask.py`)
- [ ] T018a Add test that mask files are correctly named per seed (file: `tests/unit/test_mask_naming.py`)

---

## Phase 2: User Story 1 – Subspace Sufficiency Verification (Priority: P1) 🎯

- [ ] T019 Implement Frozen‑Subspace OPD training script that loads the OPD mask, freezes other parameters, and trains (file: `src/train/frozen_subspace_opd.py`)
- [ ] T019a Add test that training respects mask and logs required fields (file: `tests/unit/test_frozen_opd_mask.py`)
- [ ] T019b Implement Seed Loop Orchestrator for Frozen‑Subspace OPD over `EVAL_SEEDS` (file: `src/pipeline/orchestrate_frozen_opd_seeds.py`)
- [ ] T020 Implement evaluation script computing GSM8K held‑out accuracy (file: `src/eval/evaluate.py`)
- [ ] T020a Add test for evaluation CSV format (file: `tests/unit/test_evaluate_output.py`)
- [ ] T021 Implement statistical analysis module performing pre‑test power analysis and paired TOST equivalence test, recording power and decision (file: `src/eval/stats.py`)
- [ ] T021a Add unit tests for power analysis and TOST correctness (file: `tests/unit/test_stats_analysis.py`)
- [ ] T021b Implement sensitivity aggregation across variance thresholds into `results/experiment_summary.csv` (file: `src/pipeline/aggregate_sensitivity.py`)
- [ ] T022 Implement orchestration script `src/pipeline/run_us1.py` that runs T015b‑T021b, logs resources, and produces `results/us1_summary.csv` (file: `src/pipeline/run_us1.py`)
- [ ] T022a Add end‑to‑end test that `run_us1.py` produces a complete summary CSV (file: `tests/integration/test_run_us1.py`)
- [ ] T013 US1 Contract test that `results/experiment_summary.csv` contains required columns per `contracts/experiment.schema.yaml` (file: `tests/contract/test_experiment_schema.py`)
- [ ] T013a Enhance test to assert column presence and correct data types.
- [ ] T014 US1 Integration test that a single seed run of `src/train/frozen_subspace_opd.py` produces a CSV row with non‑null `accuracy` and `peak_ram_gb` (file: `tests/integration/test_frozen_subspace_opd.py`)
- [ ] T014a Extend integration test to assert reasonable ranges for `accuracy` and `peak_ram_gb`.

---

## Phase 3: User Story 2 – Comparative Geometric Distinctness (Priority: P2)

- [ ] T025 Implement a random‑mask generator that creates a binary mask of the same dimensionality as the OPD mask (seeded) (file: `src/model/mask.py`)
- [ ] T025a Add test that random mask is reproducible given a seed (file: `tests/unit/test_random_mask.py`)
- [ ] T025b Add test that random mask dimensionality matches that of the OPD mask (file: `tests/unit/test_random_mask_dim.py`)
- [ ] T026 Implement Frozen‑Subspace SFT training script that loads a given mask (OPD or random) and trains with standard SFT objective (file: `src/train/frozen_subspace_sft.py`)
- [ ] T026a Add test that mask is correctly applied during SFT (file: `tests/unit/test_sft_mask_application.py`)
- [ ] T026b Implement Seed Loop Orchestrator for Frozen‑Subspace SFT over `EVAL_SEEDS` for both OPD and random masks (file: `src/pipeline/orchestrate_sft_seeds.py`)
- [ ] T027 Implement Frozen‑Subspace Random training script re‑using `frozen_subspace_sft.py` with the random mask (file: `src/train/frozen_subspace_random.py`)
- [ ] T027a Verify reuse of SFT script for random mask (file: `tests/unit/test_random_reuse.py`)
- [ ] T028 Extend `src/eval/evaluate.py` to compute accuracy for SFT runs and append to `results/frozen_sft_accuracy.csv` (file: same)
- [ ] T028a Add test for correct CSV appending behavior (file: `tests/unit/test_evaluate_sft_append.py`)
- [ ] T029 Extend `src/eval/stats.py` to compute mean accuracy drop, run paired two‑sample t‑test (or Wilcoxon fallback), detect loss plateau (ΔL < 0.001 for two epochs), **and explicitly evaluate/report the 'percentage point' threshold decision logic** required by SC-002 (file: `src/eval/stats.py`)
- [ ] T029a Add unit test for loss‑plateau detection logic (file: `tests/unit/test_plateau_detection.py`)
- [ ] T062 Implement power‑analysis module for US2 that computes pre‑test power for the paired t‑test (effect size δ=0.03, σ=0.015, α=0.05) and records the achieved power in `results/us2_summary.csv` (file: `src/eval/power_us2.py`)
- [ ] T062a Add unit tests verifying correct power calculation given known parameters (file: `tests/unit/test_power_us2.py`)
- [ ] T062b Add contract test ensuring the power value is present and correctly typed in `results/us2_summary.csv` (file: `tests/contract/test_us2_power_schema.py`)
- [ ] T030 Add driver script `src/pipeline/run_us2.py` that orchestrates mask generation, SFT runs, random runs, evaluation, statistical reporting, and incorporates power‑analysis results, producing `results/us2_summary.csv` (file: `src/pipeline/run_us2.py`)
- [ ] T030a Add end‑to‑end test that `run_us2.py` yields expected summary schema (file: `tests/integration/test_run_us2.py`)
- [ ] T023 US2 Contract test that `results/us2_summary.csv` contains columns `mask_type`, `mean_accuracy_drop`, `t_stat`, `p_value` (file: `tests/contract/test_us2_schema.py`)
- [ ] T023a Extend contract test to verify column types.
- [ ] T024 US2 Integration test that a single seed run of `src/train/frozen_subspace_sft.py` completes without OOM and writes a row to `results/frozen_sft_accuracy.csv` (file: `tests/integration/test_frozen_subspace_sft.py`)
- [ ] T024a Add assertions for OOM absence and CSV entry correctness.
- [ ] T051 Refine SC‑002 into a single measurable predicate and add contract test (file: `tests/contract/test_sc002_predicate.py`)

---

## Phase 4: User Story 3 – Resource Feasibility & Reproducibility (Priority: P3)

- [ ] T032 Create top‑level pipeline script `src/pipeline/run_all.py` that sequentially calls `run_us1.py`, `run_us2.py`, and aggregates all result CSVs into `results/experiment_summary.csv` (file: `src/pipeline/run_all.py`)
- [ ] T032b Implement Unified Summary Generator `src/pipeline/generate_unified_summary.py` merging US1, US2, and US3 CSVs into a single `results/experiment_summary.csv` (file: `src/pipeline/generate_unified_summary.py`)
- [ ] T032a Add end‑to‑end test for `run_all.py` aggregation correctness (file: `tests/integration/test_run_all.py`)
- [ ] T032b-schema Add contract test that the unified `results/experiment_summary.csv` conforms to `contracts/experiment.schema.yaml` (file: `tests/contract/test_unified_summary_schema.py`)
- [ ] T033 Extend `src/utils/resource_monitor.py` to write a JSON summary `ci_metrics.json` at the end of the full pipeline (peak RAM, total wall‑clock) (file: `src/utils/resource_monitor.py`)
- [ ] T033a Add contract test that `ci_metrics.json` respects the schema `{ "peak_ram_gb": number, "wall_clock_min": number }` (file: `tests/contract/test_ci_metrics_schema.py`)
- [ ] T042 Add per‑run RAM assertion in `resource_monitor.py` that raises an error if peak RAM exceeds 7 GB (file: `src/utils/resource_monitor.py`)
- [ ] T043 Add per‑run wall‑clock assertion in `resource_monitor.py` that raises an error if runtime exceeds a predefined maximum duration. (file: `src/utils/resource_monitor.py`)
- [ ] T034 Update the GitHub Actions workflow to invoke `python -m src.pipeline.run_all`, **enforce matrix-splitting**, and upload `ci_metrics.json` as an artifact (file: `.github/workflows/ci.yml`)
- [ ] T034a Add CI workflow schema validation test (file: `tests/contract/test_ci_workflow_schema.py`)
- [ ] T031 CI sanity test that the workflow `ci.yml` finishes without timeout and publishes `ci_metrics.json` (file: `tests/ci/test_ci_limits.py`)
- [ ] T031a Extend CI sanity test to parse `ci_metrics.json` and assert per‑run RAM ≤ 7 GB and wall‑clock ≤ 360 min.
- [ ] T060 Add contract test that the final `state.yaml` artifact conforms to **both** `contracts/experiment.schema.yaml` **and** `contracts/experiment_results.schema.yaml` (file: `tests/contract/test_state_yaml_schema.py`)
- [ ] T061 Implement `src/pipeline/export_state_yaml.py` that reads `results/experiment_summary.csv` and writes `state.yaml` (file: `src/pipeline/export_state_yaml.py`)
- [ ] T061a Add integration test that `export_state_yaml.py` produces a valid `state.yaml` matching the schema (file: `tests/integration/test_export_state_yaml.py`)

---

## Phase 5: Polish & Cross‑Cutting Concerns

- [ ] T037‑ruff Apply `ruff` autofixes across the codebase (file: `src/` modules)
- [ ] T037‑type‑hints Add type hints to all modules and run `mypy --strict` (files: all `src/` modules)
- [ ] T037‑mypy Add CI step that runs `mypy --strict` and fails on any error (file: CI config)
- [ ] T037a Add CI step that runs `ruff` and fails on lint errors (file: CI config)
- [ ] T038 Add additional unit tests for utility functions (`random_seed` and `resource_monitor`) with explicit test files `tests/unit/test_random_seed.py` and `tests/unit/test_resource_monitor_edge.py`
- [ ] T038a Ensure edge‑case coverage for utilities (invalid seeds, missing files) (file: `tests/unit/test_resource_monitor_edge.py`)
- [ ] T039 Run the full test suite with `pytest -q` in CI and enforce **all structural tests pass** (research outcomes like 'inconclusive' are valid and do not count as failures) (file: CI config)
- [ ] T039‑threshold Enforce that **structural tests** (syntax, schema, linting) have a [deferred] pass rate; explicitly exclude research outcome tests from this threshold (file: `tests/contract/test_pass_rate_threshold.py`)
- [ ] T040‑secret‑scan Add secret‑scan test and verify `.gitignore` excludes cache directories (file: `tests/security/test_secret_scan.py`)
- [ ] T040‑gitignore Add `.gitignore` entries for caches, model checkpoints, and other large artifacts (file: `.gitignore`)
- [ ] T040‑poetry‑lock Pin dependency hashes in `poetry.lock` and verify integrity (file: `poetry.lock`)
- [ ] T040a Add contract test that verifies `.gitignore` correctly excludes specified directories (file: `tests/contract/test_gitignore.py`)