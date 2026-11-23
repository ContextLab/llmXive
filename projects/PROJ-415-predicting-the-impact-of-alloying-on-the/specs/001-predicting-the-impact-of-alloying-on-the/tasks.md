# Tasks: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

**Inputs**: Active `spec.md`, `plan.md`, data-model and contracts under `specs/001-predict-alloy-diffusion-on-the/`.
**Re-plan note**: Consolidates the prior fragmented task list into 15 substantive tasks, makes all transformations write new derivative files (Constitution Principle III), and aligns every artifact path with the plan, data model, and contracts. The Single Source of Truth curated dataset is `data/curated/filtered.csv` (per plan, data-model, and FR-008). Parallel execution is removed where it caused race conditions.

**Spec-amendment gate (hard blocking)**: The plan's Spec Gap requires amending FR-001 to authorize solute/impurity rows. **T015 is the first task in this document and in the execution order**; it routes the FR-001 amendment through the spec-stage kickback. **T001 is blocked on T015**: until the amended FR-001 lands at spec stage, T001 implements the current authoritative spec (self-only filtering) and the pipeline halts after producing the baseline set; the dual-mode (self + solute) branch of T001 activates only under the amended spec. The task list does not authorize its own spec amendment — the pipeline must not silently override the authoritative spec.

**Verifier feedback addressed**: The independent verifier rejected the prior ingestion task (tracked as T062, artifact `code/data/streaming_loader.py`) as missing/empty/invalid. That work is folded back into **T001**, which is reopened and must be redone so the streaming loader is a real, runnable implementation with a verified real data source — no placeholder or synthetic stand-in. The loader must FAIL LOUDLY (raise) if the real fetch fails; it must never fall back to generated data.

## Phase 1: Setup and first end-to-end analysis

- [ ] T015 [FR-001 amendment — HARD BLOCKING GATE; must complete before T001's dual-mode branch] Amend the specification `specs/001-predict-alloy-diffusion-on-the/spec.md` (via the spec-stage kickback routed in the plan's Spec Gap) to update FR-001: the data ingestion requirement explicitly allows filtering for **both** `diffusion_mode == "self"` (to create the baseline set) **and** `diffusion_mode == "solute"` (to create the training set). Update the associated User Story 1 acceptance scenarios to reflect this dual-mode requirement and the corresponding error handling. Until this amendment is ratified at spec stage, T001 executes the current self-only FR-001.
  - Verification: a schema-validation test ensures the updated spec contains the amended FR-001 text; future tasks referencing FR-001 will be compliant.

- [ ] T001 [US1] [FR-001] **(REDO — previously rejected as T062: `code/data/streaming_loader.py` was missing/empty/invalid) — BLOCKED ON T015** Implement real-data acquisition and streaming ingestion in `code/data/streaming_loader.py`. Fetch diffusion data from a verified, reachable real source for NIST SRD 150 diffusion data (use the exact package/recipe if the execution stage injects a "VERIFIED REAL DATA SOURCE" block; otherwise use the official NIST SRD 150 access route or a named, reachable verified mirror URL — never an invented or guessed URL). Stream in configurable chunks, filter rows to `crystal_structure == "FCC"`. **Filtering mode is spec-gated**: under the current (un-amended) FR-001, retain only `diffusion_mode == "self"`; once T015's amended FR-001 is ratified, retain **both** `diffusion_mode == "self"` (baseline set) **and** `diffusion_mode == "solute"` (training set). Convert activation energies to eV/atom and concentrations to at.%. Enforce the Data Availability Check: if fewer than 1 valid row is found, raise and halt with the exact message `"ERROR: No verified real dataset found. Synthetic data is not permitted for this research goal."` If the real fetch itself fails, the loader MUST raise (fail loudly) — no `try/except` fallback to synthetic or placeholder data. Write `data/curated/baselines.csv` (self rows) and, under the amended spec, `data/curated/solute_raw.csv` (solute rows).
  - Verification: `pytest code/tests/test_streaming_loader.py` confirms the halt error on empty input, that a failed fetch raises rather than substituting data, correct column handling (mapping `solute_concentration_at_pct` → `concentration_at_percent` per the DiffusionRecord contract), and that the filter mode follows the active spec state; the file exists, is non-empty, and runs.

