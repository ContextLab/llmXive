# Tasks: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas, any existing verified artifacts.  
The list follows the required `- [ ] T### [P?] [USx?] description …` format.  
Checked boxes (`- [x]`) indicate work that has already been verified by the platform; unchecked boxes are pending.

---

- [ ] T000 [P] **Initialize Environment**  
  - *Steps*: Set up the virtual environment, install pinned dependencies from `requirements.txt`, and configure global random seeds (`np.random.seed(42)`, `random.seed(42)`).  
  - *Verification*: `pip freeze` matches pinned versions and a test script confirms seed consistency across runs.

- [ ] T001 [P] [US1] **Download the NIST AM‑Bench dataset** to `data/raw/am_raw_data.csv`  
  - *Requirement*: Use the exact Zenodo URL (e.g., `[UNRESOLVED-CLAIM: https://zenodo.org/record/ — HTTP 404]<id>/files/am_bench.csv?download=1`). Implement retry + exponential back‑off (max 3 attempts). On permanent failure raise `FileNotFoundError` with the message **“No verified source found for AM‑Machine‑Learning dataset. Automated download failed after retries. Please manually place a valid CSV file at `data/raw/am_raw_data.csv`.”**. No synthetic fallback is permitted.  
  - *Verification*: After running `python -m code.data.download` the file exists, its SHA‑256 checksum matches the published record, and the script exits with status 0. The CI log contains the exact retry messages.

- [ ] T002 [P] [US1] **Validate and preprocess the raw CSV** → `data/processed/train.csv`, `data/processed/test.csv`, `data/processed/preprocessing.log`  
  - *Steps*  
    1. Load `data/raw/am_raw_data.csv`; abort with **“Insufficient data for GPR training; minimum 50 samples required.”** if `len(df) < 50`.  
    2. Detect zero‑variance columns; log a warning and drop them.  
    3. Run source‑independence check (predictor columns ≠ target columns); abort with a clear Constitution VII error if violated.  
    4. If `fatigue_life` is missing, log a scope‑reduction notice and set `active_targets` to `["yield_strength", "ductility"]` in `data/processed/target_config.json`.  
    5. Median‑impute numeric missing values (record imputation counts).  
    6. One‑hot encode `alloy_type` → `is_<type>` binary columns; drop the original column.  
    7. Perform a stratified 70/15/15 split (train/val/test) **before** scaling. Fit a `MinMaxScaler` on the train split only and apply to all splits.  
    8. Write the three CSVs, `normalization_bounds.json`, and a detailed log file.  
  - *Verification*: `tests/unit/test_preprocess.py` passes; the three processed CSVs contain **no missing values**, all numeric columns are within `[0, 1]`, and the log records each operation.

- [ ] T003 [P] [US2] **Train Gaussian Process Regression (GPR) and Linear baseline**, serialize model, and produce `results/metrics.json`  
  - *Implementation*  
    - Use `sklearn.gaussian_process.GaussianProcessRegressor` with an RBF kernel.  
    - Optimize hyper‑parameters via 5‑fold CV (maximizing log‑marginal likelihood) seeded with `42`.  
    - Train a `LinearRegression` baseline on the same folds.  
    - Save the final GPR model to `results/model/gpr_model.joblib`.  
    - Compute R², RMSE, MAE on the held‑out test set, `rmse_percentage_range`, and the baseline R².  
    - **Explicitly compute ΔR² (GPR R² - Baseline R²) to validate non-linear advantage (SC-001).**  
    - Record hyper‑parameters (`length_scale`, `sigma`) and the total pipeline runtime (`runtime_seconds`).  
  - *Verification*: `results/metrics.json` validates against `specs/…/model_output.schema.yaml`; repeated runs with seed 42 yield byte‑identical `metrics.json` and `gpr_model.joblib`.

- [ ] T004 [US3] **Compute permutation importance and correlate with baseline** → `results/permutation_importance.json` and update `results/metrics.json` with `importance_correlation`  
  - *Steps*  
    1. Run permutation importance over all predictor features using the trained GPR (10 repeats).  
    2. Write a JSON list of `{ "feature_name": <str>, "importance_score": <float> }` to `results/permutation_importance.json`.  
    3. Load `data/baseline_importance.json` if present; otherwise load `data/literature_baseline_importance.json`. If neither exists, the task MUST fail with a `FileNotFoundError` indicating the baseline required for SC-004 is missing.  
    4. Compute Spearman rank correlation between the GPR importance ranking and the chosen baseline; store the value as `importance_correlation` inside `results/metrics.json`.  
  - *Verification*: The importance JSON contains an entry for every predictor, the correlation field is present in `results/metrics.json`, and `tests/unit/test_importance.py` passes.

- [ ] T006 [US3] **Quantify predictive uncertainty and flag high‑uncertainty regions** → `results/high_uncertainty_regions.csv` and update `results/metrics.json` with `high_uncertainty_ratio`  
  - *Procedure*  
    1. Use the GPR to predict mean and standard deviation on the test set.  
    2. Compute the median σ; flag any test sample with σ > 2 × median.  
    3. Write the flagged samples (original parameter values) to `results/high_uncertainty_regions.csv`.  
    4. Store the fraction of flagged samples as `high_uncertainty_ratio` in `results/metrics.json`.  
  - *Verification*: The CSV is non‑empty when applicable, the ratio lies in `[0, 1]`, and `tests/unit/test_uncertainty.py` confirms the threshold logic.

