# Tasks: Predicting the Yield Strength of High‑Entropy Alloys

**Inputs**: `spec.md`, `plan.md`, JSON‑schema contracts in `specs/001-predicting-the-yield-strength-of-high-en/contracts/`.  
**Goal**: Deliver the smallest complete study that satisfies every functional requirement (FR‑001 – FR‑024) and success criterion (SC‑001 – SC‑011) in the specification. All data are real, fetched from the authorized Zenodo archive; no synthetic fall‑backs are permitted. Every numeric value in the final markdown report must be programmatically generated and linked to a provenance ID.

---

## Phase 0 – Project Setup  

- [ ] T000 [P0] **Project environment setup** – create a virtual environment, install pinned dependencies from `requirements.txt`, and validate `requirements.txt` against its schema.  
  - **Implementation**: `code/setup/setup_env.py`  
  - **Verification**: `code/tests/test_setup_env.py` asserts that the virtualenv is created, all packages install without error, and the schema validation passes.

---

## Phase 1 – Data acquisition & descriptor calculation  

- [ ] T001 [P1] [FR‑001] **Download curated HEA dataset from Zenodo** – fetch from `[UNRESOLVED-CLAIM: https://zenodo.org/record/1234567/files/hea_dataset.csv` — HTTP 404] and write to `data/raw/heas_raw.csv`; validate each record against `contracts/dataset.schema.yaml`; abort with a clear error if any required field is missing.  
  - **Implementation**: `code/data/fetch_heas.py`.  
  - **Verification**: `code/tests/test_fetch_heas.py` checks that a record missing `yield_strength` raises `ValueError` and that the produced CSV passes schema validation.

- [ ] T002 [P1] [FR‑002] **Compute composition‑based descriptors** from `data/raw/heas_raw.csv` using the frozen elemental‑property table `data/raw/elemental_properties.csv`; output `data/processed/hea_descriptors.csv` and validate against both `contracts/descriptor.schema.yaml` and `contracts/hea_schema.schema.yaml`.  
  - **Implementation**: `code/data/descriptors.py` (calculates mixing entropy, atomic‑size mismatch δ, electronegativity variance Δχ, VEC, melting‑point variance).  
  - **Verification**: `code/tests/test_descriptors.py` contains known‑value checks (e.g., CoCrFeMnNi) and asserts that a missing element symbol raises a clear `KeyError`.

- [ ] T014 [P1] [FR‑009] **Validate user‑provided composition CSV** – accept a CSV at `data/input/compositions.csv`, validate each record against `contracts/hea_composition.schema.yaml`; abort with a clear error if any required field (e.g., missing element fraction) is absent.  
  - **Implementation**: `code/data/validate_user_composition.py`.  
  - **Verification**: `code/tests/test_user_composition.py` asserts that missing fields raise `ValueError` with an informative message.

---

## Phase 2 – Power analysis, modeling, validation, and stability  

- [ ] T004 [P2] [FR‑015] **Statistical power analysis** targeting power ≥ 0.80, α = 0.05, effect size derived from R² ≥ 0.6; write `data/results/power_analysis.json` (`required_n`, `achieved_power`); abort if actual N < required N.  
  - **Implementation**: `code/analysis/power.py` (uses `statsmodels.stats.power.FTestPower`).  
  - **Verification**: `code/tests/test_power.py` asserts that the abort path triggers when a deliberately truncated CSV is supplied.

- [ ] T005 [P2] [FR‑003][FR‑016] **Train‑test split, VIF handling, and Random Forest training** – 80/20 split (seed 42) → `data/processed/train.parquet` / `data/processed/test.parquet`; compute VIF for each descriptor, drop any with VIF > 5 and record `data/results/vif_summary.json`; train `RandomForestRegressor(n_estimators=500, max_features='sqrt', random_state=42)` with 5‑fold CV; persist model to `data/results/model_rf.joblib` and CV scores to `data/results/cv_metrics.json`.  
  - **Implementation**: `code/models/train_full.py`.  
  - **Verification**: `code/tests/test_train_full.py` checks that no descriptor with VIF > 5 remains and that re‑running with the same seed yields identical CV metrics.

