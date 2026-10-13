# Tasks: Dynamic Socio‑Cognitive State Injection

**Inputs**: `specs/001-dynamic-state-injection/spec.md`, `plan.md`, `data-model.md`, `contracts/`

The goal is to answer the research question: *Does real‑time adaptation of LLM mediator prompts based on inferred socio‑cognitive states improve consensus‑gap closure in high‑emotion, culturally diverse conflicts compared to static prompting?*

All tasks are written as executable checklist items. Each task lists the exact artifact(s) it must produce, its dependencies, and the verification steps required by the specification.

---

## Phase 0 – Data creation, feasibility, and classifier preparation

- [ ] **T001** [US1] **Generate synthetic conflict trajectories with targeted oversampling**
  *Creates* `data/processed/trajectories.json` and `data/processed/generation_stats.json`.
  *Depends on*: —
  - Implement and run `code/data/generate_trajectories.py` with `--oversample-high-emotion --oversample-diverse-cultural`. The script MUST be complete (no truncation) and MUST write both output files before exiting.
  - Each trajectory is a JSON object conforming to `contracts/dataset.schema.yaml` (fields: `trajectory_id`, `dialogue_history`, `emotional_reactivity_score`, `cultural_identity_tags`, `ideal_resolution`).
  - `generation_stats.json` MUST contain `total_count`, `high_emotion_count`, `high_cultural_count`, `oversampling_ratio` (fraction of trajectories in the high‑emotion or diverse‑cultural axes), and `underpowered_flag` (true if `total_count < 500`).
  - **Verification**: both files exist; every trajectory validates against `contracts/dataset.schema.yaml`; `oversampling_ratio ≥ 0.40`; script exits 0.

- [ ] **T014** [US1] **Verify oversampling ratio (authoritative FR‑001 check)**
  *Creates* `data/results/oversampling_report.json`.
  *Depends on*: T001
  - Reads `data/processed/trajectories.json` and `data/processed/generation_stats.json` produced by T001; recomputes the high‑difficulty fraction independently and confirms `oversampling_ratio ≥ 0.40`.
  - Fails loudly (non‑zero exit) if the ratio is insufficient or if either input file is missing or malformed — no fallback, no synthetic substitute.
  - **Verification**: report contains `total_count`, `high_difficulty_count`, `oversampling_ratio`, `passes_fr001` (`true`).

- [ ] **T015** [US1] **Statistical power analysis and under‑powered flag**
  *Creates* `code/analysis/power_analysis.py` and `data/results/power_analysis_report.json`.
  *Depends on*: T014
  - Uses `statsmodels.stats.power.TTestPower().solve_power(effect_size=0.5, power=0.80, alpha=0.05)` to compute `required_n`.
  - Compares to `total_count` from `generation_stats.json`; records `required_n`, `actual_n`, `is_sufficient`, `underpowered_flag`.
  - **Verification**: JSON includes all four fields; script exits 0.

