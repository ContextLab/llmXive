# Tasks: Predicting the Impact of Alloying on Magnetic Properties via Public Data  

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and concrete verification/reviewer feedback.  

The study is organised into logical research phases that mirror the specification.  
Each task follows the canonical checklist format and lists the exact artifact
paths it creates or modifies.  All scientific requirements from the spec are
covered; no requirement is omitted or weakened.

---

## Phase 0 – Data acquisition (US‑1)

- [ ] T001 [P] [US1] **Download public magnetic‑property datasets via official APIs**   <!-- FAILED-IN-EXECUTION: code/download_datasets.py exit=1 -->
  *Artifacts*: `data/raw_mp.jsonl`, `data/raw_oqmd.csv`, `data/data_sources.yaml`  
  *Steps*:  
  1. Retrieve the Materials Project magnetic entries by streaming the REST API (`datasets.load_dataset("materialsproject", split="all", streaming=True, filter={"magnetic_type": {"$ne": "NM"}})`).  
  2. Retrieve the OQMD magnetic CSV from the verified HuggingFace URL.  
  3. Verify each download succeeded (file existence, SHA‑256 checksum) and write the version identifiers to `data/data_sources.yaml`.  

---

## Phase 1 – Cleaning & deduplication (US‑1)

- [ ] T002 [P] [US1] **Clean and deduplicate raw records, enforce size requirement**  
  *Artifacts*: `data/data.csv`, `logs/cleaning.log`  
  *Steps*:  
  1. Load `raw_mp.jsonl` and `raw_oqmd.csv`.  
  2. Standardise formulas with `pymatgen`.  
  3. Discard entries missing `composition`, `spacegroup`, or lattice parameters (FR‑003).  
  4. Apply FR‑015: drop rows without `magnetic_moment`; retain rows missing `curie_temperature` for saturation‑magnetisation modelling only (log a warning).  
  5. Resolve duplicates per FR‑016 by keeping the most recent `last_updated`.  
  6. After cleaning, **assert that the resulting dataset contains ≥ 3 500 records for each modelling target** (saturation magnetisation and Curie temperature) as required by FR‑014.  
  7. Write the cleaned dataset to `data/data.csv`.  

---

## Phase 2 – Feature engineering (US‑1)

- [ ] T003 [P] [US1] **Generate numerical feature matrix**  
  *Artifacts*: `data/feature_matrix.npy`, `data/feature_names.json`, `logs/feature_engineering.log`  
  *Steps*:  
  1. For every record in `data/data.csv` compute:  
     - Fractional elemental abundances.  
     - Element‑wise averages of atomic radius, first ionisation energy, d‑electron count, electronegativity, bulk modulus (via `matminer.ElementProperty`).  
     - Crystal‑structure descriptors: space‑group number, lattice constants (a, b, c), angles (α, β, γ), packing fraction.  
  2. Save the dense matrix as `feature_matrix.npy` and the ordered column list as `feature_names.json`.  
  3. Verify the matrix shape matches the number of cleaned records and that all required columns from FR‑004 are present.  

---

## Phase 3 – Model training & hyper‑parameter tuning (US‑1)

- [ ] T004 [P] [US1] **Train regression models for each target**  
  *Artifacts*: `artifacts/model_saturation_rf.pkl`, `artifacts/model_saturation_gb.pkl`, `artifacts/model_curie_rf.pkl`, `artifacts/model_curie_gb.pkl`, `logs/training.log`  
  *Steps*:  
  1. Split the feature matrix into an 80 % train / 20 % test split (seed = 42).  
  2. For **saturation magnetisation** and **Curie temperature** independently:  
     - Train a Random Forest Regressor (`n_estimators=300`, `max_depth=20`).  
     - Train a Gradient Boosting Regressor (`learning_rate=0.05`, `n_estimators=500`).  
  3. Run `GridSearchCV` (5‑fold CV) over a modest hyper‑parameter grid; enforce a total wall‑clock ≤ 30 min per target (FR‑006).  
  4. Persist the best‑performing model for each target as `artifacts/model_{target}_{type}.pkl`.  
  5. Log all random seeds (`np.random.seed(42)`, `random_state=42`) and the full hyper‑parameter search space (FR‑010).  

---

## Phase 4 – Internal evaluation (US‑1)

- [ ] T005 [P] [US1] **Evaluate models on internal test split**  
  *Artifacts*: `metrics/internal_saturation.json`, `metrics/internal_curie.json`  
  *Steps*:  
  1. Load the best model (by R²) for each target.  
  2. Compute R², MAE, RMSE on the held‑out 20 % test set.  
  3. Store the metrics in the JSON files above.  
  4. Verify that **R² ≥ 0.80** for saturation magnetisation (SC‑001) and **R² ≥ 0.75** for Curie temperature (SC‑002).  

---

## Phase 5 – External validation (US‑1)

