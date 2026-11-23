# Tasks: Quantifying Neural Representation Drift During Skill Learning

**Inputs**: Active `spec.md`, `plan.md`, and the read‑only contracts under `specs/001-quantify-neural-drift/contracts/`. This is an explicitly authorized mathematical/simulation study: the plan designates a seeded synthetic generator (random rotation of tuning curves) as the data source, so no external dataset download is required.

**Compute**: CPU‑only, ≤2 cores, ≤7 GB RAM, <6 h (FR‑010, SC‑005). No GPU‑dependent libraries.

## Phase 0: Foundations

- [~] T001 [P] [US1] Establish the study skeleton and runnable entry point: create `code/src/` (modules `data/`, `analysis/`, `validation/`, `utils/`) and `code/tests/`, and document the runnable command (`python -m code.src.main --stage all`) in `specs/001-quantify-neural-drift/quickstart.md`. Implement `code/src/config.py` with the `primary_model` flag (`linear` default for FR‑005 output; `exponential` for Constitution‑VII prediction input) and a fixed random seed. Verification: `quickstart.md` names the exact command and the seed; `python -c "from code.src.config import CONFIG"` succeeds.

- [ ] T002 [P] [US1] Implement the seeded synthetic data generator and input validator in `code/src/data/loader.py`: generate per‑subject, per‑day records (`subject_id`, `session_id`, `day_index`, `spike_counts` per unit per 20 ms bin, `trial_success`) for N=20 subjects × 10 days, with known ground‑truth drift injected via random rotation of tuning curves (SC‑001) and known drift–learning‑speed correlation (r≈0.6, US‑2 independent test). Implement `code/src/data/validator.py` enforcing FR‑009: raise a `RuntimeError` naming the missing variable and the step if `spike_counts`, `trial_success`, `subject_id`, or `day_index` is absent — never fall back to placeholder data. Validate every generated record against `specs/001-quantify-neural-representation-drift/contracts/input_schema.schema.yaml` and write records to `data/raw/synthetic_records.jsonl` with a SHA‑256 checksum in `data/raw/checksums.json`. Verification: `pytest code/tests/test_loader.py` passes, including a test that a record missing `trial_success` raises. <!-- FAILED-IN-EXECUTION: code/src/data/loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/main.py exit=1 -->

- [ ] T003 [P] [US1] Implement preprocessing in `code/src/data/preprocessor.py`: (a) align spikes to trial events in 20 ms bins (FR‑001); (b) retain only units present in ≥80 % of sessions, recording excluded units with reason `low_presence` (FR‑002); (c) exclude performance‑modulated units via regression of unit firing on trial‑error signals, reason `performance_modulated` (FR‑003); (d) linearly interpolate missing behavioral logs and flag subjects with gaps >2 days as incomplete (US‑1 Scenario 3, FR‑009); (e) write one `NeuralPopulationMatrix` per subject/day to `data/processed/neural_matrix_{subject_id}_day{day}.json` conforming to `contracts/neural_population.schema.yaml` (including `excluded_units`, `stability_threshold`, `checksum`). Verification: `pytest code/tests/test_preprocessor.py` checks that a unit present in <80 % of sessions is excluded and that a >2‑day gap flags the subject.

- [ ] T004 [P] [US1] Compute RDMs and fit the **linear** drift model (primary per `drift_result.schema.yaml`). Use metric implementations from `code/src/utils/metrics.py` (Pearson, Cosine, Mahalanobis). Store per‑subject linear fit results in `data/results/drift_results.json` conforming to `drift_result.schema.yaml` (fields: `subject_id`, `drift_rate_b`, `intercept_a`, `r_squared`, `model_type` set to `"linear"` or `"constant"` on fallback, `convergence_status`, `stability_threshold`, `distance_metric`, `standard_error`). On linear‑fit failure, fallback to a constant model (`model_type: "constant"`). Wire the entry point so `python -m code.src.main --stage drift` runs T002→T004 on a small case (5 subjects) and produces a schema‑compliant result file. Verification: command executes; `data/results/drift_results.json` exists with required fields for each subject.

- [ ] T005 [P] [US1] **Create** `code/src/validation/synthetic.py` and run ground‑truth validation (SC‑001): compare recovered drift rates `b_lin`/`b_exp` against the known rotation‑injected ground truth across all 20 subjects, asserting recovery within 5 % error tolerance, and write the validation table to `data/results/sc001_validation.json` (per‑subject ground truth, estimate, relative error, pass flag). Verification: `pytest code/tests/test_sc001.py` passes on the full generated dataset; the JSON records actual errors, not expected ones.

