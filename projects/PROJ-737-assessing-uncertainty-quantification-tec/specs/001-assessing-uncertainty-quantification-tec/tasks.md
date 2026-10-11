# Tasks: Assessing Uncertainty Quantification Techniques for Materials Property Predictions  

**Inputs**: `specs/001-assessing-uncertainty-quantification-tec/spec.md`, `plan.md`, `data-model.md`, `contracts/`  

The following checklist implements the smallest complete, reproducible study that satisfies **all** functional, non‑functional, and success‑criteria requirements in the specification.  
Unchecked items indicate work that still needs to be performed (or re‑performed after a failure).  
Checked items have been verified to meet their contract and are retained.

---

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] **T001** [US1] **Create required project directories and verify schema completeness**  
  - Create empty directories: `data/raw/`, `data/processed/`, `data/results/`, `figures/`, `code/models/`, `code/metrics/`, `code/stats/`, `code/utils/`, `tests/unit/`, `tests/integration/`.  
  - Ensure the `per_sample_errors.schema.yaml` file at `specs/001-assessing-uncertainty-quantification-tec/contracts/per_sample_errors.schema.yaml` contains **exactly** the columns `sample_id, dataset, method, prediction, lower_bound, upper_bound, ground_truth, abs_error`.  
  - Verification: run `python -c "import yaml; schema = yaml.safe_load(open('specs/001-assessing-uncertainty-quantification-tec/contracts/per_sample_errors.schema.yaml')); assert {c['name'] for c in schema['columns']} == {'sample_id','dataset','method','prediction','lower_bound','upper_bound','ground_truth','abs_error'}"` and ensure exit status 0.  

- [ ] **T002** [US1] **Download the three real materials datasets with retry & partial‑result handling**  
  - Implement `code/download.py` to fetch:  
    1. **Band Gap** – OQMD CSV from `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/materialsproject/oqmd-data/master/band_gap.csv` — HTTP 404]  
    2. **Formation Energy** – OQMD CSV from `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/materialsproject/oqmd-data/master/formation_energy.csv` — HTTP 404]  
    3. **Thermal Conductivity** – AFLOW CSV from `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/aflow/aflow-data/master/thermal_conductivity.csv` — HTTP 404]  
  - Use exponential back‑off retry (max 3 attempts) on HTTP errors; on persistent failure raise an exception **after** writing any successfully downloaded files to `data/raw/` and recording which URLs failed in `data/raw/download_log.json`.  
  - Write each raw file to `data/raw/<dataset_id>.csv`.  
  - Compute SHA‑256 checksum for each file and store in `data/raw/<dataset_id>_metadata.json` together with `dataset_id`, `source_url`, `n_samples_original`, `n_samples_used`, `checksum`.  
  - **Cap** each dataset at **5 000** samples (deterministic seed 42, `itertools.islice`). Record the cap size in the metadata file.  

- [ ] **T003** [US1] **Thin end‑to‑end run on a 100‑sample subset with schema verification**  
  - Subset each downloaded dataset to the first 100 rows (seed 42) and write to `data/processed/<dataset_id>_subset.csv`.  
  - Featurize using `matminer` (fallback to simple composition fractions via `pymatgen` if import fails). Store the processed files as `data/processed/<dataset_id>.csv`.  
  - Perform a stratified 70 %/15 %/15 % train/val/test split (by target property range) and save the split indices in `data/processed/<dataset_id>_split.json`.  
  - Train a baseline **XGBoost** regressor and the four UQ methods (GPR, MC‑Dropout MLP with ≤ 200 passes, Deep Ensemble of ≤ 3 MLPs, Split‑Conformal XGBoost) **only on the 100‑sample split**.  
  - Write per‑sample predictions (including lower/upper bounds) to a **single** `data/results/per_sample_errors.csv` that conforms to `specs/001-assessing-uncertainty-quantification-tec/contracts/per_sample_errors.schema.yaml`. Compute `abs_error = |prediction – ground_truth|` for each row.  
  - Record pipeline execution metadata in `data/results/pipeline_run.json` adhering to `specs/001-assessing-uncertainty-quantification-tec/contracts/pipeline.schema.yaml`.  
  - **Verification**: after generation, run a validator that loads `per_sample_errors.csv` and checks column names/types against the schema; also validate `pipeline_run.json` against its schema.  