- [ ] T006 [P] [US1] **Create and evaluate on an external validation set**  
  *Artifacts*: `data/external_validation.csv`, `metrics/external_saturation.json`, `metrics/external_curie.json`  
  *Steps*:  
  1. From the full cleaned Materials Project pool, exclude any alloy present in the internal splits (matching composition + spacegroup).  
  2. Randomly sample **200** distinct alloys (seed = 42) that contain *both* `magnetic_moment` and `curie_temperature`.  
  3. Evaluate the best internal model for each target on this set and record R², MAE, RMSE.  
  4. Assert that the external metrics meet the same thresholds as the internal ones (SC‑001, SC‑002).  

---

## Phase 6 – Statistical comparison (US‑1)

- [ ] T007 [P] [US1] **Wilcoxon signed‑rank test vs linear baseline**  
  *Artifacts*: `stats/wilcoxon_saturation.json`, `stats/wilcoxon_curie.json`  
  *Steps*:  
  1. Fit a simple linear regression baseline for each target on the same training data.  
  2. Compute residuals for the baseline and for the best ensemble model.  
  3. Perform a paired Wilcoxon signed‑rank test (Bonferroni‑corrected α = 0.0125) comparing the two residual sets (FR‑008).  
  4. Store the test statistic, raw p‑value, and corrected p‑value.  
  5. Verify **p < 0.0125** for both targets (SC‑003).  

---

## Phase 7 – Feature‑importance analysis (US‑2)

- [ ] T008 [P] [US2] **Extract and visualise permutation importance**  
  *Artifacts*: `reports/feature_importance_saturation.csv`, `reports/feature_importance_saturation.png`, `reports/feature_importance_curie.csv`, `reports/feature_importance_curie.png`  
  *Steps*:  
  1. Using the best‑performing model for each target, compute permutation‑importance scores (scikit‑learn).  
  2. Rank descriptors and write the full table to the CSV files.  
  3. Plot the top‑20 descriptors as bar charts (PNG).  
  4. Verify that **at least five** distinct elemental properties (e.g., atomic radius, d‑electron count) have importance ≥ 10 % above the mean importance (SC‑004).  

---

## Phase 8 – Prediction service (US‑3)

- [ ] T009 [P] [US3] **Implement single‑alloy prediction CLI**  
  *Artifacts*: `src/cli/predict.py`, `data/prediction_example.json`, `tests/test_predict_cli.py`  
  *Steps*:  
  1. CLI reads a JSON file containing `composition` (string) and crystal‑structure fields (`spacegroup`, `a`, `b`, `c`, `alpha`, `beta`, `gamma`).  
  2. Compute the feature vector using the same pipeline as in T003.  
  3. Load the best model for each target, generate point predictions, and obtain 95 % confidence intervals via 10 000 bootstrap resamples.  
  4. Emit a JSON response that conforms exactly to the schema in FR‑012 (validated with `jsonschema`).  
  5. Benchmark the end‑to‑end call on the CI runner; assert wall‑clock time **≤ 2 seconds**.  
  6. Store a successful example output in `data/prediction_example.json` and include a pytest that checks schema compliance and runtime.  

---

## Phase 9 – Reproducibility hand‑off

- [ ] T010 [P] Document the complete, reproducible workflow  
  *Artifacts*: `quickstart.md`, `code/tests/test_end_to_end.py`  
  *Steps*:  
  1. Add a concise “Run the full pipeline” command to `quickstart.md` (e.g., `python -m src.models.train`).  
  2. List prerequisite steps (install dependencies, set `PYTHONHASHSEED=0`).  
  3. Provide a minimal end‑to‑end pytest (`test_end_to_end.py`) that runs the pipeline on a tiny sampled subset (≤ 500 records) and asserts that the key output files from T001‑T009 exist.  
  4. Verify the test passes in CI, guaranteeing that any future reviewer can reproduce every artifact from the documented entry point.  

---

## Phase 10 – Pipeline runtime verification (SC‑006)

- [ ] T011 [P] **Benchmark total end‑to‑end wall‑clock time**  
  *Artifacts*: `metrics/runtime.json`  
  *Steps*:  
  1. Execute the full pipeline (tasks T001‑T009) wrapped by a timing utility (e.g., `time.perf_counter()`).  
  2. Record total elapsed seconds in `metrics/runtime.json` together with a boolean `within_limit` indicating whether the time is ≤ 21 600 seconds (6 hours).  
  3. Fail the task if `within_limit` is false, thereby enforcing FR‑011 / SC‑006.  

---

### Dependency / Requirement Mapping (summary)

| Requirement | Covered by Task(s) |
|-------------|--------------------|
| FR‑001, FR‑002 | T001 |
| FR‑003, FR‑015, FR‑016, FR‑014, SC‑007 | T002 |
| FR‑004 | T003 |
| FR‑005, FR‑006, FR‑010 | T004 |
| FR‑007, SC‑001, SC‑002 | T005 |
| FR‑013 | T006 |
| FR‑008, SC‑003 | T007 |
| FR‑009, SC‑004 | T008 |
| FR‑012, SC‑005 | T009 |
| FR‑011, SC‑006 | T011 (runtime check) |
| US‑1 | T001‑T007 |
| US‑2 | T008 |
| US‑3 | T009 |

All tasks are unchecked (‑ [ ]) so the execution engine will run them in the order shown, respecting data‑flow dependencies. The pipeline therefore satisfies every functional requirement, success criterion, and user story defined in `spec.md`.  
