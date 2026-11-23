# Tasks: Quantifying the Effect of Alloying Elements on the Glass-Forming Ability of Metallic Glasses

**Input**: `spec.md`, `plan.md`, existing research artifacts, contracts, and reviewer feedback.  
All tasks follow the canonical `- [ ] T### [P?] [USx?] description …` format.  
Completed tasks are marked with `[X]`. Unchecked tasks are ready to be implemented or re‑implemented.

---

## Phase 1 – Project Setup & Quick‑Start Documentation

| ID | Status | Description |
|----|--------|-------------|
- [ ] T001 **Setup project layout** – Create the directory tree under `projects/PROJ-124-quantifying-the-effect-of-alloying-eleme/` (`code/`, `data/raw/`, `data/processed/`, `state/`, `output/`, `tests/`, `docs/`). Verify all folders exist and are writable. *(Path: repository root)*
- [ ] T002 **Initialize Python environment** – Add `requirements.txt` with pinned versions: `pymatgen==2024.5.1`, `scikit-learn==1.5.0`, `pandas==2.2.2`, `numpy==2.0.0`, `shap==0.46.0`, `statsmodels==0.14.2`, `scipy==1.13.1`. Verify `pip install -r requirements.txt` succeeds. *(Path: `code/requirements.txt`)*
- [ ] T003 **Add lint/format config** – Create `.ruff.toml` and `pyproject.toml` sections for Black. Run `ruff check .` and `black .` to confirm no style violations. *(Path: repository root)*
- [ ] T004 **Document quick‑start** – Write `quickstart.md` with a single command `python -m code.main --run all` and list required environment variables. Verify the command executes end‑to‑end on the smallest test dataset. *(Path: `quickstart.md`)*

---

## Phase 2 – Foundational Infrastructure (blocks all user stories)

- [ ] T005 **Create data folders** – `data/raw/` for downloads, `data/processed/` for engineered features. Verify existence. *(Path: `data/`)*
- [ ] T006 **Checksum utilities** – Implement `code/data/checksums.py` with `generate_checksum()` and `verify_checksum()`. Produce a `.sha256` file for each downloaded artifact. Verify that `verify_checksum()` returns `True` for a known good file. *(Path: `code/data/checksums.py`)*
- [ ] T007 **Artifact‑hash manager** – Implement `code/utils/state_manager.py` to append SHA‑256 hashes to `state/artifact_hashes.yaml`. Verify the YAML updates after each artifact creation. *(Path: `code/utils/state_manager.py`)*
- [ ] T008 **Structured logger** – Implement `code/utils/logger.py` with `get_logger()`, `log_info()`, `log_warning()`, `log_error()`. Log to console and `logs/pipeline.log`. Verify that a test message appears in both places. *(Path: `code/utils/logger.py`)*
- [ ] T009 **Environment config** – Add `code/config/env.py` exposing `load_config()` that reads required env vars (`RANDOM_SEED`, `HF_DATASET_URL`, `MP_API_KEY`) and validates them. Verify that missing variables raise a clear `RuntimeError`. *(Path: `code/config/env.py`)*
- [ ] T010 **Elements list** – Create `data/config/elements.yaml` containing the 30 abundant metallic elements listed in the specification. Verify the file loads with `yaml.safe_load()` and contains exactly 30 entries. *(Path: `data/config/elements.yaml`)*
- [ ] T011 **Family‑map definition** – Create `data/config/family_map.yaml` mapping each element to a chemical family (e.g., `Zr: Zr-family`, `Cu: Cu-family`). Verify that every element in `elements.yaml` appears as a key. *(Path: `data/config/family_map.yaml`)*
- [ ] T012 **Contracts for output files** – Add `contracts/candidates_csv.schema.yaml` and `contracts/verification.schema.yaml` matching the JSON‑schema definitions in the specification. Run `jsonschema` validation on a dummy file to confirm the schemas are syntactically correct. *(Path: `contracts/`)*

