# Tasks: llmXive follow-up: extending "Self-Distilled Agentic Reinforcement Learning"

**Inputs**: `specs/001-llmxive-student-only-gating/spec.md`, `plan.md`, `data-model.md`, `contracts/gating_signal.schema.yaml`, `contracts/training_run.schema.yaml`
**Re-plan context**: T005 and T011 were rejected by the independent verifier (missing lint config artifacts; missing dry-run memory measurement). T004's pinned dependency list contains corrupted placeholder text (`{{claim:...}} (pi, ...)`) that must be repaired. All other verified foundational work (T001, T006–T010) is preserved as checked.

## Phase 1: Setup and first end-to-end analysis

- [X] T001 Create project root structure `code/` with subdirectories `code/agents/`, `code/environments/`, `code/metrics/`, `code/utils/`, `code/tests/`, `code/models/`, `code/config.py`, and `data/`, `data/processed/` per plan.md structure.

- [X] T004 [P] Repair `code/requirements.txt` to contain **exact pinned** versions of the real dependencies:
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

- [ ] T005 [P] Create real linting/formatting configuration artifacts: `code/pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections (line length 100, target Python 3.11).   <!-- FAILED-IN-EXECUTION: code/scripts/verify_lint_t005.sh exit=1 --> <!-- FAILED-IN-EXECUTION: code/scripts/verify_lint_t005.sh exit=1 -->
  **Verification**: file exists, parses as valid TOML, and `ruff check code/` runs with zero errors (ruff installed via T004).  

- [X] T006 [P] Configure `code/config.py` (seeds, hyperparameters, variant flags).  
  **Verification**: `python -c "import code.config"` imports cleanly; the module defines `SEEDS = [0,1,2,3,4]` and a `DEFAULTS` dict matching plan hyperparameters.

- [ ] T007 [P] Implement JSON/CSV logging infrastructure in `code/utils/logging.py` for `TrainingRun` and `GatingSignal` artifacts.  
  **Verification**: unit test `code/tests/test_logging.py` round‑trips a dummy `TrainingRun` record through the logger and validates against `training_run.schema.yaml`.

- [ ] T008 [P] Set up environment wrappers `code/environments/alfworld_env.py` and `code/environments/webshop_env.py` using pip‑installable packages; loaders fail loudly on fetch errors (no synthetic fallback).  
  **Verification**: importing each wrapper raises an exception if the underlying package cannot be imported; no try/except fallback to mock data.

- [ ] T009 Create base agent class `code/agents/base_agent.py` defining the RL loop interface.  
  **Verification**: `python -c "from code.agents.base_agent import BaseAgent"` imports without error; a minimal subclass passes a sanity‑check run.

- [ ] T010 Set up cost profiling utility `code/metrics/cost_profiler.py` tracking CPU time and RSS memory per step.  
  **Verification**: `code/tests/test_cost_profiler.py` asserts that the profiler records `cpu_time_sec` and `peak_memory_mb` for a dummy loop.

- [ ] T011 [P] [US1] REDO (verifier‑rejected): create `code/scripts/dry_run_memory_check.py` that (a) loads Qwen2.5‑1.7B 8‑bit quantized via `transformers` (`load_in_8bit=True`), (b) loads the quantized `sentence‑transformers/all‑MiniLM‑L6‑v2` retriever, (c) runs one real forward pass through each, and (d) records peak RSS memory (via `psutil`) to `data/processed/memory_dry_run.json`.   <!-- FAILED-IN-EXECUTION: code/scripts/dry_run_memory_check.py exit=1 -->
  The script **exits non‑zero** if peak RSS exceeds **7 GB** (Constitution VI). If CPU loading fails, the script raises the exception so the execution stage can off‑load to Kaggle GPU (`device="cuda"`).  
  **Verification**: script file exists, its JSON output contains numeric `peak_rss_mb`, and the process exit code respects the 7 GB gate.  
  **Ordering**: runs after T004 (requirements installed).

- [ ] T002 [US1] Implement the student‑only gating mechanism in `code/utils/gating.py` and `code/agents/student_only_agent.py`: compute token entropy $H_t$, context stability $S_t$ (cosine similarity of retrieved chunks via the retriever), and $g_t = \sigma(\alpha H_t + \beta S_t)$ with **NO teacher model invocation** (FR‑001). Include robustness handling for $S_t \approx 0$ and NaN/Inf bounding per FR‑006. Bundle focused unit tests in `code/tests/test_gating.py` verifying: gate values in [0,1], no NaN under noisy/zero‑similarity context, and that no teacher model is loaded or called. Gating signals are logged per the `GatingSignal` contract.  
  **Verification**: tests pass; runtime logs contain `final_gate` within [0,1] and `is_valid` true.

- [ ] T003 [US1] Wire `code/main.py` to accept `--variant student-only --env alfworld --seed N` and run a **small real** training case (reduced step cap, e.g. 200 steps) on the real ALFWorld environment, producing real `TrainingRun` and `GatingSignal` JSONL artifacts under `data/processed/` with per‑step CPU time, memory, $H_t$, $S_t$ (FR‑003), and early‑stopping logic (avg per‑episode cumulative reward ≥ 0.8 for 3 consecutive episodes OR step cap).  
  **Verification**: the command `python code/main.py --variant student-only --env alfworld --seed 0` executes end‑to‑end on a fresh runner and the resulting files validate against `training_run.schema.yaml` and `gating_signal.schema.yaml`.

## Phase 2: Complete the study and validate its evidence

- [ ] T012 [P] [US2] Implement `code/agents/baseline_agent.py` (dual‑model SDAR) and `code/agents/grpo_agent.py` (GRPO baseline), both inheriting `base_agent.py`, logging metrics and teacher‑student gap scores to `data/processed/` with shared `paired_trajectory_id` (FR‑002, FR‑004).  
  **Teacher model selection**: attempt to load `Qwen2.5‑7B` 8‑bit; if loading raises an OOM error, fall back to `Qwen2.5‑3B` 8‑bit, record the chosen model name in the `TrainingRun` metadata, and note the substitution in `RESULTS.md`.  
  **Verification**: after a short run, `data/processed/<run_id>.jsonl` contains a `teacher_model` field with the actual model used and validates against the schema.

- [ ] T013 [US2] Implement paired‑trajectory replay in `code/scripts/replay_paired.py` (or within `student_only_agent.py`): load saved Baseline trajectories, replay the exact same states through the Student‑Only agent, compute $g_t$ on identical states, and compute the **Pearson correlation** between student‑only scores and baseline teacher‑student gaps, writing results to `data/processed/correlation_analysis.csv` and `data/processed/correlation_results.json` (Constitution VII).  

- [ ] T014 [US2] Execute the full experimental grid via `code/main.py`: 5 independent runs (seeds 0–4) for each of GRPO, Baseline SDAR, and Student‑Only on ALFWorld, then the same on WebShop, enforcing the Early Stopping Protocol (reward threshold 0.8 for 3 consecutive episodes OR fixed step cap within the 6‑hour budget).  
  **Verification**: `data/processed/` contains **30** `TrainingRun` artifacts (3 variants × 2 environments × 5 seeds), each validates against `training_run.schema.yaml` and includes non‑null `avg_cpu_time_per_step` and `peak_memory_mb`.

- [ ] T015 [US3] Implement `code/metrics/statistical_test.py` with **both** Mann‑Whitney U test (prioritized) and a bootstrapping fallback (as per FR‑005). The module must:
  1. Check normality (e.g., Shapiro‑Wilk); if normal, optionally run a t‑test (allowed but not required).
  2. Otherwise run Mann‑Whitney U and also produce bootstrapped confidence intervals, p‑values, and Cohen’s d for the N = 5 bounded data regime.  
  **Verification**: unit tests in `code/tests/test_statistics.py` confirm that each statistical path is exercised on synthetic data and that the outputs contain the required fields.

- [ ] T016 [US3] Implement `code/scripts/analyze_results.py` and `code/scripts/compare_variants.py` to aggregate all run logs and output to `data/processed/summary.json` (ComparisonReport per data‑model):
  - cost reduction % (CPU time, Student‑Only vs Baseline, target ≥ 60 %),
  - performance retention % with the explicit SC‑001 inequality check `(Success_Student - Success_GRPO) ≥ 0.8 × (Success_Baseline - Success_GRPO)` reported as PASS/FAIL,
  - convergence steps comparison (SC‑004),
  - bootstrap p‑value and effect size (SC‑003),
  - Pearson correlation from T013,
  - **Noise‑robustness check**: perturb the **retrieved chunks** used for $S_t$ with random noise, recompute gates, and verify that $g_t$ remains bounded and that performance impact is reported.  
  **Verification**: `summary.json` contains all listed fields with correct types, and a separate `noise_robustness_report.json` documents the perturbation results.

## Phase 3: Reproducible results and paper handoff

- [ ] T017 [P] Compute SHA‑256 checksums for every file under `data/processed/` and write a manifest `data/processed/checksums.sha256`.  
  **Verification**: the manifest exists, each line matches the actual file hash, and a verification script `code/scripts/verify_checksums.py` reports zero mismatches.

- [ ] T018 Generate the specified tables and figures directly from `data/processed/` outputs: training curves per variant, cost comparison, correlation scatter (student heuristic vs teacher gap), and the variant comparison table, saved under `figures/` with generation scripts in `code/scripts/`. No hand‑typed statistics (Constitution IV).

- [ ] T019 Write `specs/001-llmxive-student-only-gating/quickstart.md` documenting the exact runnable commands for all three variants and the analysis pipeline, and a concise methods/results account in `data/processed/RESULTS.md` linked to actual output files and figures, honestly reporting negative findings, the N = 5 power limitation, any teacher‑model scaling deviation, and the paper‑stage handoff (performance retention, cost reduction, significance, correlation findings). Re‑run the documented workflow end‑to‑end from declared inputs to confirm reproducibility.

## Dependencies and requirement coverage

- **FR‑001** (student‑only gating): T002, T003 — before any comparison.  
- **FR‑002** (three variants, both environments, 5 seeds): T012, T014.  
- **FR‑003** (per‑step cost/gating metrics): T003, T014 (profiler from T010).  
- **FR‑004** (artifact persistence, paired IDs): T012, T013, T014.  
- **FR‑005** (statistical test): T015, T016.  
- **FR‑006** (NaN/noisy‑context robustness): T002, T016 (noise check).  
- **Constitution VII** (Pearson correlation): T013, T016.  

**Order**: T002 → T003 (thin end‑to‑end first); T011 can run in parallel with T002 after T004; T012/T013 after T002; T014 after T012 and T003; T015 parallel with T014; T016 after T013–T015; T017 after T016; T018–T019 last.  

All previously verified tasks (T001, T006–T010) are preserved. The plan now satisfies all constitutional and specification requirements.  
