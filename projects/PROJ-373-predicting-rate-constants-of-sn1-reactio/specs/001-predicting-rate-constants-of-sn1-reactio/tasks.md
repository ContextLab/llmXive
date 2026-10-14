# Tasks: Predicting Rate Constants of SN1 Reactions from Molecular Structure

**Inputs**: `specs/001-predict-sn1-rate-constants/spec.md`, `plan.md`, `data-model.md`, `contracts/`
**Branch**: `001-predict-sn1-rate-constants`

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T011a_Gate [US1] **REDO (verifier‑rejected; consolidates T011a/T011c/T011d/T011e)**: Implement and execute `code/data/atomic_gate.py` performing ALL FR‑009 validations and download in one script.   <!-- FAILED-IN-EXECUTION: code/data/atomic_gate.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/atomic_gate.py exit=1 -->
  **File**: `code/data/atomic_gate.py`  
  **Verification**: Generates `data/raw/sn1_raw_merged.parquet`, `data/processed/exclusion_raw.log`, `data/processed/.pipeline_status`; aborts with `ABORTED` on missing metadata.

- [ ] T016 [US1] **Distribution‑Shift Check**: After merging datasets in T011a_Gate, run `code/data/distribution_shift.py` to compare temperature and solvent distributions, flagging rows with outliers (> 3 σ) or solvents absent from both sources. Excludes flagged rows, logs reasons `distribution_shift` to `exclusion_raw.log`.  
  **File**: `code/data/distribution_shift.py`  
  **Verification**: `distribution_shift_report.json` records excluded row count and criteria.

- [ ] T600 [US1] **REDO (verifier‑rejected)**: Complete `tests/unit/test_download_failure.py` to verify the no‑fallback guarantee of T011a_Gate.  
  **File**: `tests/unit/test_download_failure.py`  
  **Verification**: Asserts exit code 1, absence of any `synthetic_*` files, and correct `ABORTED` status/log.

- [ ] T012 [US1] **REDO (verifier‑rejected)**: Implement and execute `code/data/clean.py` on the merged Parquet.  
  **File**: `code/data/clean.py`  
  **Logic**: Uses only schema‑allowed exclusion reason codes (`primary_substrate`, `canonicalization_error`, `gasteiger_convergence_error`, `invalid_smiles`, `missing_substrate_class`, `unit_conversion_error`, `invalid_substrate_label`, `distribution_shift`). Writes `data/processed/cleaned_intermediate.csv` and appends to `exclusion_raw.log`.  
  **Verification**: Output has no primary rows, no nulls, and exclusion log validates against `exclusion_report.schema.yaml`.

- [ ] T013 [US1] **REDO (verifier‑rejected)**: Implement and execute `code/data/descriptors.py` computing Gasteiger charges and topological indices (CPU‑only).  
  **File**: `code/data/descriptors.py`  
  **Logic**: On Gasteiger convergence failure logs `gasteiger_convergence_error` (allowed code) and excludes the row. Produces `data/processed/descriptors.csv`.  
  **Verification**: ≥95 % of input rows survive; all exclusions appear in log with allowed codes.

- [ ] T015 [US1] **REDO (verifier‑rejected)**: Implement and execute `code/data/exclusion_report.py` to aggregate, map, and validate exclusion logs.  
  **File**: `code/data/exclusion_report.py`  
  **Logic**: Maps all logged reasons to the extended allowed set (see T999b) and validates each row against `contracts/exclusion_report.schema.yaml`. Writes `exclusion_mapped.json`, `exclusion_report.csv`, and `success_rate.json` (PASS/FAIL based on ≥0.95 retained).  
  **Verification**: Files exist and pass schema validation.

- [ ] T014 [US1] **Stratified Split**: Implement `code/data/split.py` to create 70/15/15 train/val/test splits stratified by `substrate_class`.  
  **File**: `code/data/split.py`  
  **Verification**: `split_report.json` shows per‑class proportions within 5 % variance; splits are non‑overlapping. Note: This split is used for baseline training and quick sanity checks; the final held‑out evaluation for SC‑001 relies on the outer‑fold test sets generated in T022a.

- [ ] T019 **Preserved Artifact – Training CLI**: `code/train.py` provides a CLI `python -m code.train --config <path> --max-runtime <seconds>` that trains the MPNN (or baselines) and respects the runtime limit.  
  **File**: `code/train.py`

