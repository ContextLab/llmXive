# Tasks: Predicting Yield Strength of BCC Alloys

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, all contracts under `specs/001-predicting-the-yield-strength-of-bcc-all/contracts/`, and the reviewer comment concerning the source of binary interaction parameters.

## Phase 1 – Project scaffolding & first end‑to‑end run

- [ ] T001 [US1] Create the canonical project directory tree, a pinned `code/requirements.txt`, and minimal lint/format configuration files.   <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  - **Paths**: `data/raw/`, `data/processed/`, `data/logs/`, `data/results/`, `code/`, `code/tests/`, `figures/`, `reports/`, each containing a `.gitkeep`; `code/requirements.txt` listing exact versions of `pandas`, `numpy`, `scikit-learn`, `scipy`, `periodictable`, `requests`, `pyyaml`, `ruff`, `black`; `.ruff.toml` and `.pre-commit-config.yaml` enabling `ruff` and `black`.  
  - **Verification**: `tree` (or equivalent) shows all directories with a `.gitkeep`; `pip install -r code/requirements.txt` succeeds without version conflicts; `ruff --quiet .` and `black --check .` both exit with code 0.

- [ ] T002 [US1] Implement a reproducible download script that fetches the MPEA dataset from the canonical Figshare URL associated with DOI 10.1038/s41597-020-00768-9, writes the file to `data/raw/mpea_raw.csv`, and fails loudly on any network, HTTP, or schema error.  
  - **Path**: `code/download.py` (executable via `python -m code.download`).  
  - **Verification**: Running the module on a clean runner creates `data/raw/mpea_raw.csv` containing the required columns (`composition`, `yield_strength`, `crystal_structure`). A forced bad URL raises an exception and exits non‑zero; no fallback file is written. The exact URL used is documented in `quickstart.md`.

- [ ] T003 [US1] Add a unit‑test suite for the download step.  
  - **Path**: `code/tests/test_download.py`.  
  - **Verification**: `pytest code/tests/test_download.py -q` passes; tests include a mock‑response failure case that confirms the script raises without creating a file.

## Phase 2 – Data curation, filtering, and scarcity handling

- [ ] T004 [US1] Implement `code/data_ingestion.py` to (a) read `data/raw/mpea_raw.csv`, (b) filter for rows where `crystal_structure == "BCC"` and `yield_strength` is numeric, (c) normalize each elemental composition to sum to 1.0, (d) log every rejected entry with a reason code to `data/logs/rejected_entries.log`, (e) aggregate duplicate compositions by averaging yield strengths and recording the standard deviation in `data/logs/aggregation.log`, (f) halt with exit‑code 1 and stderr message `DATA_SCARCITY: Insufficient BCC alloys (N < 80)` if the post‑filter count is < 80, (g) add the mandatory fields `yield_definition`, `source_reference`, and `processing_status` (set to `"filtered"` or `"aggregated"` as appropriate) to each record, and (h) validate every output row against `contracts/bcc_alloy.schema.yaml`.  
  - **Outputs**: `data/processed/bcc_filtered.csv` (status `filtered`) and `data/processed/bcc_aggregated.csv` (status `aggregated`).  
  - **Verification**: Running the module on the real download produces both CSVs; each row passes JSON‑schema validation; `aggregation.log` contains an entry for every duplicated composition; `rejected_entries.log` contains at least one reason code; a synthetic fixture with < 80 rows triggers the exact error message and non‑zero exit.

- [ ] T005 [US1] Add unit‑tests for the ingestion pipeline covering (i) removal of non‑BCC rows, (ii) exclusion of non‑numeric yield entries, (iii) composition normalization (sum ≈ 1.0), (iv) proper aggregation of duplicates, and (v) the scarcity‑gate behavior.  
  - **Path**: `code/tests/test_data_ingestion.py`.  
  - **Verification**: All tests pass under `pytest`; the scarcity test uses a temporary CSV with 50 rows and asserts the script exits with code 1 and the correct error string.

## Phase 3 – Binary‑interaction parameters (NIST‑JANAF) and feature engineering

- [ ] T006 [US2] Provide a curated binary‑interaction‑parameter file `data/raw/nist_janaf_params.json` containing the Ω<sub>ij</sub> values from the **NIST‑JANAF Thermochemical Tables (2022 edition)**. Document the source DOI/URL and version in a header comment.  
  - **Verification**: The JSON file includes entries for every element pair present in the filtered dataset; `code/utils.py` supplies a checksum function that confirms the file’s SHA‑256 matches the documented source hash.

