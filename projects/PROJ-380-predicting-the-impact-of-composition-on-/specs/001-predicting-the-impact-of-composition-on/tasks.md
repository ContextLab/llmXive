# Tasks: Predicting the Impact of Composition on the Shear Modulus of Bulk Metallic Glasses  

**Input**: `spec.md`, `plan.md`, `data-model.md`, contracts, and reviewer feedback.  

The tasks are ordered by research phase and respect data‑flow dependencies.  
Each task follows the canonical format `- [ ] T### [P?] [USx?] description …` and
includes the exact artifact paths that will be produced or modified.  
Indented continuation lines describe the concrete verification step that the
independent verifier will run.

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Create a reproducible project skeleton and verify that a minimal
pipeline can run on a tiny real input. |
|------|---------------------------------------------------------------|

- [ ] T001 **Create project structure** – generate the directories `code/`, `data/`, `tests/`, `docs/`, `state/`, `artifacts/` as described in `plan.md`.  
  *Path*: `./` (directory layout)  
  *Verification*: `tree` output contains all listed top‑level folders; `git status` shows them untracked.

- [X] T002 **Initialize Python 3.11 project** – write `requirements.txt` with pinned versions of `pandas`, `scikit-learn`, `numpy`, `matplotlib`, `seaborn`, `mendeleev`, `requests`, `pyyaml`.  
  *Path*: `requirements.txt`  
  *Verification*: `pip install -r requirements.txt` completes without conflict; `pip freeze` matches pinned versions.

- [ ] T003 **Configure linting and formatting** – add configuration files `.ruff.toml`, `.flake8`, and `pyproject.toml` (with `[tool.black]` section) and a helper script `scripts/lint.sh` that runs the three tools.   <!-- FAILED-IN-EXECUTION: scripts/lint.sh exit=1 -->
  *Paths*: `.ruff.toml`, `.flake8`, `pyproject.toml`, `scripts/lint.sh`  
  *Verification*: Running `bash scripts/lint.sh` exits with code 0 and produces no linting errors on the current code base; existence of each config file is asserted.

- [ ] T004 **Setup `Makefile` entry point** – provide targets `all`, `ingest`, `train`, `evaluate`, `importance`, `plots`, and `clean` that chain the pipeline scripts.  
  *Path*: `Makefile`  
  *Verification*: `make -n all` prints the full command sequence; `make all` finishes successfully and creates `artifacts/` files.

- [ ] T005 **Initialize `utils/config.py`** – define global random seeds, base data directories (`data/raw/`, `data/processed/`, `data/artifacts/`), and a logger obtained via `llmxive_toolkit.get_logger`.  
  *Path*: `code/utils/config.py`  
  *Verification*: Importing `code.utils.config` does not raise; `config.SEED` equals the value specified in `plan.md`.

---

## Phase 2 – Foundational contracts and provenance  

| Goal | Establish immutable schemas and provenance tracking before any scientific
code touches data. |
|------|---------------------------------------------------------------|

- [ ] T006 **Implement provenance utilities** – `utils/provenance.py` provides `record_artifact(file_path, state_file)` that writes SHA‑256 hashes to a YAML file under `state/`.  
  *Path*: `code/utils/provenance.py`, `state/artifact_hashes.yaml`  
  *Verification*: After running a dummy script that calls `record_artifact`, the YAML contains a correct SHA‑256 entry.

- [ ] T007a **Define BMG entry schema** – create the JSON‑Schema object for a BMG entry (as given in `specs/.../bmg_entry.schema.yaml`).  
  *Path*: `contracts/bmg_entry.schema.yaml`  
  *Verification*: `jsonschema validate` against a minimal valid BMG JSON sample passes, confirming the schema file is well‑formed.

- [ ] T007b **Write BMG entry schema to disk** – materialize the schema file.  
  *Path*: `contracts/bmg_entry.schema.yaml`  
  *Verification*: Same as T007a; the file exists and validates.

- [ ] T008a **Define model output schema** – create the JSON‑Schema for model performance metrics (as given in `specs/.../model_output.schema.yaml`).  
  *Path*: `contracts/model_output.schema.yaml`  
  *Verification*: `jsonschema validate` against a sample JSON report passes, confirming correct schema creation.