---

## Phase 3 – User Story 1: Data Acquisition & Feature Engineering (Priority P1)

- [ ] T013 **Download raw GFA dataset** – Implement `code/data/download.py` to fetch `https://huggingface.co/datasets/GFA-D2/pilot_flags` with up‑to‑3 retries and exponential back‑off. After download, verify columns `composition` and (`log10_Rc` or `Rc`) exist; otherwise raise `RuntimeError`. Store as `data/raw/gfa_dataset.csv` and generate a checksum file. *(Path: `code/data/download.py`)*  
- [ ] T014 **Ingest & normalize compositions** – Implement `code/data/ingest.py` to read the CSV, parse elemental fractions, enforce sum = 1.0 ± 0.01 (normalize if within tolerance, drop otherwise). Log warnings for rows with unknown elements. Output `data/processed/ingested.csv` and an `exclusion_log.csv`. Verify that the row count equals the number of valid rows and that no `NaN` values exist in the numeric columns. *(Path: `code/data/ingest.py`)*
- [ ] T015 **Compute physics‑based descriptors** – Extend `code/data/features.py` to calculate weighted means and variances for atomic radius, electronegativity, and VEC, plus `pairwise_size_mismatch` for every unique element pair. Store results in `data/processed/features.csv` with a `source_row_id` column. Verify that for a known test composition (e.g., `Zr50Cu40Al10`) the computed means match manual calculations within 1e‑6. *(Path: `code/data/features.py`)*
- [ ] T016 **Feature‑engineered dataset validation** – Write a pytest in `tests/integration/test_feature_engineering.py` that loads `features.csv` and asserts: (a) no missing descriptor values for known elements, (b) all fractions sum to 1.0 after normalization, (c) the schema matches `contracts/dataset.schema.yaml`. The test must initially fail on an empty `features.csv` and pass after T015 completes. *(Path: `tests/integration/test_feature_engineering.py`)*

---

## Phase 4 – User Story 2: Model Training & Validation (Priority P2)

- [ ] T017 **Train baseline models** – Implement `code/models/train.py` to train a `RandomForestRegressor` and a `GradientBoostingRegressor` on the engineered features using hyper‑parameter grids limited to 30 combos each. Save the raw models as `state/models/rf_raw.pkl` and `state/models/gb_raw.pkl`. Verify that both pickle files exist and can be loaded without error. *(Path: `code/models/train.py`)*
- [ ] T018 **Leave‑One‑Cluster‑Out (LOCO) CV** – Within `train.py`, implement LOCO splitting based on the dominant element (highest atomic fraction, tie‑break by higher atomic number) and use `family_map.yaml` to map the dominant element to a family. Compute MAE for each fold, aggregate mean and std, and write `state/loco_cv.json`. Verify the JSON contains keys `method`, `mean_mae`, `std_mae`, `folds`. *(Path: `code/models/train.py`)*  
- [ ] T019 **Model‑selection logic** – After CV, select the model with the lowest mean MAE, rename it to `output/best_model.pkl`, and write a `model_selection.json` containing `best_model_name`, `selection_reason`, `best_mae`, `best_r2`. Verify that `best_mae` is lower than the baseline mean‑predictor MAE (computed on the same CV splits). *(Path: `code/models/train.py`)*  
- [ ] T020 **Residual heteroscedasticity check** – Implement `code/models/validate.py` to run the Breusch‑Peterson test (via `statsmodels`). Output `state/heteroscedasticity_test.json` with `p_value` and `is_heteroscedastic`. Verify that the JSON file is created and the `p_value` field is a float. *(Path: `code/models/validate.py`)*  
- [ ] T021 **Weighted‑loss retraining (if needed)** – If `is_heteroscedastic` is true, bin residuals by quantiles (≥ 50 samples per bin), estimate local variance, compute inverse‑variance weights, and retrain the selected model using these sample weights. Save as `output/best_model_weighted.pkl` and set `weighted_model_saved: true` in `heteroscedasticity_test.json`. If binning fails, fall back to Huber loss and log a warning; still set `weighted_model_saved: true`. Verify that the weighted model file exists and that the JSON flag reflects the path taken. *(Path: `code/models/validate.py`)*  
- [ ] T022 **Generate SHAP explanations** – Implement `code/utils/shap_utils.py` to compute global SHAP values for the final selected model (weighted if available, otherwise baseline). Save `output/shap_feature_importance.json`. Verify the JSON contains a non‑empty dictionary with feature names as keys. *(Path: `code/utils/shap_utils.py`)*  

