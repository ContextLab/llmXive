# Tasks: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas, and original research question.

This research implementation follows a linear pipeline: data acquisition → preprocessing → non‑linear modeling → uncertainty analysis → validation. All tasks use the NIST AM‑Bench dataset as the verified real‑world source.

## Phase 1: Setup and first end‑to‑end analysis

**Goal**: Establish the pipeline and produce an initial set of predictive metrics on real data.

- [ ] T001 [P] **Initialize Environment and Provenance**  
  Set up the virtual environment, install pinned dependencies from `requirements.txt`, and configure global random seeds (`np.random.seed(42)`, `random.seed(42)`) in `code/utils/io_utils.py`.  
  *Verification*: `pip freeze` matches pinned versions and a test script confirms seed consistency across runs.

- [ ] T002 **Implement Strict Data Loader** → `data/raw/am_raw_data.csv`   <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 -->
  Implement a loader in `code/data_loader.py` to download the NIST AM‑Bench dataset from Zenodo with retry logic and exponential back‑off. Validate that the dataset contains ≥ 50 samples and required columns (laser power, scan speed, layer thickness, yield strength, ductility). Implement a source‑independence check to ensure target properties are not mathematically derived from predictors. **Compute a SHA‑256 checksum of the downloaded CSV and write it to `data/checksums/am_raw_data.sha256`.**  
  *Verification*: `python -m code.data_loader` produces `data/raw/am_raw_data.csv` and the checksum file; the script fails loudly with a `FileNotFoundError` if the download fails, if samples < 50, or if checksum generation fails.

- [ ] T003 **Preprocessing Pipeline** → `data/processed/train.csv`, `data/processed/test.csv`, `data/processed/preprocessing.log`  
  Implement `code/preprocessing.py` to: 1) Drop zero‑variance features; 2) Perform median imputation for missing values; 3) One‑hot encode `alloy_type`; 4) Perform a stratified 70/15/15 split; 5) Apply `MinMaxScaler` to numeric features (fitted on train only).  
  *Verification*: `pytest tests/test_preprocessing.py` passes; processed CSVs contain no missing values and all numeric columns are in \[0, 1\].

- [ ] T004 **Core GPR Training and Baseline Comparison** → `results/metrics.json`, `results/model/gpr_model.joblib`  
  Implement `code/models/gpr_model.py` using `GaussianProcessRegressor` with an RBF kernel and 5‑fold CV for hyperparameter optimization. Implement a `LinearRegression` baseline in `code/models/baseline.py`. Calculate R², RMSE, MAE, **RMSE expressed as a percentage of the observed target range (`rmse_percentage_range`)**, and ΔR² (GPR vs baseline) on the test set. Store all metrics in `results/metrics.json`.  
  *Verification*: `results/metrics.json` contains all required metrics (including `rmse_percentage_range`); repeated runs with seed 42 produce byte‑identical model artifacts.

- [ ] T005 [P] **Permutation Importance and Baseline Correlation** → `results/permutation_importance.json`   <!-- FAILED-IN-EXECUTION: code/analysis/importance.py exit=1 -->
  Implement `code/analysis/importance.py` to rank processing parameters using permutation importance. Calculate the Spearman rank correlation between the GPR rankings and a baseline ranking from `data/literature_baseline_importance.json` (produced by T015). Update `results/metrics.json` with the `importance_correlation` score.  
  *Verification*: `results/permutation_importance.json` contains entries for all predictors; correlation score is recorded in the metrics file.

- [ ] T006 [P] **Uncertainty Quantification** → `results/high_uncertainty_regions.csv`  
  Implement `code/analysis/uncertainty.py` to extract predictive standard deviation (σ) for the test set. Identify samples where σ > 2 × median(σ) and save their original (non‑normalized) parameter values to `results/high_uncertainty_regions.csv`. Update `results/metrics.json` with the `high_uncertainty_ratio`.  
  *Verification*: The CSV is non‑empty and contains original parameter values for flagged regions.

## Phase 2: Complete the study and validate its evidence

**Goal**: Quantify uncertainty, analyze residuals, and generate scientific visualizations.

- [ ] T008 [P] **Uncertainty‑Aware Visualizations** → `results/plots/*.png`, `results/plots/*.json`  
  Implement `code/visualization/plots.py` to generate: 1) Contour plots of predicted Yield Strength and Ductility over the Power × Speed space; 2) Uncertainty heatmaps (red where σ > 2 × median); 3) Partial Dependence Plots (PDPs) for the top 3 features. Every PNG must have a side‑car JSON matching `visualization.schema.yaml`.  
  *Verification*: All PNGs are ≤ 5 MB; side‑car JSONs validate against the schema.

- [ ] T009 **Contract and Schema Validation** → `results/schema_validation_report.json`  
  Implement `code/schema_validator.py` to validate `data/processed/*.csv` against `dataset.schema.yaml`, `results/metrics.json` against `model_output.schema.yaml`, and all plot metadata against `visualization.schema.yaml`.  
  *Verification*: `python -m code.schema_validator` exits with status 0; all artifacts are compliant.

- [ ] T010 **Compute Resource Profiling and Runtime Integration** → `results/memory_profile.json`  
  Wrap the full pipeline in a timer and use `tracemalloc` or `memory_profiler` to capture peak RAM usage during GPR training. Save peak MB to `results/memory_profile.json`. **Add the total runtime (seconds) directly into `results/metrics.json` as the `runtime_seconds` property** to satisfy `model_output.schema.yaml`.  
  *Verification*: `results/memory_profile.json` exists with numeric peak RAM; `results/metrics.json` now includes `runtime_seconds`; total runtime is within the 4‑hour CI limit.

