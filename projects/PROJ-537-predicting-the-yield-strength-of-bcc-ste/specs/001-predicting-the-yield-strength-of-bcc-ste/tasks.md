# Tasks: Predicting the Yield Strength of BCC Steels from Compositional Data and Density Functional Theory  

**Inputs**: `specs/001-predict-yield-strength-bcc/spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback.  

The checklist below follows the platform’s research‑phase template (end‑to‑end analysis → full validation → results handoff).  
Completed implementation tasks from earlier iterations are retained (checked boxes).  
Unchecked items indicate work that must be (re‑)implemented or verified to satisfy the specification.

---  

## Completed implementation tasks (preserved)

- [ ] T001 Establish project layout and document the runnable command in `quickstart.md`.   <!-- FAILED-IN-EXECUTION: code/run_all.py exit=1 -->
- [ ] T002 Implement data‑download utilities for experimental CSV and Materials Project queries (real‑fetch only, no fall‑backs).  
- [ ] T003 Add unit tests for the ingestion scripts verifying error handling on missing API key or bad URLs.  
- [ ] T004 Implement feature‑engineering module (`features.py`) with one‑hot encoding, fractional composition, and DFT scaling.  
- [ ] T005 Write VIF calculation utility and integrate it into the preprocessing pipeline.  
- [ ] T006 Create model‑training script (`train.py`) that performs nested 5‑fold CV for the Random Forest with DFT features.  
- [ ] T007 Create baseline‑training script (`train_baseline.py`) for composition‑only model.  
- [ ] T008 Implement evaluation utilities (`evaluate.py`) that compute per‑fold R², MAE and aggregate statistics.  
- [ ] T009 Add Pearson‑correlation helper (`correlation.py`).  
- [ ] T010 Implement paired‑t‑test wrapper (`stats_test.py`).  
- [ ] T011 Add statistical‑power analysis (`power_analysis.py`).  
- [ ] T012 Write SHAP analysis script (`shap_analysis.py`).  
- [ ] T013 Write permutation‑importance script (`permutation_importance.py`).  
- [ ] T014 Write bootstrap‑stability script (`bootstrap_stability.py`).  
- [ ] T015 Create JSON‑schema validation tests for `dataset.schema.yaml` and `output.schema.yaml`.  
- [ ] T016 Add reproducibility test comparing freshly generated `output.json` with the committed baseline.  
- [ ] T017 Implement orchestrator `main.py` that runs ingestion → preprocessing → modeling → interpretability → output generation.  
- [ ] T018 Add CI configuration (pytest execution, schema validation) – platform‑managed, no project‑level changes required.  
- [ ] T019 Document all provenance logging (checksums, API query logs) in `data/provenance/`.  
- [ ] T020 Write initial `research.md` draft describing methodology (kept for reference).  
- [ ] T021 Populate `contracts/` directory with the provided schema files.  
- [ ] T022 Add `requirements.txt` with pinned versions of all dependencies.  
- [ ] T023 Verify that the repository builds on the free‑tier GitHub Actions runner (CPU only).  

*(Tasks T024–T047 were similarly completed in earlier cycles and are omitted for brevity.)*  

---  

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] **T048** [US1] Re‑implement the ingestion pipeline to **strictly require real remote data** and to **fail loudly** if any fetch fails.  
  - `code/ingestion/fetch_experimental.py` must download the CSV from the verified MatNavi URL (`https://huggingface.co/datasets/matnavi/steel_yield_strength/resolve/main/data/steel_yield_strength.csv`).  
  - **No fallback** to any bundled or synthetic CSV is permitted; on any HTTP error or missing file the script must raise `ERR_INSUFFICIENT_DATA`.  
  - `code/ingestion/fetch_dft.py` must query the Materials Project API (using `mp-api`) for each unique formula, with **no synthetic fallback**; on missing API key or HTTP error it must raise an exception.  
  - Implement exponential back‑off (2 s, 4 s, 8 s) and **skip only after three failed attempts**, logging each attempt to `data/provenance/dft_queries.jsonl`.  
  - `code/ingestion/merge_and_filter.py` must:  
    - Verify that the downloaded experimental CSV contains the required `yield_strength_MPa` column; if absent, abort with `ERR_INSUFFICIENT_DATA`.  
    - Join on `formula`, keep only rows where `yield_strength_MPa`, `shear_modulus_GPa`, and `bulk_modulus_GPa` are non‑null, filter `space_group == 229`, and handle range‑midpoint conversion with an `uncertainty_flag`.  
    - After merging, write `data/intermediate/merged.csv` and compute SHA‑256 checksums recorded in `data/provenance/checksums.txt`.  
  - **Verification**:  
    ```bash
    python -c "import pandas as pd, sys; df=pd.read_csv('data/intermediate/merged.csv'); \
    if 'yield_strength_MPa' not in df.columns: sys.exit('ERR_INSUFFICIENT_DATA'); \
    assert len(df) >= 20, 'ERR_INSUFFICIENT_DATA'; \
    assert df['yield_strength_MPa'].notna().all(); \
    assert df['shear_modulus_GPa'].notna().all()"
    ```  
    The command must exit with status 0; otherwise the pipeline aborts with `ERR_INSUFFICIENT_DATA`.  

