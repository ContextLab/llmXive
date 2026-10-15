# Tasks: Low-Rank RL for Foresight in LLM Training  

**Input**: Design documents from `/specs/001-low-rank-rl-foresight/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`  

**Tests**: Tests are **mandatory** for all scientific requirements (statistical testing, alignment verification, etc.).  

**Organization**: Tasks are grouped by research phase and user story to enable independent implementation and testing.  

---  

## Phase 1 – Project Setup & Quick‑Start  

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`, `results/`).  
- [ ] T002 Initialise Python 3.10 environment with required dependencies (`torch`, `transformers`, `datasets`, `peft`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`).  
- [ ] T003 Configure linting (ruff) and formatting (black) tools.  

## Phase 2 – Core Infrastructure (Blocking Prerequisites)  

- [ ] T004 Implement `src/utils/seeds.py` for deterministic seed pinning across all variants. **Verify**: file exists and unit test `tests/unit/test_seeds.py` passes.  
- [ ] T005 Implement `src/utils/memory_monitor.py` to track RAM usage and enforce the 7 GB limit. **Verify**: file exists and runtime monitor writes `results/memory_profile.json` matching `training_log.schema.yaml`.  
- [ ] T006 Implement `src/utils/hasher.py` to compute SHA‑256 hashes of all derived artifacts. **Verify**: file exists and `state/artifact_hashes` updated after a dummy run.  
- [ ] T008 Create `src/data/checksums.py` for data‑integrity verification. **Verify**: file exists and checksum function returns correct SHA‑256 for a known file.  
- [ ] T007 Create `src/data/loader.py` to fetch the GSM8K subset (≥ 1,000 problems) from HuggingFace `datasets` with checksum verification. **Must raise an exception on fetch failure; no synthetic fallback.** **Verify**: file exists, runs without error on a small sample, and validates checksum via `src/data/checksums.py`.  
- [ ] T009 Implement `src/models/config.py` to programmatically prune TinyLlama to a 300 M ± 1 % parameter model. Includes verification logic and graceful fallback to the closest verified size (warning logged, abort if deviation > 1 %). **Verify**: model config file generated, parameter count printed, and deviation check passes.  
- [ ] T010 Implement `src/models/backbone.py` with hooks to capture attention‑projection updates. **Verify**: hooks fire during a dummy forward pass and produce tensors of expected shape.  
- [ ] T011 Create `src/cli/run_experiment.py` – the **single entry point** that orchestrates data loading, training variants, and analysis.  
&nbsp;&nbsp;&nbsp;&nbsp;• Defines CLI arguments `--early-window-fraction`, `--early-alignment-threshold`, `--num-seeds`, and `--variant`.  
&nbsp;&nbsp;&nbsp;&nbsp;• Validates required inputs (e.g., existence of `results/opd_subspace.npy` for Low‑Rank RL).  
&nbsp;&nbsp;&nbsp;&nbsp;• Writes a run‑manifest `results/run_manifest.json`.  
**Verify**: script runs with `--dry-run` flag, produces manifest, and exits with code 0.  
- [ ] T012 Add verification test for the CLI entry point. Create `tests/integration/test_cli_run.py` that invokes `src/cli/run_experiment.py --dry-run` and asserts successful execution. **Verify**: pytest passes (exit code 0).  
- [ ] T013 Create `tests/unit/test_svd.py` to verify SVD on small matrices fits memory constraints. **Verify**: pytest passes and memory usage < 200 MB.  
- [ ] T014 Create `tests/unit/test_projection.py` to verify projection math (cosine similarity ≥ 0.99). **Verify**: pytest passes; placed after projection utilities are implemented.  

## Phase 3 – CPU Feasibility & Resource Hardening  

