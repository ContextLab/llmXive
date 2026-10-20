# Tasks: Structural topology as a predictor of GUI policy transferability (simulation‑scoped pipeline validation)

**Inputs**: `specs/001-llmxive-follow-up-extending-ui-mopd-mult/spec.md`, `plan.md`, `data-model.md`, `contracts/structural_record.schema.yaml`. The plan flags a spec‑scope mismatch (no verifiable open source of Uni‑GUI logs); this study executes the plan's clearly‑labeled **simulation study** that validates the analysis pipeline end‑to‑end. All results are reported as applying to the simulated setting only, with anti‑circularity controls (noise‑calibration sweep, shuffled‑label null, uninformative‑feature control).

## Task format and paths

Use `- [ ] T### [P?] [USx?] description with exact artifact paths`. Paths are relative to the project directory. Code lives under `code/`, tests under `code/tests/`, results under `data/results/`, figures under `figures/`.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [P] [US1] Generate a seeded synthetic structural‑record dataset `code/src/generate/synthetic_dataset.py` producing `data/raw/structural_records_raw.csv` (N = 10 000 records conforming to `specs/.../contracts/structural_record.schema.yaml`). The generator writes only the required columns; a separate control file `data/derived/noise_feature.csv` holds the random noise feature. Command: `python -m code.src.generate.synthetic_dataset --n 10000 --seed 42`.
  - Requirement: FR‑001 (simulated analog), FR‑008, SC‑000.

- [ ] T016 [ ] [US1] Implement the structural extractor `code/src/extract/structural_extractor.py` applying FR‑008 cleaning rules (flag/exclude missing data, truncate navigation‑graph cycles at depth 10, set `structural_ambiguity` when identical topology maps to divergent outcomes). Write the cleaned dataset to the canonical `data/derived/structural_records.csv`. Verification: `code/tests/unit/test_extractor.py` asserts schema conformance, ≥ 95 % non‑null predictor fields, N ≥ 10 000, deterministic checksum, and no synthetic‑fallback path. Requirement: FR‑001 (simulated analog), FR‑008, SC‑000.

- [ ] T017 [ ] [US1] Document the runnable command and usage in `specs/001-llmxive-follow-up-extending-ui-mopd-mult/quickstart.md`. Verification: test script checks the file exists and contains the exact command from T001. Requirement: reproducibility.

- [ ] T002 [ ] [US2] Implement the lightweight CPU adapter training in `code/src/model/train.py` with two backends: a small feature‑based linear model (`code/src/model/adapter_linear.py`) and a small GNN (`code/src/model/adapter_gnn.py`). The trainer depends on the cleaned dataset `data/derived/structural_records.csv`. Select backend via `--backend`; automatically fall back to the linear model when memory usage would exceed 7 GB (FR‑008/FR‑002 fallback). Use a stratified 60/20/20 split (seed 42), one‑hot encode `platform_id`, and run on CPU‑only torch. Verification: `code/tests/unit/test_training.py` asserts convergence on a small subset, writes model artifact to `data/artifacts/adapter_<backend>.pt`, and produces per‑split metrics JSON `data/results/training_metrics.json` containing AUC‑ROC, Brier score, and R². Command: `python -m code.src.model.train --backend linear`.

- [ ] T003 [ ] [US2] Run the first end‑to‑end analysis: train the linear adapter on the full cleaned dataset at the mid‑noise level and produce result rows in `data/results/first_e2e_metrics.json` (AUC‑ROC, Brier, R², n_train/n_val/n_test, **runtime_seconds**) plus a calibration figure `figures/first_e2e_calibration.png`. Verification: the command must complete within the 6‑hour CI limit; `first_e2e_metrics.json` must contain non‑null fields, AUC ∈ [0,1], Brier ∈ [0,1], and `runtime_seconds` ≤ 21600. Command: `python -m code.src.model.train --backend linear --tag first_e2e`.

## Phase 2: Complete the study and validate its evidence

