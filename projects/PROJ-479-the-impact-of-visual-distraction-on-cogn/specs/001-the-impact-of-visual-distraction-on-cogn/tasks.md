---
description: "Task list for feature 001‑visual‑distraction‑cognitive‑control"
---

# Tasks: The Impact of Visual Distraction on Cognitive Control in Remote Work Environments  

**Inputs**: `spec.md`, `plan.md`, existing artifacts in `code/`, `data/`, `results/`, `specs/…/contracts/`  

**Verification**: Every task lists a concrete verification step (unit‑/contract‑test, file‑existence check, schema validation, or runtime‑output check).

---

- [ ] T001 **Create project skeleton & core utilities** –  
  • Initialise directory tree `code/`, `data/raw/`, `data/processed/`, `results/`, `tests/`, `specs/001-visual-distraction-cognitive-control/`.  
  • Write `code/requirements.txt` with pinned versions of `numpy`, `pandas`, `scikit-learn`, `scipy`, `opencv-python-headless`, `ultralytics>=8.0.0`, `matplotlib`, `seaborn`, `pillow`, `pytest`, `statsmodels`, `requests`, `openml`.  
  • Add linting script `code/lint.sh` (ruff + black) and utility module `code/utils.py` containing (`get_logger`, `compute_checksum`, `set_global_seed`, `sanitize_images`, `log_error`).  
  • **Verification**: `tree .` shows the expected directories; `pip install -r code/requirements.txt` succeeds; `./code/lint.sh` exits with status 0; unit tests in `tests/unit/test_utils.py` pass.

- [ ] T001a **Scaffold data‑acquisition script** –  
  • Create file `code/01_data_acquisition.py` with stub functions: `download_cognitive_data()`, `download_workspace_images()`, `perform_proxy_linkage()`, `generate_synthetic_dataset()`.  
  • Include docstrings and `if __name__ == "__main__":` placeholder.  
  • **Verification**: `pytest tests/unit/test_01_data_acquisition_stub.py` confirms the module imports and all four functions exist.

- [ ] T002 [US1] **Download and validate raw datasets** –  
  • Implement `code/01_data_acquisition.py::download_cognitive_data()` to fetch a Stroop (or Flanker) dataset from OpenML (e.g., ID 4444) and save as `data/raw/cognitive_data.csv`.  
  • Implement `code/01_data_acquisition.py::download_workspace_images()` to query the Unsplash API for **N = 150** “home office” images, store originals in `data/raw/workspace_images/`, and save the API response as `data/raw/unsplash_query_log.json`.  
  • Verify that `cognitive_data.csv` contains ≥ 100 rows with ≤ 5 % missing values for `reaction_time` and `accuracy`; that exactly 150 image files (> 10 KB each) exist; and that `unsplash_query_log.json` records successful HTTP 200 responses.  
  • **Verification**: Integration test `tests/integration/test_raw_download.py` asserts row counts, missing‑value thresholds, and image‑file existence.

- [ ] T001b **Scaffold visual‑metrics script** –  
  • Create file `code/02_visual_metrics.py` with stub functions: `compute_edge_density(img_path)`, `compute_color_entropy(img_path)`, `compute_object_count(img_path)`.  
  • Include imports for OpenCV and a placeholder for YOLOv5‑tiny model loading (CPU‑only).  
  • **Verification**: Unit test `tests/unit/test_02_visual_metrics_stub.py` confirms the module imports and that all three functions are defined.

- [ ] T003 [US1] **Sanitise images & extract metadata** –  
  • Use `code/utils.py::sanitize_images(src_dir, dst_dir)` to strip EXIF data, rename each image to `img_<sha256>.jpg`, and place them in `data/processed/sanitized_images/`.  
  • Write accompanying metadata (original Unsplash ID, `environment_tag`, `lighting_condition`) to `data/processed/image_metadata.json`.  
  • **Verification**: `tests/unit/test_sanitise.py` checks that every file in `sanitized_images/` is > 10 KB, has a SHA‑256‑based name, and that the JSON metadata contains 150 entries matching the original query.

- [ ] T001c **Scaffold analysis script** –  
  • Create file `code/03_analysis.py` with stub functions: `compute_vif(df)`, `run_pca(df)`, `pearson_correlations(df)`, `ols_regressions(df)`, `apply_holm_correction(pvals)`, `power_analysis_a_priori()`, `power_analysis_post_hoc()`.  
  • Include imports for `statsmodels`, `scipy`, `sklearn.decomposition`, and placeholder bodies raising `NotImplementedError`.  
  • **Verification**: Unit test `tests/unit/test_03_analysis_stub.py` confirms the module imports and that all listed functions exist.

