# Tasks: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

**Inputs**: Active `spec.md`, `plan.md`, data‑model and contracts under `specs/001-predict-alloy-diffusion/`.
**Re‑plan note**: Consolidates the prior fragmented task list (T002–T073) into 12 substantive tasks, adds missing tasks to satisfy the plan’s coverage map, and makes all transformations write new derivative files to respect Constitution Principle III. Parallel execution is removed where it caused race conditions. All runtime‑measurement and script‑naming requirements are now explicit.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [US1] [FR-001] Implement real‑data acquisition and streaming ingestion in `code/data/streaming_loader.py`. Fetch diffusion data **directly from the official NIST SRD 150 URL** (no mirrors). Stream in configurable chunks, filter rows to `crystal_structure == "FCC"` and retain **both** `diffusion_mode == "self"` (baseline set) **and** `diffusion_mode == "solute"` (training set) as mandated by the **amended FR‑001**. Convert activation energies to eV/atom and concentrations to at.%. Enforce the Data Availability Check: if fewer than 1 valid row is found, raise and halt with the exact message `"ERROR: No verified real dataset found. Synthetic data is not permitted for this research goal."` Write `data/curated/baselines.csv` (self rows) and `data/curated/solute_raw.csv` (solute rows).  
  - Verification: `pytest code/tests/test_streaming_loader.py` confirms the halt error on empty input, no synthetic fallback, and correct column handling.

- [ ] T013 [US1] [FR-007] Create `code/ingestion/ingest.py` as a thin wrapper that calls `streaming_loader.py`, logs provenance, and writes `data/curated/data_provenance.json` (source_url, SHA‑256 hash, timestamp, filter_criteria, chunks_processed, rows_retained).  
  - Verification: unit test checks that provenance JSON contains all required fields and matches the streamed data.

- [ ] T002 [US1] Implement curation and exclusion logging in `code/data/curation.py`: read `data/curated/solute_raw.csv`, drop rows with missing solute concentration (log count with reason code `"MISSING_CONCENTRATION"` to `data/logs/exclusions.log`), and flag solutes whose atomic radius is unavailable, excluding them and appending records to `errors/missing_atomic_data.csv`. Output the cleaned set to `data/curated/curated_clean.csv` (preserves schema).  
  - Verification: unit test feeds a fixture with known missing values and asserts exclusion counts and error‑file contents.

- [ ] T003 [US2] [FR-002] Implement feature engineering in `code/processing/feature_engineering.py`: compute `size_mismatch = (solute_radius - host_radius) / host_radius`, `electronegativity_diff` (Pauling scale), and `valence_electron_diff` via the pinned `periodictable==0.20.1`. Write the enriched dataset **without extra columns** to `data/curated/engineered.csv` (conforms to `dataset.schema.yaml`). Write the additional descriptor columns (`electronegativity_diff`, `valence_electron_diff`) to a separate file `data/curated/engineered_extra.csv`.  
  - Verification: `pytest code/tests/test_feature_engineering.py` checks `size_mismatch` against manual calculations and asserts zero nulls in `engineered.csv`.

- [ ] T004 [US3] [FR-006, FR-008] Implement `code/processing/baseline.py`: read `data/curated/baselines.csv` to extract pure‑host activation energies `Q_host`. For any host missing from this baseline set, halt with `"ERROR: Baseline activation energy for host [X] not found in NIST SRD 150. Pipeline halted."` Compute `baseline_shift_eV = activation_energy_eV - Q_host` for each row in `data/curated/engineered.csv` and write the result to `data/curated/baseline_shifted.csv`.  
  - Verification: `pytest code/tests/test_baseline.py` confirms correct baseline shifts and exact halt message on missing hosts.

- [ ] T005 Run the end‑to‑end data pipeline (T001 → T004) via the command documented in `quickstart.md`. This produces `data/curated/baseline_shifted.csv`, `data/curated/baselines.csv`, and `data/curated/data_provenance.json`. Afterwards execute the **schema‑validation script** `code/validation/validate_curated.py` to ensure `baseline_shifted.csv` conforms to `dataset.schema.yaml` and contains ≥1 valid row.  
  - Verification: `validate_curated.py` returns exit code 0; its success is asserted in the integration test.

## Phase 2: Complete the study and validate its evidence

- [ ] T006 [US2] [FR-003, FR-004] Implement Random Forest training in `code/models/train_rf.py`: split `data/curated/baseline_shifted.csv` (80/20 hold‑out before tuning if <50 rows, otherwise nested 5‑fold CV with stratification by host metal, falling back to random split with warning). Perform `GridSearchCV` over `max_depth` 3‑10 and `n_estimators` 50‑200, maximizing R²; tie‑break on lowest `max_depth` then lowest `n_estimators`. Save the model to `models/final_rf.pkl` and metrics (R², RMSE, MAE) to `models/rf_metrics.json`. Record training CPU time to `data/logs/training_time_rf.log` and assert it is ≤15 minutes on a 2‑core runner.  
  - Verification: `pytest code/tests/test_train_rf.py` checks deterministic seeds, split logic, tie‑breaking, metric schema, and runtime assertion.

- [ ] T014 [US2] [FR-003, FR-004] Implement Gradient Boosting training in `code/models/train_gb.py` with the same protocol as T006, saving to `models/final_gb.pkl` and `models/gb_metrics.json`. Runtime and tie‑breaking requirements are identical to T006.  
  - Verification: `pytest code/tests/test_train_gb.py` analogous to RF test.