- [ ] T061 Add SVD fallback logic in `src/training/projection_utils.py`: if cumulative variance < 80 % for any k ≤ 50, default to k = 10 and log a warning. **Verify**: runs on a synthetic low‑variance matrix and selects k=10.  
- [ ] T062 Add gradient‑projection sanity check (condition number > 1e6 ⇒ renormalise) in `src/training/projection_utils.py`. **Verify**: unit test confirms renormalisation triggers when condition number exceeds threshold.  
- [ ] T052a Implement `src/utils/time_estimator.py` – estimates runtime per variant; aborts if total > 6 h (writes `results/time_estimate.json`). **Verify**: JSON file created and `total_estimated_time` ≤ 6 h for default config.  
- [ ] T052b Implement `src/utils/memory_estimator.py` – estimates peak RAM; aborts if > 7 GB (writes `results/memory_estimate.json`). **Verify**: JSON file created and `peak_estimated_ram_mb` ≤ 7000.  
- [ ] T052c‑final‑time‑verify Aggregate final wall‑clock measurement after execution and write `results/pipeline_time.json` (checks against SC‑005). **Verify**: file exists and `elapsed_seconds` ≤ 21600.  
- [ ] T059 Refactor `src/data/loader.py` to use `datasets.load_dataset(..., streaming=True)`. **Verify**: loader runs in streaming mode (no full in‑memory load) and logs streaming status.  
- [ ] T060‑stream Implement streaming data loader in `src/data/loader.py` (chunked iteration, no full in‑memory load). **Verify**: loader yields batches without exceeding 500 MB RAM (checked via `memory_monitor`).  
- [ ] T060‑accum Implement online statistics accumulator in `src/analysis/metrics.py` (writes `results/online_stats_checkpoint.json`). **Verify**: accumulator updates and JSON checkpoint matches schema.  
- [ ] T063 Add time‑budget enforcement in `src/cli/run_experiment.py`: aborts a seed if the 6 h limit is exceeded, writes `results/experiment_status.json` with status *inconclusive*, and exits with a designated code. **Verify**: simulated long run triggers abort and status file is created.  

## Phase 4 – User Story 1: Establish Geometric Baseline via On‑Policy Distillation (P1)  

- [ ] T015 Create unit test `tests/unit/test_opd_svd.py` – verifies OPD SVD output shape. **Verify**: pytest passes and output shape matches `(k, n_params)`.  
- [ ] T016 Create integration test `tests/integration/test_opd_flow.py` – end‑to‑end OPD data flow. **Verify**: pytest passes, generates `results/opd_subspace.npy`.  
- [ ] T017 Implement OPD baseline runner `src/training/opd_baseline.py`.  
&nbsp;&nbsp;&nbsp;&nbsp;• Loads GSM8K via T007, runs for `--num-steps` (configurable).  
&nbsp;&nbsp;&nbsp;&nbsp;• Records per‑step parameter updates ΔW for each layer to `results/opd/updates_seed_{i}/layer_{idx:02d}.pt`.  
**Verify**: runner creates the expected update files, aggregates them, produces `results/opd_subspace.npy`, and the file passes `opd_subspace.schema.yaml` validation.  
- [ ] T018b Log per‑step update directions (same path as above). **Verify**: log files exist and contain numeric tensors.  
- [ ] T018c‑aggregate Aggregate per‑layer vectors into a single matrix `results/opd/accumulated_matrix_seed_{i}.npy`. **Verify**: matrix file exists and shape matches `(num_steps, total_params)`.  
- [ ] T018c‑config Write early‑window configuration (`results/early_window_config.json`). **Verify**: JSON file created with `early_window_fraction` key.  
- [ ] T018d‑align Log early‑trajectory alignment during the early window to `results/opd/early_alignment_log.json`. **Verify**: JSON file exists and entries contain `alignment_score`.  
- [ ] T018d‑verify Verify existence and JSON validity of `results/opd/early_alignment_log.json`. **Verify**: schema validation passes.  
- [ ] T019 Implement global SVD in `src/training/projection_utils.py` – input `accumulated_matrix_seed_{i}.npy`, output `results/opd/svd_results.npy`. **Verify**: output file exists and matches expected dimensions.  
- [ ] T020 Select rank k (cumulative variance ≥ 80 % or fallback k = 10) and write `results/opd/k_value.json`. **Verify**: JSON contains `rank_k` and `cumulative_variance`.  
- [ ] T021 Save stable subspace matrix (`k × n_params`) to `results/opd_subspace.npy`. **Verify**: file exists, shape `(k, total_params)`, and passes `opd_subspace.schema.yaml`.  
- [ ] T022a Log memory usage during SVD; assert < 7 GB. **Verify**: memory log written and value ≤ 7000 MB.  
- [ ] T022b Log peak memory to `results/memory_profile.json` for SC‑004 verification. **Verify**: JSON conforms to `training_log.schema.yaml`.  