- [ ] **T004** [US1] **Full‑scale pipeline on all three datasets (5 000‑sample cap) with unified outputs**  
  - Re‑run the full pipeline (download → featurize → split → train all four UQ methods) on the capped datasets from `data/raw/`.  
  - Persist per‑sample predictions for **all** dataset × method combinations in the **single** `data/results/per_sample_errors.csv` (add columns `dataset_id` and `method_id` to differentiate rows).  
  - Collect **cost metrics** (training time, inference time, peak RAM) for each run and write a consolidated CSV `data/results/cost_metrics.csv` with columns `dataset_id, method_id, train_time_s, inference_time_s, peak_ram_mb`.  
  - **Verification**: validate `per_sample_errors.csv` against the per‑sample schema and `cost_metrics.csv` against a simple schema (numeric types, non‑negative values).  

- [ ] **T005** [US2] **Compute calibration, sharpness, and coverage metrics with timestamp validation**  
  - Implement `code/metrics/evaluation.py` to read `per_sample_errors.csv` and calculate:  
    - **Calibration Error** (expected calibration error for prediction intervals)  
    - **Sharpness** (average interval width)  
    - **Coverage Error** (difference between nominal and empirical coverage)  
  - Write a single CSV `data/results/metrics_raw.csv` that conforms to `specs/001-assessing-uncertainty-quantification-tec/contracts/metrics.schema.yaml`. Required columns: `dataset_id, method_id, metric_type, value, nominal_coverage, timestamp`. Use the current ISO‑8601 timestamp for each row.  
  - **Verification**: after writing, load the CSV and assert each row matches the schema (including that `timestamp` parses as ISO‑8601).  

- [ ] **T006** [US3] **Paired Wilcoxon signed‑rank significance testing with CSV output**  
  - For each dataset, generate all **6 unique method pairs** and perform a Wilcoxon signed‑rank test on the per‑sample absolute errors.  
  - Produce a single CSV `data/results/statistical_report.csv` where each row conforms to `specs/001-assessing-uncertainty-quantification-tec/contracts/stats.schema.yaml`. Required fields: `dataset_id, method_a, method_b, metric_type, p_value, test_type ("wilcoxon_signed_rank"), significant, alpha (0.05), correction ("bonferroni")`.  
  - **Verification**: validate each CSV row against the schema after generation.  

- [ ] **T007** [US3] **Conformal coverage sensitivity analysis for **all** UQ methods**  
  - Sweep nominal coverage levels from **0.80** to **0.99** in steps of **0.01** for **each** of the four UQ methods (GPR, MC‑Dropout, Deep Ensemble, Split‑Conformal). For each level compute empirical coverage and average interval width.  
  - Save the results to `data/results/sensitivity_report.csv` with columns `dataset_id, method_id, nominal_coverage, empirical_coverage, avg_interval_width`.  
  - Generate a plot `figures/sensitivity_tradeoff.png` (coverage vs. interval width) faceted by method and dataset using `matplotlib`.  
  - **Verification**: validate `sensitivity_report.csv` against a simple schema (numeric ranges, non‑negative) and assert that the PNG file exists and is readable.  

- [ ] **T008** [US1] **Reproducibility smoke test**  
  - Write a script `code/tests/smoke_test.py` that re‑runs the 100‑sample pipeline (T003) and asserts that **all metric values** in `data/results/metrics_raw.csv` are identical (within 1e‑8) to a stored reference file `tests/reference/metrics_raw_ref.csv`.  
  - The test must exit with status 0 on success; any mismatch should raise an `AssertionError`.  

- [ ] **T009** [US1] **Generate summary tables and reliability diagrams with validation**  
  - Implement `code/visualize_summary.py` to aggregate calibration error, sharpness, and cost metrics into `results/summary.csv` (project‑root `results/`). Columns: `dataset_id, method_id, calibration_error, sharpness, train_time_s, inference_time_s, peak_ram_mb`.  
  - Implement `code/visualize_reliability.py` to produce a multi‑panel reliability diagram (`figures/reliability_diagrams.png`) – one panel per dataset, overlaying all four methods.  
  - **Verification**: validate `summary.csv` against a simple schema (numeric columns, non‑negative) and check that `reliability_diagrams.png` exists and can be opened by `PIL.Image`.  

