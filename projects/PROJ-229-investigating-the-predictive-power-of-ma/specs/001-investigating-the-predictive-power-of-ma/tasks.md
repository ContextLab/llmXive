# Tasks: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase‑Change Materials  

**Inputs**: `spec.md`, `plan.md`, data‑model definitions, JSON‑schema contracts, and reviewer feedback.  

The list below follows the platform’s canonical checklist format.  
Each task specifies the functional requirement it satisfies, the exact artifact
paths that will be produced, and an observable verification step (indented).
Tasks are ordered to respect data flow; later tasks depend on the outputs of
earlier ones.

---  

## Phase 0 – Contracts & supporting infrastructure (fulfills Constitution I)

- [ ] T013 [P] Add and version all JSON‑schema contracts required by the pipeline, **including** `contracts/target_decision.schema.yaml`.  
  *Path*: `contracts/dataset.schema.yaml`, `contracts/material_compound.schema.yaml`, `contracts/model_result.schema.yaml`, `contracts/target_decision.schema.yaml`, `contracts/validation_result.schema.yaml`, `contracts/collinearity.schema.yaml`  
  *Verification*: Contract test suite `tests/contract/test_all_schemas.py` loads each schema and validates a representative example file; the suite fails if any schema is missing, malformed, or does not match the specification.

---  

## Phase 1 – Data acquisition (fulfills FR‑001, FR‑008, SC‑006)

- [ ] T001 [P] [US‑1] Stream the Materials Project dataset, filter for entries that have both melting‑point and heat‑capacity data, and write a parquet file.  
  *Path*: `code/data/fetch_materials.py` → `data/raw/pcm.parquet`  
  *Verification*: Unit test `tests/unit/test_fetch_materials.py` checks that the parquet file exists, contains ≥ 5 000 rows, conforms to `contracts/dataset.schema.yaml` (required columns present, types correct), and that the streaming process never exceeds 7 GB RAM (monitored via `psutil`).  

- [ ] T002 [P] [US‑1] Download crystal‑structure CIFs for the compounds listed in `pcm.parquet` from the Open Materials Database (OMDB) HuggingFace dataset.  
  *Path*: `code/data/fetch_omdb_structures.py` → `data/raw/omdb_structures/` (one CIF per `material_id`).  
  *Verification*: Integration test `tests/integration/test_fetch_omdb.py` confirms that at least 80 % of the material IDs have a corresponding CIF and that the script raises an error (no synthetic fallback) if the remote fetch fails.  

- [ ] T003 [P] [US‑1] Retrieve a curated literature PCM list (≈ 50 entries) for independent validation and store it as CSV.  
  *Path*: `code/data/fetch_literature_pcm.py` → `data/external/literature_pcms_raw.csv`  
  *Verification*: Unit test `tests/unit/test_fetch_literature_pcm.py` ensures the CSV exists, has ≥ 50 rows, and that the script aborts with an exception if the download fails (no placeholder data).  

- [ ] T004 [P] [US‑1] Retrieve the open NIST PCM dataset, merge it with the Materials Project entries, and write a JSON file for internal use.  
  *Path*: `code/data/fetch_nist_data.py` → `data/raw/nist_data.json`  
  *Verification*: Contract test `tests/contract/test_nist_schema.py` validates the JSON against `contracts/dataset.schema.yaml` and asserts that the overlap with Materials Project IDs is ≥ 100 entries; otherwise a logged fallback flag is set.  

---  

## Phase 2 – Feature engineering (fulfills FR‑002, FR‑006, SC‑001)

- [ ] T005 [P] [US‑1] Compute elemental descriptors (average atomic number, electronegativity, atomic radius, etc.) and crystal‑graph features (adjacency matrix, node attributes) for every compound, then merge these with thermodynamic columns to produce the master dataset.  
  *Path*: `code/data/compute_descriptors.py` → `data/processed/full_dataset.csv`  
  *Verification*: Unit test `tests/unit/test_compute_descriptors.py` checks that the CSV contains all required columns (including `has_structure`), that no NaN/Inf values remain (via `code/utils/stability_checks.py`), and that the file size stays ≤ 2 GB.  