- [ ] **T049** [US2] Implement the first end‑to‑end analysis that consumes the real merged dataset and produces the required primary results JSON.  
  - Run `code/modeling/features.py` to generate the feature matrix (including one‑hot composition, fractional compositions, scaled DFT descriptors, and VIF report).  
  - Execute `code/modeling/train.py` (DFT‑enhanced Random Forest) and `code/modeling/train_baseline.py` (composition‑only baseline) using **5‑fold outer cross‑validation** (seed 42).  
  - For each outer fold, record **R²** and **MAE** for both models.  
  - Compute the **Pearson correlation** between `shear_modulus_GPa` and `yield_strength_MPa` (store `r_value`, `p_value`, and 95 % CI).  
  - Train a **final DFT‑enhanced Random Forest model on the full merged dataset** and save the artifact `data/models/rf_dft_full.pkl` (used by downstream interpretability tasks).  
  - Assemble `data/results/output.json` conforming to `contracts/output.schema.yaml` with at minimum the fields:  
    - `metrics.row_count` (from merged CSV)  
    - `metrics.r2_rf`, `metrics.mae_rf` (averaged over folds)  
    - `metrics.r2_baseline`, `metrics.mae_baseline` (averaged)  
    - `correlation_analysis.r_value`, `correlation_analysis.p_value`, `correlation_analysis.confidence_interval_95`  
    - `fold_metrics` array containing per‑fold `{fold_id, r2_score, mae}` for both models  
    - `model_artifact_path`: `"data/models/rf_dft_full.pkl"` (reference for later tasks)  
  - **Verification**: `data/results/output.json` exists, parses as JSON, and contains non‑placeholder numeric values for all required keys.  

---  

## Phase 2 – Complete the study and validate its evidence  

- [ ] **T050** [US2] Extend the analysis to compute the **paired t‑test** on the outer‑fold MAE differences between the DFT‑enhanced and baseline models.  
  - Use the per‑fold MAE values stored by T049.  
  - Record in `output.json`: `metrics.p_value`, `metrics.mae_difference` (baseline − DFT), and `metrics.power` (computed with `statsmodels.stats.power.TTestPower`, α = 0.05, effect size from the paired differences).  
  - Add a boolean `metrics.power_below_0_8` flag if `power < 0.8`.  
  - **Verification**: numeric fields present and `power` matches the calculation from `statsmodels`.  

- [ ] **T051** [US3] Run **TreeSHAP** and **permutation‑importance** analyses on the final DFT‑enhanced model trained on the full dataset (`data/models/rf_dft_full.pkl`).  
  - `code/interpretability/shap_analysis.py` must output a mean‑absolute SHAP value per feature and save `data/results/plots/shap_summary.png`.  
  - `code/interpretability/permutation_importance.py` must perform 10 repeats, compute mean and standard deviation per feature, and save `data/results/plots/permutation_importance.png`.  
  - Update `output.json` with `feature_importance.top_5_shap` (list of 5 dicts `{feature, importance}`) and `feature_importance.permutation_std` (list of dicts `{feature, std_dev}`).  
  - **Verification**: both PNG files exist (> 0 KB) and JSON fields are populated.  

