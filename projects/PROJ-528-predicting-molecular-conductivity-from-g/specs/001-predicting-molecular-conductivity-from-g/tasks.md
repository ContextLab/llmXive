# Tasks: Predicting Molecular Conductivity from Graph-Based Features

**Input**: Design documents from `/specs/001-predict-molecular-conductivity-from-g/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Status**: The foundation, descriptor computation (US1), model training and sensitivity analysis (US2), and most of the analysis/plotting work (US3) are implemented and verified. Remaining work consolidates the four open items: final model-results aggregation, permutation feature importance, contract validation, and run‑book reconciliation, followed by the paper handoff.

## Verified completed work (preserve as‑is)

The following requirements are implemented and independently verified; do not redo them:

- [ ] T001–T009 Project structure, pinned `code/requirements.txt`, config (`SEED=42`, `OUTLIER_SIGMA=3.0`, `VIF_THRESHOLD=10.0`, `SENSITIVITY_THRESHOLDS=[2.5,3.0,3.5]`, `CONFIDENCE_INTERVAL_TARGET=0.95`), validators with `--validate` CLI, scaffold splitting, contracts, and data loader (`code/data_loader.py`).
- [x] T010–T012, T023–T025, T034–T036 Unit tests for descriptors (benzene aromaticity, butadiene conjugation, mixed hybridization), scaffold leakage, log transform, outlier filter, VIF, BH correction, and plot generation (`tests/`).
- [x] T013–T019c, T026, T061_RDKit–T063_RDKit Data loading, target‑variable validation with strict halt when neither conductivity nor HOMO‑LUMO gap is available (no self‑consistency fallback), quantum proxy report, full RDKit descriptor set (degree/path statistics, aromaticity, conjugation, ring counts, bond order/length, electronegativity polarity terms), NaN filtering, and `data/processed/descriptors.csv` (FR‑001, FR‑008, FR‑011, FR‑012, FR‑014).
- [x] T027–T032b-3, T032a Scaffold split, log‑transform, RF/GB training, 5‑fold CV, outlier sensitivity sweep over {2.5σ, 3.0σ, 3.5σ} with variance recording in `data/processed/sensitivity_analysis.json` (FR‑002, FR‑003, FR‑004, FR‑007).
- [x] T039a, T039b, T039c‑3 VIF identification, exclusion (VIF > 10), retraining on reduced feature set, iteration log and intermediate model versioning (FR‑013).
- [x] T040b, T041, T042, T043, T045, T044, T057, T064, T064b Feature‑importance robustness, Pearson correlations, Benjamini‑Hochberg FDR correction, correlation plots with 95 % CIs (`corr_plot_top5.png`, `corr_plot_resonance.png`), analysis summary, bootstrap CI‑coverage report, resonance‑descriptor integration and augmented sensitivity re‑run (FR‑005, FR‑006, SC‑002, SC‑003).
- [x] T046, T047, T049‑1–T049‑4, T051 Documentation updates, lint cleanup, integration tests with runtime checks, quickstart execution in fresh virtualenv (FR‑009, FR‑010).

## Phase 1: Repair rejected artifacts and finalize results

- [ ] T100 [US1/US2] **Empirical target‑proxy fallback**  
  Implement `code/target_proxy.py` that computes a topological proxy for conductivity when both measured conductivity and HOMO‑LUMO gap are missing (e.g., linear combination of aromatic_ring_count and conjugation_path_length). The pipeline must invoke this fallback automatically, log a warning, and set `target_type` to `topological_proxy`.  
  **Verification**: Run the pipeline on a dataset lacking conductivity; assert `data/processed/descriptors.csv` contains a non‑null `log_conductivity` column and `quantum_proxy_report.json` records `fallback_used: true`.  
  Depends on T013–T019c.

- [ ] T101 [US2/US3] **Finalize model results aggregation (runs‑array)**  
  Create/update `data/processed/model_output.json` conforming to `contracts/model_output_schema.yaml`. The file must contain a top‑level `runs` array; each entry includes `run_id`, `model_type`, `r2_test`, `mae_test`, `r2_cv_mean`, `r2_cv_std`, `outlier_threshold`, `target_type`, and `vif_excluded_features`.  
  **Verification**: `python -c "import json, jsonschema, pathlib; schema=json.load(open('contracts/model_output_schema.yaml')); data=json.load(open('data/processed/model_output.json')); jsonschema.validate(data, schema)"` exits 0.  
  Depends on T032b‑3, T039c‑3, T064b.

- [ ] T102 [US3] **Implement permutation feature importance**  
  Add `permutation_feature_importance(model, X, y)` to `code/analysis.py` using `sklearn.inspection.permutation_importance` (`n_repeats=10`, `random_state=SEED`). Write ranked list to `data/processed/feature_importance.csv` with columns `['feature', 'importance_score']`, sorted descending, covering all retained features from the final VIF‑filtered model.  
  **Verification**: Assert file exists, has required columns, row count equals number of retained features, and all scores are finite.  
  Depends on T039c‑3.

- [ ] T103 [US1/US2/US3] **Contract validation of all result artifacts**  
  Execute `code/validators.py --validate <file> --schema <schema>` for each artifact:  
  - `data/processed/descriptors.csv` vs `contracts/descriptor_schema.schema.yaml`  
  - `data/processed/model_output.json` vs `contracts/model_output_schema.yaml`  
  - `data/processed/feature_vif_report.json` vs `contracts/feature_schema.yaml`  
  - `data/processed/analysis_summary.json` vs `contracts/analysis_summary_schema.yaml` (new schema)  
  - `data/processed/sensitivity_analysis.json` vs `contracts/sensitivity_schema.schema.yaml`  
  Record commands and exit codes in `docs/validation_results.md`.  
  **Verification**: All validator invocations exit 0.  
  Depends on T101, T102, T108.

- [ ] T104 **Run‑book reconciliation and paper handoff**  
  Create `code/main.py` orchestrating the full pipeline in correct order (data loading → target validation/fallback → descriptor computation → VIF filtering → scaffold split → training → sensitivity analysis → permutation importance → feature/VIF report → plots). Update `docs/quickstart.md` and `plan.md` to reflect the single reproducible command `python -m code.main`.  
  **Verification**: Running the documented command on a clean runner reproduces every artifact listed in T103 without errors.

- [ ] T105 **Write concise methods/results account** (`docs/results_summary.md`)  
  Summarize: final R²/MAE/CV for both models, target type used, VIF‑excluded features, BH‑adjusted p‑values, family‑wise error rate (α=0.05) from T107, sensitivity‑analysis R² variance, CI‑coverage, and resonance‑descriptor plot references. All numbers must be traceable to files produced by earlier tasks.  
  **Verification**: Each cited number matches a value extracted from the corresponding JSON/CSV artifact.

- [ ] T106 **Full re‑run and paper‑stage handoff** (`docs/paper_handoff.md`)  
  Re‑execute the quickstart workflow in a fresh environment, confirm all unit tests and T103 validations pass within the 6‑hour CPU budget, and compile the handoff document listing figures, result tables, limitation statements, and future‑work note on Hückel‑energy analysis.  
  **Verification**: End‑to‑end run completes, logs runtime <6 h, and all checks exit 0.

- [ ] T107 [SC‑004] **Family‑wise error rate measurement**  
  After BH correction, compute the proportion of features with adjusted p‑value < 0.05 (the family‑wise error rate). Write the scalar to `data/processed/fwer_report.json` (`{"alpha":0.05,"fwer":0.XX}`) and include it in `docs/results_summary.md`.  
  **Verification**: Assert the JSON file exists and `0 <= fwer <= 1`.

- [ ] T108 [US3] **Feature/VIF JSON report**  
  Generate `data/processed/feature_vif_report.json` conforming to `contracts/feature_schema.yaml`. For each retained descriptor include `feature_name`, `importance_score` (from permutation importance), `vif_score` (per‑feature VIF), and `is_excluded` flag. Add a `summary` block with total, excluded counts, and max VIF.  
  **Verification**: Schema validation succeeds; number of entries equals number of retained features.

- [ ] T109 [SC‑001/SC‑009] **Circularity (residual‑variance) check**  
  Implement `code/circularity_check.py` that fits a linear model of the target against all retained descriptors and computes the variance explained by the model versus a null model. If R² > 0.95, abort with a clear error indicating circularity. Record the check result in `data/processed/circularity_check.json`.  
  **Verification**: Pipeline aborts when condition met; otherwise JSON contains `"passed": true`.

## Phase 2: Validation of all artifacts against contracts
*(merged into T103 above; retained for clarity)*

## Phase 3: Run‑book reconciliation and paper handoff
*(merged into T104 and T106 above)*

## Dependencies and requirement coverage

| Requirement | Task(s) | Evidence |
|---|---|---|
| FR‑001, FR‑008, FR‑014 | T013–T019c, T100 | `data/processed/descriptors.csv`, `quantum_proxy_report.json` |
| FR‑002 | T027, T032a | `tests/test_scaffold_split.py` |
| FR‑003, FR‑004, FR‑011, FR‑012 | T026–T030 | training logs, CV metrics |
| FR‑007 | T031–T032b‑3, T064b | `sensitivity_analysis.json`, `sensitivity_analysis_augmented.json` |
| FR‑005, FR‑006, SC‑002, SC‑003 | T041–T045, T057, T102, T107 | `feature_importance.csv`, plots, `fwer_report.json` |
| FR‑013, SC‑007, SC‑008 | T039a–T039c‑3, T108 | `feature_vif_report.json` |
| FR‑009, FR‑010, SC‑005 | T049‑x, T051, T106 | runtime logs, clean re‑run |
| SC‑001, SC‑009 | T109 | `circularity_check.json` |
| SC‑004 | T107 | `fwer_report.json` |

Execution order (automated by `code/main.py`): T100 → T101 → T102 → T108 → T107 → T109 → T103 → T104 → T105 → T106. All other previously checked tasks remain unchanged.  
