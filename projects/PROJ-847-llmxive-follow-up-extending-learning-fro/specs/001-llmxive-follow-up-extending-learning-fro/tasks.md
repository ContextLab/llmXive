# Tasks: Density‑Supervision Study for d‑OPSD Diffusion LLMs

**Inputs**: `spec.md`, `plan.md`, the research question “How does the density of future contextual information in diffusion language models influence the emergence of logical reasoning capabilities, and does a critical threshold exist?”, the active contracts (`training_result.schema.yaml`, `statistical_result.schema.yaml`), and the R1 analyze/panel findings.

This revision repairs the rejected data/model tasks (real streaming GSM8K fetch, a real ≤100M-parameter pretrained checkpoint — no placeholder `_IdentityDiffusionModel`), consolidates all statistical outputs into a single schema-conformant `StatisticalResult` artifact, extends timeout enforcement, step-level logging, and the bigbench logical subset to every run mode, and runs the sensitivity sweep over five seeds. Verified work (T001) is preserved.

**Known plan/spec-rooted conflicts (flagged for kickback — not resolvable in tasks.md alone)**:
1. **Seed count / power**: plan.md mandates ten seeds (42–51) and “power ≥ 0.80 with ten seeds”; the CPU budget admits only five seeds (42–46), which meets FR‑009’s “≥ 5” floor. The reduction is documented in `docs/results.md` and the statistical artifact, but plan.md (and the spec’s power assumption) must be amended to five seeds, or additional compute authorized.
2. **FR‑002 model**: the spec’s assumed checkpoint `author/lightdiff-100m` was verified NOT to exist (404/401). T003 substitutes a real pretrained ≤100M network (`distilgpt2`) wrapped in a genuine masked discrete-diffusion corruption/prediction process — a real masked-diffusion formulation, not a silent weakening — but the spec assumption should be amended to name the actual backbone.
3. **Shuffled-entropy control** (plan Phase 3) has no authorizing FR or user story in the spec; it is retained because it strengthens causal inference, but the spec should be amended to authorize it.
4. **Directory layout / output paths**: plan.md places code under `src/llmxive/` and outputs under `outputs/`, and references `specs/001-llmxive-density-analysis/contracts/`; the tasks (and the active contracts) use `code/`, `data/results/`, `figures/`, and `specs/001-llmxive-follow-up-extending-learning-fro/contracts/`. The plan’s paths must be reconciled to the active layout.

---

## Phase 1 – Setup & first end‑to‑end run

- [ ] **T001** [US‑1] **Create a reproducible entry‑point, configs, and quick‑start guide** <!-- FAILED-IN-EXECUTION: code/run_experiments.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_experiments.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_experiments.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_experiments.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_experiments_adaptive_test.py exit=4 --> <!-- FAILED-IN-EXECUTION: code/run_experiments.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_experiments.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_experiments.py exit=1 -->
  - Implement a CLI script `code/run_experiments.py` that parses a YAML config and triggers the pipeline. Define TWO configs: `configs/quickstart.yaml` (thin smoke path: loads data sample, loads model, runs ONE thin training run — i.e., T004 — and exits) and `configs/full_suite.yaml` (the complete experiment suite: T004–T012). Document in `docs/quickstart.md` which config regenerates which artifact set and the expected wall-clock cost of each.
  - **Verification**: Running `python -m code.run_experiments --config configs/quickstart.yaml` prints “Pipeline initialized”, creates `data/results/`, and completes the thin run without errors; `--config configs/full_suite.yaml` is documented as the full regeneration path.

- [ ] **T002** [US‑1] **Download & stream GSM8K (train + test) and the bigbench logical subset with a fail‑loudly loader** (REDO — verifier rejected: `code/data.py` exit=1) <!-- FAILED-IN-EXECUTION: code/data.py exit=1 -->
  - Rewrite `code/data.py` so that `load_gsm8k(split)` internally uses exactly `datasets.load_dataset("openai/gsm8k", "main", split=split, streaming=True)` and `load_bigbench_lite()` uses `datasets.load_dataset("bigbench_lite")` filtered to the logical‑deduction task, per the plan’s Verified Datasets table. **Both loaders return MATERIALIZED fixed samples as Python lists** (built via `itertools.islice` on the stream): the first 2,000 GSM8K train examples, the first 500 GSM8K test examples, and the first 500 bigbench logical-deduction examples. State the sample sizes and their representativeness limitations in `data/raw/manifest.txt` alongside dataset identifiers and byte sizes.
  - The loader MUST raise immediately (no `try/except` fallback, no synthetic/mock data) if the real fetch fails, so the execution stage can discover a verified source and retry. Process in chunks so peak RAM stays ≤ 6 GB.
  - **Verification**: `python -c "from code.data import load_gsm8k; d=load_gsm8k('test'); print(len(d))"` exits 0, prints 500 (the loader returns a materialized list, so `len()` is valid); `len(load_bigbench_lite()) == 500`; `data/raw/manifest.txt` lists both real dataset identifiers with sizes; a deliberately broken identifier raises, not falls back.