- [ ] **T002** [US3] **Statistical utilities: normality check, paired tests, Holm‑Bonferroni correction**
  *Creates* `code/analysis/stats_utils.py` and `tests/unit/test_stats_utils.py`.
  *Depends on*: —
  - Implements Shapiro‑Wilk normality test on difference scores, paired t‑test / Wilcoxon signed‑rank selection (per FR‑006), effect sizes (Cohen's d, rank‑biserial), and Holm‑Bonferroni family‑wise correction across models (per FR‑007 / SC‑004).
  - Unit tests verify correction against known p‑value vectors and test selection against synthetic normal/non‑normal samples.
  - **Verification**: `pytest tests/unit/test_stats_utils.py` passes.

- [ ] **T003** [US1] **Split trajectories into training and experiment sets**
  *Creates* `data/processed/classifier_training_set.jsonl` and `data/processed/filtered_trajectories.jsonl` (experiment subset only).
  *Depends on*: T001
  - Randomly allocate 30 % of trajectories (seeded by `config.RANDOM_SEED`) to training; 70 % remain for experiments.
  - Ensure no overlapping `trajectory_id`s between the two files.
  - **Verification**: both files exist, each line validates against `contracts/dataset.schema.yaml`, and the intersection of IDs is empty.

- [ ] **T018** [US1] **Record split metadata**
  *Creates* `data/results/split_metadata.json`.
  *Depends on*: T003
  - Stores counts of training vs. experiment trajectories and the random seed used.
  - **Verification**: JSON present and counts match the actual split files.

- [ ] **T019** [US2] **Extract sliding‑window training records**
  *Creates* `data/processed/classifier_training_data.jsonl`.
  *Depends on*: T018
  - For each trajectory in `classifier_training_set.jsonl`, slide a window of 3 turns, concatenate into `turn_text`, assign `label` based on trajectory metadata (`high_reactivity`, `cultural_friction`, `neutral`).
  - Add deterministic `confidence_score` = 1.0 and `threshold_used` = `config.CONFIDENCE_THRESHOLD`.
  - **Verification**: each record contains `trajectory_id`, `turn_text`, `label`, `confidence_score`, `threshold_used`; at least one record per trajectory; unit test `tests/unit/test_data_independence.py` passes.

- [ ] **T004** [US2] **Feature‑independence audit (vocabulary vs. adapter templates)**
  *Creates* `data/results/feature_independence_audit.json`.
  *Depends on*: T019
  - Compare vocabulary of `turn_text` in `classifier_training_data.jsonl` against instruction templates in `code/experiments/prompts.py`.
  - Report `overlap_detected` (bool) and `validation_passed` (true if no overlap).
  - **Verification**: JSON exists and `validation_passed == true`.

- [ ] **T020b** [US2] **Additional feature‑independence audit (deep token check)**
  *Creates* `data/results/feature_independence_audit_deep.json`.
  *Depends on*: T004
  - Performs n‑gram overlap analysis to ensure no indirect leakage of state labels into classifier features.
  - **Verification**: `validation_passed == true`.

- [ ] **T006** [US2] **Train lightweight logistic‑regression state classifier**
  *Creates* `models/state_classifier.pkl` and `code/models/classifier_training.py`.
  *Depends on*: T019, T004
  - Load `classifier_training_data.jsonl`, vectorize `turn_text` with TF‑IDF, train `sklearn.linear_model.LogisticRegression(max_iter=200, n_jobs=1)`.
  - Serialize the fitted pipeline (vectorizer + estimator) with `joblib.dump`.
  - **Verification**: model file < 20 MB; quick inference test returns a valid `state_label` with a `confidence` value in [0, 1].

- [ ] **T005** [US2] **Validate classifier feature set does not contain state‑label tokens**
  *Creates* `data/results/classifier_feature_audit.json`.
  *Depends on*: T006
  - Checks that the persisted TF‑IDF vocabulary does not include any of the exact state‑label strings.
  - **Verification**: `validation_passed == true`.

---

## Phase 1 – CPU‑only experiment execution (adapter vs. static)

- [ ] **T007** [US2] **Prepare model loading environment & scope adjustments**
  *Creates* `data/results/scope_adjustments.json`.
  *Depends on*: —
  - For each model in `config.TARGET_MODELS`, attempt to load the quantized GGUF checkpoint on CPU (`device_map="cpu"`).
  - If estimated RAM > 7 GB or CUDA is detected, record `{ "model_name": "...", "reason": "exceeds RAM" | "GPU detected", "estimated_ram_gb": X }` and exclude the model from later runs.
  - **Verification**: file exists; downstream tasks read this to determine runnable models.

- [ ] **T033** [US3] **Implement consensus‑gap evaluator**
  *Creates* `code/models/evaluator.py` and `data/results/evaluator_independence_audit.json`.
  *Depends on*: —
  - Implements the topic‑localized consensus‑gap metric using `sentence-transformers` (MiniLM) on CPU: cosine distance between the LLM output and the trajectory's `ideal_resolution`, mapped to a 0–1 gap score (0 = perfect).
  - The evaluator MUST NOT reference any socio‑cognitive state labels (FR‑005 independence); the audit verifies this by static inspection of `evaluator.py`.
  - **Verification**: unit test `tests/unit/test_evaluator.py` passes; `evaluator_independence_audit.json` has `validation_passed == true`.

- [ ] **T045a** [US2] **Refactor prompt‑building logic (shared between conditions)**
  *Creates* updated `code/experiments/prompts.py`.
  *Depends on*: —
  - Centralises the static baseline prompt and the dynamic state→instruction template mapping in one module used by both conditions.
  - **Verification**: unit test `tests/unit/test_prompt_builder.py` passes.

- [ ] **T045b** [US2] **Unit test for prompt‑builder correctness**
  *Creates* `tests/unit/test_prompt_builder.py`.
  *Depends on*: T045a
  - Checks that given a state label the correct instruction string is returned, and that the static prompt contains no dynamic injection.
  - **Verification**: test passes.

- [ ] **T027** [US2] **Full CPU‑only inference runner (static + adapter)**
  *Creates* `code/experiments/runner.py`, `data/results/experiment_logs/<model_name>/static.jsonl`, `data/results/experiment_logs/<model_name>/adapter.jsonl`, and updates `data/results/scope_adjustments.json` on runtime errors.
  *Depends on*: T007, T045a, T018, T020, T033
  - Loads each allowed model on CPU only; **explicitly forbids** any CUDA or bitsandbytes imports (raises `RuntimeError` if detected).
  - For every trajectory in `filtered_trajectories.jsonl`, runs both conditions **on the exact same trajectory** in a paired, randomized order (seeded) so Constitution VII's isolation guarantee holds.
  - *Adapter*: every 3 turns invoke `models/state_classifier.pkl` (trained in T006/T020); if `confidence < config.CONFIDENCE_THRESHOLD` inject the neutral instruction `"monitoring"`; otherwise inject the mapped dynamic instruction.
  - Logs all required fields per `contracts/experiment_log.schema.yaml`, including `injected_state` (or `"neutral-monitoring"`), `status`, `inference_time_ms`, `consensus_gap_score` (from the T033 evaluator).
  - Implements exponential‑backoff retry; on repeated failure marks `status: "skipped"` and records it in `scope_adjustments.json`.
  - **Verification**: all log files validate against the schema; no CUDA warnings appear; wall‑clock time ≤ 6 h on CI.

- [ ] **T008** [US3] **Validate experiment logs against `experiment_log.schema.yaml`**
  *Creates* `data/results/log_schema_validation_report.json`.
  *Depends on*: T027
  - Loads each log file and runs JSON‑Schema validation.
  - **Verification**: report lists any violations; task fails if any exist.

- [ ] **T009** [US2] **Validate injected‑state ↔ prompt consistency**
  *Creates* `data/results/injection_template_match_report.json`.
  *Depends on*: T027
  - For each adapter log entry, retrieve the instruction template for its `injected_state` from `prompts.py` and confirm the exact string appears in the stored `prompt`.
  - Report `total_records`, `matched_count`, `mismatch_details`, `validation_passed`.
  - **Verification**: `validation_passed == true`.

- [ ] **T010** [US3] **Throughput, latency, and reproducibility checks**
  *Creates* `data/results/throughput_report.json` and `data/results/reproducibility_check.json`.
  *Depends on*: T027
  - *Throughput*: compute `trajectories_per_hour` and `latency_seconds_per_trajectory`; flag `passes_throughput` (≥ 40 tp/h) and `passes_latency` (≤ 45 s) per SC‑003.
  - *Reproducibility*: run the full runner twice with identical seed; compute variance of mean `consensus_gap_score`; flag `passes` (≤ 0.01).
  - **Verification**: both JSON files exist; boolean flags are `true`.

- [ ] **T028** [US2] **Execute full experiment across all allowed LLMs**
  *Creates* final aggregated logs under `data/results/experiment_logs/` (leveraging T027).
  *Depends on*: T027
  - Ensures each allowed model from `scope_adjustments.json` is processed.
  - Records any models excluded due to RAM/GPU constraints.
  - **Verification**: logs for every allowed model exist and pass schema validation (via T008).

---

## Phase 2 – Analysis, sensitivity, and reporting

- [ ] **T011** [US3] **Statistical analysis with normality test, paired test selection, and Holm‑Bonferroni correction**
  *Creates* `data/results/stats_report.json` (conforms to `contracts/report.schema.yaml`).
  *Depends on*: T028, T008, T002
  - Loads static and adapter logs for each active model; assembles the paired dataset per trajectory & model.
  - Computes paired differences (adapter − static) on all trajectories (including neutral‑monitoring runs).
  - Performs Shapiro‑Wilk test (via `stats_utils.py`); if `p ≥ 0.05` use paired t‑test, else Wilcoxon signed‑rank.
  - Calculates `mean_diff`, `p_value`, `effect_size` (Cohen's d or rank‑biserial), `test_type`, `normality_p_value`.
  - Applies Holm‑Bonferroni correction across the models; stores corrected `p_value` and sets `is_significant` (`< 0.05`); sets `correction_applied: true`.
  - **Verification**: JSON validates against `report.schema.yaml`; all required fields present.

- [ ] **T012** [US3] **Sensitivity analysis of classifier confidence threshold**
  *Creates* `data/results/threshold_sensitivity_report.json`.
  *Depends on*: T011
  - Sweeps `config.CONFIDENCE_THRESHOLD` from 0.3 to 0.9 in 0.1 steps. For each threshold, filters adapter logs to retain runs with `confidence ≥ threshold` (no re‑run required).
  - Records `threshold`, `injected_count`, `mean_gap_adapter`, `mean_gap_static`, `effect_size`.
  - Verifies variation in `effect_size` stays within ±0.1; adds top‑level `passes_sc005` flag.
  - **Verification**: JSON exists; `passes_sc005 == true`.

- [ ] **T051** [US3] **Throughput and per‑model performance reporting**
  *Creates* `data/results/model_throughput_report.json` (per‑model breakdown complementing T010's `throughput_report.json`).
  *Depends on*: T010, T028
  - Reports `trajectories_per_hour` and average `inference_time_ms` per model.
  - **Verification**: report exists and numbers are within feasibility bounds.

- [ ] **T013** [US3] **Final research draft and quick‑start validation**
  *Creates* `docs/research_draft.md` and `data/results/quickstart_validation_report.json`.
  *Depends on*: T011, T012, T015, T051
  - *Draft generation*: ingest `stats_report.json`, `threshold_sensitivity_report.json`, `power_analysis_report.json`, `throughput_report.json`, `scope_adjustments.json`, and `generation_stats.json`. Populate Methods, Results (tables per model), Discussion, and explicit citations to each artifact (e.g., `[[generation_stats.json]]`). Fail loudly if any required artifact is missing or malformed.
  - *Quick‑start test*: run `scripts/validate_quickstart.py` on a tiny subset (`N=5`) of trajectories; capture exit code, timestamps, and any warnings. Write `quickstart_validation_report.json` with `success_flag`, `exit_code`, `throughput_warning`.
  - **Verification**: `research_draft.md` exists; `quickstart_validation_report.json` reports `success_flag == true` and `exit_code == 0`.

---

## Phase 3 – Validation table (traceability)

| Spec Item | Task(s) |
|-----------|---------|
| FR‑001 | T001, T014 |
| FR‑002 | T004, T005, T006, T019, T020b |
| FR‑003 | T027, T045a, T045b |
| FR‑004 | T007, T027 |
| FR‑005 | T033, T009 |
| FR‑006 | T002, T011 |
| FR‑007 | T002, T011 |
| SC‑001 | T011 |
| SC‑002 | T001, T014, T015 |
| SC‑003 | T010, T051 |
| SC‑004 | T002, T011 |
| SC‑005 | T012 |
| US‑1 | T001, T014, T015, T003, T018 |
| US‑2 | T004, T005, T006, T007, T027, T045a, T045b |
| US‑3 | T002, T008, T009, T010, T011, T012, T013, T033, T051 |

All tasks are unchecked (`- [ ]`) because they have yet to be implemented. Once a task is completed and its verification passes, it should be marked `[x]` by the execution platform.