- [ ] T004 [US1] **Proxy linkage & synthetic fallback** –  
  • Implement `code/01_data_acquisition.py::perform_proxy_linkage()` that joins participants and images on the shared `environment_tag` field, using a pinned random seed, and writes `data/processed/merged_data.csv`.  
  • If the merged file contains < 100 rows, call `code/01_data_acquisition.py::generate_synthetic_dataset()` (Cholesky‑based) to produce a synthetic `merged_data.csv` with N ≥ 100 and a modest negative correlation (r ≈ ‑0.3) between `visual_complexity` and `reaction_time`.  
  • Create marker file `data/processed/.ready` once the merged dataset meets the ≥ 100‑row requirement.  
  • **Verification**: `tests/integration/test_proxy_linkage.py` asserts (a) row count ≥ 100, (b) no duplicate `participant_id`, (c) existence of `.ready`.

- [ ] T001d **Scaffold sensitivity script** –  
  • Create file `code/04_sensitivity.py` with stub functions: `run_bootstrap(df, n_iter=1000)`, `run_binning_sensitivity(df, strategies=["quartiles","deciles"])`.  
  • Include imports for `numpy`, `pandas`, and `scipy.stats`.  
  • **Verification**: Unit test `tests/unit/test_04_sensitivity_stub.py` confirms module imports and function definitions.

- [ ] T005 [US2] **Compute visual‑complexity metrics** –  
  • Implement functions in `code/02_visual_metrics.py`:  
    * `compute_edge_density(img_path)` → OpenCV Canny, normalized to [0, 1].  
    * `compute_color_entropy(img_path)` → 256‑bin RGB histogram, Shannon entropy.  
    * `compute_object_count(img_path)` → YOLOv5‑tiny (CPU) detection; returns integer count or `np.nan` on failure.  
  • Batch‑process all images in `data/processed/sanitized_images/`, output `data/processed/visual_metrics.csv` with columns `image_id`, `edge_density`, `color_entropy`, `object_count`.  
  • **Verification**: Automated unit tests `tests/unit/test_edge_density.py`, `tests/unit/test_color_entropy.py`, `tests/unit/test_object_count.py` validate known‑output cases; additional test `tests/unit/test_visual_metrics_verification.py` programmatically asserts the CSV row count matches the number of sanitized images and that the `object_count` column contains at least one `NaN`.

- [ ] T006 [US1 & US2] **Merge metrics with participant data** –  
  • Join `visual_metrics.csv` with `merged_data.csv` on `image_id` → produce two files:  
    * `data/processed/final_analysis_data_all.csv` (keeps NaNs for object count).  
    * `data/processed/final_analysis_data_object_only.csv` (drops rows where `object_count` is NaN).  
  • Validate against `specs/001-visual-distraction-cognitive-control/contracts/dataset.schema.yaml` using `jsonschema`.  
  • Ensure ≤ 5 % missing per column and that variance of each visual metric > 0.  
  • **Verification**: Contract test `tests/contract/test_dataset_schema.py` passes; a small script prints “VALIDATION PASS” when run.

- [ ] T001e **Scaffold reporting script** –  
  • Create file `code/05_reporting.py` with stub functions: `generate_scatter_plots(df)`, `write_alpha_justification()`, `write_methods_citations()`, `assemble_report()`.  
  • Include imports for `matplotlib`, `seaborn`, and a placeholder for causal‑language filter.  
  • **Verification**: Unit test `tests/unit/test_05_reporting_stub.py` confirms module imports and function definitions.

- [ ] T007 [US3] **Statistical analysis & Holm‑Bonferroni correction** –  
  • In `code/03_analysis.py`:  
    1. Compute VIF for `edge_density`, `color_entropy`, `object_count` (excluding NaNs) → `results/statistics/vif_report.json`.  
    2. If any VIF ≥ 5, run PCA on the three metrics, retain the first component (`pc1`), store `results/statistics/pca_report.json` (variance explained).  
    3. Perform Pearson correlations for each predictor‑outcome pair (raw or `pc1` when PCA applied) → `results/statistics/correlation_results.json`.  
    4. Fit OLS regressions for each pair → `results/statistics/regression_results.json`.  
    5. Apply family‑wise error correction using `scipy.stats.multitest.multipletests(method='holm')` on all raw p‑values, write Holm‑adjusted p‑values back into the correlation JSON and create `results/statistics/multiplicity_table.csv` (columns: `test_name`, `raw_p`, `adjusted_p`, `metric_pair`).  
    6. Consolidate all outputs into a single `results/statistics/statistics.json` that conforms to `specs/001-visual-distraction-cognitive-control/contracts/statistics_output.schema.yaml`.  
  • **Verification**: (a) `jsonschema` validation of `statistics.json`; (b) `multiplicity_table.csv` contains exactly 6 rows (3 metrics × 2 outcomes) with corrected p‑values ≤ 1; (c) unit test `tests/unit/test_holm_correction.py` checks that the Holm‑adjusted vector matches SciPy’s output for a known p‑value list.

