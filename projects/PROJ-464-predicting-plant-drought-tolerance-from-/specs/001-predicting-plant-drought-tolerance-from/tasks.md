# Tasks: Predicting Plant Drought Tolerance from RSA Data

**Input**: Design documents from `/specs/001-predict-drought-tolerance/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data‑model.md`, `contracts/`  

---

## Phase 0 – Project scaffolding  

- [ ] T001a **Create project directory hierarchy**  
  `data/raw/`, `data/derived/`, `code/`, `tests/`, `docs/`, `state/`, `contracts/`, `results/`  
  *Verification*: `tree` output matches expected structure; no missing directories.

- [ ] T001b **Initialize `README.md` and empty `requirements.txt`**  
  *Verification*: Files exist and are tracked in Git.

- [ ] T002 **Add core Python dependencies to `requirements.txt`**  
  `pandas>=2.0.0`, `numpy>=1.24.0`, `scikit-learn>=1.3.0`, `scipy>=1.11.0`, `statsmodels>=0.14.0`, `opencv-python-headless>=4.8.0`, `scikit-image>=0.21.0`, `requests>=2.31.0`, `networkx>=3.0`, `pyyaml`, `power` (for sample‑size calculation).  
  *Verification*: `pip install -r requirements.txt` succeeds on a clean runner.

- [ ] T003 **Configure linting (ruff) and formatting (black) via `pyproject.toml`**  
  *Verification*: `ruff .` and `black .` run without errors.

- [ ] T004 **Create `code/config.py` with global paths, random seed (42), and hyper‑parameter defaults**  
  *Verification*: Importing `code.config` yields the expected constants.

- [ ] T005 **Set up project‑wide logger in `code/__init__.py`** (JSON‑formatted logs to `state/pipeline.log`).  
  *Verification*: Running any script creates a non‑empty `state/pipeline.log`.

- [ ] T006 **Define data‑model classes in `code/models.py`** (`RootImage`, `RSAMetrics`, `PhysioTrait`).  
  *Verification*: Unit tests instantiate each class and validate basic field constraints.

- [ ] T007 **Add JSON‑Schema contracts to `contracts/`** (already present in the repository).  
  *Verification*: `jsonschema.validate` succeeds against sample files.

---

## Phase 1 – Data ingestion  

- [ ] T012 **Download NPPN root images (`code/download_images.py`)** using the verified MGB3 URL via `huggingface_hub.snapshot_download`. Images are streamed into `data/raw/nppn_images/`.   <!-- FAILED-IN-EXECUTION: code/download_images.py exit=1 -->
  *Verification*: Presence of ≥ 10 images; script raises `RuntimeError` with message *“No real NPPN root images found. Pipeline cannot proceed.”* on any fetch failure.

- [ ] T013 **Validate downloaded image archive** (`code/validate_images.py`). Checksums are computed against `data/raw/nppn_checksums.json`; mismatches cause a hard stop.  
  *Output*: `state/nppn_validation.yaml`.  
  *Verification*: YAML contains `checksum_match: true`.

- [ ] T020 **Download TRY physiological traits (`code/download_traits.py`)** using the `trydata` package and API key from `TRY_API_KEY`. Output written to `data/raw/try_traits.csv`.  
  *Verification*: CSV contains at least the columns `species_name`, `stomatal_conductance`, `photosynthetic_rate`; script aborts with a clear error if the API call fails.

---

## Phase 2 – RSA extraction  

- [ ] T015 **Extract RSA metrics (`code/extract_rsa.py`)** – processes each image in `data/raw/nppn_images/` with OpenCV / scikit‑image (skeletonization, contour detection). Generates `data/derived/rsametrics.csv`.  
  *Verification*: CSV has exactly one row per successfully processed image, all numeric columns are non‑negative, and rows with `extraction_status = "failed"` are excluded. A summary `state/image_processing_stats.yaml` records the exclusion rate.

- [ ] T016 **Unit tests for image processing** (`tests/unit/test_image_processing.py`).  
  *Verification*: Tests pass on a small fixture set, confirming error handling for corrupted files and positive branch‑point counts.

- [ ] T017 **Integration test for the full image pipeline** (`tests/integration/test_image_pipeline.py`).  
  *Verification*: Running the test on a sample subset produces a CSV with the expected row count and no null values.

---

## Phase 3 – Data merging & transformation  

- [ ] T021 **Merge RSA and TRY data (`code/merge_data.py`)** – joins on `species_name`, drops rows with any missing trait, writes `data/derived/merged_data.csv`.  
  *Verification*: `merged_data.csv` contains ≥ 55 species (otherwise the pipeline halts per T008 power‑analysis step).