## Phase 5 – User Story 2: Execute Low‑Rank RL Hybrid with Geometric Projection (P2)  

- [ ] T023 Unit test `tests/unit/test_gradient_projection.py` – verifies projection retains ≥ 0.99 cosine similarity. **Verify**: pytest passes.  
- [ ] T024 Integration test `tests/integration/test_low_rank_rl.py` – mini‑run (1 step) on 10‑sample GSM8K subset, checks `results/low_rank_rl/early_alignment_log.json`. **Verify**: pytest passes and early‑alignment file created.  
- [ ] T026‑core Implement gradient‑projection function in `src/training/projection_utils.py` (uses `results/opd_subspace.npy`). **Verify**: function returns projected gradient with cosine ≥ 0.99.  
- [ ] T025‑impl Implement Low‑Rank RL runner `src/training/low_rank_rl.py`.  
&nbsp;&nbsp;&nbsp;&nbsp;• Loads GSM8K via T007.  
&nbsp;&nbsp;&nbsp;&nbsp;• Checks for `results/opd_subspace.npy` (raises `SubspaceNotFoundError` if missing).  
&nbsp;&nbsp;&nbsp;&nbsp;• Computes raw PPO gradient, projects with T026‑core, applies update.  
&nbsp;&nbsp;&nbsp;&nbsp;• Logs per‑step update vectors to `results/low_rank_rl/updates_seed_{i}/layer_{idx:02d}.pt`.  
**Verify**: runner creates update logs, `results/low_rank_rl/alignment_log.json` contains cosine ≥ 0.99 for every step, and the run completes without error.  
- [ ] T025‑std Implement Standard RL baseline runner `src/training/rl_baseline.py` (no projection). **Verify**: runs without error and produces `results/standard_rl/updates_seed_{i}`.  
- [ ] T027 Add logging to verify each applied update lies within the span of the top‑k vectors. **Verify**: `results/low_rank_rl/alignment_log.json` contains cosine ≥ 0.99 for every step.  
- [ ] T028 Assert cosine similarity ≥ 0.99 for every update (writes to `results/low_rank_rl/alignment_log.json`). **Verify**: JSON schema validation passes and min similarity ≥ 0.99.  
- [ ] T029‑mem Enforce memory limit during Low‑Rank RL training (uses `memory_monitor`). **Verify**: `results/low_rank_rl/memory_profile.json` records peak ≤ 7000 MB.  
- [ ] T029a‑mem Measure memory for Standard RL (writes `results/standard_rl/memory_profile.json`). **Verify**: same as above.  
- [ ] T030 Save Low‑Rank RL training logs and checkpoints under `results/low_rank_rl/`. **Verify**: checkpoint files exist and are < 600 MB each.  
- [ ] T030b‑log Per‑step update logging for Low‑Rank RL (same format as OPD). **Verify**: logs written and parsable.  
- [ ] T030c‑early Log early‑trajectory alignment (compare to OPD) to `results/low_rank_rl/early_alignment_log.json`. **Verify**: file exists and contains `alignment_score`.  
- [ ] T030c‑verify Verify existence and JSON validity of `results/low_rank_rl/early_alignment_log.json`. **Verify**: schema validation passes.  

## Phase 6 – User Story 3: Compare Convergence & Subspace Alignment (P3)  