### Verification of LOCO Cluster Assignment (previously unrecoverable)

- [ ] T053 **Unit test for LOCO tie‑breaker & family mapping** –  
  *Purpose*: Provide deterministic evidence that the LOCO clustering respects the specification’s tie‑breaker (highest atomic fraction, then highest atomic number) and that every element is correctly mapped to a family using `family_map.yaml`.  
  *Steps*:  
  1. Create a synthetic CSV `tests/unit/synthetic_loco.csv` containing at least four rows with compositions that force tie situations (e.g., `A50B50`, `A40B30C30`, `D33E33F34`).  
  2. Write a pytest `tests/unit/test_loco_assignment.py` that imports the clustering function from `code/models/train.py`, runs it on the synthetic file, and asserts:  
     - The dominant element for each row follows the spec (ties resolved by atomic number, verified via `pymatgen.Element`).  
     - The resulting cluster labels match the families defined in `data/config/family_map.yaml`.  
  3. The test must initially fail if the clustering logic is absent or incorrect, and pass when the logic is correctly implemented.  
  *Verification*: Running `pytest tests/unit/test_loco_assignment.py` should exit with 0 failures. The synthetic CSV and test file are committed to the repo. *(Path: `tests/unit/`)*  

- [ ] T060 **Validate existence & completeness of `family_map.yaml`** –  
  *Purpose*: Ensure the family‑map file required by LOCO exists and contains a mapping for every element listed in `elements.yaml`.  
  *Steps*:  
  1. Write a small script `code/utils/verify_family_map.py` that loads both YAML files, checks that the key sets are identical, and raises `RuntimeError` if any element is missing.  
  2. Add a pytest `tests/integration/test_family_map.py` that runs the script and asserts no exception is raised.  
  *Verification*: The test passes only when `family_map.yaml` is present and complete. *(Path: `code/utils/verify_family_map.py`)*  

---

## Phase 5 – User Story 3: Novel Composition Screening & Ranking (Priority P3)

- [ ] T030 **Generate all unique ternary combinations** – Implement `code/models/predict.py::generate_ternary_combinations()` to iterate over `elements.yaml` and write `data/config/ternary_combinations.csv`. Verify the CSV contains exactly `C(30,3) = 4060` rows. *(Path: `code/models/predict.py`)*  
- [ ] T031 **Predict GFA for candidates** – Load `best_model.pkl` (or weighted version), compute features for each ternary composition using `code/data/features.py`, and predict `log10_Rc`. Store predictions in a temporary DataFrame. Verify that the prediction column contains no `NaN`s. *(Path: `code/models/predict.py`)*  
- [ ] T032 **Domain‑of‑Applicability (DoA) calculation** –  
  1. Fit PCA on the scaled training features (`state/models/scaler.pkl` → `state/models/pca_model.pkl`).  
  2. Compute Mahalanobis distance for each candidate in PCA space.  
  3. Flag candidates with distance > 95th percentile of training distances **or** outside the convex hull as `high_extrapolation_risk`.  
  4. Save the DoA flags and raw `risk_score` in the candidate DataFrame.  
  Verify that `state/convex_hull_model.pkl` exists and that at least one candidate receives a high‑risk flag. *(Path: `code/models/predict.py`)*  