- [ ] **T003** [US‑1] **Load a REAL ≤100M‑parameter pretrained checkpoint as the diffusion denoiser** (REDO — verifier rejected: 401 Repository Not Found for `author/lightdiff-100m`, placeholder `_IdentityDiffusionModel`, missing `outputs/model_checkpoint.json`)
  - Do NOT use the invented identifier `author/lightdiff-100m` (verified nonexistent). Replace `code/model.py::load_diffusion_model` to load the real pretrained checkpoint `distilgpt2` (82M parameters, `AutoModelForCausalLM.from_pretrained("distilgpt2")`) on CPU (`device="cpu"`, full precision — no quantization) as the denoiser backbone, and implement the masked discrete-diffusion forward process in `code/diffusion.py`: a masked diffusion corruption schedule where a fraction `1 − ρ_teacher` of future (suffix) tokens is masked per step, and the model predicts the masked tokens. This is a real pretrained network performing real forward/backward passes in a genuine masked-diffusion formulation — no identity/placeholder modules. **Document this substitution and its justification (the spec’s assumed checkpoint does not exist) in `docs/results.md` and in the model artifact metadata; flag the spec’s FR‑002 assumption for amendment (see kickback list above).**
  - Write `outputs/model_checkpoint.json` containing the model id, parameter count (must be ≤ 100,000,000), device, a SHA‑256 of the downloaded config, and a `substitution_note` field explaining the FR‑002 reconciliation.
  - **Verification**: `python -c "from code.model import load_diffusion_model; m=load_diffusion_model(); print(sum(p.numel() for p in m.parameters()))"` exits 0 on a CPU-only runner, prints ≤ 100000000, logs “Model loaded on CPU”, and a forward pass on a dummy batch of 8 sequences completes without CUDA.

- [ ] **T004** [US‑1] **Thin end‑to‑end training run on real data (one ratio, one seed)**
  - Extend `code/trainer.py` to accept `rho_teacher`, `seed`, `max_epochs`, `batch_size=16`, and run the d‑OPSD loop (teacher retains ρ of self‑generated future tokens; student distills on‑policy) over the GSM8K train sample from T002 for a single configuration (ρ = 0.5, seed = 42, 2 epochs), then evaluate on the 500-example GSM8K test sample AND on the 500-example bigbench logical-deduction subset (secondary exact-match accuracy, recorded in `metadata.bigbench_accuracy` — this consumes the FR‑001 second dataset).
  - Compute exact‑match accuracy (final numeric answer match) and token‑level F1 (FR‑012) and write one `TrainingRun` JSON row to `data/results/fixed_baselines/` conforming to `specs/001-llmxive-follow-up-extending-learning-fro/contracts/training_result.schema.yaml` (fields: config, loss_trajectory, final_accuracy, final_f1, runtime_seconds, timeout).
  - **Step-level logging (US‑1 scenario 3)**: record per-step batch accuracy (`metadata.step_accuracy`, array aligned with `loss_trajectory`) and the per-step density value (`metadata.step_rho`, array; constant for fixed runs) in the run’s metadata.
  - **Timeout enforcement (FR‑005)**: check elapsed wall-clock at the start of every epoch against the 6-hour limit; on exceedance save a checkpoint to `data/results/checkpoints/timeout_{run_id}.pt`, set `timeout=true`, and exit gracefully.
  - **Verification**: `data/results/fixed_baselines/rho0.5_seed42.json` exists, validates against the schema via `jsonschema`, `final_accuracy` and `final_f1` are real measured numbers in [0,1], `loss_trajectory` is non-empty, `metadata.step_accuracy` and `metadata.step_rho` are non-empty arrays, and `metadata.bigbench_accuracy ∈ [0,1]`.

## Phase 2 – Complete fixed baselines, adaptive scheduler, and controls

