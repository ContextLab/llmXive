# Tasks: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations  

**Inputs**: `specs/001-telomere-lifespan-impact/spec.md`, `plan.md`, `data-model.md`, `contracts/`, prior task list and verifier feedback.

## Phase 0 – Dependency Specification  

- [ ] T001 [P] Create reproducible dependency manifests and verification script  
  - **Description**: Add a Python `code/requirements.txt` listing exact versions of `pandas`, `numpy`, `requests`, `rpy2`, `matplotlib`, `seaborn`, `pytest`, `pyyaml`, `tqdm`. Add an R `code/R/requirements_R.txt` listing `lme4`, `lmerTest`, `metafor`, `ggplot2`, `patchwork`, `performance`.  
  - **Verification**:  
    - Files exist, are non‑empty, and contain version‑pinned entries.  
    - Running `pip install -r code/requirements.txt` in a fresh venv succeeds (exit 0).  
    - Running `Rscript code/R/verify_requirements.R` succeeds (exit 0) confirming all R packages are installed.  

## Phase 1 – Configuration & Data Discovery  

- [ ] T002 [US‑1] Populate `code/config.yaml` with verified Dryad DOIs and other URLs, and implement `code/01_discover_data.py`  
  - **Description**: `code/01_discover_data.py` queries the Dryad API for datasets containing the keyword “telomere” and species‑level avian data, validates that each DOI returns HTTP 200, and writes a list of at least one real DOI to `config.yaml` under `dataset_ids`. Also records static URLs for the verified bird‑lifespan CSV and the AnAge/BirdLife ecological CSVs.  
  - **Verification**:  
    - After execution, `code/config.yaml` parses without error and contains a non‑empty `dataset_ids` list of real DOIs (e.g., `10.5061/dryad.abc123`).  
    - `grep -R "http"` in the ingestion and cleaning scripts shows no hard‑coded URLs; all URLs are read from `config.yaml`.  

- [ ] T003 [US‑1] Implement robust data‑ingestion pipeline (`code/02_ingest_data.py`)  
  - **Description**: Reads `config.yaml`, streams each DOI listed in `dataset_ids` using `requests`, writes raw CSVs to `data/raw/` preserving original filenames, creates a SHA‑256 checksum file `data/raw/<filename>.sha256` for each download, and also downloads the verified lifespan and ecological CSVs to `data/raw/`. Any HTTP error raises an exception (no synthetic fallback).  
  - **Verification**:  
    - After run, every expected raw file exists and its corresponding `.sha256` file is non‑empty.  
    - `sha256sum -c data/raw/*.sha256` returns all “OK”.  
    - Unit tests `tests/test_ingest.py` assert `len(downloaded_files) == len(config["dataset_ids"]) + 2`.  

## Phase 2 – Cleaning, Standardisation & Merging  

- [ ] T004 [US‑1] Build full cleaning & merge workflow (`code/03_clean_merge.py`)  
  - **Description**:  
    - Loads all raw CSVs, validates species names via the OpenTree API.  
    - Converts telomere measurements to kilobases (handles qPCR Ct → kb using documented conversion factors).  
    - Filters to wild‑caught individuals only.  
    - Merges telomere, lifespan, and ecological covariates on `species_id`.  
    - Writes `data/processed/analysis_ready.csv` conforming to `contracts/dataset.schema.yaml`.  
    - Generates logs: `logs/unit_conversion_log.csv`, `logs/merge_stats.csv`, `logs/missing_data_log.csv`, `logs/unconvertible_units.csv`.  
  - **Verification**:  
    - `data/processed/analysis_ready.csv` validates against the dataset schema (`jsonschema` validation script).  
    - `logs/merge_stats.csv` reports a merge proportion ≥ 0.90 (fulfills SC‑001).  
    - Unit tests `tests/test_clean_merge.py` check unit conversion correctness and that no hard‑coded file paths remain.  

- [ ] T005 [US‑1] Verify dataset size (`code/04_verify_dataset_size.py`)  
  - **Description**: Checks that `analysis_ready.csv` contains ≥ 500 rows and ≥ 10 distinct `species_id`s. If either condition fails, the script aborts with a clear error message.  
  - **Verification**:  
    - Script exits with status 0 only when both thresholds are met.  
    - Error message includes the actual row and species counts for traceability.  

## Phase 3 – Base Linear Mixed‑Effects Model (LMM)  