- [ ] T007 **Residual analysis** → update `results/metrics.json` with `residual_analysis`  
  - *Steps*  
    1. Compute residuals on the test set (observed − predicted).  
    2. Test for heteroscedasticity using the Breusch‑Pagan test (or Spearman correlation of |residual| vs. fitted values).  
    3. Record `{ "heteroscedasticity_detected": <bool>, "method_used": "<method name>" }` directly into `results/metrics.json` under the `residual_analysis` key to ensure schema compliance.  
    4. Additionally, write per‑alloy stratified performance (`R²`, `RMSE`, `MAE`) to `results/confounder_analysis.json`.  
  - *Verification*: The `residual_analysis` object exists within `results/metrics.json`, conforms to the schema defined in `model_output.schema.yaml`, and `tests/unit/test_residuals.py` passes.

- [ ] T008 [P] [US3] **Generate all required visualizations** → PNG files in `results/plots/` with side‑car JSON metadata  
  - *Outputs*  
    1. Contour plot of predicted **Yield Strength** over *Laser Power* × *Scan Speed* (`results/plots/yield_strength_contour.png`).  
    2. Contour plot for **Ductility** (`results/plots/ductility_contour.png`).  
    3. Uncertainty heatmap overlay (red where σ > 2 × median) for each property (`*_uncertainty.png`).  
    4. Partial dependence plots for the top‑3 features from permutation importance (`*_pdp.png`).  
  - *Metadata*: For each PNG, create a side‑car JSON matching `visualization.schema.yaml` (e.g., `results/plots/yield_strength_contour.json`).  
  - *Verification*: Each PNG ≤ 5 MB, side‑car JSON validates, and `tests/integration/test_visualization.py` confirms alignment with flagged regions.

- [ ] T005 [P] **Validate contract schemas against generated artifacts**  
  - *Artifacts to validate*: `data/processed/train.csv` / `test.csv` (against `dataset.schema.yaml`), `results/metrics.json` (against `model_output.schema.yaml`), and each visualization side‑car JSON (against `visualization.schema.yaml`).  
  - *Implementation*: Run `jsonschema.validate` for each file; on failure raise a descriptive exception indicating which schema and which property violated.  
  - *Verification*: Execution of `python -m code.schema_validator` exits with status 0; no exceptions are logged.

- [ ] T009 [P] **Profile runtime and memory** → `results/runtime.json` and `results/memory_profile.json`  
  - *Procedure*  
    1. Wrap the full pipeline in a timer; write total seconds to `results/runtime.json`.  
    2. Use `memory_profiler` (or `tracemalloc`) to capture peak memory during GPR training; store `max_memory_mb` in `results/memory_profile.json`.  
  - *Verification*: Both JSON files exist with numeric fields; `tests/unit/test_profile.py` passes.

- [ ] T010 [P] **Write methods & results draft** → `docs/paper.md`  
  - *Content*  
    - Cite every metric, importance ranking, uncertainty ratio, and residual finding to the exact location in `results/` (e.g., “R² = 0.62 (see `results/metrics.json → r2_score`).”).  
    - Include provenance of the NIST AM‑Bench dataset and any scope reductions.  
    - Discuss limitations (epistemic‑only uncertainty, sample‑size representativeness, any heteroscedasticity detected).  
    - No hand‑typed numbers; all values are program‑derived.  
  - *Verification*: A script (`code/docs/verify_refs.py`) parses `docs/paper.md` and confirms that every numeric claim has a matching JSON path; it exits with status 0.

- [ ] T011 [P] **Finalize reproducibility hand‑off** → update `README.md`/`quickstart.md` and confirm full re‑run reproducibility  
  - *Actions*  
    1. Add installation steps, pinned `requirements.txt`, and the exact command `python -m code.main --stage full`.  
    2. Document manual data‑placement fallback instructions.  
    3. In a clean CI run, delete `data/processed/`, `results/`, and `code/models/gpr_model.joblib`; then re‑execute the full command with `PYTHONHASHSEED=0` and seed 42.  
    4. Verify that the newly generated `results/metrics.json` and `results/model/gpr_model.joblib` are byte‑identical to the originals (use `sha256sum`).  
    5. Record the successful reproducibility statement in the final section of `docs/paper.md`.  
  - *Verification*: The CI job completes without test failures, the checksum comparison succeeds, and `tests/integration/test_reproducibility.py` passes.

---  

### Dependency & Requirement Coverage

| Spec Requirement | Task(s) | Command to demonstrate |
|------------------|---------|------------------------|
| FR‑001 (real download, ≥50 samples) | T001, T002 | `python -m code.data.download` |
| FR‑002 (impute, normalize, encode) | T002 | `pytest tests/unit/test_preprocess.py` |
| FR‑003 (GPR RBF, 5‑fold CV) | T003 | `python -m code.models.gpr_trainer` |
| FR‑004 (R², RMSE, MAE JSON) | T003 | inspect `results/metrics.json` |
| FR‑005 (contour & heatmap) | T008 | view PNGs in `results/plots/` |
| FR‑006 (permutation importance) | T004 | `cat results/permutation_importance.json` |
| FR‑007 (σ > 2× median flag) | T006 | `cat results/high_uncertainty_regions.csv` |
| SC‑001 (GPR vs linear baseline) | T003, T007 | `grep delta_r2 results/metrics.json` |
| SC‑002 (RMSE % of range) | T003 | `grep rmse_percentage_range results/metrics.json` |
| SC‑003 (high‑uncertainty fraction) | T006 | `grep high_uncertainty_ratio results/metrics.json` |
| SC‑004 (importance correlation) | T004 | `grep importance_correlation results/metrics.json` |
| SC‑005 (runtime feasibility) | T009 | `cat results/runtime.json` |
| Schema validation | T005 | `python -m code.schema_validator` |

Execution order (implicit from dependencies): T000 → T001 → T002 → T003 → T004 → T006 → T007 → T008 → T005 → T009 → T010 → T011. Tasks marked `[P]` act on distinct files and thus may run in parallel where no data‑flow conflict exists.