- [ ] T006 [P2] [FR‑004][FR‑014] **Test‑set evaluation & descriptor‑target correlation** – load the trained model, predict on `data/processed/test.parquet`, compute R², Pearson r, two‑tailed p‑value, MAE, RMSE, and 95 % bootstrap CIs (1 000 resamples); write `data/results/metrics.json` (validated against `contracts/metrics.schema.yaml`).  
  - Separately, using **only the training data**, compute Pearson r and p‑value for each descriptor, flag those with |r| > 0.5 & p < 0.01, and write `data/results/descriptor_correlation.json`.  
  - **Implementation**: `code/analysis/evaluate.py`.  
  - **Verification**: `code/tests/test_evaluate.py` validates schema compliance and asserts that **at least two** descriptors meet the significance thresholds (or logs an honest failure).

- [ ] T007 [P2] [FR‑005][FR‑006] **Permutation importance with Holm–Bonferroni correction** – run `sklearn.inspection.permutation_importance` on the held‑out test set with ≥ 1 000 permutations per feature; perform a non‑parametric permutation test, apply Holm‑Bonferroni correction (α = 0.05); write `data/results/perm_importance.json` (validated against `contracts/importance.schema.yaml`).  
  - **Implementation**: `code/analysis/importance.py`.  
  - **Verification**: `code/tests/test_importance.py` verifies that every feature record contains `importance_score`, `raw_p_value`, and `holm_bonferroni_p`, and that the correction matches a hand‑computed example.

- [ ] T008 [P2] [FR‑017] **External validation dataset acquisition & evaluation** – download a second, disjoint Zenodo release from `[UNRESOLVED-CLAIM: https://zenodo.org/record/7654321/files/hea_external.csv` — HTTP 404], save to `data/external/validation.csv`; validate against `contracts/dataset.schema.yaml`; compute descriptors (`data/external/validation_descriptors.csv`) using the same descriptor code; evaluate the trained model, write `data/results/external_metrics.json`; document measurement‑protocol differences in `data/results/external_provenance.md`.  
  - **Implementation**: `code/data/fetch_external.py`.  
  - **Verification**: `code/tests/test_external.py` asserts that `validation.csv` shares no `alloy_id` with the primary data and that the metrics file passes schema validation.

- [ ] T009 [P2] [FR‑021] **Stability assessment across three seeds** – repeat the full pipeline (T005 → T006 → T007) for seeds 111, 222, 333; record top‑5 feature rankings per run in `data/results/stability_rankings_seed{XXX}.json`; aggregate into `data/results/stability_rankings.json` and compute the maximum rank difference, requiring ≤ 1.  
  - **Implementation**: `code/analysis/stability.py`.  
  - **Verification**: `code/tests/test_stability.py` checks that three ranking lists exist and that the reported `max_rank_difference` matches the raw rankings.

- [ ] T015 [P2] [FR‑018] **Comprehensive contract validation** – run `jsonschema` validation on **all** generated artifacts (raw dataset, descriptor table, VIF summary, metrics, importance, stability rankings, manifest, runtime summary); abort on any validation failure.  
  - **Implementation**: `code/validation/contract_check.py`.  
  - **Verification**: `code/tests/test_contracts.py` ensures every artifact passes its respective schema.

---

## Phase 3 – Reporting, verification, and handoff  

- [ ] T010 [P3] **Figure generation** – produce PNGs directly from validated JSON artifacts:  
  1. `figures/pred_vs_meas.png` (predicted vs. measured scatter with 1:1 line and bootstrap CI band)  
  2. `figures/descriptor_corr.png` (bar chart of descriptor‑target Pearson r with p‑value annotations)  
  3. `figures/perm_importance.png` (ranked permutation‑importance plot with corrected‑p‑value markers)  
  - **Implementation**: `code/reporting/figures.py`.  
  - **Verification**: `code/tests/test_figures.py` asserts each PNG is non‑empty and that re‑generation with unchanged inputs yields identical byte streams (hash comparison).