- [ ] T008 **Power‑analysis script `code/power_analysis.py`** – computes required species count (N ≥ 55) using Cohen’s f² = 0.15, α = 0.05, power = 0.80, k = 3. Runs **after** the merged dataset is created (depends on T021). Halts with a clear error if the overlap after merging is < 55.  
  *Output*: `state/power_analysis_report.yaml` (contains `required_N`, `actual_N`, `status`).  
  *Verification*: Running the script on the merged dataset writes the YAML and exits with status 0 only when `actual_N ≥ required_N`.

- [ ] T022 **Collinearity check & PCA (`code/analysis.py`)** – computes VIF for `depth_px`, `branching_density`, `surface_area_px`. If any VIF > 5, flags the issue and proceeds to PCA on the three RSA traits. Outputs `data/derived/pca_results.csv` and `state/vif_report.yaml`.  
  *Verification*: `vif_report.yaml` lists VIF scores for all three predictors; `pca_results.csv` contains `pca_pc1`, `pca_pc2`.

- [ ] T023 **Phylogenetic tree acquisition (`code/fetch_phylogeny.py`)** – contacts the Open Tree of Life API, writes Newick tree to `data/derived/phylogenetic_tree.newick`. Retries up to three times with exponential back‑off; aborts with a clear error if all attempts fail **and then falls back to Phylogenetic Eigenvector Regression (PVR)** using distance matrices derived from the failed tree fetch.  
  *Verification*: Tree file exists and is non‑empty; `state/phylogeny_fetch.yaml` records the fetch status and whether PVR was used.

- [ ] T024 **Fit phylogenetic model (`code/models.py`)** – uses the fetched tree to fit PGLS; if PGLS fails, automatically runs PVR. Writes `data/derived/phylogenetic_model_results.csv`.  
  *Verification*: CSV includes columns `method` (`PGLS` or `PVR`), `predictor`, `coefficient`, `p_value`, `r2`, and any lambda parameter.

- [ ] T025 **Multiple‑comparison correction (`code/analysis.py`)** – applies Benjamini‑Hochberg FDR to all regression p‑values. Updated p‑values stored in `data/derived/model_results.csv`.  
  *Verification*: Adjusted p‑values are present and ≤ 1.

- [ ] T025b **Adjusted‑p‑value verification** – confirms that each adjusted p‑value is compared against the corrected alpha level (α = 0.05 / number_of_tests) and flags any violations.  
  *Verification*: `state/pvalue_verification.yaml` records pass/fail status for each hypothesis.

- [ ] T028 **Binarize physiological metrics (`code/models.py`)** – creates binary high/low classes for `stomatal_conductance` and `photosynthetic_rate` using median splits (independent of any proxy). Generates `data/derived/binary_targets.csv` containing `species_name`, `stomatal_conductance_bin`, `photosynthetic_rate_bin`.  
  *Verification*: CSV rows equal number of species; each binary column contains only 0/1 values.

- [ ] T027 **Detect independent tolerance proxy (`code/analysis.py`)** – checks for `survival_rate` or `biomass_stress` columns in `merged_data.csv`. Writes `state/proxy_detection.yaml` (`has_proxy: true/false`).  
  *Verification*: YAML accurately reflects presence/absence of a proxy (used only for optional exploratory analyses, not for primary classification).

---

## Phase 4 – Regression & classification modeling  

- [ ] T031 **Regression suite (`code/models.py`)** – fits Multiple Linear Regression **and** Random Forest Regression on the PCA components to predict `stomatal_conductance` and `photosynthetic_rate`. Uses 5‑fold `GroupKFold` (groups=`species_name`). Writes `data/derived/regression_results.csv` (includes `model_type`, `r_squared`, `coefficients`, `adjusted_p_values`).  
  *Verification*: CSV contains entries for both MLR and Random Forest models; R² scores are recorded.

- [ ] T032 **Permutation testing (`code/analysis.py`)** – performs 1000‑iteration permutation tests for all regression and classification models, generating empirical confidence intervals for coefficients, R², and F1‑score. Results stored in `data/derived/permutation_results.json`.  
  *Verification*: JSON includes 95 % CI bounds for each statistic; unit test checks that CI width > 0.

- [ ] T029 **Random Forest classification (`code/models.py`)** – trains a Random Forest classifier on the binary drought‑tolerance class derived from `stomatal_conductance_bin` (primary) **or** `photosynthetic_rate_bin` (secondary) using 5‑fold `GroupKFold`. Writes `data/derived/classification_model.pkl` and `data/derived/classification_metrics.yaml` (contains `f1_score`, `accuracy`, `confusion_matrix`).  
  *Verification*: Model file exists; metrics file contains numeric scores; classification runs regardless of proxy presence.

