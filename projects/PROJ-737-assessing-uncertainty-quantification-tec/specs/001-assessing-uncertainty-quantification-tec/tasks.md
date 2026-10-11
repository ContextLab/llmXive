# Tasks: Assessing Uncertainty Quantification Techniques for Materials Property Predictions  

**Inputs**: `specs/001-assessing-uncertainty-quantification-tec/spec.md`, `plan.md`, `data-model.md`, `contracts/`  

The checklist implements the smallest complete, reproducible study that satisfies **all** functional, non‑functional, and success‑criteria requirements in the specification.  
Unchecked items indicate work that still needs to be performed (or re‑performed after a failure).  
Checked items have been verified to meet their contract and are retained.

---

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] **T001** [US1] **Create required project directories and verify the per‑sample schema includes `abs_error`**   <!-- FAILED-IN-EXECUTION: code/main.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  - Create empty directories (if they do not already exist):  
    `data/raw/`, `data/processed/`, `data/results/`, `figures/`, `code/models/`, `code/metrics/`, `code/stats/`, `code/utils/`, `tests/unit/`, `tests/integration/`.  
  - Verify that `specs/001-assessing-uncertainty-quantification-tec/contracts/per_sample_errors.schema.yaml` contains the columns `sample_id, dataset, method, prediction, lower_bound, upper_bound, ground_truth, abs_error`.  
  - **Verification** (run from the project root):  
    ```bash
    python - <<'PY'
    import yaml, pathlib, sys
    schema_path = pathlib.Path('specs/001-assessing-uncertainty-quantification-tec/contracts/per_sample_errors.schema.yaml')
    schema = yaml.safe_load(schema_path.read_text())
    cols = {c['name'] for c in schema['columns']}
    required = {'sample_id','dataset','method','prediction','lower_bound','upper_bound','ground_truth','abs_error'}
    assert cols == required, f"Missing columns: {required - cols}"
    # directory checks
    for d in ['data/processed','data/results','figures']:
        assert pathlib.Path(d).is_dir(), f"Missing required directory: {d}"
    print("Schema and directory verification passed")
    PY
    ```  
    The command must exit with status 0.

- [ ] **T002** [US1] **Download the three real materials datasets with robust retry and deterministic capping**  
  - Implement `code/download.py` to fetch the following CSVs (all URLs are publicly reachable as of the specification date):  
    1. **Band Gap** – `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/materialsproject/oqmd-data/master/band_gap.csv` — HTTP 404] → `data/raw/band_gap.csv`  
    2. **Formation Energy** – `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/materialsproject/oqmd-data/master/formation_energy.csv` — HTTP 404] → `data/raw/formation_energy.csv`  
    3. **Thermal Conductivity** – `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/aflow/aflow-data/master/thermal_conductivity.csv` — HTTP 404] → `data/raw/thermal_conductivity.csv`  
  - Use exponential back‑off retry (max 3 attempts) on any HTTP error. On persistent failure, raise an exception *after* writing any successfully downloaded files.  
  - After each successful download, compute the SHA‑256 checksum and write a metadata file `data/raw/<dataset_id>_metadata.json` containing: `dataset_id`, `source_url`, `n_samples_original`, `n_samples_used`, `checksum`.  
  - **Cap** each dataset at **5 000** samples (deterministic seed 42, `itertools.islice`). Record the cap size in the metadata file.  
  - **Verification**: a script `code/tests/test_download.py` loads each metadata JSON, confirms the file exists, checksum matches, and `n_samples_used ≤ 5000`. The test must exit with status 0.

- [ ] **T003** [US1] **Thin end‑to‑end run on a 100‑sample subset with full schema validation**  
  - Subset each downloaded dataset to the first 100 rows (seed 42) and write `data/processed/<dataset_id>_subset.csv`.  
  - Featurize using `matminer` (fallback to simple composition fractions via `pymatgen` if `matminer` import fails). Store the processed files as `data/processed/<dataset_id>.csv`.  
  - Perform a stratified 70 %/15 %/15 % train/val/test split by target property range; save split indices in `data/processed/<dataset_id>_split.json`.  
  - Train a baseline **XGBoost** regressor and the four UQ methods (GPR, MC‑Dropout MLP with ≤ 200 passes, Deep Ensemble of ≤ 3 MLPs, Split‑Conformal XGBoost) **only on the 100‑sample split**.  
  - Write per‑sample predictions (including lower/upper bounds) to a **single** `data/results/per_sample_errors.csv` that conforms to the per‑sample schema (including `abs_error`).  
  - Record pipeline execution metadata in `data/results/pipeline_run.json` adhering to `specs/001-assessing-uncertainty-quantification-tec/contracts/pipeline.schema.yaml`.  
  - **Verification**: run `code/tests/test_thin_pipeline.py` which (a) validates `per_sample_errors.csv` against the schema, (b) validates `pipeline_run.json` against its schema, and (c) asserts that exactly 100 test samples were processed for each dataset. Exit status 0 indicates success.

