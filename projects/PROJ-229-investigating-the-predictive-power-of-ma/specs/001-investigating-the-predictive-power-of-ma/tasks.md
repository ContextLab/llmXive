# Tasks: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase‑Change Materials  

**Inputs**: `spec.md`, `plan.md`, data‑model definitions, JSON‑schema contracts, and reviewer feedback.  

The checklist follows the platform’s canonical format. Each task states the functional requirement(s) it satisfies, the exact artifact(s) it will produce, and a concrete verification step (indented). Tasks are ordered to respect data flow; later tasks depend on the outputs of earlier ones.

---  

## Phase 0 – Contracts & infrastructure (fulfills Constitution I)

- [~] T001 [P] Add and version all JSON‑schema contracts required by the pipeline, **including** `contracts/target_decision.schema.yaml`.  
  *Path*: `contracts/dataset.schema.yaml`, `contracts/material_compound.schema.yaml`, `contracts/model_result.schema.yaml`, `contracts/target_decision.schema.yaml`, `contracts/validation_result.schema.yaml`  
  *Verification*: `tests/contract/test_all_schemas.py` loads each schema and validates a representative example file; the suite fails if any schema is missing, malformed, or does not match the specification.  

---  

## Phase 1 – Data acquisition (fulfills FR‑001, FR‑008, SC‑006)

- [ ] T002 [P] [US‑1] Stream the Materials Project dataset, filter for entries that have both melting‑point and heat‑capacity data, and write a parquet file.   <!-- FAILED-IN-EXECUTION: code/data/fetch_materials.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/fetch_materials.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/fetch_materials.py exit=1 -->
  *Path*: `code/data/fetch_materials.py` → `data/raw/pcm.parquet`  
  *Verification*: `tests/unit/test_fetch_materials.py` checks that the parquet file exists, contains ≥ 5 000 rows, conforms to `contracts/dataset.schema.yaml`, and never exceeds 7 GB RAM (monitored via `psutil`).  

- [ ] T003 [P] [US‑1] Download crystal‑structure CIFs for the compounds listed in `pcm.parquet` from the Open Materials Database (OMDB) HuggingFace dataset.   <!-- FAILED-IN-EXECUTION: code/data/fetch_omdb_structures.py exit=1 -->
  *Path*: `code/data/fetch_omdb_structures.py` → `data/raw/omdb_structures/` (one CIF per `material_id`).  
  *Verification*: `tests/integration/test_fetch_omdb.py` confirms that ≥ 80 % of the material IDs have a corresponding CIF and that the script raises an error (no synthetic fallback) if the remote fetch fails.  

- [ ] T004 [P] [US‑1] Fetch a curated literature PCM list (≈ 50 entries) for independent validation and store it as CSV.  
  *Path*: `code/data/fetch_literature_pcm.py` → `data/external/literature_pcms_raw.csv`  
  *Verification*: `tests/unit/test_fetch_literature_pcm.py` ensures the CSV exists, has ≥ 50 rows, and aborts with an exception if the download fails (no placeholder data).  

- [ ] T005 [P] [US‑1] Retrieve the open NIST PCM dataset, merge it with the Materials Project entries, and write a JSON file for internal use.  
  *Path*: `code/data/fetch_nist_data.py` → `data/raw/nist_data.json`  
  *Verification*: `tests/contract/test_nist_schema.py` validates the JSON against `contracts/dataset.schema.yaml` and asserts that the overlap with Materials Project IDs is ≥ 100 entries; otherwise a logged fallback flag is set.  

---  

## Phase 2 – Feature engineering (fulfills FR‑002, FR‑006, SC‑001)

- [ ] T006 [P] [US‑1] Compute elemental descriptors (average atomic number, electronegativity, radius, etc.) and crystal‑graph features (adjacency matrix, node attributes) for every compound, then merge these with thermodynamic columns to produce the master dataset.  
  *Path*: `code/data/compute_descriptors.py` → `data/processed/full_dataset.csv`  
  *Verification*: `tests/unit/test_compute_descriptors.py` checks that the CSV contains all required columns (including `has_structure`), that no NaN/Inf values remain (`code/utils/stability_checks.py`), and that the file size ≤ 2 GB.  

