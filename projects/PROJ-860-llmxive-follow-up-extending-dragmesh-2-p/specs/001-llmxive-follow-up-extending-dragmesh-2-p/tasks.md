# Tasks: llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation

**Inputs**: Design documents from `/specs/001-virtual-tactile-adaptation/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL – only include them if explicitly requested in the feature specification.

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001a Create project directory structure per `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/` plan: Execute `mkdir -p code tests data/raw data/generated data/results state/projects` to establish the physical repository layout.  
- [ ] T001b Create empty skeleton files for project configuration: Create empty files `README.md`, `.gitignore`, and `code/requirements.txt` to establish file paths. **Do NOT populate content yet.**  
- [ ] T002 Populate `code/requirements.txt` with specific dependencies: Add `pybullet`, `numpy`, `scipy`, `pandas`, `datasets`, `pytest`, `statsmodels` with pinned versions to satisfy Constitution Principle I (Reproducibility). (DEPENDS ON T001b)  
- [ ] T003 Create `code/pytest.ini` with specific timeout configuration: Set `timeout=3600` for unit tests and `timeout=21600` for integration tests to enforce the 6 h limit. (DEPENDS ON T001b)  
- [ ] T001c Compute SHA256 hashes for `README.md`, `.gitignore`, `requirements.txt` (from T002), and `pytest.ini` (from T003) and write them to `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml` under `artifact_hashes`. **Pre‑check**: Verify all target files exist before checksumming. **Clarification**: Compute SHA256 of the *populated* `requirements.txt` and `pytest.ini` created in T002/T003, not the empty skeleton files. (DEPENDS ON T002, T003)

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T004 Setup CPU‑only PyBullet physics environment in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/environment.py` (enforce `FR‑004`, no CUDA).  
  - Insert a **global** runtime check at the start of `environment.py` that explicitly verifies PyBullet is running in CPU mode by calling `pbd.configureDebugVisualizer(pbd.COV_ENABLE_GUI,0)` and ensuring no CUDA flags are set; raise an error if GPU usage is detected.  
- [ ] T008b [P] Implement `validate_citations.py` script in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/validate_citations.py` (Constitution Principle II: Verified Accuracy).  
- [ ] T008c Execute `validate_citations.py` against DragMesh‑2 and PICA baseline citations: Run the script to verify all citations in `plan.md` and `spec.md` before any data download tasks (T005d, T012d) are permitted. **Requirement**: If any citation fails validation, the pipeline must halt immediately with a non‑zero exit code. **Output**: Generate `citations_validation.log` in `data/results/` containing the validation status and any errors. (DEPENDS ON T008b)  
- [ ] T005b Implement strict real‑data fetcher verification logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/data_loader.py`  
  - Add function `def verify_manifest_integrity(manifest_path: str) -> None:` that checks existence, non‑emptiness, and raises `FileNotFoundError` or `ConnectionError` on failure. No synthetic fallback. (DEPENDS ON T001b, T002)  