- [ ] T008 [US4] **Sensitivity & robustness checks** –  
  • Implement bootstrap resampling (≥ 1000 iterations) for each correlation pair in `code/04_sensitivity.py::run_bootstrap()`, store mean r and 95 % CI in `results/sensitivity/bootstrap_results.json`.  
  • Implement alternative binning strategies (`quartiles`, `deciles`) in `code/04_sensitivity.py::run_binning_sensitivity()`, output `results/statistics/binning_sensitivity_table.csv` (columns: `binning_strategy`, `predictor`, `outcome`, `pearson_r`, `p_value`).  
  • Validate both outputs against the schemas defined in `specs/.../contracts/` via `tests/contract/test_sensitivity_schema.py`.  
  • **Verification**: Automated unit test `tests/unit/test_sensitivity_verification.py` loads `bootstrap_results.json` and `binning_sensitivity_table.csv` and asserts CI width < 0.2 for all pairs and Δr < 0.1 across binning strategies; contract tests pass with zero failures.

- [ ] T009 [US3] **Power analysis (a‑priori & post‑hoc)** –  
  • In `code/03_analysis.py`:  
    * `power_analysis_a_priori()` uses `statsmodels.stats.power.FTestPower` with effect size r = 0.3, α = 0.05 to compute required sample size N; writes markdown `results/statistics/power_analysis_a_priori.md` containing N, achieved power, and justification.  
    * `power_analysis_post_hoc()` computes achieved power from the observed r‑values; writes `results/statistics/power_analysis_post_hoc.md`.  
  • **Verification**: Both markdown files exist, each contains a numeric N ≥ 100 (or a clear explanation if not) and a power ≥ 0.8 (or rationale). Unit test `tests/unit/test_power_analysis.py` parses the files and asserts the numeric conditions.

- [ ] T010 [US3] **Generate visualisations & final report** –  
  • `code/05_reporting.py::generate_scatter_plots()` creates PNGs for every predictor‑outcome pair whose Holm‑adjusted p < 0.05, saved as `results/figures/scatter_{predictor}_{outcome}.png`.  
  • `code/05_reporting.py::write_alpha_justification()` reads `data/citations.yaml` and produces `results/statistics/alpha_threshold_justification.md` (≥ 150 words, ASA citation).  
  • `code/05_reporting.py::write_methods_citations()` creates `results/statistics/methods_citations.md` with citations for OpenCV edge detection, color entropy, and YOLOv5‑tiny.  
  • `code/05_reporting.py::assemble_report()` compiles Methods, Results, Sensitivity, Power, Alpha justification, and Methods citations into `results/report.md`; runs a regex filter to prohibit causal language (“cause”, “effect”, “impact”). Embeds a JSON block `{"seed": <value>}` at the end of the Methods section.  
  • **Verification**: (a) At least one PNG exists in `results/figures/`; (b) `alpha_threshold_justification.md` contains ≥ 150 words and the ASA reference; (c) `methods_citations.md` lists all three primary sources; (d) `report.md` passes a regex scan for prohibited causal terms; (e) `statistics.json` is referenced from the report and matches the schema.

- [ ] T011 **Quick‑start guide & end‑to‑end validation** –  
  • Write `specs/001-visual-distraction-cognitive-control/quickstart.md` with a reproducible command sequence (e.g., `python -m code.run_pipeline --seed 42`) and explanation of data‑source selection (real vs synthetic).  
  • Add script `run_all.sh` that sets the seed, invokes the full pipeline (`python -m code.run_pipeline --seed 42`), and exits with status 0 only if `results/report.md` exists and contains at least one scatter‑plot reference.  
  • **Verification**: Running `./run_all.sh` on the CI runner completes in ≤ 6 hours, exits 0, and `grep -c "scatter_" results/report.md` returns ≥ 1.

- [ ] T012 **Comprehensive contract & schema tests** –  
  • Populate `tests/contract/` with:  
    * `test_dataset_schema.py` (validates `final_analysis_data_all.csv`).  
    * `test_analysis_schema.py` (validates `statistics.json`).  
    * `test_sensitivity_schema.py` (validates bootstrap JSON and binning CSV).  
  • Ensure the CI pipeline runs `pytest -q` and all contract tests pass.  
  • **Verification**: CI log shows “6 passed, 0 failed” for the contract test suite.

- [ ] T013 **Measure total pipeline runtime (SC‑008)** –  
  • Add script `code/measure_runtime.py` that records wall‑clock time before and after invoking the full pipeline (`python -m code.run_pipeline`).  
  • Write the elapsed time to `results/statistics/runtime_report.md` and assert it is ≤ 6 hours; the script exits with non‑zero status otherwise.  
  • **Verification**: Unit test `tests/unit/test_runtime_measurement.py` runs the script on a short dummy pipeline and checks that the generated markdown contains a numeric hour value ≤ 6.

- [ ] T014 **Document proxy‑linkage scope extension** –  
  • Create `docs/proxy_linkage_extension.md` that explains the necessity of using `environment_tag` as a proxy linkage mechanism, notes that this extension is not present in the original specification, and records the design decision and its impact on reproducibility.  
  • **Verification**: File existence check and a sanity‑check test `tests/unit/test_proxy_linkage_doc.py` that confirms the document contains the phrase “proxy linkage”.