- [ ] **T005** [US‑1] **Run the full fixed‑density baseline grid (5 ratios × 5 seeds)** (REDO of T004 grid — verifier rejected prior execution failures; now depends on the repaired T002/T003)
  - For each ρ ∈ {0.1, 0.3, 0.5, 0.7, 0.9} and each seed ∈ {42, 43, 44, 45, 46} (five seeds — the FR‑009 minimum; the plan’s ten seeds was infeasible within the CPU budget — see the kickback list and record this limitation in the run metadata and `docs/results.md`), execute the T004 trainer with max_epochs ≤ 10 or early stopping, writing one schema‑valid JSON per run to `data/results/fixed_baselines/rho{ρ}_seed{seed}.json`.
  - **Reuse rule**: the (ρ=0.5, seed=42) cell is T004’s thin run — REUSE `rho0.5_seed42.json` as-is (same config and trainer); do not re-run or overwrite it. The grid therefore produces 24 new files plus the reused thin-run file (25 total).
  - Every run (all modes) enforces the hard 6-hour wall-clock limit: check elapsed time at the start of every epoch; on exceedance save a checkpoint to `data/results/checkpoints/timeout_{run_id}.pt`, set `timeout=true`, and exit gracefully (FR‑005). Every run records `metadata.step_accuracy`, `metadata.step_rho`, and `metadata.bigbench_accuracy` per T004.
  - Aggregate all runs into `data/results/fixed_baselines_summary.json` with both accuracy metrics (GSM8K exact-match, token-F1, and bigbench secondary accuracy) per (ρ, seed).
  - **Verification**: 25 schema‑valid JSON files exist; every `final_accuracy ∈ [0,1]`; the summary contains 25 entries; all runs completed or were flagged `timeout=true` (never silent failure).

- [ ] **T006** [US‑2] **Implement the entropy‑based adaptive scheduler with NaN/Inf clamping**
  - Add `code/scheduler.py::AdaptiveScheduler` that computes prediction entropy per batch, clamps to [0, ln(N)] with fallback ρ = 0.5 when entropy is NaN/Inf (spec edge case), and maps entropy linearly to a new ρ_teacher ∈ [0.0, 1.0] (higher entropy → higher density). Add unit tests in `code/tests/test_scheduler.py` covering the clamp, bounds, and NaN fallback.
  - Integrate into `code/trainer.py` when `adaptive=True`, recording the per-step ρ series in the `density_time_series` field and in `metadata.step_rho`.
  - **Verification**: `pytest code/tests/test_scheduler.py` passes; an adaptive run’s JSON contains a non‑constant `density_time_series` with ≥ 20 distinct ρ values and no NaNs.

- [ ] **T007** [US‑2] **Execute adaptive and shuffled‑entropy control runs (5 seeds each)**
  - Run the adaptive configuration (same hyperparameters and seeds 42–46 as T005) writing `data/results/adaptive/rho_adaptive_seed{seed}.json`; each validates against `training_result.schema.yaml` with `adaptive=true`, `rho_teacher=null`.
  - Run the control scheduler (identical except entropy values are randomly permuted across steps within each seed) writing `data/results/control_shuffle/…json` — this isolates the causal contribution of the adaptive heuristic from mere density variation. (Retained per plan Phase 3; flagged for spec authorization — see kickback list.)
  - **Timeout enforcement (FR‑005)**: adaptive and control runs use the SAME epoch-start wall-clock check, checkpoint save to `data/results/checkpoints/timeout_{run_id}.pt`, and `timeout=true` flag as T005, so a hung run still produces a schema-valid artifact rather than no file. All runs also record `metadata.step_accuracy`, `metadata.step_rho`, and `metadata.bigbench_accuracy` per T004.
  - **Verification**: 10 schema‑valid JSON files exist; adaptive files have fluctuating `density_time_series`; control files exist and are kept distinct from fixed‑baseline artifacts for independent comparison (US‑2 scenario 3); every file has a boolean `timeout` field (false or true-with-checkpoint, never missing).

## Phase 3 – Statistical validation & sensitivity analysis

All statistical tasks in this phase contribute sections to ONE consolidated artifact, `data/results/statistics/statistical_result.json`, which MUST validate against `specs/001-llmxive-follow-up-extending-learning-fro/contracts/statistical_result.schema.yaml` (required fields: `t_test_result`, `quadratic_coefficients`, `peak_density`, `sensitivity_slopes`, `entropy_error_correlation`, `analysis_timestamp`; optional `causal_control_test`). Each task may also write a per-component detail file under `data/results/statistics/details/` for traceability, but the consolidated object is the contract-tested artifact (SC-006).