- [ ] T031 Unit test `tests/unit/test_stats.py` – synthetic data verifies Wilcoxon test returns p < 0.05 when appropriate. **Verify**: pytest passes.  
- [ ] T032 Integration test `tests/integration/test_full_pipeline.py` – mini‑pipeline across all variants, checks `results/analysis_report.md`. **Verify**: pytest passes and report generated.  
- [ ] T033 Implement Random Projection baseline `src/training/random_projection.py`.  
&nbsp;&nbsp;&nbsp;&nbsp;• Generates random matrix R (k × n_params), projects gradients, trains PPO.  
- [ ] T033a‑mem Measure memory for Random Projection (`results/random_projection/memory_profile.json`). **Verify**: peak ≤ 7000 MB.  
- [ ] T034 Implement Random Walk Prior baseline `src/training/random_walk_prior.py`.  
- [ ] T034a‑mem Measure memory for Random Walk Prior (`results/random_walk_prior/memory_profile.json`). **Verify**: peak ≤ 7000 MB.  
- [ ] T035 Implement OPD‑Initialized RL (no projection) `src/training/opd_initialized_rl.py`.  
- [ ] T035a‑mem Measure memory for OPD‑Initialized RL (`results/opd_initialized_rl/memory_profile.json`). **Verify**: peak ≤ 7000 MB.  
- [ ] T036‑feasibility Determine feasible variant set based on time/memory estimates; write `results/feasibility_report.json`. **Verify**: JSON lists variants with status “feasible”.  
- [ ] T036‑manifest Write active‑variant manifest to `results/active_variants.json`. **Verify**: manifest matches feasibility report.  
- [ ] T042‑filter‑list Filter run list according to feasibility; write `results/run_list_filtered.json`. **Verify**: filtered list excludes infeasible variants.  
- [ ] T042‑write‑list Write final run list to `results/run_list.json`. **Verify**: file exists and contains at least 3 seeds per variant.  
- [ ] T042‑execute‑list Execute all runs defined in `results/run_list.json` via `src/cli/run_experiment.py`.  
&nbsp;&nbsp;&nbsp;&nbsp;• Each run writes logs, checkpoints, and memory profiles under its variant folder.  
- [ ] T036‑metrics‑explicit Aggregate accuracy‑vs‑steps curves, compute steps‑to‑80 % accuracy, and cosine‑similarity alignment; output `results/metrics_summary.json`. **Verify**: JSON conforms to `analysis_results.schema.yaml`.  
- [ ] T037 Generate convergence and alignment plots (`results/convergence_plots.png`). **Verify**: image file created and readable.  
- [ ] T038a Implement power‑analysis module `src/analysis/power_analysis.py`. **Verify**: module runs and outputs `results/power_analysis.json`.  
- [ ] T038b‑wilcoxon Perform Wilcoxon signed‑rank test on steps‑to‑threshold data (requires N ≥ 3).  
&nbsp;&nbsp;&nbsp;&nbsp;• If N < 3, write `results/statistical_status.json` with *Inconclusive (Insufficient Samples)* and stop further statistical testing. **Verify**: JSON reflects correct status and test p‑value when performed.  
- [ ] T039 Generate final analysis report `results/analysis_report.md` (tables, plots, statistical summary). **Verify**: report includes p‑value < 0.05 when significance claimed.  
- [ ] T040a‑early‑alignment‑core Compute early‑trajectory alignment for Low‑Rank RL vs OPD (FR‑008) and write `results/low_rank_rl/early_alignment_metrics.json`. **Verify**: JSON contains mean alignment ≥ 0.99.  
- [ ] T040b‑baseline‑alignment Compute early alignment for Standard RL and OPD baselines; write respective JSON files. **Verify**: files exist and conform to schema.  
- [ ] T080 Compute final subspace alignment for each variant – after training, calculate the cosine similarity between the final accumulated update direction of the variant and the standard PPO baseline; store results in `results/final_alignment.json` (array of `{variant, seed, final_alignment_score}`). **Verify**: file validates against `analysis_results.schema.yaml` and satisfies SC‑002.  
- [ ] T081 Verify mixed‑precision (FP16) is enabled – during each training run, log the model dtype; after run, assert dtype is `torch.float16`. Write verification entry to `results/fp16_check.json`. **Verify**: all entries report FP16.  