- [ ] T008b **Write model output schema to disk** – materialize the schema file.  
  *Path*: `contracts/model_output.schema.yaml`  
  *Verification*: Same as T008a; file exists and validates.

- [ ] T009 **Create data sub‑directories** – make `data/raw/`, `data/processed/`, `data/artifacts/`.  
  *Path*: `data/` tree  
  *Verification*: `ls data/` lists the three sub‑folders.

- [ ] T010 **Create package init and logger** – add `code/__init__.py` and configure a project‑wide logger.  
  *Path*: `code/__init__.py`  
  *Verification*: Importing `code` yields a logger named `proj` with level INFO.

---

## Phase 3 – User Story 1: Data ingestion & feature engineering (Priority P1)  

| Goal | Obtain a clean, descriptor‑rich dataset ready for modelling. |
|------|-----------------------------------------------------------|

- [ ] T016 **Implement `ingest.py`** – download BMG data from the Materials Project API (using `MP_API_KEY` if present); if the API call fails **or returns zero valid BMG entries**, automatically generate a reproducible synthetic BMG dataset (based on literature parameters) and record its provenance.  
  *Path*: `code/data/ingest.py`  
  *Verification*: Running `python -m code.data.ingest --sample 5` writes `data/raw/bmg_raw.json`; if the API is unavailable, `data/raw/bmg_synthetic.json` is created instead, and a checksum entry is recorded in `state/`.

- [ ] T017 **Implement `clean.py`** – filter for entries where `phase == "bulk metallic glass"` and `shear_modulus` is non‑null; standardize composition to atomic percent.  
  *Path*: `code/data/clean.py`  
  *Verification*: Output CSV `data/processed/bmg_clean.csv` contains no rows with missing `shear_modulus` and all composition columns sum to 100 %.

- [ ] T018 **Implement `features.py`** – compute atomic size mismatch (δ), mixing enthalpy (ΔHmix), VEC, and electronegativity difference using the `mendeleev` package; append these columns to the cleaned CSV.  
  *Path*: `code/data/features.py`  
  *Verification*: `data/processed/bmg_features.csv` has exactly the columns `delta`, `delta_h_mix`, `vec`, `delta_chi` and no NaNs in those columns.

- [ ] T019 **Calculate VIF and prune** – within `features.py`, compute Variance Inflation Factor for each descriptor; drop any with VIF > 5, otherwise retain all.  
  *Path*: `code/data/features.py` (VIF block)  
  *Verification*: Log file `logs/vif.log` lists VIF values; the final feature matrix `bmg_pruned.csv` contains only retained descriptors.

- [ ] T020 **Implement `split.py` (LOFO / GroupKFold hybrid)** – for alloy families with ≥2 samples use Leave‑One‑Family‑Out; for smaller families fall back to GroupKFold (k=5). Save split objects as pickles.  
  *Path*: `code/data/split.py`  
  *Verification*: Pickle files `train_split.pkl` and `test_split.pkl` exist; a summary printed to console shows the chosen strategy per family.

- [ ] T021 **Validate target completeness** – add a post‑clean check that asserts every row in `bmg_pruned.csv` has a non‑null `shear_modulus`.  
  *Path*: `code/data/validation.py` (new function `assert_target_not_missing`)  
  *Verification*: Running the validation script exits with code 0; otherwise raises `ValueError`.

- [ ] T048 **Synthetic‑fallback guard** – ensure that if `ingest.py` produces a synthetic dataset, downstream tasks (clean, features, split) correctly consume `bmg_synthetic.json` and propagate provenance metadata.  
  *Path*: `code/data/ingest.py` (fallback handling block)  
  *Verification*: End‑to‑end run with forced API failure results in all downstream files present and a provenance entry indicating `source: synthetic_generator`.

---

## Phase 4 – User Story 2: Model training & performance evaluation (Priority P2)  

| Goal | Fit three regressors, tune hyperparameters, and compare them with statistically sound tests. |
|------|--------------------------------------------------------------------------------------------|