- [ ] T005d Download DragMesh‑2 dataset from verified HuggingFace URL in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/data_loader.py`: Use `datasets.load_dataset` to fetch the DragMesh‑2 manifest and data to `data/raw/`. **Error Handling**: MUST raise `ConnectionError` or `FileNotFoundError` if fetch fails; NO synthetic fallbacks. (DEPENDS ON T008c)  
- [ ] T005c Verify manifest integrity and record local checksum in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/verify_manifest.py`: Compute SHA256 of `data/raw/dataset_manifest.jsonl`. **Requirement**: If the manifest is missing or empty, raise `FileNotFoundError` immediately and halt. If the file exists and is non‑empty, record the hash to `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml` under the key `artifact_hashes.data_raw`. (DEPENDS ON T005d)  
- [ ] T005e Execute fetcher verification on fetched data in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/verify_manifest.py`: Run `verify_manifest_integrity('data/raw/dataset_manifest.jsonl')`. **Requirement**: This task executes the check. If the manifest is missing or empty, it must raise an error and halt the pipeline. (DEPENDS ON T005d, T005c, T005b)  
- [ ] T005f Analyze dataset friction distribution in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/dataset_analyzer.py`: Scan the downloaded DragMesh‑2 manifest (from T005d) to extract friction coefficients for all objects. Generate `data/generated/friction_distribution_report.json` containing the min, max, mean, and a list of object IDs with friction in the 0.8–1.2 range. **Requirement**: This report is the **only** source for determining the training exclusion filter in T012h. If no high‑friction objects exist, the filter is a no‑op. (DEPENDS ON T005d, T005c)  
- [ ] T005a Implement `VirtualTactileEstimator` class in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/estimator.py`: Calculate $k_{\text{est}} = \frac{|\Delta \tau_{\text{hand}}|}{\max(|\Delta v_{\text{object}}|,\;\epsilon)\; N}$ with moving‑average filter (window = 5) applied to the torque signal **before** differentiation, epsilon = $10^{-4}$, and clamp output to $[1\times10^{-4},\,10]$. (FR‑001, FR‑006, FR‑007)  
- [ ] T006 Implement `AdaptiveRewardScheduler` class in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/scheduler.py` mapping $k_{\text{est}}$ to reward weights with explicit logic:  
  - If $k_{\text{est}}$ exceeds the **90th percentile** of the training distribution, increase `r_detach` by ≥ 20 %.  
  - If $k_{\text{est}}$ falls below the **10th percentile**, decrease `r_detach` by ≥ 15 %. (FR‑002, FR‑011)  
  - **Verification**: Include a self‑test block that prints the calculated $k_{\text{est}}$ and the resulting reward multiplier, and asserts that the magnitude of the adjustment matches the spec’s thresholds.  
- [ ] T007 Create `NovelObjectSet` generator class in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/generator.py` to produce a set of randomized articulated geometries with friction coefficients **outside** the training range (0.2–0.6). The class MUST accept `count`, `seed`, `friction_min`, and `friction_max` arguments and output JSON manifests to `data/generated/`. (FR‑003)  
- [ ] T008a Implement seed‑fixation enforcement logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/seed_config.py` that explicitly sets seeds for `numpy`, `random`, and `torch` (if used) to satisfy Constitution Principle I (Reproducibility). (Note: This sets global seeds before T012h and T013e run.)  
- [ ] T009a Implement checksum verification logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/checksum_verify.py`: Compute SHA256 hashing function for files in `data/raw` and `data/generated`. (DEPENDS ON T001a)  
- [ ] T009c Execute checksum verification and update state: Run `checksum_verify.py` to hash all files in `data/raw` and `data/generated` and write results to `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml`. (DEPENDS ON T005f, T009a)  
- [ ] T016a Create logging configuration in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/logging_config.py` with specific file paths and formats.  
- [ ] T016b Add specific log statements for reward weight adjustments and $k_{\text{est}}$ values in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py`: Logs MUST include the constants `epsilon=1e‑4` and `filter_window=5` alongside runtime values to ensure reproducibility (Constitution Principle I).  
- [ ] T015f [P] Generate GLMM amendment proposal: Create `docs/amendments/001-glm-replacement.md` proposing the replacement of the paired‑t‑test mandated by FR‑005/SC‑005 with a GLMM to handle zero‑success baselines. **Requirement**: Document the new success criteria (Odds Ratio, p‑value) and place the proposal **before** any training or analysis tasks. (DEPENDS ON T008c)  
- [ ] T015g [P] Approve GLMM amendment proposal: Review `docs/amendments/001-glm-replacement.md`. If approved, mark the document as “APPROVED” and write `approval_signature.txt` to `data/results/`. This acts as the gate allowing T012h and T015a to proceed. (DEPENDS ON T015f)  

**Checkpoint**: Foundation ready – user‑story implementation can now begin in parallel.

## Phase 3: User Story 1 – Zero‑Shot Adaptation to Unseen Damping (Priority P1)

- [ ] T010 Unit test for `AdaptiveRewardScheduler` logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_scheduler.py`  
  - **Requirement**: Assert that for $k_{\text{est}} > 1.0$ the reward weight increases by ≥ 20 %; for $k_{\text{est}} < 0.2$ the reward weight decreases by ≥ 15 %.  