- [ ] T007 [US2] Implement `code/features.py` that (a) loads elemental properties from the static `periodictable` library, (b) reads `data/raw/nist_janaf_params.json` for Ω<sub>ij</sub>, (c) computes scalar descriptors δ, VEC, mixing entropy, mixing enthalpy, and electronegativity difference per the formulas in `data-model.md`, (d) performs a self‑contained ILR transformation using a Helmert basis (no external `skbio`), (e) catches any domain errors (e.g., `log(0)`) and substitutes `0.0` while logging the alloy ID to `data/logs/descriptor_errors.log`, (f) raises a custom `MissingElementReference` error if an element symbol is not in the periodic table, and (g) raises `MissingBinaryInteractionParameter` if a required Ω<sub>ij</sub> pair is absent. The module writes `data/processed/features_engineered.csv` conforming to `contracts/compositional_descriptor.schema.yaml`.  
  - **Verification**: Running the module on the aggregated CSV produces a features file with one row per alloy, no NaN values, and a matching schema validation; a deliberately malformed element triggers the expected exception; a missing Ω<sub>ij</sub> pair raises the named error; `descriptor_errors.log` contains entries only for compositions that legitimately caused a log‑zero situation.

- [ ] T008 [US2] Add unit‑tests for the feature‑engineering module, including (i) a reference alloy (`Mo‑25Nb‑25Ta‑25W`) whose descriptor values are pre‑computed to 1e‑6 relative tolerance, (ii) verification that an unknown element raises `MissingElementReference`, (iii) verification that a missing Ω<sub>ij</sub> raises `MissingBinaryInteractionParameter`, and (iv) that the ILR basis is orthonormal and that the inverse CLR round‑trip recovers the original composition within 1e‑12.  
  - **Path**: `code/tests/test_features.py`.  
  - **Verification**: All tests pass under `pytest`; the orthonormality test asserts `V.T @ V ≈ I`.

- [ ] T018 [US2] **Feature‑selection/complementarity enforcement** – After descriptor calculation, run an L1‑regularized linear model (or RFE) on the combined feature set and verify that at least one scalar descriptor and one ILR feature survive. If the condition fails, abort with exit code 1 and message `COMPLEMENTARITY_FAILURE`.  
  - **Verification**: The task writes a short log `data/logs/feature_selection.log`; downstream model training tasks depend on the filtered feature file `data/processed/features_selected.csv`.

- [ ] T019 [US2] **Independent feature‑engineering test** – Add `code/tests/test_features_independent.py` that builds a minimal synthetic BCC CSV (three alloys), runs `code/features.py` directly, and checks that the output conforms to `contracts/compositional_descriptor.schema.yaml` without invoking the full ingestion pipeline.  
  - **Verification**: `pytest code/tests/test_features_independent.py` passes, demonstrating US‑2 is independently testable.

## Phase 4 – Baseline model & quick sanity check

- [ ] T009 [US3] Implement `code/models.py` with a thin end‑to‑end workflow that (a) loads `features_engineered.csv`, (b) creates a stratified 80/20 train‑test split using four quantile bins of the target variable (ensuring duplicated compositions stay together), (c) trains three regressors (RandomForestRegressor, GradientBoostingRegressor, Ridge) on the training split with a single 5‑fold CV pass, (d) evaluates each model on the hold‑out set producing R², MAE, RMSE, and (e) writes a JSON file `data/results/initial_model_comparison.json` containing these metrics plus a baseline mean‑predictor R² for reference.  
  - **Verification**: Executing `python -m code.models --mode quick` produces the JSON file; repeated runs with the same `random_state=42` yield identical numbers (tolerance 1e‑8). The JSON schema matches a simplified version of `results.schema.yaml` (only the three scalar metrics are required at this stage).

- [ ] T010 [US3] Add a quick‑run test `code/tests/test_models_quick.py` that asserts the JSON file exists, contains three model entries, and that each R² is ≥ 0.0.  
  - **Verification**: `pytest code/tests/test_models_quick.py` passes.

## Phase 5 – Full validation (repeated CV, bootstrap CI, permutation importance)

- [ ] T011 [US3] Extend `code/models.py` (or a new function) to perform **Repeated 5‑Fold Cross‑Validation with 10 repeats** on the training split for all three models, using the full combined feature vector (scalar + ILR). Compute the mean R², MAE, RMSE across repeats and write `data/results/cv_results.json`.  
  - **Verification**: The JSON contains, for each model, `r_squared_mean`, `mae_mean`, `rmse_mean`, and `validation_method: "Repeated5FoldCV(10)"`. Values are deterministic with the fixed seed.

- [ ] T012 [US3] Implement bootstrap uncertainty quantification: for each model, resample the hold‑out predictions 1000 times, compute the percentile 95 % confidence interval for R², and store the intervals in `data/results/bootstrap_ci.json`. Also compute permutation importance (`sklearn.inspection.permutation_importance`) for **all three models**, extract the top‑5 features, and calculate stability metrics (median Spearman correlation of importance ranks across CV repeats and rank standard deviation). Write results to `data/results/permutation_importance.json`, matching the structure required by `contracts/results.schema.yaml`.  
  - **Verification**: The CI JSON contains `[lower, upper]` arrays for each model; the permutation JSON includes a `feature_importance` map of five features, a `feature_stability` object with `spearman_correlation` and `rank_std_dev`. All numbers are reproducible with the same seed.

