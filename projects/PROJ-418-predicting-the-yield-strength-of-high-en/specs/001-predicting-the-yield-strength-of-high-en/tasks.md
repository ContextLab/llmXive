# Tasks: Predicting the Yield Strength of High‑Entropy Alloys

**Inputs**: `spec.md`, `plan.md`, JSON‑schema contracts in `specs/001-predicting-the-yield-strength-of-high-en/contracts/`.  
**Goal**: Deliver the smallest complete study that satisfies every functional requirement (FR‑001 – FR‑024) and success criterion (SC‑001 – SC‑011) in the specification. All data are real, fetched from the authorized Zenodo archive; no synthetic fall‑backs are permitted. Every numeric value in the final markdown report must be programmatically generated and linked to a provenance ID.

---

## Phase 0 – Project Setup  

- [ ] T000 [P0] [FR-001] **Project environment setup.**  
  Implement `code/setup/setup_env.py` that creates a virtual environment, installs pinned dependencies from `requirements.txt`, and validates `requirements.txt` against `contracts/requirements.schema.yaml`.  
  **Verification:** a pytest `code/tests/test_setup_env.py` asserts that the virtualenv is created, all packages install without error, and the schema validation passes.

---

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] T001 [P1] [FR-001] **Data acquisition – real HEA dataset (Zenodo).**  
  Implement `code/data/fetch_heas.py` that downloads the curated HEA yield‑strength dataset from the Zenodo archive (URL placeholder **INSERT_ZENODO_URL_HERE**).  
  - Writes a **CSV** `data/raw/heas_raw.csv` with columns `alloy_id, composition, yield_strength, phase, temperature`.  
  - Validates each row against `contracts/dataset.schema.yaml`.  
  - Aborts with a clear error if any required field is missing (fulfills FR‑009).  
  **Verification:** a unit test `code/tests/test_fetch_heas.py` checks that a record missing `yield_strength` raises `ValueError`; after execution `data/raw/heas_raw.csv` exists, is non‑empty, and passes JSON‑schema validation.

- [ ] T002 [P1] [FR-002] **Descriptor calculation (CSV).**  
  Implement `code/data/descriptors.py` that reads `data/raw/heas_raw.csv`, loads the frozen elemental‑property table `data/raw/elemental_properties.csv` (validated against `contracts/elemental_properties.schema.yaml`), and computes the five composition‑only descriptors: `mixing_entropy`, `atomic_size_mismatch` (δ), `electronegativity_variance` (Δχ), `vec`, `tm_variance`.  
  - Writes **CSV** `data/processed/hea_descriptors.csv` containing `alloy_id, composition, mixing_entropy, atomic_size_mismatch, electronegativity_variance, vec, tm_variance, yield_strength`.  
  - Validates rows against both `contracts/descriptor.schema.yaml` and `contracts/hea_schema.schema.yaml`.  
  **Verification:** `code/tests/test_descriptors.py` contains known‑value checks (e.g., CoCrFeMnNi) and asserts that missing element symbols raise a clear `KeyError`.

---

## Phase 2 – Complete study and validation  

- [ ] T004 [US‑1] **Statistical power analysis.**  
  Implement `code/analysis/power.py` that:  
  - Uses `statsmodels.stats.power.FTestPower` with target power ≥ 0.80, α = 0.05, effect size derived from R² ≥ 0.6 (Cohen’s f² ≈ 1.5).  
  - Computes required minimum sample size and achieved power based on the actual count of rows in `data/raw/heas_raw.csv`.  
  - Writes `data/results/power_analysis.json` (`required_n`, `achieved_power`).  
  - Aborts with a clear error if actual N < required N (fulfills FR‑015, FR‑023).  
  **Verification:** a test `code/tests/test_power.py` asserts that the abort path triggers when a deliberately truncated CSV is supplied.

