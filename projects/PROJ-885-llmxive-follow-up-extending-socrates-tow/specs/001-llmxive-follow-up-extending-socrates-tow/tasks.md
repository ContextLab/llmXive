# Tasks: Dynamic Socio-Cognitive State Injection

**Inputs**: `specs/001-dynamic-state-injection/spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`
**Research question**: Does real-time adaptation of LLM mediator prompts based on inferred socio‑cognitive states improve consensus gap closure in high‑emotion, culturally diverse conflicts compared to static prompting?

## Phase 0: Data generation and feasibility checks

- [ ] T101 [US1] Generate synthetic conflict trajectories using the SoCRATES pipeline with targeted oversampling.  
  **Outputs**:  
  - `data/processed/filtered_trajectories.jsonl` (fields: `trajectory_id`, `dialogue_history`, `metadata.emotional_reactivity_score` (0.0‑1.0), `metadata.cultural_identity_tags`, `metadata.conflict_type`, `ideal_resolution`)  
  - `data/results/generation_stats.json` (`total_count`, `high_emotion_count`, `high_cultural_count`, `oversampling_ratio`, `underpowered_flag`)  
  - `data/results/generation_perf.json` (`runtime_seconds`, `peak_memory_mb`, `within_time_limit` bool, `within_memory_limit` bool)  
  **Verification**: script exits 0; `oversampling_ratio ≥ 0.40`; `runtime_seconds ≤ 1800`; `peak_memory_mb ≤ 7000`.

- [ ] T102 [US1] Compute statistical power using `statsmodels.stats.power.tt_solve_power` (Cohen’s d = 0.5, power = 0.80, α = 0.05, paired).  
  **Output**: `data/results/power_analysis_report.json` (`required_n`, `actual_n`, `is_sufficient`, `status`, `underpowered_flag`).  
  **Verification**: file exists, keys correct; always exits 0.

- [ ] T103 [US1] Derive classifier training records from the filtered trajectories.  
  **Procedure**: sliding window of `config.TURN_WINDOW_SIZE = 3` turns → `turn_text`; label derived **solely** from trajectory metadata (`high_reactivity`, `cultural_friction`, `neutral`).  
  **Outputs**: `data/processed/classifier_training_data.jsonl` (fields: `trajectory_id`, `turn_text`, `label`, `confidence_score`, `threshold_used`).  
  **Confidence**: computed via a deterministic bootstrap (1000 resamples of label frequencies, seed from `config.RANDOM_SEED`).  
  **Verification**: at least one record per window; labels limited to three values; unit test `tests/unit/test_data_independence.py` passes.

- [ ] T104 [US1] Perform independence audits.  
  **Outputs**:  
  - `data/results/feature_independence_audit.json` (`overlap_detected`, `validation_passed`) – checks vocabulary overlap between `classifier_training_data.jsonl` and evaluator instruction templates.  
  - `data/results/evaluator_independence_audit.json` (`independence_verified`) – scans `code/models/evaluator.py` for any socio‑cognitive state label usage.  
  **Verification**: both files exist; exit 0 when no overlap detected.

- [ ] T105 [US1] Validate generated trajectories against the official schema.  
  **Action**: run JSON‑Schema validation of `data/processed/filtered_trajectories.jsonl` against `contracts/trajectory.schema.yaml`.  
  **Output**: `data/results/trajectory_schema_validation.json` (`schema_valid`, `errors`).  
  **Verification**: `schema_valid == true`.

- [ ] T115 [SC‑002] Verify dataset variable completeness.  
  **Action**: scan `data/processed/filtered_trajectories.jsonl` to ensure every record contains `metadata.emotional_reactivity_score` and `metadata.cultural_identity_tags`.  
  **Output**: `data/results/dataset_variable_verification.json` (`variables_present`, `missing_fields`).  
  **Verification**: `variables_present == true`.

## Phase 1: Classifier training (already completed in prior work)

*No new tasks – classifier model is assumed trained from T103 output (FR‑002).*