- [ ] T020 **Preserved Artifact – Evaluation CLI**: `code/evaluate.py` offers `python -m code.evaluate --model <path> --split <train|val|test>` for inference and metric calculation.  
  **File**: `code/evaluate.py`

- [ ] T021 **Preserved Artifact – MPNN Architecture**: `code/models/MPNN.py` defines the Message Passing Neural Network used throughout the project.  
  **File**: `code/models/MPNN.py`

- [ ] T024 **Preserved Artifact – Collinearity Unit Test**: `tests/unit/test_collinearity.py` validates VIF computation against known small examples.  
  **File**: `tests/unit/test_collinearity.py`

## Phase 2: Complete the study and validate its evidence

- [ ] T022a [US2] **Nested CV – Outer Scaffold Splits**: Generate `data/processed/outer_folds.json` with 5 scaffold‑based outer folds.  
  **File**: `code/modeling/outer_folds.py`  
  **Verification**: JSON contains non‑overlapping train/validation indices per fold.

- [ ] T022b [US2] **Nested CV – Inner Random Search**: For each outer fold, run a 5‑fold inner CV (≤50 random configs) and record results in `artifacts/hyperparameter_search.csv`.  
  **File**: `code/modeling/inner_search.py`  
  **Verification**: CSV columns `config_id,learning_rate,hidden_dim,dropout,r2_val,mae_val`.

- [ ] T022c [US2] **Baseline Training (Random, Linear, KRR)**: Train Random, Linear Regression, and **Kernel Ridge Regression (KRR)** baselines on each outer‑fold training split using the same descriptor set. Store metrics in `artifacts/baseline_metrics.csv`.  
  **File**: `code/modeling/baselines.py`  
  **Verification**: CSV includes `model_type` values `random`, `linear`, `krr`.

- [ ] T022d [US2] **Bootstrap Comparison & SC‑001 Status**: Perform 1000 bootstrap resamples (seed = 42) comparing MPNN vs each baseline on R² and MAE, apply Holm‑Bonferroni correction, and write `artifacts/sc-001_status.json`.  
  **File**: `code/modeling/bootstrap_compare.py`  
  **Verification**: JSON conforms to amended `model_output.schema.yaml` and contains `delta_r2`, `p_value`, `status`.

- [ ] T999a **Schema Amendment – Add KRR Baseline**: Extend `contracts/model_output.schema.yaml` to (a) add `"KRR"` to the `model_type` enum, (b) add a `krr` object under `baselines` with required `r2` and `mae`.  
  **File**: `specs/001-predicting-rate-constants-of-sn1-reactio/contracts/model_output.schema.yaml`

- [ ] T022 [US2] **Orchestrate Modeling Stage**: Run T022a → T022b → T022c → T022d sequentially. Save best MPNN weights to `artifacts/best_model.pt` and overall metrics to `artifacts/metrics.json` (conforming to amended schema).  
  **File**: `code/modeling/run_pipeline.py`  
  **Verification**: All downstream artifacts exist; `metrics.json` validates.

- [ ] T602 [US2] **Timeout Mechanism Test**: Complete `tests/integration/test_timeout_mechanism.py` verifying that `code/train.py` respects `--max-runtime`.  
  **File**: `tests/integration/test_timeout_mechanism.py`  
  **Verification**: Test passes; `artifacts/feasibility_test_log.json` records timeout status.

- [ ] T028 [US3] **Collinearity Diagnostic**: Implement `code/analysis/collinearity.py` (FR‑007). Excludes Gasteiger charges, computes VIF for all cross‑class descriptor pairs, flags VIF > 5, writes `artifacts/collinear_report.json`.  
  **File**: `code/analysis/collinearity.py`  
  **Verification**: JSON validates against `contracts/collinear.schema.yaml`; unit test `tests/unit/test_collinearity.py` passes.

- [ ] T026 [US3] **SHAP Attributions**: Execute `code/analysis/interpret.py` on the best model to produce SHAP values, then `code/analysis/aggregate_shap.py` to obtain top‑10 atoms. Save `artifacts/node_shap_values.npy`, `node_to_atom_mapping.json`, `top_k_atoms.json`, and a summary plot.  
  **Files**: `code/analysis/interpret.py`, `code/analysis/aggregate_shap.py`  
  **Verification**: Plot and JSON/NPY exist; generated text contains no causal language.