- [ ] T004 [ ] [US2] Implement and run the noise‑calibration sweep and null controls in `code/src/evaluate/calibration.py`: sweep label‑noise ε so the Bayes‑optimal AUC spans ≈ 0.55–0.85 (report the ε grid and achieved Bayes‑optimal AUC per level); at each level train the adapter and report AUC‑ROC/Brier/R² **alongside** a shuffled‑label null control (labels permuted). Emit `data/results/noise_sweep.csv` (columns: epsilon, bayes_optimal_auc, adapter_auc, null_auc, adapter_brier, null_brier, adapter_r2) and `figures/noise_sweep.png`. Report regimes where the absolute FR‑002 thresholds (AUC‑ROC ≥ 0.80, Brier ≤ 0.20) are met or not. Verification: `code/tests/unit/test_evaluation.py` asserts the null control's AUC ≈ 0.5 (±0.05) and that ≥ 5 noise levels are covered. Requirement: FR‑002 (reporting), SC‑001.

- [ ] T005 [ ] [US2] Implement feature‑importance analysis in `code/src/evaluate/feature_importance.py`: compute SHAP (KernelExplainer) and permutation importance for the three topology features **plus the random control feature**, apply Bonferroni correction across tested features (FR‑007); compute Spearman rank correlation between SHAP and permutation rankings (target ≥ 0.8, SC‑004); verify the control feature’s importance is near zero. Emit `data/results/feature_importance.csv` (feature, shap_mean_abs, perm_mean_abs, bonferroni_p, corrected_significant) and `figures/feature_importance.png`. Requirement: FR‑003, FR‑007, SC‑004. Command: `python -m code.src.evaluate.feature_importance`.

- [ ] T006 [ ] [US2] Implement and run the sensitivity analysis in `code/src/evaluate/sensitivity.py`: sweep depth ∈ {3,4,5}, branching_factor ∈ {1.0,1.5,2.0}, graph_connectivity ∈ {0.3,0.5,0.7} (FR‑006), reporting the model’s predicted success probability and the variance of overall predicted success rates across each sweep; report the variance of overall success rates across the depth sweep (target ≤ 0.02, SC‑006). Emit `data/results/sensitivity_sweep.csv` and `figures/sensitivity_sweep.png`. Requirement: FR‑006, SC‑006. Command: `python -m code.src.evaluate.sensitivity`.

- [ ] T007 [ ] [US3] Implement policy‑head simulation and benchmarking in `code/src/evaluate/benchmark.py`: generate simulated policy heads under `data/artifacts/policy_heads/` (manifest with `head_id`, `platform_id`, `artifact_path`, `checksum` validated against the newly added `contracts/policy_head.schema.yaml`). Run adapter‑driven head selection on the held‑out test set using only structural input (FR‑004). Log per‑record inference latency (ms), peak RSS memory (MB), and task success to `data/results/adapter_output.csv` matching the `AdapterModelOutput` entity (validated against `contracts/adapter_output.schema.yaml`). Compute a simulated heavy UI‑MOPD baseline for the same test set and report latency/memory ratio (target ≤ 1/5 baseline latency, SC‑002) and success‑rate tolerance (target within 5 %, SC‑003). Verification: `code/tests/unit/test_evaluation.py` asserts CSV schema compliance, non‑null latency/memory fields, and that ratio statistics are derived from measured values. Requirement: FR‑004, FR‑005, SC‑002, SC‑003. Command: `python -m code.src.evaluate.benchmark`.

- [ ] T008 [ ] [US3] Implement statistical comparison in `code/src/evaluate/statistical_tests.py`: perform McNemar’s test on paired binary task‑success outcomes (adapter vs simulated baseline) (SC‑005); report exact p‑value, test statistic, and conclusion relative to the 5 % tolerance. Emit `data/results/mcnemar_test.json`. Requirement: FR‑005, SC‑005. Command: `python -m code.src.evaluate.statistical_tests`. Depends on T007’s `adapter_output.csv`.