- [ ] T013 [US3] Add comprehensive tests `code/tests/test_models_full.py` that (a) confirm the presence and correct schema of `cv_results.json`, `bootstrap_ci.json`, and `permutation_importance.json`, (b) verify that the best‑model’s R² CI does **not** include the baseline mean‑predictor R² (fulfilling SC‑001), (c) assert that `mae_mean` ≤ 50 MPa yields `practical_utility.mae_vs_threshold = true` (used later in the final report), (d) validate that the descriptor‑error count equals the number of fallback 0.0 values (fulfilling SC‑006).  
  - **Verification**: All assertions pass on the real dataset; failures would cause the CI to include the baseline, which the test would flag.

- [ ] T020 [US3] **MAE vs. experimental uncertainty** – After model evaluation, compare the reported MAE to the experimental uncertainty (~45 MPa). Record a boolean flag `mae_vs_uncertainty` and the numeric difference in `reports/results.json` under `practical_utility`.  
  - **Verification**: The flag is present and correctly reflects the comparison; unit‑test `code/tests/test_mae_uncertainty.py` checks the logic.

- [ ] T021 [US3] **Descriptor‑error count validation** – Count entries in `data/logs/descriptor_errors.log` and verify that the same number of alloys received a fallback value of 0.0 during feature calculation. Include this count and the validation result in `reports/results.json`.  
  - **Verification**: The task writes `data/logs/descriptor_error_validation.log` and the JSON field `descriptor_error_count_match` (true/false). Unit‑test confirms equality.

- [ ] T022 [US3] **Metadata coverage (Phase 0.5)** – Scan the original MPEA CSV for optional testing‑condition columns (temperature, strain‑rate). Log the fraction of rows that contain complete metadata to `data/logs/confounding_metadata.log` and propagate this fraction into `reports/results.json` as `metadata_coverage_fraction`.  
  - **Verification**: The log file exists, contains a single line with the fraction (e.g., `0.68`), and the JSON field matches.

## Phase 6 – Consolidated results report

- [ ] T014 [US3] Assemble `reports/results.json` that (a) records `experiment_id` (UUID generated at runtime), `feature_set_type: "combined"`, the final `n_samples` (post‑filter count), the descriptor‑error count from `descriptor_errors.log`, the aggregation statistics from `aggregation.log`, and the confounding‑metadata coverage fraction from `data/logs/confounding_metadata.log`, (b) includes a `models` array where each element conforms exactly to `contracts/results.schema.yaml` (populated from the three JSON artifacts produced in T011–T012), (c) adds the `practical_utility` fields (`mae_vs_threshold`, `mae_value`, `mae_vs_uncertainty`), and (d) records the SC‑001 significance outcome as a free‑text field `statistical_significance` (e.g., `"significant"` or `"non‑significant"`).  
  - **Verification**: Running a single command `python -m code.report` produces `reports/results.json` that validates against `contracts/results.schema.yaml` (using a small validation script). The file references no manually typed numbers; all values are read from prior result artifacts.

## Phase 7 – Figures, tables, and documentation handoff

- [ ] T015 [US3] Generate a model‑comparison table (`figures/model_comparison.csv`) and a scatter plot of measured vs. predicted yield strength for the best model (`figures/prediction_scatter.png`). The table includes mean R² with CI, MAE, RMSE, and baseline values. The plot includes a 1:1 reference line, axis labels with units (MPa), and a legend indicating the model type. After creation, compute a SHA‑256 checksum of the PNG and append it to `data/logs/figures_checksum.log`.  
  - **Verification**: The CSV file contains the expected columns; the PNG is produced without error; `figures_checksum.log` contains a line `<sha256>  prediction_scatter.png`.

- [ ] T016 [US3] Write a concise methods‑and‑results markdown file `paper/methods_results.md` that (a) cites the exact data provenance (MPEA DOI, NIST‑JANAF parameter source URL), (b) describes each pipeline stage with file‑path references, (c) reports SC‑001 and SC‑002 outcomes verbatim from `reports/results.json`, (d) discusses limitations (power analysis, metadata scarcity), and (e) explicitly states that `mae_vs_threshold` is a reported comparison, not a gating criterion.  
  - **Verification**: A reviewer script checks that every quantitative claim (e.g., R² value, CI bounds, MAE) appears as a substring of `reports/results.json`; the document contains no placeholder text.

- [ ] T017 [US3] Perform a full reproducibility run in a clean temporary environment: (a) create a fresh virtual environment, install from `code/requirements.txt`, (b) execute the documented command chain in `quickstart.md` (`python -m code.download && python -m code.data_ingestion && python -m code.features && python -m code.models && python -m code.report`), (c) run `pytest code/tests/` and confirm all tests pass, (d) compare the newly generated `reports/results.json` hash to the previously committed one (they must match). Document the outcome in `quickstart.md` under a newly added “Reproducibility Check” section.  
  - **Verification**: The reproducibility script exits with code 0 and prints “Reproducibility check passed”. Any mismatch aborts with a clear error message.

- [ ] T023 [US3] Update `quickstart.md` to include a “Reproducibility Check” subsection that describes the steps in T017 and records the hash‑comparison result.  
  - **Verification**: The markdown file contains the new subsection; the CI test `code/tests/test_quickstart.py` checks for its presence.