- [ ] **T008** [US‑2] **Entropy–error correlation on held‑out validation data (FR‑010, SC‑007)**
  - Implement `code/analysis.py::entropy_error_correlation` that, for each seed, computes per‑example prediction entropy and per‑example error (0/1 exact‑match) on a held‑out validation slice — the bigbench logical-deduction subset from T002 (disjoint from GSM8K training data and never used for scheduler calibration) — then reports Pearson’s r and two‑tailed p‑value. Write the `entropy_error_correlation` block (`pearson_r`, `p_value`) into `data/results/statistics/statistical_result.json` (plus a detail file `data/results/statistics/details/entropy_error_corr.json` with per-seed values).
  - **Verification**: the consolidated JSON’s `entropy_error_correlation` contains `pearson_r` and `p_value` computed from real per‑example measurements (not simulated); the validation slice (bigbench) is disjoint from training data, satisfying the independence principle.

- [ ] **T009** [US‑3] **Paired t‑tests: adaptive vs. fixed ρ=0.5, and adaptive vs. shuffled control (FR‑006)**
  - Implement `code/analysis.py::run_paired_t_test` matching accuracies across the five shared seeds (42–46); compute the paired t‑test (SciPy `ttest_rel`) for (a) adaptive vs. fixed ρ=0.5 and (b) adaptive vs. shuffled‑entropy control. Write the `t_test_result` block (`t_statistic`, `p_value`, `df`) and the `causal_control_test` block into `data/results/statistics/statistical_result.json` (plus detail file `data/results/statistics/details/paired_t_test.json`).
  - Include a power analysis for the paired design at the observed effect size with n=5, reporting achieved/estimated power and the explicit limitation versus the plan’s ≥0.80-with-ten-seeds target (which is plan-rooted and flagged for kickback); record it in the detail file and `docs/results.md`.
  - **Verification**: The consolidated JSON validates against `statistical_result.schema.yaml`; `p_value ∈ [0,1]`; `df = 4`; seed pairing is exact (no reordering).

- [ ] **T010** [US‑3] **Quadratic density–performance fit with LOOCV and peak CI (FR‑008, FR‑011, SC‑002)**
  - Implement `code/analysis.py::quadratic_loocv`: fit a·ρ² + b·ρ + c to the five fixed‑ratio mean accuracies using leave‑one-ratio‑out cross‑validation; report coefficients, the cross‑validated peak density (clamped to [0,1]), and a 95% bootstrap confidence interval for the peak (resampling seeds). Write the `quadratic_coefficients` (3-element array) and `peak_density` blocks into `data/results/statistics/statistical_result.json` (plus detail file `data/results/statistics/details/quadratic_fit.json` containing the CI).
  - **Verification**: The consolidated JSON contains a 3‑element `quadratic_coefficients` array and `peak_density ∈ [0,1]`; the CI appears in the detail file; the LOOCV procedure is visible in code (held‑out ratio excluded from each fold’s fit).

- [ ] **T011** [US‑3] **Sensitivity sweep around the peak density (FR‑007, SC‑004) — five seeds per offset**
  - For offsets ±0.05 and ±0.1 around the T010 peak (ρ clamped to [0,1]), run the fixed trainer for **all five seeds (42–46)** per offset and compute mean accuracy change per 0.01 density relative to the peak, with a per-offset variance/SD estimate across seeds (removing the prior single-seed noise asymmetry). Write the four mean slopes under keys `plus_0.05`, `minus_0.05`, `plus_0.1`, `minus_0.1` in the `sensitivity_slopes` block of `data/results/statistics/statistical_result.json` (per-seed slopes and SDs in `data/results/statistics/details/sensitivity_analysis.json`).
  - **Reuse rule**: any (ρ, seed) cell whose clamped offset ρ coincides with an existing T005 grid cell (including the peak cell itself) is REUSED from `data/results/fixed_baselines/` — only genuinely new (ρ, seed) combinations are run. Document the resulting file set in the detail file.
  - **Verification**: All four slopes in the consolidated JSON are real measured numbers from actual training runs (not read off the fitted curve); per-seed slopes and SDs are present in the detail file; the consolidated JSON validates against the schema.