- [ ] T006 [P] [US2] Implement the behavioral correlation and hypothesis testing in `code/src/analysis/correlation.py`: derive "time to reach success threshold" from learning curves using a concrete threshold `trial_success ≥ 0.8` (exclude subjects with flat curves, log exclusion reason). Compute Pearson `r` between drift rates (from the primary model defined in `config.primary_model`) and learning speeds, assert `r > 0.5`. Run a permutation test with **10 000** label shuffles (FR‑006, SC‑002) and fit a linear mixed‑effects model with subject random effects via `statsmodels`; apply Bonferroni correction when `metrics_tested` > 1 (FR‑007). Set `power_warning=True` if N < 15. Emit explicit significance labels ("statistically significant at α=0.05") and write the `CorrelationResult` record to `data/results/correlation_results.json` per `contracts/correlation_result.schema.yaml`. Verification: `pytest code/tests/test_correlation.py` verifies that synthetic subjects with known r≈0.6 yield permutation p < 0.05, LMM fixed‑effect significance, and r > 0.5.

- [ ] T007 [P] [US3] Run robustness and sensitivity suite in `code/src/validation/sensitivity.py`: (a) recompute drift rates under Pearson, Cosine, and Mahalanobis metrics and report variance in `b` across the three; (b) sweep unit‑stability thresholds **both** `{0.70, 0.80, 0.90}` (spec independent test) **and** `{0.75, 0.80, 0.85}` (scenario) and record number of included units and drift rate change; (c) perform split‑half reliability check correlating drift rates from two random halves of the units. Produce a **full** results file `data/results/full_results.json` that conforms to `output_schema.schema.yaml` (includes per‑subject `drift_rate`, `learning_speed`, `correlation_results`, and `robustness` block). Verification: `pytest code/tests/test_sensitivity.py` asserts sign consistency of the drift–learning correlation across metrics and thresholds.

- [ ] T008 [P] [US1] Generate study figures in `code/src/utils/plots.py` directly from the validated outputs: (a) RDM heatmaps and fitted drift trajectories per subject (`figures/fig_rdm_drift_{subject_id}.png` for 3 representative subjects); (b) drift‑rate vs learning‑speed scatter with fitted LMM trend (`figures/fig_drift_learning_scatter.png`); (c) threshold‑sweep plot showing included units and drift rate vs threshold (`figures/fig_sensitivity_thresholds.png`); (d) split‑half reliability plot (`figures/fig_splithalf.png`). Write all figures to `docs/paper/figures/` as required by Phase 4 deliverable. Verification: each figure file exists after re‑running `python -m code.src.main --stage figures`.

- [ ] T009 [P] [US1] Run the performance benchmark (SC‑005, FR‑010): add `code/src/validation/benchmark.py` that executes the full pipeline on the complete 20‑subject dataset, measures wall‑clock time and peak memory (assert ≤7 GB, <6 h), checks that no GPU‑dependent libraries are imported, and verifies Docker container image size ≤2 GB (via task T014). Record `passed`, `runtime_seconds`, `peak_memory_gb`, `container_size_mb`, and `power_warning` (True if N < 15) in `data/results/performance_benchmark.json`. Verification: the JSON records actual measured values and passes all thresholds.

- [ ] T010 [P] Write the methods and results account to `specs/001-quantify-neural-drift/research.md` (or `paper/results.md` if occupied): link every reported number to the exact rows in `data/results/*.json` and `data/results/lmm_summary.csv`, and to the figure files in `docs/paper/figures/`; state the synthetic‑generator design, the seeded ground truth, actual SC‑001 recovery errors, actual correlation r and p‑values, sensitivity outcomes, and honest limitations (simulation‑based evidence, N=20, power framing). Verification: every claim in the document cites an existing artifact path whose value matches.

