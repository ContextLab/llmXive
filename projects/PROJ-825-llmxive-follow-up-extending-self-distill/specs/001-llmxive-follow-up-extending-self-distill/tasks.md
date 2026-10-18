# Tasks: llmXive follow-up: extending "Self-Distilled Agentic Reinforcement Learning"

**Inputs**: `specs/001-llmxive-student-only-gating/spec.md`, `plan.md`, `data-model.md`, `contracts/gating_signal.schema.yaml`, `contracts/training_run.schema.yaml`
**Re-plan context**: The verifier rejected T005, T007–T011 (missing schema contract, broken package imports, mismatched profiler field names, failed lint and memory-check executions). Verified foundational work (T001, T004, T006) is preserved as checked. Rejected tasks are reopened and repaired below without duplicating completed work.

## Phase 0: Foundations and Pilot Checks

- [ ] T001 Create project root structure `code/` with subdirectories `code/agents/`, `code/environments/`, `code/metrics/`, `code/utils/`, `code/tests/`, `code/models/`, `code/config.py`, and `data/`, `data/processed/` per plan.md structure.

- [ ] T004 Repair `code/requirements.txt` to contain **exact pinned** versions of the real dependencies:
  ```
  transformers==4.40.0
  datasets==2.14.0
  sentence-transformers==2.2.0
  torch==2.0.0
  scikit-learn==1.3.0
  pytest==7.4.0
  alfworld==0.3.0
  webshop==0.1.0
  pandas==2.0.0
  numpy==1.24.0
  ruff==0.2.0
  black==24.2.0
  ```
  The corrupted placeholder entry `pytest>=7.0.0 (pi, https://en.wikipedia.org/wiki/Pi)` is removed.
  **Verification**: `pip install -r code/requirements.txt` succeeds, and `grep -c "claim:" code/requirements.txt` returns `0`.

- [ ] T006 Configure `code/config.py` (seeds, hyperparameters, variant flags).  
  **Verification**: `python -c "import code.config"` imports cleanly; the module defines `SEEDS = [0,1,2,3,4]` and a `DEFAULTS` dict matching plan hyperparameters. **Note**: The seed list will be updated by task T020 to the required 20 seeds (42‑61) to align with the experimental design.