- [ ] T011 [P] **Draft Methods and Results Account** → `docs/paper.md`  
  Write a concise report linking every claim (metrics, importance, uncertainty) to the specific JSON path in `results/`. Document the NIST AM‑Bench provenance and any scope reductions (e.g., if fatigue life was unavailable). Discuss the epistemic nature of the GPR uncertainty.  
  *Verification*: A verification script `code/docs/verify_refs.py` confirms all numeric values in `paper.md` match the values in the `results/` artifacts.

- [ ] T012 **Final Reproducibility Audit** → `docs/quickstart.md`  
  Document the exact execution command in `docs/quickstart.md`. In a clean environment, execute the full pipeline from raw data and verify that the resulting `results/metrics.json` and `results/model/gpr_model.joblib` are byte‑identical to the original artifacts using SHA‑256 checksums.  
  *Verification*: Checksum comparison succeeds; `tests/integration/test_reproducibility.py` passes.

## New Supporting Tasks (Addressing Plan‑Task Alignment & Missing Requirements)

- [ ] T013 **Verify Checksum Generated by T002** → `data/checksums/am_raw_data.sha256`  
  After T002 completes, confirm that the SHA‑256 checksum file exists and matches the hash of `data/raw/am_raw_data.csv`. Record the verification result in the project state.  
  *Verification*: The checksum file exists and its content matches the computed hash of the raw CSV.

- [ ] T015 **Acquire Literature Baseline Importance JSON** → `data/literature_baseline_importance.json`  
  Download a publicly available baseline importance ranking (e.g., from a peer‑reviewed study) or, if unavailable, create a placeholder JSON with equal scores for all features. This file enables T005 to run without external manual steps.  
  *Verification*: The JSON is present and conforms to the expected schema.

- [ ] T016 **Plan‑ID Wrapper: Preprocessing (Plan T016)** → `data/processed/train.csv`, `data/processed/test.csv`  
  Alias for T003 to provide a direct correspondence with the plan’s T016 entry. Executes the same preprocessing pipeline.  
  *Verification*: Mirrors T003 verification.

- [ ] T017 **Plan‑ID Wrapper: Metrics Calculation (Plan T029)** → `results/metrics.json`  
  Alias for T004 to map the plan’s T029 entry to the implemented metrics task.  
  *Verification*: Mirrors T004 verification.

- [ ] T018 **Plan‑ID Wrapper: Uncertainty Flags (Plan T045)** → `results/high_uncertainty_regions.csv`  
  Alias for T006 to map the plan’s T045 entry to the uncertainty‑flag generation task.  
  *Verification*: Mirrors T006 verification.

- [ ] T019 **Detect Heteroscedasticity** → `results/residual_analysis.json`  
  Perform a Breusch‑Pagan test (or equivalent) on model residuals to set `heteroscedasticity_detected` flag used by the Sparse GPR fallback logic.  
  *Verification*: JSON file contains a boolean flag.

- [ ] T057 **Sparse GPR Fallback Implementation** → `results/model/sparse_gpr_model.joblib`  
  If `len(train) > 500` **or** `heteroscedasticity_detected` is true (from T019), switch to a Sparse Gaussian Process (e.g., using `GaussianProcessRegressor` with inducing points) and train on the dataset. Save the fallback model artifact and update `results/metrics.json` with a `sparse_fallback_used` flag.  
  *Verification*: Fallback model file exists when conditions are met; metrics JSON records usage.

## Dependency & Requirement Coverage

| Spec Requirement | Task(s) | Command to demonstrate |
| :--- | :--- | :--- |
| **FR‑001** (Real download, ≥ 50 samples) | T002, T013 | `python -m code.data_loader && cat data/checksums/am_raw_data.sha256` |
| **FR‑002** (Impute, Normalize, Encode) | T003 | `pytest tests/test_preprocessing.py` |
| **FR‑003** (GPR RBF, 5‑fold CV) | T004 | `python -m code.models.gpr_model` |
| **FR‑004** (R², RMSE, MAE JSON) | T004 | `cat results/metrics.json` |
| **FR‑005** (Contour & Heatmaps) | T008 | `ls results/plots/` |
| **FR‑006** (Permutation Importance) | T005 | `cat results/permutation_importance.json` |
| **FR‑007** (Uncertainty σ > 2 × median) | T006 | `cat results/high_uncertainty_regions.csv` |
| **SC‑001** (GPR vs Linear Baseline) | T004 | `grep delta_r2 results/metrics.json` |
| **SC‑002** (RMSE % of range) | T004 | `grep rmse_percentage_range results/metrics.json` |
| **SC‑003** (High‑uncertainty fraction) | T006 | `grep high_uncertainty_ratio results/metrics.json` |
| **SC‑004** (Importance correlation) | T005 | `grep importance_correlation results/metrics.json` |
| **SC‑005** (Runtime feasibility) | T010 | `cat results/metrics.json | grep runtime_seconds` |
| **Schema Validation** | T009 | `python -m code.schema_validator` |

**Execution Order**: T001 → T002 → T013 → T003 → T016 → T004 → T017 → T005 → T015 → T006 → T018 → T008 → T009 → T010 → T011 → T012 → T019 → T057 (conditional)  