- [ ] T005 [US‑1] **Full training pipeline with VIF handling.**  
  Implement `code/models/train_full.py` that:  
  1. Loads `data/processed/hea_descriptors.csv`.  
  2. Performs the same 80/20 split (seed 42) and saves `data/processed/train.parquet` / `data/processed/test.parquet` (validated against `contracts/processed_data.schema.yaml`).  
  3. Computes Variance Inflation Factor for each descriptor on the training set (statsmodels).  
  4. Drops any descriptor with VIF > 5, records the VIF values and dropped features in `data/results/vif_summary.json`.  
  5. Trains a **RandomForestRegressor** (`n_estimators=500`, `max_features='sqrt'`) with 5‑fold cross‑validation on the cleaned training matrix.  
  6. Persists the final model to `data/results/model_rf.joblib` and CV scores to `data/results/cv_metrics.json`.  
  **Verification:** after run, `data/results/vif_summary.json` shows no descriptor with VIF > 5 remaining; re‑running with the same seed reproduces identical CV metrics (asserted in `code/tests/test_train_full.py`).

- [ ] T006 [US‑1] **Test‑set evaluation & descriptor‑target correlation (training data).**  
  Implement `code/analysis/evaluate.py` that:  
  - Loads the trained model and `data/processed/test.parquet`.  
  - Predicts yield strength, computes R², Pearson r, two‑tailed p‑value, MAE, RMSE, and 95 % bootstrap confidence intervals (1 000 resamples, seeded).  
  - Writes `data/results/metrics.json` validated against `contracts/metrics.schema.yaml`.  
  - Separately, using **only the training data**, computes Pearson r and p‑value for each descriptor; flags those with |r| > 0.5 and p < 0.01, and writes `data/results/descriptor_correlation.json`.  
  **Verification:** `code/tests/test_evaluate.py` checks that the JSON files conform to their schemas and that at least one descriptor passes the |r| > 0.5 / p < 0.01 threshold (or records a truthful failure).

- [ ] T007 [US‑1] **Permutation importance with Holm–Bonferroni correction.**  
  Implement `code/analysis/importance.py` that runs `sklearn.inspection.permutation_importance` on the held‑out test set with **≥ 1 000 permutations per feature**.  
  - Performs a non‑parametric permutation test for each feature, obtains raw p‑values, applies Holm‑Bonferroni correction (α = 0.05).  
  - Writes `data/results/perm_importance.json` validated against `contracts/importance.schema.yaml`.  
  **Verification:** a unit test `code/tests/test_importance.py` verifies the correction against a hand‑computed example and that every feature record contains `importance_score`, `raw_p_value`, and `holm_bonferroni_p`.

- [ ] T008 [US‑1] **External validation dataset acquisition & evaluation.**  
  Implement `code/data/fetch_external.py` that performs a second, disjoint Zenodo query (different release) and writes **CSV** `data/external/validation.csv` (same columns as `heas_raw.csv`).  
  - Validates against `contracts/dataset.schema.yaml`.  
  - Re‑uses `code/data/descriptors.py` to generate `data/external/validation_descriptors.csv`.  
  - Loads the trained model from T005, predicts on this external set, and writes `data/results/external_metrics.json` (schema `contracts/metrics.schema.yaml`).  
  - Documents measurement‑protocol differences and any confounds in `data/results/external_provenance.md`.  
  **Verification:** a test `code/tests/test_external.py` asserts that `validation.csv` shares no `alloy_id` with the primary data and that the metrics file passes schema validation.

- [ ] T009 [US‑1] **Stability assessment across three seeds.**  
  Implement `code/analysis/stability.py` that repeats the full pipeline (T005 → T006 → T007) for seeds **111, 222, 333**.  
  - For each run, records the top‑5 feature rankings in `data/results/stability_rankings_seed{XXX}.json`.  
  - Aggregates the three rankings into `data/results/stability_rankings.json` and computes the maximum rank difference; writes a flag `max_rank_difference ≤ 1` (fulfills FR‑021, SC‑006).  
  **Verification:** `code/tests/test_stability.py` checks that the aggregated JSON contains three ranking lists and that the computed `max_rank_difference` matches the raw rankings.

- [ ] T010 [US‑1] **Figure generation.**  
  Implement `code/reporting/figures.py` that produces PNG files directly from the validated JSON artifacts:  
  1. `figures/pred_vs_meas.png` – predicted vs. measured scatter with 1:1 line and bootstrap CI band.  
  2. `figures/descriptor_corr.png` – bar chart of descriptor‑target Pearson r with p‑value annotations.  
  3. `figures/perm_importance.png` – ranked permutation‑importance plot with corrected‑p‑value markers.  
  All figures are generated deterministically (seeded) and saved under `figures/`.  
  **Verification:** a test `code/tests/test_figures.py` asserts that each PNG file is non‑empty and that re‑generation with unchanged inputs yields identical byte streams (hash comparison).