- [ ] T009 [ ] [US3] Implement FR‑009 synthetic‑variation evaluation in `code/src/evaluate/variations.py`: evaluate the trained adapter on synthetic variations of the navigation graphs (shuffled widget order, altered screen resolution) derived from the held‑out test set; report degradation in AUC/Brier relative to the original test set (target ≤ 5 % relative degradation, SC‑007); flag any excess degradation. Emit `data/results/variation_evaluation.csv` and `figures/variation_degradation.png`. Requirement: FR‑009, SC‑007. Command: `python -m code.src.evaluate.variations`.

- [ ] T010 [ ] Consolidate the full result set into the study’s summary tables and figures directly from the validated outputs: `data/results/summary_metrics.csv` aggregating noise‑sweep, importance, sensitivity, benchmark, McNemar, and variation results, and `figures/` containing all generated figures. Verification: every table row and figure must trace to an existing result file produced by T003–T009 (single source of truth); no hand‑entered values. Command: `python -m code.src.evaluate.summarize`.

- [ ] T011 [ ] Write `research.md` (the feature’s research notes) summarising methods and results, explicitly noting the **simulation‑only scope**, the anti‑circularity controls, any regimes where FR‑002 thresholds are unmet, and the baseline‑validity caveat for latency/success comparisons. The document must link each mentioned result to a file under `data/results/` and each figure to a file under `figures/`. Verification: a test script checks that every referenced file exists and that all citations are present. Requirement: documentation handoff.

- [ ] T012 [ ] Re‑run the documented workflow end‑to‑end from its declared inputs (seeded generation → extraction → training → all evaluations) via the commands in `specs/.../quickstart.md`; confirm all pytest suites in `code/tests/` pass, artifact checksums are reproducible across two runs, and the required result files exist with non‑null measured values. Document the confirmed paper‑stage handoff (list of result files and figures the paper stage consumes) in `specs/.../research.md`. No script may write to `state/` or `.github/`. Requirement: reproducibility and handoff.

## New Tasks for Missing Artifacts

- [ ] T013 [ ] Conduct the a‑priori power analysis for detecting ΔAUC = 0.05 with three predictors under Bonferroni correction; write the report to `data/results/power_analysis.md`. Verification: a test asserts the document contains the calculated sample size and power estimate.

- [ ] T014 [ ] Author the missing contract files:
  - `specs/001-llmxive-follow-up-extending-ui-mopd-mult/contracts/policy_head.schema.yaml`
  - `specs/001-llmxive-follow-up-extending-ui-mopd-mult/contracts/adapter_output.schema.yaml`
  and add validation steps in T007/T008 to use them. Verification: a test checks that both schema files exist and are valid JSON‑Schema.

- [ ] T015 [ ] Implement utility modules:
  - `code/src/utils/data_io.py` (CSV/Parquet loading helpers)
  - `code/src/utils/logger.py` (standardised logger via `llmxive_toolkit.get_logger`)
  and add unit tests under `code/tests/unit/`. Verification: tests assert the modules load without error and provide the documented functions.

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command |
|---|---|---|
| FR‑001 (simulated analog), FR‑008, SC‑000 | T001, T016 | `python -m code.src.generate.synthetic_dataset --n 10000 --seed 42` |
| FR‑002, FR‑008 fallback, SC‑001 | T002, T003, T004 | `python -m code.src.model.train --backend linear` |
| FR‑003, FR‑007, SC‑004 | T005 | `python -m code.src.evaluate.feature_importance` |
| FR‑006, SC‑006 | T006 | `python -m code.src.evaluate.sensitivity` |
| FR‑004, FR‑005, SC‑002, SC‑003 | T007 | `python -m code.src.evaluate.benchmark` |
| SC‑005 | T008 (after T007) | `python -m code.src.evaluate.statistical_tests` |
| FR‑009, SC‑007 | T009 | `python -m code.src.evaluate.variations` |
| Power‑analysis artifact | T013 | `python -m code.src.evaluate.power_analysis` |
| Schema contracts | T014 | (no command, file creation) |
| Utils modules | T015 | (no command, unit tests) |
| Reproducibility & handoff | T010–T012 | full quickstart re‑run |

Execution order: T001 → T016 → T017 → T002 → T003 → T004–T009 (any order respecting data dependencies) → T010 → T011 → T012. T013, T014, T015 are independent preparatory tasks.