- [ ] T025 **Implement `train.py`** – train Linear Regression, Random Forest, and Gradient Boosting on `bmg_pruned.csv`; if VIF pruning left > 5 features, apply Ridge Regression as a fallback.  
  *Path*: `code/models/train.py`  
  *Verification*: Model pickle files appear under `data/artifacts/models/` and can be loaded without error.

- [ ] T026 **Grid‑search with ≤ 50 combos** – define a parameter grid that respects the 50‑combination cap; use `GridSearchCV` with 5‑fold CV.  
  *Path*: `code/models/train.py` (grid‑search block)  
  *Verification*: Log `grid_search.log` reports the total number of evaluated combos ≤ 50.

- [ ] T027 **Statistical comparison (Wilcoxon primary)** – after cross‑validation, run a Wilcoxon signed‑rank test between each non‑linear model and the Linear Regression baseline; if the dataset size ≥ 30 and residuals are normal, fall back to the corrected resampled t‑test.  
  *Path*: `code/models/evaluate.py` (stat_test function)  
  *Verification*: `artifacts/model_report.json` contains fields `statistical_test.method` and `p_value`; values are numeric and within [0,1].

- [ ] T028 **Implement LOFO evaluation** – reuse splitter from T020 to compute test‑set metrics for each family‑held‑out fold; store per‑family scores.  
  *Path*: `code/models/evaluate.py` (LOFO block)  
  *Verification*: `artifacts/lofo_metrics.json` lists families and their R²/MAE/RMSE.

- [ ] T029 **Generate consolidated JSON report** – produce `artifacts/model_report.json` that conforms to `contracts/model_output.schema.yaml`.  
  *Path*: `artifacts/model_report.json`  
  *Verification*: `jsonschema` validation passes.

- [ ] T030 **Bayes Factor fallback comparison** – if Wilcoxon or corrected t‑test is inconclusive (p > 0.10), compute Bayes Factors for each model vs. the Linear Regression baseline and record them.  
  *Path*: `code/models/evaluate.py` (bayes_factor block)  
  *Verification*: `artifacts/model_report.json` includes a `bayes_factor` field for each model when applicable.

- [ ] T031 **Record MAE improvement over baseline** – compute the absolute MAE reduction of Random Forest and Gradient Boosting relative to Linear Regression and store the values in `artifacts/mae_improvement.json`.  
  *Path*: `artifacts/mae_improvement.json`  
  *Verification*: JSON contains keys `rf_mae_improvement` and `gb_mae_improvement` with positive numeric values when improvement is achieved.

- [ ] T049 **Data‑flow integrity check before training** – add a guard at the start of `train.py` that raises `FileNotFoundError` if the input CSV is missing or empty.  
  *Path*: `code/models/train.py` (pre‑load check)  
  *Verification*: Running `python -m code.models.train` with a missing file aborts with the expected exception.

---

## Phase 5 – User Story 3: Feature importance, permutation testing & visualisation (Priority P3)  

| Goal | Quantify predictive contribution of each descriptor and produce publication‑ready figures. |
|------|--------------------------------------------------------------------------------------------|

- [ ] T034 **Implement `importance.py`** – extract feature importances from the best tree‑based model (selected by highest CV R²).  
  *Path*: `code/models/importance.py`  
  *Verification*: JSON `artifacts/feature_importances.json` lists features with importance scores.

- [ ] T035 **Permutation importance (100 permutations)** – run `permutation_importance` from scikit‑learn with 100 repeats; store mean importance and p‑values.  
  *Path*: `code/models/importance.py` (permutation block)  
  *Verification*: `artifacts/importance_report.json` contains `p_value` for each descriptor.

- [ ] T036 **Label results as predictive contribution** – ensure all JSON fields and plot captions explicitly state “predictive contribution within the trained model”.  
  *Path*: `code/models/importance.py` (output formatting)  
  *Verification*: Search for the phrase in generated files returns matches; no ambiguous wording.

- [ ] T037 **Partial dependence plots** – generate PDPs for the top‑3 important features; save as PNG.  
  *Path*: `code/viz/plots.py` (pdp function) → `artifacts/plots/pdp_{feature}.png`  
  *Verification*: Files exist and are non‑empty (size > 10 KB).