- [ ] T007 [US3] [FR-005] Implement Linear Regression in `code/models/train_linear.py`: fit on the same training split using the three feature columns `size_mismatch`, `electronegativity_diff`, `valence_electron_diff`. Extract the `size_mismatch` coefficient, its standard error, p‑value, and a 95 % bootstrap confidence interval (≥1000 resamples, stratified by host when possible). Write results to `models/linear_coef.json` conforming to `model_output.schema.yaml`.  
  - Verification: `pytest code/tests/test_train_linear.py` validates coefficient extraction and CI ordering.

- [ ] T008 [US3] [FR-005, FR-009] Implement `code/validation/stability_index_report.py`: use predictions from the **Random Forest** model (`models/final_rf.pkl`) together with baseline shifts to sweep the classification threshold over `{0.45,0.46,…,0.55}` eV. Compute classification rates, calculate the stability index `std(rates) / (0.55‑0.45)`, and write `validation/stability_index_report.json` (schema‑compliant) and a plot `validation/threshold_sweep.png`.  
  - Verification: `pytest code/tests/test_sensitivity.py` validates sweep grid, index formula, and report schema.

- [ ] T009 [US3] Implement `code/validation/stats.py` to aggregate bootstrap statistics (from T007), model metrics (from T006/T014), and stability metrics (from T008) into `validation/validation_report.json`. Include fields `significance_verified`, `model_comparison` (R²/RMSE/MAE vs. mean predictor), and `stability_target_met`.  
  - Verification: existence and schema compliance of the report; all values trace back to source artifacts.

## Phase 3: Reproducible results and paper handoff

- [ ] T010 Generate tables and figures from validated outputs:  
  * `data/results/model_comparison.csv` (metrics table)  
  * `figures/shift_vs_mismatch.png` (scatter with fitted linear trend)  
  * Create a **spot‑check script** `code/validation/spot_check.py` that randomly samples 5 rows from `data/curated/baseline_shifted.csv` and confirms that plotted values match the CSV entries.  
  - Verification: spot‑check script runs without error; a test `pytest code/tests/test_spot_check.py` asserts consistency.

- [ ] T011 Write a concise methods/results account in `specs/001-predicting-the-impact-of-alloying-on-the/research.md` (or `reports/final_report.md`). Every numeric claim must reference a value from `models/*.json`, `validation/*.json`, or the curated CSV files. Include discussion of limitations, observational nature, and any low‑R² outcomes as valid findings.  
  - Verification: a lint script checks that each number is sourced from a JSON/CSV artifact.

- [ ] T012 Re‑run the documented workflow end‑to‑end (as per `quickstart.md`). Verify: all tests pass, curated files validate against schemas, **peak RSS ≤ 7 GB**, **total runtime ≤ 6 h**, **training CPU‑time ≤ 15 min** (already logged), **model‑training CPU‑time ≤ 2 CPU‑hours**, and **raw dataset size ≤ 10 MB** (checked via `data/logs/dataset_size.log`). Log resource usage to `data/logs/resource_usage.log` and confirm SC‑004 and Principle VI compliance. Document the paper‑stage handoff (tables, figures, report locations) in `quickstart.md`.  
  - Verification: a final integration test parses `resource_usage.log` and asserts all limits.

- [ ] T015 [FR-001 amendment] Amend the specification `specs/001-predicting-the-impact-of-alloying-on-the/spec.md` to update FR-001: the data ingestion requirement now explicitly allows filtering for **both** `diffusion_mode == "self"` (to create the baseline set) **and** `diffusion_mode == "solute"` (to create the training set). Update the associated User Story 1 acceptance scenarios to reflect this dual‑mode requirement and the corresponding error handling.  
  - Verification: a schema‑validation test ensures the updated spec contains the amended FR‑001 text; future tasks referencing FR‑001 will be compliant.

## Dependencies and requirement coverage (updated)

| Requirement | Task(s) | Key artifacts |
|---|---|---|
| FR-001 (ingest/filter) | T001, T015 | `code/data/streaming_loader.py`, `data/curated/solute_raw.csv`, `data/curated/baselines.csv` |
| FR-002 (size_mismatch) | T003 | `code/processing/feature_engineering.py`, `data/curated/engineered.csv` |
| FR-003 (RF/GB) | T006, T014 | `models/final_rf.pkl`, `models/final_gb.pkl` |
| FR-004 (nested CV/hold‑out) | T006, T014 | metric JSONs |
| FR-005 (linear + sweep) | T007, T008 | `models/linear_coef.json`, `validation/stability_index_report.json` |
| FR-006 (baseline source) | T004 | `code/processing/baseline.py`, `data/curated/baselines.csv` |
| FR-007 (provenance) | T013 | `data/curated/data_provenance.json` |
| FR-008 (baseline_shift) | T004 | `data/curated/baseline_shifted.csv` |
| FR-009 (stability report) | T008 | `validation/stability_index_report.json` |
| SC-001 (R² > mean) | T006, T014, T009 | metric JSONs |
| SC-002 (coef significance) | T007, T009 | `models/linear_coef.json` |
| SC-003 (stability ≤ 0.05) | T008, T009 | `validation/stability_index_report.json` |
| SC-004 (resource limits) | T012 | `data/logs/resource_usage.log` |

Execution order (updated):  
T015 → T001 → T013 → T002 → T003 → T004 → T005 → (T006 & T014 in parallel) → T007 → T008 → T009 → T010 → T011 → T012.