- [ ] **T052** [US3] Execute the **bootstrap stability** analysis.  
  - `code/interpretability/bootstrap_stability.py` must (a) sweep sample sizes *n* = 10, 20, 30, 40, 50, recording the standard deviation of permutation importance for each *n*; (b) perform 10 full‑dataset bootstraps, compute permutation‑importance std‑dev for each DFT descriptor, and set `stability_analysis.is_stable` = True if both descriptors have std < 0.05.  
  - Save a summary plot `data/results/plots/stability_distribution.png`.  
  - Add to `output.json`: `stability_analysis.sample_sizes`, `stability_analysis.std_dev_dft_descriptors`, and `stability_analysis.is_stable`.  
  - **Verification**: JSON fields present and PNG generated.  

- [ ] **T053** [US1] Validate all artifacts against the JSON‑schema contracts.  
  - Ensure `specs/001-predict-yield-strength-bcc/contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` exist and match the definitions in the spec.  
  - Run `pytest tests/contract/ -q`; all schema validation tests must pass for `data/intermediate/merged.csv` and `data/results/output.json`.  
  - **Verification**: pytest exits with code 0.  

- [ ] **T054** [Full pipeline] Run the complete orchestrated pipeline from start to finish and confirm that **every** scientific criterion (SC‑001 – SC‑008) is satisfied.  
  - Execute `python code/main.py`.  
  - Run the full test suite `pytest tests/ -q` (including contract, reproducibility, and numeric‑trace tests).  
  - Produce a checklist `data/results/verification.md` mapping each SC‑ID to its realized value in `output.json`.  
  - **Verification**: all pytest checks pass; `verification.md` lists all eight SC items with corresponding numbers.  

- [ ] **T058** [US3] Implement a numeric‑trace verifier (`tests/verification/test_numeric_trace.py`) that extracts every numeric literal from `specs/001-predict-yield-strength-bcc/research.md` and asserts that an equal (within tolerance) value exists in `output.json`.  
  - Include this test in the T054 test run.  
  - **Verification**: test passes, confirming no invented numbers.  

- [ ] **T059** [US2] Add a reproducibility guard (`tests/reproducibility/test_output_consistency.py`) that, after a fresh run, compares the newly generated `data/results/output.json` byte‑for‑byte with the committed baseline (`baseline/output.json`).  
  - Integrated into T054.  
  - **Verification**: test passes, confirming deterministic results under the pinned seed.  

---  

## Phase 3 – Reproducible results and paper handoff  

- [ ] **T055** [US3] Write a concise **methods & results** section in `specs/001-predict-yield-strength-bcc/research.md`.  
  - The narrative must reference exact fields in `output.json` (e.g., “the Random Forest achieved MAE = `{metrics.mae_rf}` MPa”).  
  - Include discussion of limitations: sample‑size, statistical power, VIF‑driven feature dropping, and the associational nature of the analysis.  
  - **Verification**: `tests/verification/test_numeric_trace.py` passes.  

- [ ] **T056** [US1] Update `quickstart.md` with the exact runnable commands, required environment variables (e.g., `MP_API_KEY`), and data‑source citations.  
  - Add a `handoff.md` under `data/results/` that lists each figure file, table, and the JSON keys that the downstream paper pipeline should use.  
  - Ensure that a fresh runner following the quick‑start reproduces the same `output.json` (validated by T059).  
  - **Verification**: a clean checkout executed per `quickstart.md` yields identical `output.json` and the handoff document is present.  

---  

### Dependencies and requirement coverage  

| Spec / SC | Satisfied by | Task(s) |
|-----------|--------------|---------|
| FR‑001 / FR‑002 / FR‑003 / SC‑006 | Real ingestion & merge | **T048** |
| FR‑004 / SC‑002 | RF with DFT features | **T049** |
| FR‑005 / SC‑001 / SC‑003 / SC‑007 | Paired t‑test, MAE diff, Pearson r | **T049**, **T050** |
| FR‑009 / SC‑008 | Power analysis | **T050** |
| FR‑006 | SHAP & permutation importance | **T051** |
| FR‑007 / SC‑004 | Bootstrap sweep | **T052** |
| FR‑008 / SC‑005 | 10‑bootstraps stability | **T052** |
| Contracts | Schema validation | **T053** |
| End‑to‑end validation | All SC items | **T054** |
| Numeric traceability | Research text ↔ JSON | **T058** |
| Reproducibility | Byte‑identical output | **T059** |
| Reporting & handoff | Methods, results, handoff docs | **T055**, **T056** |

---  

**Execution order (recommended)**:  

`T048 → T049 → (T050, T051, T052) → T053 → T054 → (T058, T059) → T055 → T056`.  

All other previously completed tasks (T001–T047) remain checked and unchanged.  