- [ ] T015 [P] Generate MaterialCompound records validated against `contracts/material_compound.schema.yaml`.  
  *Path*: `code/data/generate_material_compound.py` → `data/processed/material_compound_records.json`  
  *Verification*: Contract test `tests/contract/test_material_compound_schema.py` validates the JSON file against `contracts/material_compound.schema.yaml`.  

- [ ] T006 [P] Define the binary “phase‑change‑suitable” label (`latent_heat_J_per_g > 150` J/g), compute the imputation rate for latent‑heat values, and write the decision‑metadata files.  
  *Path*: `code/data/target_consistency_check.py` → `data/results/target_decision.json` and `data/results/imputation_rate_report.json`  
  *Verification*: Contract test `tests/contract/test_target_decision_schema.py` validates both JSON files against `contracts/target_decision.schema.yaml`; it also asserts that `imputation_rate` ≤ 0.2 and that `label_threshold_J_per_g` equals 150 (or the value used in the sweep).  

- [ ] T017 [P] Compute Pearson correlation between identified structural features and the binary phase‑change suitability label (SC‑001).  
  *Path*: `code/analysis/compute_feature_correlation.py` → `data/results/feature_correlation.json`  
  *Verification*: Unit test `tests/unit/test_feature_correlation.py` checks that the JSON contains a numeric `pearson_r` field and that its absolute value is recorded; the test also ensures the value is within the expected range (‑1 ≤ r ≤ 1).  

---  

## Phase 3 – Baseline modelling (fulfills FR‑003, FR‑007, SC‑002, SC‑005)

- [ ] T007 [P] [US‑2] Train Random Forest and Gradient‑Boosting regressors on the training split, and also train a shallow MLP (2 hidden layers, 64 units each) as a deep‑learning baseline. Save model artefacts and a consolidated metrics JSON.  
  *Path*: `code/models/train_baselines.py` → `data/models/rf_model.pkl`, `data/models/gb_model.pkl`, `data/models/mlp_model.pt`; metrics → `data/results/baseline_metrics.json`  
  *Verification*: Integration test `tests/integration/test_baseline_training.py` ensures each model finishes within 2 h CPU time, uses ≤ 7 GB RAM, and that every R² ≥ 0.0. It also checks that the Pearson correlation between MLP predictions and tree‑ensemble predictions ≤ 0.8 (FR‑007).  

- [ ] T016 [P] Emit a unified ModelResult JSON validated against `contracts/model_result.schema.yaml`.  
  *Path*: `code/models/assemble_model_result.py` → `data/results/model_result.json`  
  *Verification*: Contract test `tests/contract/test_model_result_schema.py` validates the JSON file against `contracts/model_result.schema.yaml`.  

---  

## Phase 4 – Interpretable modelling (fulfills FR‑003, FR‑007, SC‑002, SC‑005)

- [ ] T008 [P] [US‑2] Perform SHAP analysis on the trained Random Forest and Gradient‑Boosting models; export per‑feature importance rankings.  
  *Path*: `code/interpret/shap_analysis.py` → `data/results/shap_importances.json`  
  *Verification*: Contract test `tests/contract/test_shap_schema.py` validates the JSON against `contracts/model_output.schema.yaml` and confirms that at least the top 10 features are listed with non‑negative importance scores.  

- [ ] T009 [P] [US‑2] Run symbolic regression with PySR (max 500 generations, early‑stop on R² > 0) to discover explicit mathematical formulas linking descriptors to latent heat.  
  *Path*: `code/models/train_symbolic.py` → `data/results/pysr_formulas.json`  
  *Verification*: Unit test `tests/unit/test_pysr_output.py` checks that the file contains at least one formula, that the best R² ≥ 0.0, and that the runtime ≤ 4 h on the free‑tier runner.  

---  

## Phase 5 – Sensitivity & threshold sweeps (fulfills FR‑004, FR‑008, SC‑004, SC‑007)