- [ ] T030 **Sensitivity analysis (`code/analysis.py`)** – sweeps predicted‑probability thresholds from 0.0 to 1.0 in 0.01 steps, computes FPR, FNR, accuracy, and F1 for each.  
  *If classification was performed* → outputs `results/sensitivity_fpr_fnr.csv` and `results/figures/sensitivity_curve.png`.  
  *If classification was skipped* → writes `results/sensitivity_na_justification.md` with the required justification.  
  *Verification*: Presence of the CSV **or** the justification file, matching the pipeline branch taken.

- [ ] T030b **Sensitivity‑baseline deviation check** – calculates the baseline performance (optimal threshold from `classification_metrics.yaml`) and reports the maximum deviation in F1/accuracy across the sweep. Results appended to `results/sensitivity_fpr_fnr.csv` as additional columns `delta_f1`, `delta_accuracy`.  
  *Verification*: CSV contains the new columns and they reflect the computed deviations.

---

## Phase 5 – Reporting & compliance checks  

- [ ] T032a **Generate scientific report (`code/report.py`)** – assembles a markdown report (`results/reports/final_report.md`) that:  
  * Summarizes VIF findings and PCA usage.  
  * States that results are **associational** (per FR‑009).  
  * Includes regression tables (with CI from permutation tests), classification metrics, sensitivity‑analysis plots or justification, and phylogenetic correction method used.  
  * Cites the phylogenetic tree source.  
  *Verification*: Report file exists and contains sections titled “VIF & PCA”, “Regression Results”, “Classification”, “Sensitivity Analysis”, and “Phylogenetic Correction”.

- [ ] T033 **VIF heatmap generation (`code/visualize_vif.py`)** – reads `state/vif_report.yaml` and creates `results/figures/vif_heatmap.png`.  
  *Verification*: PNG file is non‑empty and matches the dimensions specified in the test suite.

- [ ] T034a **Runtime profiling of auxiliary scripts (`code/profile_runtime.py`)** – wraps individual scripts (e.g., download, extraction) with `cProfile`, writes summaries to `state/runtime_aux.yaml`.  
  *Verification*: YAML exists and contains timing info for each script.

- [ ] T034b **Full‑pipeline runtime profiling (`code/profile_full_pipeline.py`)** – runs the complete pipeline (`python code/pipeline.py`) under `cProfile`, writes `state/runtime_profile.yaml` with `total_seconds` and a warning flag if `total_seconds > 21600` (6 h).  
  *Verification*: YAML exists; `total_seconds` is numeric; warning flag set appropriately.

- [ ] T035 **Generator‑based image loader (`code/stream_images.py`)** – implements a Python generator that yields one image at a time from the remote HuggingFace repository, enabling true streaming without storing the entire dataset locally. Updated `code/extract_rsa.py` now imports this generator.  
  *Verification*: Unit test `tests/unit/test_stream_images.py` confirms that the generator yields the expected number of images and that peak memory (checked via `memory_profiler`) stays < 7 GB.

- [ ] T036 **Memory‑usage profiling for the streaming loader (`code/profile_memory.py`)** – runs the pipeline on the full NPPN set using the new generator, writes `state/memory_profile.yaml` with `peak_memory_mb`.  
  *Verification*: YAML reports `peak_memory_mb < 7000`.

---

## Phase 6 – Final verification & hand‑off  

- [ ] T059 **End‑to‑end validation on a small subset (`python code/pipeline.py --subset 50`)** – ensures all previous stages run without error, produces `state/e2e_validation_report.yaml`.  
  *Verification*: Report contains `status: success` and lists all generated artifact paths.

- [ ] T060 **Schema validation of all output artifacts** (`tests/contract/test_all_schemas.py`).  
  *Verification*: Test suite passes; any failure aborts the CI job.

- [ ] T061 **Static analysis for silent error handling** – scans `code/` for `try/except` blocks that swallow exceptions without re‑raising.  
  *Verification*: Linter produces zero findings; results logged to `state/code_review_checklist.yaml`.

- [ ] T062 **Classification‑skip framing check** – runs the pipeline on a mock dataset lacking a proxy, then asserts that `results/reports/final_report.md` contains the exact sentence “Classification Skipped: No Independent Proxy Found”.  
  *Verification*: Unit test passes; the sentence appears verbatim in the report.

- [ ] T063 **Verification of adjusted‑p‑value threshold compliance** – checks that every adjusted p‑value in `data/derived/model_results.csv` is below the corrected alpha level (α = 0.05 / number_of_tests).  
  *Verification*: `state/pvalue_threshold_check.yaml` records pass/fail for each hypothesis.