- [ ] T007 [P] Generate `MaterialCompound` records validated against `contracts/material_compound.schema.yaml`.  
  *Path*: `code/data/generate_material_compound.py` → `data/processed/material_compound_records.json`  
  *Verification*: `tests/contract/test_material_compound_schema.py` validates the JSON file against the schema.  

- [ ] T008 [P] Define the binary “phase‑change‑suitable” label (`latent_heat_J_per_g > 150 J/g`), compute the imputation rate for latent‑heat values, and write the decision‑metadata files.  
  *Path*: `code/data/target_consistency_check.py` → `data/results/target_decision.json` and `data/results/imputation_rate_report.json`  
  *Verification*: `tests/contract/test_target_decision_schema.py` validates both JSON files against `contracts/target_decision.schema.yaml`, asserts `imputation_rate ≤ 0.2`, and confirms `label_threshold_J_per_g` equals the value used in the sweep.  

- [ ] T009 [P] Compute Pearson correlation between each structural/elemental feature and the binary phase‑change label (supporting SC‑001).  
  *Path*: `code/analysis/compute_feature_correlation.py` → `data/results/feature_correlation.json`  
  *Verification*: `tests/unit/test_feature_correlation.py` checks that the JSON contains a numeric `pearson_r` for every feature and that each value lies in [‑1, 1].  

---  

## Phase 3 – Modeling (fulfills FR‑003, SC‑002, SC‑005)

- [ ] T010 [P] [US‑2] Train baseline models (Random Forest, Gradient Boosting) and a shallow MLP (2 hidden layers, 64 units each) on the training split; save model artefacts and a consolidated metrics JSON that includes R² and MAE.  
  *Path*: `code/models/train_baselines.py` → `data/models/rf_model.pkl`, `data/models/gb_model.pkl`, `data/models/mlp_model.pt`; metrics → `data/results/baseline_metrics.json`  
  *Verification*: `tests/integration/test_baseline_training.py` ensures each model finishes within 2 h CPU time, uses ≤ 7 GB RAM, and yields R² ≥ 0.0.  

---  

## Phase 4 – Interpretable modelling (fulfills FR‑003, FR‑007, SC‑002, SC‑005)

- [ ] T011 [P] [US‑2] (a) Perform SHAP analysis on the trained Random Forest and Gradient‑Boosting models and export per‑feature importance rankings; (b) Run symbolic regression with PySR (max 500 generations, early‑stop on R² > 0) to discover explicit formulas linking descriptors to latent heat.  
  *Path*: `code/interpret/shap_analysis.py` → `data/results/shap_importances.json`  
  *Path*: `code/models/train_symbolic.py` → `data/results/pysr_formulas.json`  
  *Verification*:  
    - `tests/unit/test_shap_output.py` validates that `shap_importances.json` contains a mapping of feature names to numeric scores for the top 10 features.  
    - `tests/unit/test_pysr_output.py` ensures the PySR file contains ≥ 1 formula, that the best R² ≥ 0.0, and that runtime ≤ 4 h on the free‑tier runner.  
    - `tests/integration/test_interpretable_constraints.py` asserts (i) the Pearson correlation between PySR predictions and MLP predictions is ≤ 0.8 (FR-007), and (ii) a paired-t-test confirms |R²_interpretable − R²_baseline| ≤ 0.05 (SC-002).  

---  

## Phase 5 – Sensitivity & threshold sweeps (fulfills FR‑004, FR‑008, SC‑004, SC‑007)