- [ ] T005 Fix linting/formatting configuration artifacts: create `code/pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections (line length 100, target Python 3.11) and ensure all source files pass lint. This task only touches config files; it runs after code‑generation tasks.
  **Verification**: `code/pyproject.toml` exists, parses as valid TOML, and `ruff check code/ --config code/pyproject.toml` runs with zero errors; the verification script `code/scripts/verify_lint_t005.sh` exits 0.

- [ ] T007 Implement JSON/CSV logging infrastructure in `code/utils/logging.py` **and** add the missing contract `specs/001-llmxive-student-only-gating/contracts/training_run.schema.yaml` so schema validation works on a fresh run. The schema must include the fields the logger emits for both run‑summary and per‑step records: `run_id`, `variant`, `environment`, `seed`, `step`, `reward`, `cpu_time_sec`, `step_peak_memory_mb`, `timestamp` (match the read‑only contract provided in the active data model).
  **Verification**: unit test `code/tests/test_logging.py` round‑trips a dummy `TrainingRun` record through the logger and validates against the now‑present `training_run.schema.yaml`; `pytest code/tests/test_logging.py` exits 0 with the schema file present at the referenced path.

- [ ] T008 Fix the broken `code/environments/__init__.py` so it only imports symbols that actually exist in `alfworld_env.py` / `webshop_env.py` (or add the missing `create_alfworld_env` / `verify_alfworld_install` helpers), keeping the loud‑failure behavior: each wrapper raises `RuntimeError` if the underlying package cannot be imported, with NO try/except fallback to mock data.
  **Verification**: `python -c "import code.environments"` succeeds, and `pytest code/tests/test_environment_wrappers.py` exits 0, demonstrating both the import path works and the loud‑failure behavior on missing packages.

- [ ] T009 Make `code/agents` an importable package (add `code/agents/__init__.py`) and fix imports in `code/agents/base_agent.py` to use package‑relative or absolute `code.`‑prefixed imports (e.g., `from code.config import TrainingConfig`) so the abstract RL loop interface resolves from the project root.
  **Verification**: `python -c "from code.agents.base_agent import BaseAgent"` executes without error from the project root, and a minimal concrete subclass passes a sanity‑check loop in `code/tests/test_base_agent.py`.

- [ ] T010 Fix `code/metrics/cost_profiler.py` so it records the **required field names and semantics**: `cpu_time_sec` (per‑step CPU time) and `peak_memory_mb` (peak RSS, not instantaneous per‑step RSS), and replace the fragile `cpu_time >= 0.01` sleep assertion in `code/tests/test_cost_profiler.py` with a CPU‑bound workload (e.g., a numeric loop) so `time.process_time()` reliably registers nonzero CPU time.
  **Verification**: `pytest code/tests/test_cost_profiler.py` exits 0 and the recorded metrics dict contains `cpu_time_sec` and `peak_memory_mb` keys with numeric values.

- [ ] T011 [P] Verify CPU‑only environment before heavy loading: load Qwen2.5‑0.5B 8‑bit quantized via `transformers` (`load_in_8bit=True`) and the quantized `sentence-transformers/all-MiniLM-L6-v2` retriever, run a single forward pass through each, and record peak RSS memory (via `psutil`) to `data/processed/memory_dry_run.json`. The script **must abort** with a clear `RuntimeError` if `torch.cuda.is_available()` is true, in accordance with FR‑009. It also **depends on** T004 (pinned requirements) being installed.
  **Verification**: `python code/scripts/dry_run_memory_check.py` exits 0, its JSON output contains numeric `peak_rss_mb`, and the exit code respects the 7 GB gate.

- [ ] T000d Build the student model wrapper (`code/models/student_model.py`) loading Qwen2.5‑0.5B in 8‑bit CPU mode, exposing a `forward` method that returns token logits for entropy calculation.
  **Verification**: Import succeeds and unit test `code/tests/test_student_model.py` validates shape of logits.

- [ ] T000e Build the dense retriever wrapper (`code/models/retriever.py`) loading `sentence-transformers/all-MiniLM-L6-v2` quantized, exposing a `retrieve(context)` method returning embedding vectors for cosine‑similarity stability computation.
  **Verification**: Retriever loads without OOM and unit test `code/tests/test_retriever.py` passes.

- [ ] T002 [P] Implement the student‑only gating mechanism in `code/utils/gating.py` and `code/agents/student_only_agent.py`: compute token entropy $H_t$, context stability $S_t$ (cosine similarity of retrieved chunks via the retriever), and $g_t = \sigma(\alpha H_t + \beta S_t)$ with **NO teacher model invocation** (FR‑001). Include robustness handling for $S_t \approx 0$ and NaN/Inf bounding per FR‑006 (clamp $g_t$ to [0,1], minimum gate 0.05, `is_valid=False` on pathological inputs). Bundle focused unit tests in `code/tests/test_gating.py` verifying: gate values in [0,1], no NaN under noisy/zero‑similarity context, and that no teacher model is loaded or called. Gating signals are logged per the `GatingSignal` contract.
  **Verification**: `pytest code/tests/test_gating.py` exits 0; runtime logs contain `final_gate` within [0,1] and `is_valid` true.

- [ ] T003 [P] Wire `code/main.py` to accept `--variant student-only --env alfworld --seed N` and run a **small real** training case (reduced step cap, e.g. 200 steps) on the real ALFWorld environment, producing real `TrainingRun` and `GatingSignal` JSONL artifacts under `data/processed/` with per‑step CPU time, memory, $H_t$, $S_t$ (FR‑003), and early‑stopping logic (avg per‑episode cumulative reward ≥ 0.8 for 3 consecutive episodes OR step cap). Enforce the CPU‑only guard (FR‑009): raise `RuntimeError` if `torch.cuda.is_available()` is true.
  **Verification**: `python code/main.py --variant student-only --env alfworld --seed 0` executes end‑to‑end on a fresh runner and the resulting files validate against `training_run.schema.yaml` and `gating_signal.schema.yaml`.

- [ ] T000b **Pilot Correlation Analysis (Phase 0b)**: run two short Baseline SDAR sessions (2 k steps each) on ALFWorld and WebShop, compute per‑step teacher‑student confidence‑gap scores, $H_t$, and $S_t$, and calculate Pearson $r$. Proceed to the full study only if $r \ge 0.4$ for each environment.
  **Verification**: Script `code/scripts/pilot_correlation.py` outputs $r$ values; CI fails if any $r < 0.4$.

- [ ] T000c **Runner Pinning & Variance Control**: for every training run, log `lscpu` output and `psutil.cpu_freq()` to `data/processed/hardware_log.json`. After all runs, compute the coefficient of variation of CPU frequency across jobs; abort the pipeline if variance exceeds 5 %.
  **Verification**: `code/scripts/check_hardware_variance.py` exits 0 only when variance < 5 %.

- [ ] T012 [P] Implement the dual‑model SDAR **Baseline** agent (`code/agents/baseline_agent.py`) and the **Student‑Only** agent (`code/agents/student_only_agent.py`). Both must log metrics and teacher‑student gap scores (for the baseline) to `data/processed/`. Record the baseline success metric (`Success_Baseline`) per environment as required by FR‑008. Use a lightweight 0.5 B teacher model (same architecture as the student) to stay within the < 7 GB RAM budget; no fallback to larger models.
  **Verification**: After a short run, `data/processed/<run_id>.jsonl` contains a `teacher_model` field set to `"qwen2.5-0.5b"` and a `final_success_rate` field; FR‑008 is satisfied.

- [ ] T013 [P] Implement paired‑trajectory replay in `code/scripts/replay_paired.py`: load the 20 baseline trajectories generated by T012, replay the identical states through the Student‑Only agent, compute $g_t$ on those states, and calculate the Pearson correlation $r$ between student‑only gates and teacher‑student gap scores. Require at least 100 paired gating scores (minimum trajectory length 50 steps) and source runs must be the baseline runs from T012.
  **Verification**: `correlation_results.json` contains numeric `r` and at least 100 paired entries; no simulated data used.

- [ ] T014a [P] Execute the full experimental grid: for each variant (Baseline SDAR, Student‑Only) and each environment (ALFWorld, WebShop), run **20 independent seeds per variant per environment** (seeds 42‑61), yielding **120 runs** in total. Use early‑stopping (reward ≥ 0.8 for 3 consecutive episodes) or a hard cap of **10 000 steps** (matching FR‑002). Log all metrics per `training_run.schema.yaml`.
  **Verification**: `data/processed/` contains **120** `TrainingRun` JSONL files, each validates against the schema and includes `avg_cpu_time_per_step`, `peak_memory_mb`, and `convergence_steps`.

- [ ] T014b **Cost‑Only Sub‑Phase**: for both variants, run a fixed‑step (10 000 steps) training job without early stopping to obtain uniform per‑step CPU cost measurements. Record `avg_cpu_time_per_step` and `peak_memory_mb`.
  **Verification**: Two additional `TrainingRun` artifacts (one per variant) with `total_steps = 10000` and no early‑stopped flag.

- [ ] T015a **Persist EpisodeMetrics**: after each run, aggregate per‑episode statistics (cumulative reward, success, steps, avg $g_t$, avg $H_t$, avg $S_t$) into `data/processed/episode_metrics.parquet` as defined in the data model.
  **Verification**: Parquet file exists and schema matches `EpisodeMetrics` definition.

- [ ] T015 **Statistical Testing**: implement `code/metrics/statistical_test.py` with Mann‑Whitney U as primary test, Shapiro‑Wilk normality check, optional t‑test, and bootstrapped confidence intervals. Use the episode‑level data from `episode_metrics.parquet` across all runs (120 runs). Output p‑value, effect size (Cohen’s d), and confidence intervals.
  **Verification**: Unit tests in `code/tests/test_statistics.py` pass; outputs contain required fields.

- [ ] T016a **Analysis & Comparison Report**: implement `code/scripts/analyze_results.py` to aggregate all run logs and produce `data/processed/summary.json` (ComparisonReport) containing:
  - cost reduction % (Student‑Only vs Baseline)
  - performance retention % using the spec’s SC‑001 formula `(Success_Student - Success_Baseline) / Success_Baseline ≥ 0.80`
  - convergence steps comparison
  - p‑value and effect size (from T015)
  - Pearson $r$ (from T013)
  **Verification**: `summary.json` contains all fields with correct types and passes schema validation.

- [ ] T016b **Noise‑Robustness Check**: perturb retrieved chunk embeddings with Gaussian noise (σ = 0.1) on a random 5 % of steps, recompute $g_t$, and verify gates stay within [0,1] and report any degradation in success rate. Store results in `data/processed/noise_robustness_report.json`.
  **Verification**: Report file exists, contains `max_gate`, `min_gate`, and `success_delta` fields.

- [ ] T017 Compute SHA‑256 checksums for every file under `data/processed/` and write a manifest `data/processed/checksums.sha256`.
  **Verification**: Manifest exists; `code/scripts/verify_checksums.py` exits 0 with zero mismatches.

- [ ] T018 Generate the specified tables and figures directly from `data/processed/` outputs: training curves per variant, cost comparison, correlation scatter (student heuristic vs teacher gap), and the variant comparison table, saved under `figures/` with generation scripts in `code/scripts/`. No hand‑typed statistics (Constitution IV).
  **Verification**: Each figure file exists and is reproducibly regenerated by its script.

- [ ] T019 Write `specs/001-llmxive-student-only-gating/quickstart.md` documenting the exact runnable commands for all three variants and the analysis pipeline, and a concise methods/results account in `data/processed/RESULTS.md` linked to actual output files and figures, honestly reporting negative findings, the N = 5 power limitation, any teacher‑model scaling deviation, and the paper‑stage handoff (performance retention, cost reduction, significance, correlation findings). Re‑run the documented workflow end‑to‑end from declared inputs to confirm reproducibility.
  **Verification**: Every command in `quickstart.md` executes successfully on a fresh environment, and `RESULTS.md` cites only artifacts that exist under `data/processed/` and `figures/`.

- [ ] T020 **Align Configuration Seed List**: Update `code/config.py` to set `SEEDS = list(range(42, 62))` (20 seeds) so that the experimental runs in T014a use the correct seed range.
  **Verification**: Importing `code.config` shows `SEEDS` containing the integers 42 through 61 inclusive; downstream tasks referencing `SEEDS` now align with the experimental design.

## Dependencies and requirement coverage

- **FR‑001**: System MUST implement the Student‑Only gating mechanism $g_t = \sigma(\alpha H_t + \beta S_t)$ using student token entropy ($H_t$) and retrieved context stability ($S_t$) without invoking a teacher model. (See T002, T003)
- **FR‑002**: System MUST execute the training loop for both the Baseline SDAR (dual‑model) and Proposed Student‑Only variants on the ALFWorld and WebShop environments for a fixed number of **10 000** training steps. (See T014a, T014b)
- **FR‑003**: System MUST log per‑step computational metrics including CPU time, peak memory usage, and the specific values of $H_t$ and $S_t$ for every training step. (See T003, T014a, T014b)
- **FR‑004**: System MUST persist all baseline training artifacts (including teacher‑student gap scores and student heuristics) to a shared storage location to ensure retrievability for cross‑variant performance analysis. (See T012, T013)
- **FR‑005**: System MUST perform a statistical hypothesis test (prioritizing Mann‑Whitney U test or bootstrapping for small‑n bounded data; t‑test only if normality is confirmed) on the final task success rates of the two variants to determine significance at **p < 0.05**. (See T015)
- **FR‑006**: System MUST handle cases where the retrieved context is noisy by ensuring the gating score $g_t$ remains bounded and does not produce NaN values during the sigmoid activation. (See T002, T016b)
- **FR‑007**: System MUST compute the Pearson correlation coefficient $r$ between the student‑only heuristic score $g_t$ and the original teacher‑student confidence‑gap score for each step, and log this value per run. (See T013, T016a)
- **FR‑008**: System MUST record the baseline SDAR success metric (Success_Baseline) per environment to enable the comparative calculation required by SC‑001. (See T012‑FR008)
- **FR‑009**: System MUST ensure that all runs are executed on CPU‑only GitHub Actions runners using an 8‑bit quantized Qwen model; any attempt to fall back to GPU must be aborted and flagged as a failure. (See T011, T003, T014a)

## Order and Execution Notes

- Tasks are ordered to respect data flow: model/retriever builders (T000d/e) → gating implementation (T002) → thin end‑to‑end run (T003) → pilot correlation (T000b) → full grid (T014a/b) → metrics persistence (T015a) → statistical analysis (T015) → final reporting (T016a/b, T017‑T019). Lint fixing (T005) runs after code generation but before any import‑dependent tasks.

- Parallel batches are safe: T005 only touches config files; T007‑T010 each modify distinct modules; T011 depends on T004, so it is scheduled after T004.

- All new tasks have unique IDs and preserve existing IDs where unchanged. The added task T020 ensures seed consistency across the pipeline.