- [ ] T011 [US‑1] **Provenance‑tracked report and manifest.**  
  Implement `code/reporting/report.py` that assembles `paper/report.md` containing the nine mandatory sections (dataset statistics, power‑analysis justification, VIF summary, model performance with CIs, descriptor‑target correlations, permutation importance with corrected p‑values, external‑validation results & protocol, stability assessment, provenance log).  
  - Every numeric value is emitted with a provenance ID (e.g., `[PV-r2]`) and a mapping entry in `data/results/provenance_linking.json` linking the ID to the source artifact and code block (fulfills FR‑010, FR‑024, SC‑011).  
  - Writes `data/results/manifest.json` (run_id, timestamp, seeds, package_versions, SHA‑256 checksums of **all** input and output files) validated against `contracts/manifest.schema.yaml`.  
  **Verification:** `code/tests/test_report.py` uses regexes to confirm all required section headings exist, that each numeric token matches an entry in `provenance_linking.json`, and that the manifest checksums are correct.

- [ ] T012 [US‑1] **Success‑criteria verification and handoff.**  
  Implement `code/verify_success_criteria.py` that parses every artifact under `data/results/` and produces `data/results/verification_report.json` with a pass/fail entry for each SC‑001 – SC‑011 (including honest failure messages if thresholds are not met).  
  - Updates `quickstart.md` with the exact runnable command sequence and the expected location of `paper/report.md`.  
  - Writes `data/results/final_handoff.json` containing artifact paths, their manifest hashes, and a pointer to `paper/report.md` for the downstream paper stage.  
  **Verification:** after a clean run, `verification_report.json` reports “pass” for every criterion; `final_handoff.json` contains matching SHA‑256 hashes (checked by a test `code/tests/test_handoff.py`).

- [ ] T013 [US‑1] **Full reproducibility check.**  
  Execute the documented workflow from scratch (`python -m code.pipeline.full_run`) on a fresh clone, then re‑run `code/verify_success_criteria.py`.  
  - Confirm that **all** generated files (`*.csv`, `*.json`, `*.joblib`, `*.png`, `report.md`) have identical SHA‑256 checksums to those recorded in `manifest.json`.  
  - If any mismatch occurs, the task fails and the discrepancy is logged.  
  **Verification:** a CI step runs this task; success is required for the pipeline to be marked “pass”.

---

### Dependency & Requirement Mapping

| Requirement | Task(s) | Demonstrating command |
|-------------|---------|-----------------------|
| FR‑001 (data acquisition) | T001 | `python -m code.data.fetch_heas` |
| FR‑002 (descriptor calculation) | T002 | `python -m code.data.descriptors` |
| FR‑003 (model training) | T005 | `python -m code.models.train_full` |
| FR‑004 (test evaluation) | T006 | `python -m code.analysis.evaluate` |
| FR‑005 / FR‑006 (permutation importance) | T007 | `python -m code.analysis.importance` |
| FR‑008 / FR‑010 / FR‑024 (report & provenance) | T011 | `python -m code.reporting.report` |
| FR‑009 (missing‑field abort) | T001, T002 | unit tests in `code/tests/` |
| FR‑014 (descriptor‑target correlation) | T006 | `data/results/descriptor_correlation.json` |
| FR‑015 / FR‑022 / FR‑023 (power analysis) | T004 | `python -m code.analysis.power` |
| FR‑016 (VIF) | T005 | `data/results/vif_summary.json` |
| FR‑017 (external validation) | T008 | `python -m code.data.fetch_external` |
| FR‑018 (contract validation) | T010, T011, T012 | `pytest code/tests/` |
| FR‑021 (stability) | T009 | `data/results/stability_rankings.json` |
| SC‑001 – SC‑011 (success criteria) | T012 | `python -m code.verify_success_criteria` |
| SC‑013 (CI success) – out‑of‑scope | — | — |

**Execution order:** T000 → T001 → T002 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013. All downstream tasks depend only on the artifacts produced by their predecessors.

--- 

*All tasks are unchecked (`[ ]`) until the corresponding implementation passes its verification step. Checked boxes will be added automatically by the CI system once the artifact validation succeeds.*  