- [ ] **T016** [FR-001] **Validate processed dataset files against `dataset.schema.yaml`**  
  - For each dataset CSV produced in `data/processed/`, load the file and validate it against `specs/001-assessing-uncertainty-quantification-tec/contracts/dataset.schema.yaml` using a pytest validator.  
  - The test must fail if any required field is missing, types are incorrect, or checksum mismatches.  
  - **Verification**: `code/tests/test_dataset_schema.py` runs the validator; exit 0 on success.

- [ ] **T004** [US1] **Full‑scale pipeline on all three capped datasets (≤ 5 000 samples) with unified outputs**  
  - Re‑run the complete pipeline (download → featurize → split → train all four UQ methods) on the capped datasets from `data/raw/`.  
  - Persist per‑sample predictions for **all** dataset × method combinations in the **single** `data/results/per_sample_errors.csv` (columns exactly `sample_id, dataset, method, prediction, lower_bound, upper_bound, ground_truth, abs_error`).  
  - Collect cost metrics (training time, inference time, peak RAM) for each run and write `data/results/cost_metrics.csv` with columns `dataset_id, method_id, train_time_s, inference_time_s, peak_ram_mb`.  
  - **Verification**: `code/tests/test_full_pipeline.py` validates both CSVs against their contracts (schema for per‑sample errors and a simple numeric schema for cost metrics). The test must pass with exit 0.

- [ ] **T005** [US2] **Calculate calibration error, sharpness, and coverage metrics with timestamps**  
  - Implement `code/metrics/evaluation.py` to read `per_sample_errors.csv` and compute for each dataset‑method pair:  
    * Calibration Error (ECE for prediction intervals)  
    * Sharpness (average interval width)  
    * Coverage Error (|empirical – nominal|).  
  - Write a single CSV `data/results/metrics_raw.csv` that conforms to `specs/001-assessing-uncertainty-quantification-tec/contracts/metrics.schema.yaml`. Required columns: `dataset_id, method_id, metric_type, value, nominal_coverage, timestamp`. Use the current ISO‑8601 timestamp for each row.  
  - **Verification**: `code/tests/test_metrics.py` loads the CSV, checks schema compliance, and asserts that `timestamp` parses as ISO‑8601. Exit 0 on success.

- [ ] **T022** [US2] **Generate reference metrics file for reproducibility smoke test**  
  - After T005 completes on the thin 100‑sample pipeline, copy `data/results/metrics_raw.csv` to `tests/reference/metrics_raw_ref.csv`.  
  - Record the path in `tests/reference/README.md` for traceability.  
  - **Verification**: `code/tests/test_reference_exists.py` asserts the reference file exists; exit 0.

- [ ] **T006** [US3] **Paired Wilcoxon signed‑rank significance testing with contract‑compliant CSV**  
  - For each dataset, generate all **6 unique method pairs** and perform a Wilcoxon signed‑rank test on the per‑sample absolute errors.  
  - Produce `data/results/statistical_report.csv` where each row follows `specs/001-assessing-uncertainty-quantification-tec/contracts/stats.schema.yaml`. Required fields: `dataset_id, method_a, method_b, metric_type, p_value, test_type ("wilcoxon_signed_rank"), significant, alpha (0.05), correction ("bonferroni")`.  
  - **Verification**: `code/tests/test_statistics.py` validates the CSV against the schema and checks that the Bonferroni‑adjusted α = 0.05/18 ≈ 0.00278 is used for the `significant` flag. Exit 0.

- [ ] **T021** [FR-004] **Validate statistical results against `statistics.schema.yaml`**  
  - Load `data/results/statistical_report.csv` and validate it against `specs/001-assessing-uncertainty-quantification-tec/contracts/statistics.schema.yaml`. Ensure that `test_type` is only `wilcoxon_signed_rank`.  
  - **Verification**: `code/tests/test_statistics_schema.py` runs the validator; exit 0 on success.

- [ ] **T007** [US3] **Conformal coverage sensitivity sweep for all UQ methods**  
  - Sweep nominal coverage levels from **0.80** to **0.99** (step 0.01) for each of the four UQ methods. For each level compute empirical coverage and average interval width.  
  - Save results to `data/results/sensitivity_report.csv` with columns `dataset_id, method_id, nominal_coverage, empirical_coverage, avg_interval_width`.  
  - Generate a plot `figures/sensitivity_tradeoff.png` (coverage vs. interval width) faceted by method and dataset using `matplotlib`.  
  - **Verification**: `code/tests/test_sensitivity.py` validates the CSV (numeric ranges, non‑negative) and asserts that the set of `nominal_coverage` values equals `{0.80,0.81,…,0.99}` (exact step size). It also asserts that the PNG file can be opened with `PIL.Image`. Exit 0.

- [ ] **T008** [US1] **Reproducibility smoke test on the 100‑sample pipeline**  
  - Add `code/tests/smoke_test.py` that re‑runs the thin pipeline (T003) and asserts that **all metric values** in `data/results/metrics_raw.csv` are identical (within 1e‑8) to the stored reference file `tests/reference/metrics_raw_ref.csv`.  
  - The test must exit with status 0; any mismatch raises an `AssertionError`.

