# Tasks: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase‑Change Materials  

**Inputs**: `spec.md`, `plan.md`, data‑model definitions, JSON‑schema contracts, and reviewer feedback.  

The list below follows the canonical checklist format required by the platform.  
Each task specifies the requirement it satisfies, the exact artifact paths that will be produced, and an observable verification step (indented).  Tasks are ordered to respect data flow; later tasks depend on the outputs of earlier ones.

---  

## Phase 1 – Data acquisition (fulfills FR‑001, FR‑008, SC‑006)

- [ ] T001 [P] [US‑1] Stream the Materials Project dataset, filter for entries with melting‑point and heat‑capacity data, and write a parquet file.  
  *Path*: `code/data/fetch_materials.py` → `data/raw/pcm.parquet`  
  *Verification*: Unit test `tests/unit/test_fetch_materials.py` checks that the file exists, contains ≥ 5 000 rows, and that the streaming process never exceeds 7 GB RAM (monitored via `psutil`).

- [ ] T002 [P] [US‑1] Download crystal‑structure CIFs for the compounds in `pcm.parquet` from the Open Materials Database (OMDB) HuggingFace dataset.  
  *Path*: `code/data/fetch_omdb_structures.py` → `data/raw/omdb_structures/` (one CIF per `material_id`).  
  *Verification*: Integration test `tests/integration/test_fetch_omdb.py` confirms that at least 80 % of the material IDs have a corresponding CIF and that the script raises an error (no synthetic fallback) if the remote fetch fails.

- [ ] T003 [P] [US‑1] Retrieve the open NIST PCM dataset, merge it with the Materials Project data, and write a JSON file.  
  *Path*: `code/data/fetch_nist_data.py` → `data/raw/nist_data.json`  
  *Verification*: Contract test `tests/contract/test_nist_schema.py` validates the JSON against `contracts/dataset.schema.yaml` and asserts that the overlap with Materials Project IDs is reported (≥ 100 entries, otherwise a logged fallback flag is set).

---  

## Phase 2 – Feature engineering (fulfills FR‑002, FR‑006, SC‑001)

- [ ] T004 [P] [US‑1] Compute elemental descriptors (average atomic number, electronegativity, radius, etc.) and crystal‑graph features (adjacency matrix, node attributes) for every compound, then merge with thermodynamic columns.  
  *Path*: `code/data/compute_descriptors.py` → `data/processed/full_dataset.csv`  
  *Verification*: Unit test `tests/unit/test_compute_descriptors.py` checks that the CSV contains all required columns, that `has_structure` is 0/1, and that no NaN/Inf values remain (checked via `code/utils/stability_checks.py`).

- [ ] T005 [P] [US‑1] Define the binary “phase‑change‑suitable” label (latent‑heat > 150 J/g), compute the imputation rate for latent‑heat values, and write decision‑metadata files.  
  *Path*: `code/data/target_consistency_check.py` → `data/results/target_decision.json` and `data/results/imputation_rate_report.json`  
  *Verification*: Contract test `tests/contract/test_target_decision_schema.py` validates both JSON files against `contracts/target_decision.schema.yaml`; the test also asserts that `imputation_rate` ≤ 0.2 and that `label_threshold_J_per_g` equals 150 (or the value used in the sweep).

---  

## Phase 3 – Baseline modelling (fulfills FR‑003, FR‑007, SC‑002, SC‑005)

- [ ] T006 [P] [US‑2] Train Random Forest and Gradient‑Boosting regressors on the training split; also train a shallow MLP (2 hidden layers, 64 units each) as a deep‑learning baseline. Save models and performance metrics.  
  *Path*: `code/models/train_baselines.py` → `data/models/rf_model.pkl`, `data/models/gb_model.pkl`, `data/models/mlp_model.pt`; metrics JSON → `data/results/baseline_metrics.json`  
  *Verification*: Integration test `tests/integration/test_baseline_training.py` ensures each model finishes within 2 h CPU time, RAM ≤ 7 GB, and that every R² ≥ 0.0. It also checks that the Pearson correlation between MLP predictions and tree‑ensemble predictions ≤ 0.8 (FR‑007).

---  

## Phase 4 – Interpretable modelling (fulfills FR‑003, FR‑007, SC‑002, SC‑005)

- [ ] T007 [P] [US‑2] Perform SHAP analysis on the trained Random Forest and Gradient‑Boosting models; export per‑feature importance rankings.  
  *Path*: `code/interpret/shap_analysis.py` → `data/results/shap_importances.json`  
  *Verification*: Contract test `tests/contract/test_shap_schema.py` validates the JSON against `contracts/model_output.schema.yaml` and confirms that at least the top 10 features are listed with non‑negative importance scores.