## Phase 2: Experiment execution (Adapter vs. Static, CPU‑only)

- [ ] T106a [US2] Prepare model loading environment.  
  **Steps**:  
  1. Load each model listed in `config.TARGET_MODELS` from `data/raw/models/` using `transformers` with `device="cpu"`.  
  2. If a model exceeds 7 GB RAM (checked via `memory_profile_report.json`) or `torch.cuda.is_available()` is true, record exclusion in `data/results/scope_adjustments.json` (`model_name`, `reason`, `estimated_ram_gb`).  
  3. Write deterministic seed handling (`--seed` flag) to `data/results/seeding_info.json`.  
  **Output**: `data/results/scope_adjustments.json` (list, possibly empty).  
  **Verification**: file exists; no CUDA usage in subsequent tasks.

- [ ] T106b [US2] Run **static** condition inference.  
  **Procedure**: for each allowed model and each trajectory in `data/processed/filtered_trajectories.jsonl`, construct the fixed baseline prompt, run inference on CPU, compute `consensus_gap_score` using `code/models/evaluator.py`, and record a log entry conforming to `contracts/experiment_log.schema.yaml`.  
  **Output**: `data/results/experiment_logs/<model_name>/static.jsonl`.  
  **Fields** (per schema): `run_id`, `trajectory_id`, `model_name`, `condition="static"`, `prompt`, `output`, `metrics.consensus_gap_score`, `metrics.inference_time_ms`, `injected_state` set to the empty string `""`, `status="success"`, `timestamp`.

- [ ] T106c [US2] Run **adapter** condition inference.  
  **Procedure**: reuse `split_trajectory_into_turns` from T103, invoke the logistic‑regression state classifier every 3 turns, map the predicted label to a dynamic instruction template (or `"neutral-monitoring"` if confidence < `config.CONFIDENCE_THRESHOLD`). Inject the instruction into the system prompt, run inference, compute `consensus_gap_score`, and log.  
  **Output**: `data/results/experiment_logs/<model_name>/adapter.jsonl`.  
  **Fields**: same as static, but `condition="adapter"` and `injected_state` contains the state label (including `"neutral-monitoring"`). No additional fields such as `exclude_from_stats` are added; all records fully comply with `contracts/experiment_log.schema.yaml`.

- [ ] T028b [US2] Validate that injected_state matches the corresponding instruction template.  
  **Action**: for each record in the adapter logs, retrieve the instruction template associated with the logged `injected_state` and verify that the prompt actually contains that exact template string.  
  **Output**: `data/results/injection_template_match_report.json` (`total_records`, `matched_count`, `mismatch_details`, `validation_passed`).  
  **Verification**: `validation_passed == true`; mismatches cause task failure.

- [ ] T106d [US2] Aggregate experiment logs.  
  **Action**: concatenate all static and adapter logs into a single file `data/processed/experiment_logs.jsonl` while preserving schema compliance.  
  **Verification**: file exists; each line validates against `contracts/experiment_log.schema.yaml`.

- [ ] T106e [US2] Ensure reproducibility.  
  **Action**: run the full experiment driver twice with the same seed (`--seed <value>`). Verify that the mean `consensus_gap_score` variance across runs is ≤ `config.STATISTICAL_VARIANCE_TOLERANCE` (0.01).  
  **Output**: `data/results/reproducibility_check.json` (`variance`, `passes`).  
  **Verification**: `passes == true`.

- [ ] T107 [US2] Measure throughput and latency.  
  **Action**: compute trajectories per hour and seconds per trajectory from `data/processed/experiment_logs.jsonl`.  
  **Output**: `data/results/throughput_report.json` (`throughput_trajectories_per_hour`, `latency_seconds_per_trajectory`, `passes_sc003`).  
  **Verification**: file exists; boolean reflects thresholds (≥ 40 tp/h, ≤ 45 s).