- [ ] T033 **Apply +1.0 penalty for high‑risk candidates** – For any candidate flagged in T032, add exactly `+1.0` to its predicted `log10_Rc` to produce `final_score`. Verify that the penalty is applied *only* to flagged rows and that the increment equals 1.0 (check with a numeric assertion). *(Path: `code/models/predict.py`)*  
- [ ] T034 **Threshold‑based filtering** – Compute the 10th percentile of `log10_Rc` values in the training set. Keep candidates whose *raw* prediction (before penalty) falls below this percentile; if the training set has fewer than 10 samples, fall back to the absolute cutoff `log10_Rc < 4.0`. Save the filtered set. Verify that a `threshold.json` file records the numeric threshold used. *(Path: `code/models/predict.py`)*  
- [ ] T035 **Bootstrapped ensemble for confidence intervals** –  
  1. Train 10 bootstrapped RandomForest models on the *original* scaled training data (same hyper‑parameters as the selected model).  
  2. Predict each candidate with all 10 models, compute the 2.5 th and 97.5 th percentiles → `ci_lower`, `ci_upper`.  
  3. Save ensemble models under `state/bootstrapped_models/ensemble_{i}.pkl`.  
  Verify that exactly 10 files exist and that the CI columns are added to the candidate DataFrame. *(Path: `code/models/predict.py`)*  
- [ ] T036 **Novelty check against external databases** –  
  1. Attempt a Materials Project query via `pymatgen.ext.matproj.MPRester` using `MP_API_KEY`.  
  2. If the query fails, fall back to the local `data/known_alloys.csv` (populated by `code/utils/literature_scraper.py`).  
  3. Assign `novelty_status` = `novel`, `known`, or `unverified_external` per FR‑013.  
  4. Log the source used for each candidate.  
  Verify that `output/verification_requests.json` contains the correct enum values and that no candidate is labeled `novel` when the composition appears in either source. *(Path: `code/utils/novelty.py`)*  
- [ ] T037 **Rank & select top candidates** – Sort candidates by ascending `final_score` (after penalty). Select up to the top 10 rows. Write `output/candidates.csv` with columns: `composition`, `predicted_log10_Rc`, `ci_lower`, `ci_upper`, `doa_risk`, `penalty_applied`, `final_score`, `novelty_status`, `risk_score`. Verify the CSV header matches the schema in `contracts/candidates_csv.schema.yaml` and that the file contains ≤ 10 rows. *(Path: `code/models/predict.py`)*  
- [ ] T038 **Create verification request JSON** – Transform the top‑10 candidate rows into the structure defined by `contracts/verification.schema.yaml` and write `output/verification_requests.json`. Verify the JSON validates against the schema (use `jsonschema`). *(Path: `code/models/predict.py`)*  
- [ ] T039 **Handle empty‑candidate edge case** – If no candidate passes the threshold in T034, output an empty `candidates.csv` with only the header line and write a log entry “No candidates found below threshold”. Verify both the empty CSV and the log entry exist. *(Path: `code/models/predict.py`)*  

---

## Phase 6 – Polishing, Profiling & Documentation (Cross‑Cutting)

- [ ] T040 **Profiling the full pipeline** – Wrap the end‑to‑end execution (`python -m code.main --run all`) with `cProfile`, store raw profile at `output/profiling_raw.cprof`, extract wall‑time & memory peaks into `output/profiling_metrics.json`. Verify that total runtime ≤ 6 h and peak memory ≤ 7 GB on the CI runner. *(Path: `code/main.py`)*  
- [ ] T041 **Paper‑stage handoff docs** – Draft `docs/paper/01-introduction.md` and `docs/paper/02-methods.md` summarizing data sources, descriptor engineering, model training, DoA, and screening logic. Verify that each markdown file contains at least 300 words and references the relevant contracts. *(Path: `docs/paper/`)*
- [ ] T042 **Dry‑run mode for novelty check** – Add a `--dry-run` flag to `code/utils/novelty.py` that logs intended API calls without performing network requests. Verify that running with `--dry-run` produces log entries but no external traffic. *(Path: `code/utils/novelty.py`)*  