- [ ] T029A [US3] **Descriptor Sensitivity Sweep**: Rank descriptors by absolute SHAP magnitude. For k = 1 .. 10, remove the top‑k descriptors, retrain MPNN using the full Nested CV pipeline, and record metrics in `artifacts/sensitivity_k{N}_metrics.json`. Compile results into `artifacts/descriptor_sensitivity_report.csv` and compute variance of R². **No fallback to a subset is permitted**; if runtime exceeds the 5.5 h budget the task fails and flags SC‑003 as unmet.  
  **File**: `code/analysis/sensitivity_sweep.py`  
  **Verification**: Variance < 0.01 recorded; all per‑k metric files exist.

- [ ] T029B [US3] **Atom Perturbation Study**: Implement `code/analysis/atom_perturbation.py` to zero features of top‑k atoms (from `top_k_atoms.json`) in the test split, re‑run inference via `code/evaluate.py`, and report R² drop in `artifacts/atom_perturbation_report.md`.  
  **File**: `code/analysis/atom_perturbation.py`  
  **Verification**: Report contains pre/post R² and references the atom list.

- [ ] T035A [US3] **SHAP Consistency Across Seeds**: Implement `code/analysis/multi_seed_runner.py`. Retrains MPNN across seeds `[42,1,2,3,4]`, generates per‑seed SHAP values, runs `code/analysis/consistency.py` to compute average Spearman rank correlation (PASS ≥ 0.8) and measures R² drop when top‑10 SHAP atoms are removed (PASS ≥ 0.02). Writes `artifacts/shap_consistency_report.md`.  
  **File**: `code/analysis/multi_seed_runner.py`  
  **Verification**: Report lists seeds, both PASS/FAIL decisions.

- [ ] T039 [US3] **Final Comprehensive Report & Combined Output**: Generate `artifacts/final_report.md` aggregating all real outputs and produce `artifacts/combined_output.json` conforming to `contracts/output.schema.yaml`. Includes PASS/FAIL for SC‑001 through SC‑005 using thresholds defined in earlier tasks.  
  **File**: `code/reporting/generate_final_report.py`  
  **Verification**: `combined_output.json` validates; markdown references only real artifact sources; no causal language.

## Phase 3: Reproducible results and paper handoff

- [ ] T040 **End‑to‑End Validation Run**: Implement missing orchestration in `code/main.py` to wire ingestion, descriptor computation, splitting, modeling (Nested CV, baselines, bootstrap), interpretability (SHAP, sensitivity, perturbation, collinearity, consistency), and final report generation. Enforce `--max-runtime` for all training runs; on timeout write `artifacts/feasibility_test_log.json` with `status: 'TIMEOUT'` and actual runtime, then exit gracefully. On success record total runtime and set SC‑002 PASS/FAIL (runtime ≤ 6 h). Verify that **all** downstream artifacts (`metrics.json`, `combined_output.json`, etc.) exist after the run.  
  **File**: `code/main.py` (updated orchestration)  
  **Verification**: Log contains measured runtime and SC‑002 status; all required artifacts are present.

- [ ] T999d **Documentation of Prior Artifacts**: Record that the following previously‑implemented artifacts are available for downstream tasks: `code/train.py`, `code/evaluate.py`, `code/models/MPNN.py`, `tests/unit/test_collinearity.py`. This satisfies ordering/executability concerns for T022, T602, and T028.  
  **File**: `docs/legacy_artifacts.md`

- [ ] T999b **Schema Amendment – Extend Exclusion Report Reason Codes**: Update `contracts/exclusion_report.schema.yaml` to include the full set of reason codes used throughout the pipeline (`primary_substrate`, `canonicalization_error`, `gasteiger_convergence_error`, `invalid_smiles`, `missing_substrate_class`, `unit_conversion_error`, `invalid_substrate_label`, `distribution_shift`, `ambiguous_structure`, `ambiguous_stereochemistry`, `descriptor_failure`).  
  **File**: `specs/001-predicting-rate-constants-of-sn1-reactio/contracts/exclusion_report.schema.yaml`

- [ ] T999c **Standardize Reason Codes in Cleaning & Mapping**: Modify T012, T013, and T015 to emit and map only the codes listed in the amended schema (see T999b), guaranteeing schema compliance.  
  **Files Modified**: `code/data/clean.py`, `code/data/descriptors.py`, `code/data/exclusion_report.py`

- [ ] T999f **Constitution Amendment – Waiver for Principle VII**: Add a formal amendment to the constitution granting a waiver for the exclusion of NIST/Reaxys/UCI datasets, documenting the justification and linking to the plan’s rationale.  
  **File**: `constitution/waiver_principle_VII.md`