- [ ] T013 [US1] [FR-007] Create `code/requirements.txt` pinning every dependency (`pandas`, `scikit-learn`, `numpy`, `matplotlib`, `seaborn`, `periodictable==0.20.1`, `statsmodels`, `joblib`, `pytest` — exact pinned versions) per Constitution Principle I. Create `code/ingestion/ingest.py` as a thin wrapper that calls `streaming_loader.py`, logs provenance, writes `data/curated/data_provenance.json` (source_url, SHA-256 hash, timestamp, filter_criteria, chunks_processed, rows_retained), and records the raw download size in bytes to `data/logs/dataset_size.log` (producer for T012's ≤10 MB check).
  - Verification: unit test checks that provenance JSON contains all required fields, matches the streamed data, and that `dataset_size.log` contains a parseable byte count; `pip install -r code/requirements.txt` succeeds and pins `periodictable==0.20.1`.

- [ ] T002 [US1] Implement curation and exclusion logging in `code/data/curation.py`: read `data/curated/solute_raw.csv`, drop rows with missing solute concentration (log count with reason code `"MISSING_CONCENTRATION"` to `data/logs/exclusions.log`), and flag solutes whose atomic radius is unavailable, excluding them and appending records to `errors/missing_atomic_data.csv`. Output the cleaned set to `data/curated/curated_clean.csv` (preserves schema; intermediate file — the SSoT `filtered.csv` is produced by T004).
  - Verification: unit test feeds a fixture with known missing values and asserts exclusion counts and error-file contents.

- [ ] T003 [US2] [FR-002] Implement feature engineering in `code/processing/feature_engineering.py`: compute `size_mismatch = (solute_radius - host_radius) / host_radius`, `electronegativity_diff` (Pauling scale), and `valence_electron_diff` via the pinned `periodictable==0.20.1`. Write `data/curated/engineered.csv` containing **all** columns required by `dataset.schema.yaml` — including `electronegativity_diff` and `valence_electron_diff` — so the file fully conforms to the schema (no separate extra-descriptor file; downstream tasks read this single file).
  - Verification: `pytest code/tests/test_feature_engineering.py` checks `size_mismatch` against manual calculations, asserts zero nulls in `engineered.csv`, and validates the file against `dataset.schema.yaml` including the electronegativity and valence columns.

- [ ] T004 [US3] [FR-006, FR-008] Implement `code/processing/baseline.py`: read `data/curated/baselines.csv` to extract pure-host activation energies `Q_host`. For any host missing from this baseline set, halt with `"ERROR: Baseline activation energy for host [X] not found in NIST SRD 150. Pipeline halted."` Compute `baseline_shift_eV = activation_energy_eV - Q_host` for each row in `data/curated/engineered.csv` and write the final curated Single Source of Truth to **`data/curated/filtered.csv`** (the artifact named by FR-008, the plan, and the data model; conforms to `dataset.schema.yaml`).
  - Verification: `pytest code/tests/test_baseline.py` confirms correct baseline shifts, the exact halt message on missing hosts, and that `filtered.csv` validates against `dataset.schema.yaml`.

- [ ] T005 Run the end-to-end data pipeline (T001 → T004, **including T013** for provenance and dataset-size logging). This produces `data/curated/filtered.csv` (SSoT), `data/curated/baselines.csv`, and `data/curated/data_provenance.json`. Afterwards execute the **schema-validation script** `code/validation/validate_curated.py` to ensure `filtered.csv` conforms to `dataset.schema.yaml` and contains ≥1 valid row.
  - Verification: `validate_curated.py` returns exit code 0; its success is asserted in the integration test.

## Phase 2: Complete the study and validate its evidence

- [ ] T006 [US2] [FR-003, FR-004] Implement Random Forest training in `code/models/train_rf.py`: split `data/curated/filtered.csv` (80/20 hold-out before tuning if <50 rows, otherwise nested 5-fold CV with stratification by host metal, falling back to random split with warning). Perform `GridSearchCV` over `max_depth` 3-10 and `n_estimators` 50-200, maximizing R²; tie-break on lowest `max_depth` then lowest `n_estimators`. Save the model to `models/final_rf.pkl` and metrics (R², RMSE, MAE) to `models/rf_metrics.json`. Record training CPU time to `data/logs/training_time_rf.log`. The unit test does NOT assert runtime (environment-dependent); the ≤15-minute budget assertion lives in the T012 integration test, which parses the log.
  - Verification: `pytest code/tests/test_train_rf.py` checks deterministic seeds, split logic, tie-breaking, metric schema, and that CPU time is logged; the runtime-budget assertion is deferred to T012.

- [ ] T014 [US2] [FR-003, FR-004] Implement Gradient Boosting training in `code/models/train_gb.py` with the same protocol as T006 (input `data/curated/filtered.csv`), saving to `models/final_gb.pkl` and `models/gb_metrics.json`, with CPU time logged to `data/logs/training_time_gb.log`. Tie-breaking and runtime-handling requirements are identical to T006.
  - Verification: `pytest code/tests/test_train_gb.py` analogous to RF test.

- [ ] T007 [US3] [FR-005] Implement Linear Regression in `code/models/train_linear.py`: fit on the same training split of `data/curated/filtered.csv` using the three feature columns `size_mismatch`, `electronegativity_diff`, `valence_electron_diff` (all present in `filtered.csv` per T003/T004). Extract the `size_mismatch` coefficient, its standard error, p-value, and a 95 % bootstrap confidence interval using **exactly 10,000 resamples** with the **percentile-inversion p-value procedure** (sampling with replacement, stratified by host when possible), matching the data model's contract for `models/linear_coef.json`. Write results to `models/linear_coef.json` conforming to `model_output.schema.yaml`.
  - Verification: `pytest code/tests/test_train_linear.py` validates coefficient extraction, CI ordering, the 10,000-resample count, and the percentile-inversion p-value procedure.

- [ ] T008 [US3] [FR-005, FR-009] Implement `code/validation/sensitivity_analysis.py` (the filename mandated by the plan's FR/SC coverage map): use predictions from the **Random Forest** model (`models/final_rf.pkl`) together with baseline shifts from `data/curated/filtered.csv` to sweep the classification threshold over `{0.45,0.46,…,0.55}` eV. Compute classification rates, calculate the stability index `std(rates) / (0.55-0.45)`, and write `validation/stability_index_report.json` (schema-compliant with `validation_report.schema.yaml`) and a plot `validation/threshold_sweep.png`.
  - Verification: `pytest code/tests/test_sensitivity.py` validates sweep grid, index formula, and report schema.

- [ ] T009 [US3] **Depends on: T006, T007, T008, T014.** Implement `code/validation/stats.py` to aggregate bootstrap statistics (from T007), model metrics (from T006/T014), and stability metrics (from T008) into `validation/validation_report.json`. Required fields: `significance_verified` (bool), `model_comparison` (R²/RMSE/MAE vs. mean predictor for RF and GB), `stability_target_met` (bool), and `low_predictive_power` (bool; set to true with the exact string `"Low Predictive Power - Null Result Hypothesis Supported"` in a `low_predictive_power_note` field when the best test R² < 0.1, per the spec's Edge Cases — this is a valid scientific outcome and does NOT trigger the data-halt condition).
  - Verification: since no dedicated JSON schema exists for this report, the test performs explicit field-level checks: all four required keys present with correct types, `model_comparison` values traceable to `models/rf_metrics.json` / `models/gb_metrics.json`, `significance_verified` traceable to `models/linear_coef.json`, and `stability_target_met` traceable to `validation/stability_index_report.json`; the `low_predictive_power` flag is exercised with a fixture having R² < 0.1.

## Phase 3: Reproducible results and paper handoff

- [ ] T010 Generate tables and figures from validated outputs:
  * `data/results/model_comparison.csv` (metrics table)
  * `figures/shift_vs_mismatch.png` (scatter with fitted linear trend)
  * Create a **spot-check script** `code/validation/spot_check.py` that randomly samples 5 rows from `data/curated/filtered.csv` and confirms that plotted values match the CSV entries.
  - Verification: spot-check script runs without error; a test `pytest code/tests/test_spot_check.py` asserts consistency.

- [ ] T011 Write a concise methods/results account in `specs/001-predict-alloy-diffusion-on-the/research.md` (or `reports/final_report.md`). Every numeric claim must reference a value from `models/*.json`, `validation/*.json`, or the curated CSV files. The report MUST state the `low_predictive_power` outcome (including the exact flag string) whenever T009 sets it, per the spec's Edge Cases. Include discussion of limitations, observational nature, and any low-R² outcomes as valid findings.
  - Verification: the named lint script `code/validation/check_report_sources.py` extracts every numeric literal from the report and requires each to match (within floating-point tolerance) a value appearing in `models/*.json`, `validation/*.json`, or `data/curated/*.csv`; it exits 0 only if every number is sourced, and its pass is asserted by `pytest code/tests/test_check_report_sources.py`.

- [ ] T012 Re-run the documented workflow end-to-end (as per `quickstart.md`). Verify: all tests pass, curated files validate against schemas, **peak RSS ≤ 7 GB**, **total runtime ≤ 6 h**, **training CPU-time ≤ 15 min per model** (parsed from `data/logs/training_time_rf.log` and `data/logs/training_time_gb.log`, produced by T006/T014), **model-training CPU-time ≤ 2 CPU-hours**, and **raw dataset size ≤ 10 MB** (parsed from `data/logs/dataset_size.log`, produced by T013). Log resource usage to `data/logs/resource_usage.log` and confirm SC-004 and Principle VI compliance. Document the paper-stage handoff (tables, figures, report locations) in `quickstart.md`.
  - Verification: a final integration test parses `resource_usage.log`, `training_time_*.log`, and `dataset_size.log` and asserts all limits.

## Dependencies and requirement coverage (updated)

| Requirement | Task(s) | Key artifacts |
|---|---|---|
| FR-001 (ingest/filter) | T015 (gate), T001 | `code/data/streaming_loader.py`, `data/curated/solute_raw.csv`, `data/curated/baselines.csv` |
| FR-002 (size_mismatch) | T003 | `code/processing/feature_engineering.py`, `data/curated/engineered.csv` |
| FR-003 (RF/GB) | T006, T014 | `models/final_rf.pkl`, `models/final_gb.pkl` |
| FR-004 (nested CV/hold-out) | T006, T014 | metric JSONs |
| FR-005 (linear + sweep) | T007, T008 | `models/linear_coef.json`, `validation/stability_index_report.json` |
| FR-006 (baseline source) | T004 | `code/processing/baseline.py`, `data/curated/baselines.csv` |
| FR-007 (provenance) | T013 | `data/curated/data_provenance.json` |
| FR-008 (baseline_shift from filtered.csv) | T004 | `data/curated/filtered.csv` (SSoT) |
| FR-009 (stability report) | T008 | `code/validation/sensitivity_analysis.py`, `validation/stability_index_report.json` |
| Edge case (R² < 0.1 flag) | T009, T011 | `validation/validation_report.json` (`low_predictive_power`) |
| SC-001 (R² > mean) | T006, T014, T009 | metric JSONs |
| SC-002 (coef significance) | T007, T009 | `models/linear_coef.json` |
| SC-003 (stability ≤ 0.05) | T008, T009 | `validation/stability_index_report.json` |
| SC-004 (resource limits) | T012, T013 | `data/logs/resource_usage.log`, `data/logs/dataset_size.log` |
| Constitution I (pinned deps) | T013 | `code/requirements.txt` |

Execution order (matches checklist body order):
T015 (blocking gate) → T001 (redo, real runnable `streaming_loader.py` with verified real source; dual-mode branch active only under amended FR-001) → T013 → T002 → T003 → T004 → T005 → T006 → T014 → T007 → T008 → T009 → T010 → T011 → T012.