- [ ] **T012** [US‑3] **Generate tables and figures directly from validated artifacts**
  - Create `figures/accuracy_vs_rho.png` (per‑seed scatter + LOOCV quadratic curve with peak and CI), `figures/rho_over_time.png` (adaptive density time‑series across seeds), `figures/loss_curves.png`, and `figures/entropy_error_scatter.png`; produce `data/results/summary_table.csv` aggregating final accuracies (both metrics), t‑test outcomes, peak density, and sensitivity slopes — every number read programmatically from the JSON artifacts (`statistical_result.json`, training-run JSONs), none hand‑typed.
  - **Verification**: All PNGs are readable images; each CSV cell traces to a JSON artifact path; no figure contains invented values.

## Phase 4 – Reproducibility, validation & paper hand‑off

- [ ] **T013** [US‑3] **Contract tests for all output artifacts**
  - Add `code/tests/test_contracts.py` that validates every training-run JSON in `data/results/` against `specs/001-llmxive-follow-up-extending-learning-fro/contracts/training_result.schema.yaml` and the consolidated `data/results/statistics/statistical_result.json` against `specs/001-llmxive-follow-up-extending-learning-fro/contracts/statistical_result.schema.yaml`, and asserts cross‑artifact consistency (e.g., the summary CSV matches the JSONs; detail files agree with the consolidated object).
  - **Verification**: `pytest code/tests/ -q` passes with zero failures over all produced artifacts, including the consolidated statistical result.

- [ ] **T014** **Methods/results account, suite wall-clock aggregation, and scoped reproducibility re‑run with paper handoff**
  - Write `docs/results.md` describing the setup (real model id and the documented FR‑002 substitution, sample sizes, five‑seed design and its power limitation versus the plan’s ten seeds), the fixed/adaptive/control findings (p‑values, peak density, sensitivity slopes, entropy–error r), negative or null results reported honestly, and explicit path references to every artifact. Document the paper‑stage handoff: figures, tables, statistical results, and the observational (non‑causal) framing of density effects are ready for the paper pipeline.
  - **SC‑005 evidence**: aggregate suite-level wall-clock time — sum of all per-run `runtime_seconds` across T004–T007 and T011 runs plus orchestration overhead — into `data/results/suite_runtime.json`, reporting total suite wall-clock, per-phase breakdown, and the comparison against the 6-hour per-job limit.
  - **Scoped reproducibility re‑run**: from a clean checkout, re-run `python -m code.run_experiments --config configs/quickstart.yaml` (the thin path: data load + model load + the single T004 run) and confirm its artifacts regenerate and pass T013’s tests. The FULL suite regeneration path is `python -m code.run_experiments --config configs/full_suite.yaml`; document in `docs/results.md` its expected multi-job wall-clock (each job bounded by the 6-hour limit) rather than executing it end-to-end in this task.
  - **Verification**: The final log prints “Pipeline completed successfully, all artifacts validated”; `pytest code/tests/ -q` passes; `data/results/suite_runtime.json` exists with a total wall-clock number; `docs/results.md` renders with no broken links.

---

## Dependency Mapping

| Requirement | Satisfied by Task(s) |
|-------------|----------------------|
| FR‑001 – dataset download + preprocessing (streaming, fail‑loudly, bigbench consumed) | T002, T004, T005, T008 |
| FR‑002 – real ≤100M CPU model (documented substitution; spec flagged) | T003 |
| FR‑003 – fixed‑density training | T004, T005 |
| FR‑004 – adaptive scheduler | T006, T007 |
| FR‑005 – 6‑hour timeout + checkpointing (ALL run modes) | T004, T005, T007 |
| FR‑006 – paired t‑test (+ causal control) | T009 |
| FR‑007 – sensitivity analysis (5 seeds per offset) | T011 |
| FR‑008 / FR‑011 – quadratic fit with LOOCV + peak CI | T010 |
| FR‑009 – ≥5 seeds per condition | T005, T007, T011 |
| FR‑010 – entropy–error correlation | T008 |
| FR‑012 – exact‑match + token‑F1 metrics | T004, T005 |
| US‑1 – baseline convergence (incl. scenario 3 step-level logging) | T002–T005 |
| US‑2 – adaptive scheduler | T006–T008 |
| US‑3 – statistical validation | T009–T013 |
| SC‑001–SC‑007 | T005, T007–T012, T014 (SC‑005 via suite_runtime.json) |

Data‑flow ordering is strict: real data (T002) and real model (T003) precede any training; all training precedes all statistics; statistics precede figures (T012), contract tests (T013), and the report (T014). T005 reuses T004’s (ρ=0.5, seed=42) artifact; T011 reuses any coinciding T005 grid cells. Research scripts write only to `code/`, `data/`, `figures/`, `docs/`, and `outputs/`; platform state under `state/` is never touched.