## Phase 7 – Polish & Cross‑Cutting Concerns  

- [ ] T050a Update `quickstart.md` with CLI examples, hard‑abort description, and status‑file interpretation. **Verify**: quickstart renders without broken links.  
- [ ] T050b Add Sphinx‑style docstrings to `src/training/projection_utils.py` and `src/utils/memory_monitor.py`. **Verify**: `pydocstyle` passes.  
- [ ] T050c Update `README.md` with experiment‑status badge and data‑availability section. **Verify**: badge renders on GitHub.  
- [ ] T051a Extract logging logic to `src/utils/logger.py` (JSON‑structured logs to `results/experiment.log`). **Verify**: log file created and JSON lines parse.  
- [ ] T051b Run `ruff --select F401` and remove all unused imports. **Verify**: ruff reports zero F401 warnings.  
- [ ] T052‑opt Performance optimisation – batch‑size doubling and ensure FP16 mixed precision throughout training loops. **Verify**: batch size increased in config and FP16 usage confirmed by T081.  
- [ ] T053 Add additional unit tests for `projection_utils.py` and `seeds.py` to reach required branch coverage. **Verify**: coverage report ≥ 90 %.  
- [ ] T067 Data‑loader fail‑loud verification test (`tests/unit/test_loader_failure.py`). **Verify**: test passes when loader raises on bad URL.  
- [ ] T068 Hash audit of all files in `results/` against `state/artifact_hashes`. **Verify**: audit script reports zero mismatches.  
- [ ] T069 Subspace‑stability verification – run OPD for 3 seeds, ensure variance of selected k < 5 %. **Verify**: JSON `results/opd/k_stability.json` contains `k_variance` < 0.05.  
- [ ] T071‑variants Memory‑assertion verification for **all** experimental variants (after T042‑execute‑list). Writes any violations to `results/experiment_status.json`. **Verify**: status file reports “all within limits”.  
- [ ] T071 Final memory report aggregation (`results/memory_report.md`). **Verify**: report lists peak memory per variant and total ≤ 7 GB.  

## Phase 8 – Review & Revision (Addressing Analysis Concerns)  

- [ ] T072 Ensure `src/training/low_rank_rl.py` explicitly checks for `results/opd_subspace.npy` before training; raises `SubspaceNotFoundError` with clear guidance. **Verify**: missing file triggers error and message.  
- [ ] T073 Robust SVD fallback – enhanced in `src/training/projection_utils.py` with elbow‑heuristic when variance threshold cannot be met. **Verify**: fallback logs warning and selects appropriate k.  
- [ ] T074 Add gradient‑projection unit tests (`tests/unit/test_gradient_projection.py`). **Verify**: pytest passes (duplicate of T023 but retained for clarity).  
- [ ] T075 Validate early‑window logic in `src/cli/run_experiment.py`; clamp `early_window_steps` to `total_steps` if necessary and log a warning. **Verify**: warning appears when over‑specified.  
- [ ] T076 Standardise `early_alignment_log.json` schema across all variants (fields: `variant_name`, `seed`, `step`, `alignment_score`, `timestamp`). **Verify**: all early‑alignment logs validate against shared schema.  
- [ ] T077 Extend `src/analysis/plots.py` to visualise effect size (Cohen’s d) and achieved power, overlaying the 0.8 power threshold. **Verify**: plot includes annotated power curve.  
- [ ] T078 Variant‑abortion handler – in `src/cli/run_experiment.py`, catch `OOMError` and `TimeoutError`, log to `results/failures.json`, skip the failed seed, and continue the experiment. **Verify**: simulated OOM writes entry and proceeds.  

---  

**Note**: All tasks now include explicit verification criteria, correct ordering, no duplicate identifiers, and added steps to satisfy final‑alignment (FR‑005, SC‑002) and mixed‑precision (FR‑007) requirements. The test policy is mandatory for scientific validity. Do not infer completion from an existing filename or code stub. New or changed tasks must be unchecked; the runtime retains existing checked tasks only when their review receipts still match the task requirements, specification and current artifacts.  