- [ ] T108 [US2] GPU policy unit test.  
  **Test**: `tests/unit/test_gpu_policy.py` monkey‑patches `torch.cuda.is_available()` to True and asserts a `GPU_detected` entry appears in `scope_adjustments.json` and no model is loaded.  
  **Verification**: pytest passes.

## Phase 3: Evaluation, statistics, and validation

- [ ] T109 [US3] Verify consensus‑gap scores and neutral‑monitoring handling.  
  **Action**: scan `data/processed/experiment_logs.jsonl` to confirm every record has `metrics.consensus_gap_score` in [0.0, 1.0]; generate `data/results/neutral_filter_verification.json` (`neutral_count`, `total_records`, `validation_passed`).  
  **Verification**: `validation_passed == true`. (Neutral‑monitoring records are retained for analysis.)

- [ ] T110 [US3] Perform statistical analysis.  
  **Steps**:  
  1. Determine active LLMs (those not excluded in `scope_adjustments.json` and with `estimated_ram_gb ≤ 7.0`).  
  2. For each active LLM, compute paired differences (adapter − static) on **all** trajectories, **including** neutral‑monitoring adapter records.  
  3. Run Shapiro‑Wilk normality test; if p ≥ 0.05 use paired t‑test, else Wilcoxon signed‑rank.  
  4. Apply Holm‑Bonferroni correction across all active LLMs.  
  **Output**: `data/results/stats_report.json` (conforms to `contracts/report.schema.yaml`).  
  **Verification**: schema validation passes; corrected p‑values reported.

- [ ] T111 [US3] Sensitivity analysis of classifier confidence threshold.  
  **Action**: sweep `config.CONFIDENCE_THRESHOLD` from 0.3 to 0.9 (step 0.1); for each threshold recompute adapter logs (using existing logs filtered by confidence) and record number of injected directives.  
  **Output**: `data/results/sensitivity_analysis_report.json` (`thresholds`, `injected_counts`, `passes_sc005`).  
  **Verification**: file exists; boolean true if variation stays within acceptable range.

- [ ] T112 [US3] Validate experiment log schema.  
  **Action**: run JSON‑Schema validation of `data/processed/experiment_logs.jsonl` against `contracts/experiment_log.schema.yaml`.  
  **Output**: `data/results/experiment_log_schema_validation.json` (`schema_valid`, `errors`).  
  **Verification**: `schema_valid == true`.

- [ ] T113 [US3] Generate final research draft.  
  **Action**: ingest all result artifacts (`stats_report.json`, `sensitivity_analysis_report.json`, `power_analysis_report.json`, `throughput_report.json`, `scope_adjustments.json`, `memory_profile_report.json`) and produce `docs/research_draft.md` with Methods, Results, Discussion, and explicit citations to each artifact. Fail loudly if any required input is missing or malformed.  
  **Verification**: draft file exists; `code/analysis/verify_exclusion_citations.py` confirms all citations trace to data files.

- [ ] T114 [US3] Quickstart end‑to‑end validation.  
  **Action**: execute the documented pipeline on a tiny subset (N = 5) via `scripts/validate_quickstart.py`.  
  **Output**: `data/results/quickstart_validation_report.json` (`timestamp`, `exit_code`, `log_file_path`, `success_flag`, `error_message`, `sc003_status`, `throughput_warning`).  
  **Verification**: `success_flag == true` and `exit_code == 0`.

## Phase 4: Results handoff (already covered by T113/T114)

*No further tasks.*

## Coverage Table (traceability)

| Spec Item | Task(s) |
|-----------|---------|
| FR‑001 | T101 |
| FR‑002 | T103 |
| FR‑003 | T106c |
| FR‑004 | T106a |
| FR‑005 | T109 |
| FR‑006 | T110 |
| FR‑007 | T110 |
| SC‑001 | T110 |
| SC‑002 | T115 |
| SC‑003 | T107 |
| SC‑004 | T102 |
| SC‑005 | T111 |
| SC‑006 | (not required) |
| SC‑007 | (not required) |