- [ ] T012b Verify and fetch PICA baseline in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/baseline_fetcher.py`: Query the verified HuggingFace registry for the `dragmesh/pica-baseline-v` checkpoint, resolve the actual SHA256 hash, and write it to `data/raw/baseline/`. (DEPENDS ON T008c)  
- [ ] T012d Download PICA baseline policy in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/baseline_fetcher.py`: Download the artifact resolved in T012b to `data/raw/baseline/`. **Strict Requirement**: Write to `data/raw/baseline/` (no alternate paths). (DEPENDS ON T012b)  
- [ ] T012c Load and validate static PICA baseline policy in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/baseline_runner.py`: Dry‑run load of the checkpoint to ensure it can be deserialized on CPU. No full evaluation is performed here. (DEPENDS ON T012b, T012d)  
- [ ] T012h Implement the training loop in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py` integrating `VirtualTactileEstimator` (T005a) and `AdaptiveRewardScheduler` (T006).  
  - **Requirement**: Assert CPU‑only mode at runtime start to enforce **FR‑004**.  
  - **Filter Logic**: Read `data/generated/friction_distribution_report.json` (from T005f). If high‑friction objects (0.8–1.2) are present, exclude them from the training set to ensure zero‑shot evaluation. If none exist, train on the full DragMesh‑2 dataset. (DEPENDS ON T005a, T006, T008a, T005f, T015g)  
- [ ] T013a Generate NovelObjectSet for zero‑shot evaluation: `python code/generator.py --count 25 --seed 42 --friction-min 0.8 --friction-max 1.2 --output data/generated/novel_objects/` producing **25** high‑friction objects (0.8–1.2).  
  - **Requirement**: Deterministic generation via `seed=42`. (DEPENDS ON T007)  
- [ ] T013b Verify generated artifacts exist and are valid in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/verify_generated.py`: Ensure at least 25 JSON manifests exist in `data/generated/novel_objects/`, each non‑empty, and compute SHA256 hashes to write to `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml`. (DEPENDS ON T013a)  
- [ ] T013c Partition generated object set into subsets in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/generator.py`: Write manifest `data/generated/subsets.yaml` mapping each object ID to `high_friction`. (DEPENDS ON T013b)  
- [ ] T013d Implement pre‑flight check for evaluation in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/evaluate.py`: Verify existence of `data/generated/` artifacts and successful execution of T013c before proceeding. Halt with clear error if missing or insufficient diversity. (DEPENDS ON T013b, T013c)  
- [ ] T013e Implement inference runner in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/evaluate.py`: Run inference on novel objects using **both** adaptive and static policies.  
  - **Requirement**: Assert CPU‑only mode at runtime.  
  - Read `data/generated/subsets.yaml` to tag results with friction category.  
  - Output per‑trial rows to `data/results/eval_logs.csv` with columns `trial_id,object_id,policy_type,friction_category,success,k_est`. (DEPENDS ON T013d, T012h)  