- [ ] T012 [P] [US‑3] Sweep the latent‑heat label threshold over {100, 125, 150, 175, 200 J/g} and the SHAP feature‑importance cut‑off over {0.01, 0.05, 0.1}. Record R², MAE, false‑positive/false‑negative rates for each combination and verify that (i) the maximum absolute change in false‑positive rate ≤ 0.05 (SC‑004) and (ii) variation in R² across label thresholds ≤ 0.05 (SC‑007).  
  *Path*: `code/sensitivity/threshold_sweep.py` → `data/results/threshold_sweep.json`  
  *Verification*: `tests/unit/test_threshold_sweep.py` asserts the above numeric bounds and validates that `threshold_sweep.json` contains the `label_thresholds` array and `metrics_by_threshold` object as defined in the data model.  

---  

## Phase 6 – External validation (fulfills FR‑005, FR‑006, FR‑007, SC‑003, SC‑004)

- [ ] T013 [P] [US‑3] Prepare the independent literature PCM validation set (map literature IDs to Materials Project IDs, fetch missing structures), apply the best symbolic formula(s), and compute ranking accuracy on the top‑20 latent‑heat materials as well as overall R². Perform collinearity diagnostics (VIF) and explicitly adjust the interpretation narrative for any flagged dependencies (framing them as descriptive rather than causal).  
  *Path*: `code/validation/prepare_external_validation.py` → `data/interim/external_validation_prepared.csv`  
  *Path*: `code/validation/evaluate_external.py` → `data/results/external_validation.json`  
  *Path*: `code/validation/collinearity_adjustment.py` → `data/results/collinearity_diagnostic.json`, `data/results/interpretation_adjustments.json`  
  *Verification*: `tests/contract/test_external_validation_schema.py` validates the JSON against `contracts/validation_result.schema.yaml` and asserts `rank_accuracy ≥ 0.60`. `tests/unit/test_collinearity_fix.py` asserts that `interpretation_adjustments.json` exists and contains annotations for every variable with VIF > 5.  

---  

## Phase 7 – Reporting & reproducible hand‑off (fulfills remaining SCs)

- [ ] T014 [P] Generate all figures, tables, and a concise `quickstart.md` that reproduces the full pipeline from raw fetch to final results.  
  *Path*: `code/report/generate_report.py` → `paper/figures/`, `paper/tables/`, `quickstart.md`  
  *Verification*: End‑to‑end integration test `tests/integration/test_full_pipeline.py` runs the command documented in `quickstart.md`, checks that every artifact referenced in the report exists, and confirms that a second run produces identical file hashes (deterministic reproducibility).  

---  

## Phase 8 – Sanity & debugging (early executable end‑to‑end check)

- [ ] T015 [P] Run a lightweight sanity check that executes the minimal pipeline (T002 → T006 → T010 → T011 → T012) on a sampled subset (first 1 000 rows) to guarantee core data‑flow before full‑scale runs.  
  *Path*: `code/debug/sanity_run.py` → `data/debug/sanity_report.json`  
  *Verification*: `tests/unit/test_sanity_run.py` asserts that the sanity report contains successful status flags for each sub‑step and that total runtime ≤ 30 min on the free‑tier runner.  

---  

### Dependency map (summary)

| Requirement | Task(s) |
|-------------|---------|
| FR‑001 | T002 |
| FR‑002 | T006 |
| FR‑003 | T010, T011 |
| FR‑004 | T012 |
| FR‑005 | T013 |
| FR‑006 | T006 (has_structure flag) & T013 (collinearity diagnostics & adjustment) |
| FR‑007 | T011 (correlation check) |
| FR‑008 | T008 & T012 |
| SC‑001 | T009 |
| SC‑002 | T011 |
| SC‑003 | T013 |
| SC‑004 | T012 |
| SC‑005 | T010, T011 |
| SC‑006 | T002 |
| SC‑007 | T012 |

All tasks are currently unchecked (`[ ]`) to indicate they still need implementation and verification. The checklist respects the required scientific workflow, data‑flow ordering, and the platform’s constraints on compute and storage.