- [ ] T011 [P] Re‑run the documented workflow from its declared inputs and document the paper‑stage handoff: delete `data/results/` and `data/processed/`, re‑run `python -m code.src.main --stage all` per `quickstart.md`, confirm all `pytest code/tests/` pass and the regenerated artifacts match the previously reported values (seeded determinism), and append a "Paper‑stage handoff" section to `quickstart.md` listing the result tables, figures, and open questions (including the non‑linear‑vs‑linear model comparison result from the spec's model‑validity assumption) that the paper pipeline must carry forward. Verification: full re‑run reproduces identical `drift_results.json` and `correlation_results.json` (up to JSON key order).

## Additional Coverage Tasks

- [ ] T012 [P] [US1] Implement `src/models/schemas.py` containing Pydantic wrappers for all contracts (`input_schema`, `neural_population`, `rdm_schema`, `drift_result`, `correlation_result`, `output_schema`). Verification: `pytest code/tests/test_schemas.py` passes.

- [ ] T013 [P] [US1] Imputation sensitivity analysis: re‑run drift computation with (a) linear interpolation (default) and (b) mean‑imputation of missing behavioral logs; compare drift rates and record impact. Output to `data/results/imputation_sensitivity.json`. (covers FR‑009 sensitivity)

- [ ] T014 [P] [US1] Verify Docker container size ≤2 GB. Build the container and record its size in `data/results/container_size.json`. Verification: size ≤2 GB.

- [ ] T015 [P] [US1] Store exponential drift fit results in `data/results/drift_exponential_results.json` with fields `subject_id`, `drift_rate_b`, `intercept_a`, `r_squared`, `model_type:"exponential"`, `standard_error`. No schema validation required (secondary artifact).

- [ ] T016 [P] [US1] Implement distance metrics in `code/src/utils/metrics.py` (Pearson, Cosine, Mahalanobis) as a separate module. Verification: unit tests in `code/tests/test_metrics.py`.

- [ ] T017 [P] [US1] Reconcile duplicate NeuralPopulationMatrix schemas: adopt `neural_population.schema.yaml` as canonical, deprecate `neural-population.schema.yaml`. Update validation code to use the chosen schema. Verification: schema validation passes; dead schema ignored.

- [ ] T018 [P] [US1] Apply documented offset correction between behavioral timestamps and neural 20 ms bins; store offset value in `data/processed/offset_correction.json`. Verification: offset value recorded and used in downstream analysis.

- [ ] T019 [P] [US1] Ingest real electrophysiology and behavioral data (e.g., OpenNeuro ds004xxx). Download raw `.nwb` files, verify with Kilosort2 (CPU‑compatible stub) or accept pre‑sorted data. Validate presence of required variables; raise clear `RuntimeError` if missing. Output raw validated files under `data/raw/real/`. Verification: `pytest code/tests/test_real_ingest.py`.

- [ ] T020 [P] [US1] Document model selection: generate `specs/001-quantify-neural-representation-drift/model_decision.md` explaining the conflict between linear (spec) and exponential (constitution) primary metrics and stating which will be used for each downstream analysis. (plan‑root cause; flagged for kickback)

- [ ] T021-A [P] Resolve Conflict‑Resolution sub‑task A: ensure both linear and exponential fits are computed for each subject (covered by T004 and T015). Verification: both result files exist.

- [ ] T021-B [P] Resolve Conflict‑Resolution sub‑task B: set `config.primary_model` based on `model_decision.md`. Verification: config flag matches documented choice.

- [ ] T021-C [P] Resolve Conflict‑Resolution sub‑task C: update downstream tasks (T006, T007) to read the primary model as per config. Verification: tasks reference config.

- [ ] T022 [P] [US1] Align enum values for non‑drifting flag across contracts: generate `code/src/utils/enum_adapter.py` that translates `"constant"` to `"non_drifting"` where needed, and update validation code to accept both. Verification: schema validation passes for both contracts.

## Dependencies

- T002, T003 → T001  
- T004 → T002, T003, T016  
- T005 → T002  
- T006 → T004, T005  
- T007 → T006, T004, T013  
- T008 → T006, T007  
- T009 → T006, T008, T014  
- T010 → T009  
- T011 → T010  
- T012 → (none) – used by all validation tasks  
- T013 → T004  
- T014 → (none)  
- T015 → T004  
- T016 → (none) – used by T004  
- T017 → (none) – used by T003 validation  
- T018 → T003  
- T019 → (none) – satisfies FR‑001 & Constitution VI  
- T020 → (none) – documentation only  
- T021‑A → T004, T015  
- T021‑B → T020  
- T021‑C → T006, T007  
- T022 → (none) – used by drift‑result validation