- [ ] T008 [P] [US‑2] Run symbolic regression with PySR (max 500 generations, early‑stop on R² > 0) to discover explicit mathematical formulas linking descriptors to latent heat.  
  *Path*: `code/models/train_symbolic.py` → `data/results/pysr_formulas.json`  
  *Verification*: Unit test `tests/unit/test_pysr_output.py` checks that the file contains at least one formula, that the best R² ≥ 0.0, and that the runtime ≤ 4 h on the free‑tier runner.

---  

## Phase 5 – Sensitivity & threshold sweeps (fulfills FR‑004, FR‑008, SC‑004, SC‑007)

- [ ] T009 [P] [US‑3] Sweep the latent‑heat label threshold over {100, 125, 150, 175, 200 J/g} and the SHAP feature‑importance cut‑off over {0.01, 0.05, 0.1}. Record performance (R², MAE, false‑positive/negative rates) for each combination.  
  *Path*: `code/sensitivity/threshold_sweep.py` → `data/results/threshold_sweep.json`  
  *Verification*: Test `tests/unit/test_threshold_sweep.py` asserts that the maximum absolute change in false‑positive rate across the sweep ≤ 0.05 and that the R² variation across label thresholds ≤ 0.05 (SC‑007).

---  

## Phase 6 – External validation (fulfills FR‑005, FR‑006, FR‑007, SC‑003, SC‑004)

- [ ] T010 [P] [US‑3] Prepare the independent NIST PCM validation set (map literature IDs to Materials Project IDs, fetch missing structures), apply the best symbolic formula(s), and compute ranking accuracy on the top‑20 latent‑heat materials.  
  *Path*: `code/validation/prepare_external_validation.py` → `data/interim/external_validation_prepared.csv`  
  *Path*: `code/validation/evaluate_external.py` → `data/results/external_validation.json`  
  *Verification*: Contract test `tests/contract/test_external_validation_schema.py` validates the JSON against `contracts/validation_result.schema.yaml` and asserts that `rank_accuracy` ≥ 0.60 (60 % of top‑20 correctly ranked) and that collinearity diagnostics (VIF > 5) are logged in `data/results/collinearity_diagnostic.json`.

---  

## Phase 7 – Reporting & reproducible hand‑off (fulfills all remaining SCs)

- [ ] T011 [P] [US‑3] Generate all figures, tables, and a concise methods/results markdown (`quickstart.md`) directly from the validated artifacts.  
  *Path*: `code/report/generate_report.py` → `paper/figures/`, `paper/tables/`, `quickstart.md`  
  *Verification*: End‑to‑end integration test `tests/integration/test_full_pipeline.py` runs the entire pipeline from raw fetch to report generation, checks that the final report contains references to every artifact, and confirms that re‑running the pipeline from `quickstart.md` reproduces identical result files (hash comparison).

---  

## Phase 8 – Schema contracts (supporting infrastructure)

- [ ] T012 [P] Define and version all JSON‑schema contracts required by the pipeline (dataset, target decision, model output, validation result, collinearity diagnostics).  
  *Path*: `contracts/dataset.schema.yaml`, `contracts/target_decision.schema.yaml`, `contracts/model_output.schema.yaml`, `contracts/validation_result.schema.yaml`, `contracts/collinearity.schema.yaml`  
  *Verification*: Contract test suite `tests/contract/test_all_schemas.py` loads each schema and validates a representative example file; the suite fails if any schema is missing or malformed.

---  

### Dependency map (summary)

| Requirement | Task(s) |
|-------------|---------|
| FR‑001 | T001, T002, T003 |
| FR‑002 | T004 |
| FR‑003 | T006, T007, T008 |
| FR‑004 | T009 |
| FR‑005 | T010 |
| FR‑006 | T004 (has_structure flag) & T010 (collinearity VIF) |
| FR‑007 | T006 (correlation check) & T008 (symbolic vs. deep‑learning) |
| FR‑008 | T005, T009 |
| SC‑001 | T004 |
| SC‑002 | T006 |
| SC‑003 | T010 |
| SC‑004 | T009 |
| SC‑005 | T006 |
| SC‑006 | T001 |
| SC‑007 | T009 |

All tasks are unchecked (`[ ]`) to indicate they still need to be executed; completed infrastructure work from previous rounds (directory creation, logging utilities, etc.) remains checked in the repository but is omitted here for brevity, as it does not affect the scientific deliverables.