- [ ] **T010** [US1] **Write quick‑start documentation with command test**  
  - Populate `specs/001-assessing-uncertainty-quantification-tec/quickstart.md` with:  
    - One‑line command to run the full pipeline (`python -m code.main`).  
    - Description of the 5 000‑sample cap and deterministic sampling rule.  
    - Explanation of why Wilcoxon signed‑rank was chosen (paired nature, Constitution compliance).  
    - Any datasets that were substituted (Formation Energy for Elastic Modulus).  
  - **Verification**: add a lint test that parses the markdown and runs `python -c "import subprocess; subprocess.run(['python','-m','code.main','--dry-run'], check=True)"` to ensure the command is executable.  

- [ ] **T011** [US1] **Paper‑stage handoff record with hash verification**  
  - Create `specs/001-assessing-uncertainty-quantification-tec/handoff.md` documenting:  
    - The exact command used to generate all results.  
    - SHA‑256 hashes of the three raw dataset files and of the final `results/summary.csv`.  
    - Locations of all CSVs and figures required for the manuscript.  
  - **Verification**: script that recomputes hashes of the referenced files and asserts they match the values recorded in `handoff.md`.  

- [ ] **T013** [US2] **Pin and verify all dependencies**  
  - Ensure `requirements.txt` exists at the repository root and that every line follows the format `package==X.Y.Z`.  
  - Run `pip install -r requirements.txt` in a fresh virtual environment and capture the installed package list.  
  - Record the outcome (success/failure, installed package list) in `data/results/requirements_check.json`.  
  - **Verification**: compare the captured package list against the pinned versions in `requirements.txt`; raise an error if any discrepancy is found.  

- [ ] **T014** [US1] **Create entry‑point script with integration test**  
  - Add `code/main.py` that imports `code/pipeline.py` and executes a function `run_pipeline()` with default arguments (process all three datasets, full 5 000‑sample cap).  
  - Verify that `python code/main.py` finishes without error and produces all expected result files.  

- [ ] **T015** [US1] **Full‑pipeline integration test**  
  - Add `tests/integration/test_pipeline.py` which invokes `code.main` (or `code.pipeline.run_pipeline`) on the capped datasets and asserts the existence of:  
    - `data/results/per_sample_errors.csv`  
    - `data/results/metrics_raw.csv`  
    - `data/results/statistical_report.csv`  
    - `data/results/sensitivity_report.csv`  
    - `results/summary.csv` and `figures/reliability_diagrams.png`  
  - The test must exit with status 0; any missing file raises an `AssertionError`.  

- [ ] **T016** [FR‑002] **Verify model‑constraint limits after training**  
  - After each training run, assert:  
    - Deep‑Ensemble creates **≤ 3** sub‑models.  
    - MC‑Dropout uses **≤ 200** stochastic forward passes.  
    - All torch/tensorflow models are instantiated with `device="cpu"` and `torch.backends.openmp.enabled=False`.  
  - Log any violations to `data/results/model_constraints.log` and fail the pipeline if limits are exceeded.  

- [ ] **T017** [NFR‑001 & Constitution VI] **Measure and assert total runtime & peak RAM**  
  - Wrap the full pipeline (T004) with a resource monitor (e.g., `psutil`) that records total wall‑clock time and peak memory usage.  
  - After completion, assert `total_duration_seconds < 3600` and `memory_peak_mb <= 2000`.  
  - Write these measurements to `data/results/performance_log.json`.  

- [ ] **T018** [FR‑005] **Validate all generated CSVs against their contracts**  
  - After each CSV generation step (per‑sample, metrics, statistical, cost, sensitivity, summary), run a schema validator that loads the CSV and checks column names, types, and value ranges according to the corresponding contract YAML/JSON schema.  
  - Any schema violation aborts the pipeline and writes details to `data/results/schema_validation.log`.  