- [ ] T011 [P3] [FR‑008] **Provenance‑tracked markdown report** – assemble `paper/report.md` containing the nine mandatory sections (dataset statistics, power‑analysis justification, VIF summary, model performance with CIs, descriptor‑target correlations, permutation importance with corrected p‑values, external‑validation results & protocol, stability assessment, provenance log).  
  - Every numeric value is emitted with a provenance ID (e.g., `[PV‑r2]`) and a mapping entry in `data/results/provenance_linking.json` linking the ID to the source artifact and code block.  
  - Write `data/results/manifest.json` (run_id, timestamp, seeds, package_versions, SHA‑256 checksums of **all** input and output files) validated against `contracts/manifest.schema.yaml`.  
  - **Implementation**: `code/reporting/report.py`.  
  - **Verification**: `code/tests/test_report.py` uses regexes to confirm all required section headings exist, that each numeric token has a matching entry in `provenance_linking.json`, and that manifest checksums are correct.

- [ ] T012 [P3] **Success‑criteria verification & handoff** – parse every artifact under `data/results/` and produce `data/results/verification_report.json` with pass/fail for each SC‑001 – SC‑011 (including honest failure messages if thresholds are not met).  
  - Update `quickstart.md` with the exact runnable command sequence and the location of `paper/report.md`.  
  - Create `data/results/final_handoff.json` containing artifact paths, their manifest hashes, and a pointer to `paper/report.md` for the downstream paper stage.  
  - **Implementation**: `code/verify_success_criteria.py`.  
  - **Verification**: `code/tests/test_handoff.py` ensures that all criteria report “pass” and that the hashes in `final_handoff.json` match those recorded in `manifest.json`.

- [ ] T013 [P3] **Full reproducibility check** – execute the documented workflow from a fresh clone via `python -m code.pipeline.full_run`; then re‑run the verification step; confirm that **all** generated files (`*.csv`, `*.json`, `*.joblib`, `*.png`, `report.md`) have SHA‑256 checksums identical to those recorded in `manifest.json`.  
  - **Implementation**: `code/pipeline/full_run.py`.  
  - **Verification**: CI step runs this task; success is required for the pipeline to be marked “pass”.

- [ ] T016 [P3] [II] **Citation verification (Principle II)** – invoke the Reference‑Validator Agent on every external citation present in `spec.md`, `plan.md`, `code/`, and `report.md`; ensure title‑token overlap ≥ 0.7; abort the pipeline if any citation fails validation.  
  - **Implementation**: `code/validation/citation_check.py`.  
  - **Verification**: `code/tests/test_citation_validation.py` confirms that a deliberately mismatched citation triggers pipeline abort.

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
| FR‑009 (missing‑field abort) | T014 | `python -m code.data.validate_user_composition` |
| FR‑014 (descriptor‑target correlation) | T006 | `data/results/descriptor_correlation.json` |
| FR‑015 / FR‑022 / FR‑023 (power analysis) | T004 | `python -m code.analysis.power` |
| FR‑016 (VIF) | T005 | `data/results/vif_summary.json` |
| FR‑017 (external validation) | T008 | `python -m code.data.fetch_external` |
| FR‑018 (contract validation) | T015 | `pytest code/tests/test_contracts.py` |
| FR‑021 (stability) | T009 | `data/results/stability_rankings.json` |
| FR‑030 (citation verification) | T016 | `python -m code.validation.citation_check` |
| SC‑001 – SC‑011 (success criteria) | T012 | `python -m code.verify_success_criteria` |
| SC‑013 (CI success) – out‑of‑scope | — | — |

**Execution order**: T000 → T001 → T002 → T014 → T004 → T005 → T006 → T007 → T008 → T009 → T015 → T010 → T011 → T012 → T013 → T016. All downstream tasks depend only on artifacts produced by their predecessors.

---  

*All tasks are unchecked (`[ ]`) until the corresponding implementation passes its verification step. Checked boxes will be added automatically by the CI system once artifact validation succeeds.*  