---

## Phase 7 – Revision & Analysis‑Driven Refinement (post‑analysis)

- [ ] T048 **Fail‑loudly on data‑fetch failure** – Ensure `code/data/download.py` raises a `RuntimeError` with the exact message `"Data fetch failed after retries: [error details]. Pipeline halted."` when all retries are exhausted. Verify by mocking a network failure. *(Path: `code/data/download.py`)*  
- [ ] T049 **Deterministic seed enforcement** – At the start of `code/models/train.py`, assert that `RANDOM_SEED` is set in the environment and that `PYTHONHASHSEED` matches it. Log a warning if mismatched. Verify that two successive runs with the same seed produce identical `best_model.pkl` hashes. *(Path: `code/models/train.py`)*  
- [ ] T050 **Memory‑efficient ternary generation** – Refactor `generate_ternary_combinations()` to a generator (`yield`) and process predictions in batches of 500. Verify that peak memory usage (from profiling) stays < 2 GB during the combinatorial step. *(Path: `code/models/predict.py`)*  
- [ ] T051 **Document the fixed +1.0 penalty** – Add an explanatory comment in `code/models/predict.py` and a subsection in `docs/paper/02-methods.md` describing why the spec‑mandated +1.0 penalty is used and how `risk_score` is provided for downstream analysis. Verify that the comment appears in the source file and the markdown contains the phrase “fixed +1.0 penalty”. *(Path: `code/models/predict.py`, `docs/paper/02-methods.md`)*  
- [ ] T052 **Robust Pymatgen property lookup** – Wrap all `Element` property accesses in `try/except`. On failure, log the element symbol and composition ID, and exclude the row. Verify with a synthetic composition containing an unknown element (`Xx`) that the row is omitted and a warning is logged. *(Path: `code/data/features.py`)*  
- [ ] T054 **Reproducible bootstrapping** – In `code/models/predict.py::train_ensemble`, set each model’s `random_state = MASTER_SEED + i`. Verify that two full pipeline runs with the same `MASTER_SEED` produce identical `ci_lower`/`ci_upper` values. *(Path: `code/models/predict.py`)*  
- [ ] T055 **Dry‑run novelty check (already in T042)** – Confirm that `--dry-run` produces the expected log output without contacting Materials Project. *(Path: `code/utils/novelty.py`)*  
- [ ] T056 **DoA threshold sanity check** – In `calculate_doa()`, log the chi‑squared quantile used and the number of PCA components. Verify the log line appears and the threshold value matches `scipy.stats.chi2.ppf(0.95, df=n_components)`. *(Path: `code/models/predict.py`)*  
- [ ] T057 **Percentile fallback handling** – Add a guard in the filtering step that uses the absolute cutoff `log10_Rc < 4.0` when the training set size < 10. Verify with a tiny synthetic training set that the fallback is triggered and logged. *(Path: `code/models/predict.py`)*  
- [ ] T058 **Verification‑request size assertion** – After writing `verification_requests.json`, assert that the number of entries equals the length of the filtered top‑10 list (or 0). Raise an error if mismatched. Verify that the assertion passes on the full dataset. *(Path: `code/models/predict.py`)*  

---

### Dependency & Execution Order Summary

1. **Phase 1 → Phase 2** must finish before any user‑story work.  
2. **Phase 3 (US 1)** depends only on Phase 2.  
3. **Phase 4 (US 2)** depends on Phase 3 output (`features.csv`). It also requires the new verification tasks **T053** and **T060**.  
4. **Phase 5 (US 3)** depends on Phase 4 (selected model, scaler, PCA, family map).  
5. **Phases 6‑7** can run in parallel after their respective prerequisites are satisfied.  

All tasks are written as concrete, verifiable steps that produce real files, run deterministic tests, and respect the specification’s scientific and constitutional constraints.