- [ ] T006 [US‑2] Fit the base LMM (`code/05_fit_lmm_base.py`)  
  - **Description**: Python driver uses `rpy2` to call `code/R/fit_base_lmm.R`, fitting  
    `lifespan_days ~ telomere_length_kb + sex + age_at_measurement_days + body_mass_g + breeding_latitude + (1|species_id) + (1|batch_id)`.  
    - Writes `results/model_base.csv` adhering to `contracts/model_output.schema.yaml`.  
    - If `n_species < 15`, sets `low_power_flag: true`, adds `low_power_message: "Low Power: species‑level inference unreliable"` and logs the warning to `logs/low_power_base.txt`.  
  - **Verification**:  
    - `results/model_base.csv` passes schema validation.  
    - `logs/base_model_fit.log` contains the model summary, AIC, and convergence status.  

## Phase 4 – Interaction Model (Ecological Moderators)  

- [ ] T007 [US‑3] Fit the interaction LMM (`code/06_fit_lmm_interaction.py`)  
  - **Description**: Calls `code/R/fit_interaction_lmm.R` to fit  
    `lifespan_days ~ telomere_length_kb * migration_status + telomere_length_kb * breeding_latitude + sex + age_at_measurement_days + body_mass_g + (1|species_id) + (1|batch_id)`.  
    - Rows with `migration_status == "Unknown"` are retained as a distinct category.  
    - Writes `results/model_interaction.csv` (same schema).  
    - Computes ΔAIC versus the base model and records it in `delta_aic` field; also writes `logs/aic_comparison.txt`.  
  - **Verification**:  
    - `results/model_interaction.csv` validates against the schema.  
    - `logs/interaction_exclusion_log.csv` reports the count of “Unknown” rows excluded from interaction coefficient estimation (should be zero because they are kept as a category).  

## Phase 5 – Sensitivity & Power Analysis  

- [ ] T008 [US‑2] Perform sensitivity checks and power simulation (`code/07_sensitivity_power.py`)  
  - **Description**:  
    - Reads `results/model_base.csv` for `n_species`.  
    - If `n_species ≥ 10`, runs leave‑one‑out cross‑validation by species; otherwise performs jackknife by data source. Each iteration refits the base LMM and records `iteration_id`, `excluded_species` (or `excluded_source`), `coef_telomere`, `p_value_telomere` to `results/sensitivity_log.csv`.  
    - If `n_species ≥ 15`, runs 1 000 simulation datasets mirroring observed variance components and effect sizes {0.05,0.10,0.15,0.20,0.25,0.30}; computes power to detect a standardized slope of 0.2 at α = 0.05 and writes `results/power_report.yaml`.  
    - Writes method justification to `logs/sensitivity_method.txt`.  
  - **Verification**:  
    - `results/sensitivity_log.csv` exists, has one row per iteration, and the full‑sample coefficient lies within the recorded range.  
    - When performed, `results/power_report.yaml` contains a numeric `power_estimate` between 0 and 1.  

## Phase 6 – Random‑Effects Meta‑Analysis  

- [ ] T009 [US‑2] Conduct species‑level meta‑analysis (`code/08_meta_analysis.py`)  
  - **Description**:  
    - For each species, fits an LMM (same covariates as the base model) to obtain a species‑specific telomere‑lifespan slope and its standard error.  
    - Aggregates these slopes with `metafor::rma` (random‑effects).  
    - Writes `results/meta_analysis.yaml` (conforms to `contracts/meta_analysis.schema.yaml`) containing per‑species rows plus a repeated `i2` field for the overall heterogeneity statistic.  
    - Saves forest plot `results/meta_forest.png`.  
  - **Verification**:  
    - `results/meta_analysis.yaml` validates against the meta‑analysis schema.  
    - `results/meta_forest.png` opens without error and its SHA‑256 checksum is recorded in `logs/meta_forest_checksum.txt`.  

## Phase 7 – External Significance Validation (Permutation Test)  

- [ ] T010 [US‑2] Run permutation test (`code/09_permutation_test.py`)  
  - **Description**: Generates 10 000 permutations of `lifespan_days` (keeping covariates fixed), refits the base LMM for each permutation via `rpy2`, extracts the telomere coefficient, and computes the empirical p‑value as the proportion of permuted absolute coefficients ≥ the observed absolute coefficient.  
    - Writes `results/permutation_pvalue.yaml` containing the empirical p‑value.  
    - Updates `results/model_base.csv` and `results/model_interaction.csv` fields `permutation_pvalue` and `significance_flag` (true only if both model‑based p‑value and permutation p‑value < 0.05).  
  - **Verification**:  
    - `results/permutation_pvalue.yaml` contains a numeric value in [0,1].  
    - The updated model CSVs still pass schema validation after the new fields are added.  