- [ ] T013f Stream large result logs to `data/results/eval_logs.csv` in append mode rather than accumulating all objects × trials in memory. Preserve columns `object_id`, `policy_type`, and `friction_category` for pairing. (DEPENDS ON T013e)  
- [ ] T014 Aggregate success‑rate data: `code/aggregate.py` reads `eval_logs.csv` and writes `data/results/aggregated.csv` containing per‑object and per‑policy success statistics. (DEPENDS ON T013f)  
- [ ] T015a Implement GLMM analysis in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/glmm_analysis.py`: Fit a **Generalized Linear Mixed Model** (logit link) on `aggregated.csv` with `policy_type` as fixed effect and `object_id` as random intercept. Output model summary to `data/results/glmm_summary.json` including p‑value and odds ratios. (DEPENDS ON T014, T015g)  
- [ ] T015b Implement `analysis.py` to read `glmm_summary.json`, extract overall p‑value, odds ratio for high‑friction subset, and compute improvement % (adaptive vs. static). Write JSON report `data/results/analysis_glmm.json` with fields `p_value`, `odds_ratio_high`, `improvement_pct_high_friction`. (DEPENDS ON T015a)  
- [ ] T015c Validate analysis results: Read `analysis_glmm.json` and write verification JSON `data/results/analysis_validation.json` containing `p_value`, `improvement_pct_high_friction`, and boolean flags `pass_sc001` (≥ 15 % improvement) and `pass_sc005` (p < 0.05). (DEPENDS ON T015b)  
- [ ] T015d Enforce statistical significance (SC‑005): CI must FAIL if `p_value >= 0.05`. Log outcome. (DEPENDS ON T015c)  
- [ ] T015e Enforce high‑friction improvement threshold (SC‑001): CI must FAIL if `improvement_pct_high_friction < 15`. Log outcome. (DEPENDS ON T015c)  
- [ ] T015h Record amendment approval in state: Update `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml` to record approval of Amendment 001 and link it to `approval_signature.txt` from T015g. (DEPENDS ON T015g)

**Checkpoint**: User Story 1 fully functional and testable.

## Phase 4: User Story 2 – Virtual Tactile Stiffness Estimation (Priority P2)

- [ ] T033a Unit test for stiction handling (epsilon clamp) in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_stiction.py`: Verify that when $\Delta v_{\text{object}} \approx 0$, the estimator applies $\epsilon = 10^{-4}$ and returns a high, finite $k_{\text{est}}$. (DEPENDS ON T005a)  
- [ ] T033b Unit test for range clamping logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_clamping.py`: Verify that inputs outside the defined bounds produce clamped outputs. (DEPENDS ON T005a)  
- [ ] T033c Unit test for moving‑average filter logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_filter.py`: Verify that the filter window size is 5 and correctly smooths the torque signal before differentiation. (DEPENDS ON T005a)  
- [ ] T033d Unit test for noise robustness in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_noise.py`: Verify estimator stability under simulated simulation jitter. (DEPENDS ON T005a)  
- [ ] T021a Sweep generator script: `code/sweep_generator.py` creates `data/generated/sweep.csv` with columns `[trial_id, friction_value, raw_torque, raw_velocity]` by simulating interactions with known friction values.  
  - **Requirement**: Include explicit stiction cases where `raw_velocity ≈ 0`. Output **raw** signals only; no derivatives or $k_{\text{est}}$ are computed here. (DEPENDS ON T004)  
- [ ] T021b Execute sweep: `python code/sweep_generator.py --n_trials 40 --friction-min 0.0 --friction-max 2.5 --output data/generated/sweep.csv`. Ensure ground‑truth friction for each trial is recorded. (DEPENDS ON T021a)  
- [ ] T021c Run estimator on raw sweep data: `python code/estimator.py --input data/generated/sweep.csv --output data/generated/sweep_processed.csv`. This invokes `VirtualTactileEstimator` (T005a) to compute $k_{\text{est}}$, applying filter and clamping. (DEPENDS ON T021b, T005a)  
- [ ] T021d Correlation analysis: `code/correlation_analysis.py` reads `sweep_processed.csv`, computes Pearson $r$ between $k_{\text{est}}$ and ground‑truth friction, and writes `data/results/correlation_report.json`. **Requirement**: Must achieve $r ≥ 0.8$ over ≥ 30 trials. (DEPENDS ON T021c)  
- [ ] T038 Adaptive policy on sweep data: `code/sweep_policy_eval.py` runs the adaptive policy on `sweep.csv`, using the estimator to compute $k_{\text{est}}$ on‑the‑fly, and outputs `data/results/sweep_policy_results.csv` with columns `trial_id,policy_type,success,k_est`. Validate that adaptive success rate exceeds static baseline by ≥ 10 % for the varying‑friction scenario (SC‑002). (DEPENDS ON T021b, T005a)

**Checkpoint**: User Stories 1 & 2 independently functional.

## Phase 5: User Story 3 – CPU‑Tractable Inference Pipeline (Priority P3)

- [ ] T026 Optimize `code/generator.py` for low memory usage during geometry generation (streaming writes, avoid large in‑memory lists).  
- [ ] T027 Optimize `code/train.py` batch sizes and simulation steps to fit within the 6 h wall‑clock limit and ≤ 7 GB RAM.  
- [ ] T028a Create orchestration script `code/run_benchmark.py`:  
  - Executes generation (T013a), training (T012h), evaluation (T013e), aggregation (T014), and analysis (T015a).  
  - Writes a summary JSON `data/results/benchmark_summary.json` containing total wall‑clock time, peak memory, and boolean flags `pass_sc003`, `pass_sc004`. (DEPENDS ON T013a, T012h, T013e, T014)  
- [ ] T028b Add step wrappers inside `run_benchmark.py` for each pipeline stage (generation, training, evaluation, aggregation, analysis). (DEPENDS ON T028a)  
- [ ] T025 Implement memory‑profiling script `code/memory_profiler.py` using `tracemalloc` to capture peak memory usage; integrate it into `run_benchmark.py` so that `benchmark_summary.json` includes `peak_memory_gb`. (MANDATORY for SC‑004)  
- [ ] T029 Execute full benchmark: `python code/run_benchmark.py --output data/results/benchmark_metrics.json`. Log wall‑clock time and peak memory. (SC‑003, SC‑004 measurement)  
- [ ] T029b Enforce limits: CI must FAIL (non‑zero exit) if `wall_clock_time > 21600` s (6 h) **or** `peak_memory_gb > 7`. Log specific violation. (DEPENDS ON T029)

**Checkpoint**: Entire pipeline verified to run within CPU‑only resource constraints.

## Phase N: Polish & Cross‑Cutting Concerns

- [ ] T030 Documentation updates in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/docs/README.md` and `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/README.md`:  
  - Populate both files with **Installation**, **Running the pipeline**, **Results**, and **Reproducibility** sections.  
  - Include concrete CLI examples for each major script (data download, object generation, training, evaluation, benchmark).  
  - Add a checklist linking to core tasks (T010‑T029) and describing expected output artifacts (e.g., `data/results/glmm_summary.json`, `benchmark_summary.json`).  
  - Verify that the files are non‑empty, correctly formatted in Markdown, and committed to the repository.  