- [ ] T038 **Correlation heatmap** – compute Pearson correlation matrix between all descriptors and shear modulus; plot heatmap.  
  *Path*: `code/viz/plots.py` (heatmap function) → `artifacts/plots/correlation_heatmap.png`  
  *Verification*: Heatmap file exists and visual inspection shows a colored matrix.

- [ ] T040 **Hypothesis verification (SC‑001)** – compute R² for the full descriptor set and for the restricted set `{δ, ΔHmix}`; store boolean `hypothesis_verified` in `artifacts/hypothesis_report.json`.  
  *Path*: `code/models/hypothesis.py` → `artifacts/hypothesis_report.json`  
  *Verification*: The JSON contains keys `full_model_r2`, `restricted_model_r2`, `hypothesis_verified`; the boolean is true only if `full_model_r2 ≥ 0.60`.

- [ ] T039 **Deterministic plot filenames** – after `model_report.json` is written, compute its SHA‑256 hash and embed it in all plot filenames as described.  
  *Path*: `code/viz/plots.py` (filename logic)  
  *Verification*: Filenames follow pattern `plot_{feature}_{seed}_{hash[:8]}.png`.

- [ ] T050 **Visualization integrity guard** – before saving any figure, check the underlying data array for NaN/Inf; raise `ValueError` if found.  
  *Path*: `code/viz/plots.py` (validation wrapper)  
  *Verification*: Injecting NaNs into the data causes the script to abort with the expected error message.

---

## Phase N – Polishing & cross‑cutting concerns  

| Goal | Ensure the whole pipeline is reproducible, fast, and documented. |
|------|-------------------------------------------------------------------|

- [ ] T043 **Update `README.md`** – add usage instructions for `make all`, explain the synthetic‑fallback policy, and list required environment variables.  
  *Path*: `README.md`  
  *Verification*: `cat README.md` contains the new sections; CI builds the docs without error.

- [ ] T044 **Code cleanup & refactoring** – run `ruff` and `black` (once T003 is completed) to auto‑format all source files.  
  *Path*: all `code/**/*.py`  
  *Verification*: `git diff --quiet` after `make lint` indicates no style violations.

- [ ] T045 **Performance validation** – instrument the pipeline to report total runtime; ensure it stays below 6 h on the GitHub Actions free‑tier runner.  
  *Path*: `code/utils/timer.py` (new helper) and CI job logs.  
  *Verification*: CI log shows `Total pipeline time: XXm` with `XX < 360`.

- [ ] T046 **Full end‑to‑end run** – execute `make all` and verify that every artifact listed in `artifacts/` exists and passes its respective schema validation.  
  *Path*: `artifacts/` (directory)  
  *Verification*: A CI step runs a Python script that loads each JSON/YAML artifact and validates against the corresponding schema; all return success.

- [ ] T047 **Validate `quickstart.md`** – ensure the quick‑start guide reproduces the full pipeline from a fresh clone.  
  *Path*: `quickstart.md`  
  *Verification*: Running the steps in a fresh container results in the same artifacts as the CI run.

---

### Dependency summary  

| Task | Depends on |
|------|------------|
| T003 | none (stand‑alone) |
| T016 | none (raw data source) |
| T017 | T016 |
| T018 | T017 |
| T019 | T018 |
| T020 | T019 |
| T021 | T020 |
| T048 | T016 |
| T025 | T020, T021 |
| T026 | T025 |
| T027 | T025 |
| T028 | T020 |
| T029 | T027, T028 |
| T030 | T027 (fallback trigger) |
| T031 | T025 (baseline MAE) |
| T049 | T025 |
| T034‑T038 | T025 (trained model) |
| T039 | T029 |
| T040 | T025 |
| T050 | T037‑T038 |
| T044 | T003 (linting config) |
| T045‑T047 | all previous computational tasks |

All tasks together constitute a complete, reproducible study that satisfies every functional requirement (FR‑001 – FR‑011), success criteria (SC‑001 – SC‑005), and the constitution’s reproducibility, verified‑accuracy, and data‑hygiene principles.  