- [ ] **T009** [US1] **Generate summary tables and reliability diagrams with validation**  
  - Implement `code/visualize_summary.py` to aggregate calibration error, sharpness, and cost metrics into `results/summary.csv` (project‑root `results/`). Columns: `dataset_id, method_id, calibration_error, sharpness, train_time_s, inference_time_s, peak_ram_mb`.  
  - Implement `code/visualize_reliability.py` to produce a multi‑panel reliability diagram `figures/reliability_diagrams.png` (one panel per dataset, all four methods overlaid).  
  - **Verification**: `code/tests/test_visualization.py` validates `summary.csv` against a simple numeric schema and checks that both PNG files exist and are readable. Exit 0.

- [ ] **T010** [US1] **Documentation, quick‑start guide, and paper‑stage handoff with hash verification**  
  - Populate `specs/001-assessing-uncertainty-quantification-tec/quickstart.md` with:  
    * One‑line command to run the full pipeline (`python -m code.main`).  
    * Description of the 5 000‑sample cap and deterministic sampling rule.  
    * Rationale for choosing Wilcoxon signed‑rank (paired nature, constitutional compliance).  
    * Note about the substitution of Formation Energy for Elastic Modulus.  
  - Create `specs/001-assessing-uncertainty-quantification-tec/handoff.md` documenting:  
    * Exact command used to generate all results.  
    * SHA‑256 hashes of the three raw dataset files and of the final `results/summary.csv`.  
    * Locations of all CSVs and figures required for the manuscript.  
  - **Verification**: `code/tests/test_handoff.py` recomputes the hashes of the referenced files and asserts they match the values recorded in `handoff.md`. Exit 0.

- [ ] **T011** [US1] **Pin all dependencies and verify a clean installation**  
  - Ensure `requirements.txt` exists at the repository root and that every line follows `package==X.Y.Z`.  
  - In a fresh virtual environment, run `pip install -r requirements.txt` and capture the installed package list.  
  - Write the outcome to `data/results/requirements_check.json` with the structure:  
    ```json
    {
      "status": "success",
      "installed": ["pkg1==1.2.3", "pkg2==4.5.6", ...]
    }
    ```  
  - **Verification**: `code/tests/test_requirements.py` compares the `installed` list against the pinned versions; any discrepancy raises an error. Exit 0.

- [ ] **T012** [US1] **Create entry‑point script and integration test**  
  - Add `code/main.py` that imports `code/pipeline.py` and executes `run_pipeline()` with default arguments (process all three datasets, full 5 000‑sample cap).  
  - Add `tests/integration/test_pipeline.py` which invokes `python -m code.main` and asserts the existence of all expected result files:  
    `data/results/per_sample_errors.csv`, `data/results/metrics_raw.csv`, `data/results/statistical_report.csv`, `data/results/sensitivity_report.csv`, `results/summary.csv`, `figures/reliability_diagrams.png`.  
  - The test must exit with status 0.

- [ ] **T013** [FR‑002, NFR‑001] **Enforce model‑constraint limits, monitor performance, and validate all CSV contracts**  
  - After each model training run, assert:  
    * Deep‑Ensemble creates ≤ 3 sub‑models.  
    * MC‑Dropout uses ≤ 200 stochastic forward passes.  
    * All torch models are instantiated with `device="cpu"` and `torch.backends.openmp.enabled=False`.  
    * Log any violations to `data/results/model_constraints.log` and abort the pipeline if limits are exceeded.  
  - Wrap the full pipeline (T004) with a resource monitor (`psutil`) that records total wall‑clock time and peak memory usage. After completion, assert `total_duration_seconds < 3600` and `memory_peak_mb <= 2000`. Write these measurements to `data/results/performance_log.json`.  
  - After each CSV generation step (per‑sample, metrics, statistical, cost, sensitivity, summary), run a schema validator that checks column names, types, and value ranges against the corresponding contract file. Abort on any violation and write details to `data/results/schema_validation.log`.  
  - **Verification**: `code/tests/test_all_validations.py` runs the above checks end‑to‑end; it must exit with status 0.

- [ ] **T014** [US1] **Final end‑to‑end verification and readiness for analysis**  
  - Execute the full pipeline (`python -m code.main`) on the capped datasets.  
  - Run `code/tests/test_all_validations.py` to confirm that:  
    * All required CSVs and figures exist and pass schema validation.  
    * Model‑constraint and performance limits are satisfied.  
    * Dependency check (T011) succeeded.  
    * Documentation and handoff hashes are correct (T010).  
  - If all checks pass, the project is ready for the next `/speckit.analyze` run.  
  - **Verification**: this task is considered complete when the script exits with status 0 and prints “READY”.  

---  

*All tasks follow the canonical checklist format `- [ ] T### [USx?] description …` with indented verification steps.  The ordering respects data flow: directory creation → data download → thin pipeline → full pipeline → metrics → statistical tests → sensitivity → reproducibility → visualization → documentation → dependency & entry‑point → constraints & validation → final readiness.*  