- [ ] T031 Code cleanup and refactoring of `code/estimator.py` and `code/scheduler.py` (remove dead code, improve docstrings).  
- [ ] T032 Performance optimization for simulation loop in `code/environment.py` (reduce sub‑steps, enable `DIRECT` mode).  
- [ ] T039 Implement reproducibility audit script `code/audit_reproducibility.py`: Generate a deterministic report of all random seeds, environment variables, and dependency hashes used in the final run; write to `data/results/reproducibility_audit.json`. (Addresses Constitution Principle I)  
- [ ] T035 Verify `validate_citations.py` passes against all data sources (run as CI step).  

## Dependencies & Execution Order

| Phase | Depends on |
|-------|------------|
| Phase 1 | – |
| Phase 2 | Phase 1 |
| Phase 3 (US 1) | Phase 2 |
| Phase 4 (US 2) | Phase 2 |
| Phase 5 (US 3) | Phase 2 |
| Phase N (Polish) | All prior phases (especially tasks that generate artifacts referenced in the docs) |

Tasks marked **[P]** can run in parallel when their file targets differ. All other tasks must respect the ordering indicated in the “DEPENDS ON” notes.

---  

*All tasks are written to be executable on a standard GitHub Actions free‑tier runner (2 CPU, 7 GB RAM) without any CUDA or GPU‑specific calls. Real data sources are fetched directly; any failure to fetch aborts the pipeline loudly, satisfying the “no synthetic fallback” rule.*