## Phase 8 – Visualization  

- [ ] T011 [US‑2] Produce deterministic visual summaries (`code/10_visualize.py`)  
  - **Description**:  
    - Reads the finalized model CSVs and meta‑analysis output.  
    - Generates:  
      1. Fixed‑effect forest plot → `results/association_forest.png`.  
      2. Moderator plot (grouped scatter by `migration_status` and latitude gradient) → `results/moderator_plot.png`.  
      3. Species‑level meta‑analysis forest plot (already produced in T009).  
    - Computes SHA‑256 checksums for each PNG and records them in `logs/visualization_checksums.csv`.  
  - **Verification**:  
    - All PNGs exist, are ≥ 10 KB, and re‑running the script yields identical checksums (asserted in `tests/test_visualization.py`).  

## Phase 9 – Validation & Reporting  

- [ ] T012 Validate all artifacts and assemble report (`code/11_validate_report.py`)  
  - **Description**:  
    - Runs JSON‑Schema validation on `data/processed/analysis_ready.csv`, both model CSVs, and `results/meta_analysis.yaml`.  
    - Checks that all checksum logs match the current file hashes.  
    - Compiles `results/report.yaml` summarising every SC (SC‑001 … SC‑007), including dataset size, permutation p‑value, I², ΔAIC, power estimate, and the final `significance_flag`.  
  - **Verification**:  
    - The script exits with status 0 only when all validations succeed.  
    - `results/report.yaml` contains entries for each measurable outcome defined in the specification.  

## Phase 10 – Documentation & Paper‑Stage Hand‑off  

- [ ] T013 Write a reproducible quick‑start guide and hand‑off section (`quickstart.md`)  
  - **Description**:  
    - Provides the exact command sequence to run the full pipeline from a fresh clone (e.g., `make all` or a series of `python` commands).  
    - Lists expected artifact paths with their SHA‑256 checksums (generated by the pipeline).  
    - Includes a “Paper‑Stage Hand‑off” subsection enumerating figures (`association_forest.png`, `moderator_plot.png`, `meta_forest.png`), tables (`model_base.csv`, `model_interaction.csv`, `meta_analysis.yaml`), limitations, and suggested figure/table captions.  
  - **Verification**:  
    - A fresh environment can follow the guide verbatim and reproduce identical checksums for all result files (validated by `tests/test_quickstart_repro.py`).  

## Phase 11 – State‑Hash Management (optional but recommended)  

- [ ] T014 Implement deterministic state‑hash updates (`code/utils.py` → `update_state_hashes`) and verify (`code/R/verify_state_hashes.R`)  
  - **Description**:  
    - `utils.update_state_hashes(root_paths)` walks `data/`, `results/`, and `logs/`, computes SHA‑256 for every file, and writes a mapping `relative_path: hash` to `state/projects/PROJ-055-investigating-the-impact-of-telomere-len.yaml`.  
    - All pipeline scripts invoke this function as their final step.  
    - `code/R/verify_state_hashes.R` reads the YAML and confirms each recorded hash matches the on‑disk file (exits 0 on success).  
  - **Verification**:  
    - After any pipeline stage, the state YAML exists and all hashes are correct.  
    - Running the R verification script returns exit 0.  

---  

### Dependency Mapping (summary)

| Specification Requirement | Satisfying Task(s) |
|---------------------------|--------------------|
| FR‑001, FR‑002, FR‑003    | T002, T003, T004   |
| FR‑004                    | T006               |
| FR‑005, FR‑008            | T007               |
| FR‑006                    | T008               |
| FR‑007                    | T011               |
| FR‑009                    | T009               |
| FR‑010                    | T010               |
| FR‑011                    | T005               |
| SC‑001                    | T004 (merge proportion) |
| SC‑002                    | T006 (model p‑value) & T010 (empirical p‑value) |
| SC‑003                    | T007 (ΔAIC) |
| SC‑004                    | T008 (coefficient stability) |
| SC‑005                    | T008 (power simulation) |
| SC‑006                    | T009 (I²) |
| SC‑007                    | T010 (dual‑p‑value flag) |
| US‑1, US‑2, US‑3          | T003‑T011          |

All tasks respect data flow, write only to project‑owned directories, avoid synthetic data, and are fully deterministic and reproducible, satisfying every functional and success‑criteria requirement from the specification.