- [ ] T010 [P] [US‑3] Sweep the latent‑heat label threshold over {100, 125, 150, 175, 200 J/g} and the SHAP feature‑importance cut‑off over {0.01, 0.05, 0.1}. Record performance (R², MAE, false‑positive/false‑negative rates) for each combination and verify both SC‑004 and SC‑007 criteria.  
  *Path*: `code/sensitivity/threshold_sweep.py` → `data/results/threshold_sweep.json`  
  *Verification*: Test `tests/unit/test_threshold_sweep.py` asserts that the maximum absolute change in false‑positive rate across the sweep ≤ 0.05, that the variation in R² across label thresholds ≤ 0.05, and that the absolute change in overall model performance across the full label‑threshold sweep ≤ 0.05 (SC‑007).  

---  

## Phase 6 – External validation (fulfills FR‑005, FR‑006, FR‑007, SC‑003, SC‑004)

- [ ] T011 [P] [US‑3] Prepare the independent literature PCM validation set (map literature IDs to Materials Project IDs, fetch missing structures), apply the best symbolic formula(s), and compute ranking accuracy on the top‑20 latent‑heat materials.  
  *Path*: `code/validation/prepare_external_validation.py` → `data/interim/external_validation_prepared.csv`  
  *Path*: `code/validation/evaluate_external.py` → `data/results/external_validation.json`  
  *Verification*: Contract test `tests/contract/test_external_validation_schema.py` validates the JSON against `contracts/validation_result.schema.yaml` and asserts that `rank_accuracy` ≥ 0.60 (≥ 60 % of top‑20 correctly ranked) and that collinearity diagnostics (VIF > 5) are logged in `data/results/collinearity_diagnostic.json`.  

---  

## Phase 7 – Reporting & reproducible hand‑off (fulfills all remaining SCs)

- [ ] T012 [P] [US‑3] Generate all figures, tables, and a concise methods/results markdown (`quickstart.md`) directly from the validated artifacts.  
  *Path*: `code/report/generate_report.py` → `paper/figures/`, `paper/tables/`, `quickstart.md`  
  *Verification*: End‑to‑end integration test `tests/integration/test_full_pipeline.py` runs the entire pipeline from raw fetch to report generation, checks that the final report references every artifact, and confirms that re‑running the pipeline from the command in `quickstart.md` reproduces identical result files (hash comparison).  

---  

## Phase 8 – Sanity & debugging (fulfills early‑stage robustness)

- [ ] T014 [P] Run a lightweight end‑to‑end sanity check that executes the minimal pipeline (T001 → T005 → T007 → T008 → T010) on a sampled subset (first 1 000 rows) to guarantee that the core data‑flow works before full‑scale runs.  
  *Path*: `code/debug/sanity_run.py` → `data/debug/sanity_report.json`  
  *Verification*: Unit test `tests/unit/test_sanity_run.py` asserts that the sanity report contains successful status flags for each sub‑step and that runtime ≤ 30 min on the free‑tier runner.  

---  

### Dependency map (summary)

| Requirement | Task(s) |
|-------------|---------|
| FR‑001 | T001, T002, T004 |
| FR‑002 | T005 |
| FR‑003 | T007, T008, T009 |
| FR‑004 | T010 |
| FR‑005 | T011 |
| FR‑006 | T005 (has_structure flag) & T011 (collinearity diagnostics) |
| FR‑007 | T007 (correlation check) & T009 (symbolic vs. deep‑learning) |
| FR‑008 | T006, T010 |
| SC‑001 | T017 |
| SC‑002 | T007 |
| SC‑003 | T011 |
| SC‑004 | T010 |
| SC‑005 | T007 |
| SC‑006 | T001 |
| SC‑007 | T010 |
| Coverage of MaterialCompound | T015 |
| Coverage of ModelResult | T016 |

All tasks are unchecked (`[ ]`) to indicate they still need to be executed; completed infrastructure work from previous rounds (directory creation, logging utilities, etc.) remains checked in the repository but is omitted here for brevity, as it does not affect the scientific deliverables.  