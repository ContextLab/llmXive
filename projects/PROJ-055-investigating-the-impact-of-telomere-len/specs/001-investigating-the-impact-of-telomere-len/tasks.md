# Tasks: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations  

**Inputs**: `specs/001-telomere-lifespan-impact/spec.md`, `plan.md`, `data-model.md`, `contracts/`, prior task list and verifier feedback.

---

## Phase 0 – Dependency Specification  

- [ ] T001 [P] Create reproducible dependency manifests  
  - **Python**: `code/requirements.txt` listing pinned versions of `pandas`, `numpy`, `requests`, `rpy2`, `matplotlib`, `seaborn`, `pytest`, `pyyaml`, `tqdm`.  
  - **R**: `code/R/requirements_R.txt` containing package names and versions for `lme4`, `lmerTest`, `ggplot2`, `patchwork`, `performance`.  
  - **Verification**:  
    - Both files exist and are non‑empty.  
    - `pip install -r code/requirements.txt` succeeds in a fresh virtual environment.  
    - Running `Rscript code/R/verify_requirements.R` exits with status 0, confirming all listed R packages are installed.

---

## Phase 1 – Data Discovery, Configuration & Ingestion  

- [ ] T002 [US-1] Populate a complete configuration file  
  - Create `code/config.yaml` with the following mandatory keys:  
    - `dryad_api_base: "https://datadryad.org/api/v2/datasets"`  
    - `dataset_ids:` a **real, non‑empty list** of Dryad DOIs (e.g., `["[UNRESOLVED-CLAIM: 10.5061/dryad.abc123 — HTTP 404]", "[UNRESOLVED-CLAIM: 10.5061/dryad.def456 — HTTP 404]"]`).  
    - `anage_url: "[UNRESOLVED-CLAIM: https://genomics.senescence.info/species/age_data.csv — HTTP 404]"` (fallback to BirdLife if unavailable).  
    - `random_seed: 42`  
    - `alpha: 0.05`  
    - `chunk_size: 100_000` (for streaming large CSVs).  
  - Add a short “discovery” script `code/01_discover_data.py` that queries the Dryad API for datasets containing the keyword “telomere” and writes the resulting DOIs into `config.yaml`.  
  - Ensure **no hard‑coded URLs or seeds** appear in any downstream script; all scripts must read these values from `config.yaml`.  
  - **Verification**:  
    - `config.yaml` parses without error and `dataset_ids` contains at least one real DOI.  
    - Running `python code/01_discover_data.py` updates the file (or confirms existing IDs).  
    - Static analysis (e.g., `grep` or `ast` check) of `code/02_ingest_data.py` and `code/03_clean_merge.py` confirms they import `yaml.safe_load(open("code/config.yaml"))` and contain no literal URL strings or numeric seeds.

- [ ] T003 [US-1] Implement robust data‑ingestion pipeline  
  - `code/02_ingest_data.py` reads `config.yaml`, downloads each DOI listed under `dataset_ids` (using `requests` with streaming), writes the raw CSVs to `data/raw/` preserving original filenames, and computes a SHA‑256 checksum file `data/raw/<filename>.sha256`.  
  - The script also downloads the AnAge CSV (or BirdLife fallback) to `data/raw/anage_lifespan.csv` with its checksum.  
  - All downloads must **fail loudly** if a remote file is missing (raise an exception; no synthetic fallback).  
  - **Verification**:  
    - After execution, every expected raw file exists and its corresponding `.sha256` file is non‑empty.  
    - A checksum verification step (`sha256sum -c *.sha256`) passes.  
    - Unit tests `tests/test_ingest.py` assert that the number of downloaded files equals the length of `dataset_ids` + 1 (AnAge).

---

## Phase 2 – Cleaning, Standardisation & Merging  

- [ ] T004 [US-1] Build a full cleaning & merge workflow  
  - `code/03_clean_merge.py` reads all raw CSVs, performs the following steps:  
    1. **Taxonomic validation**: keep only rows whose species resolve to birds via the OpenTree of Life API.  
    2. **Unit conversion**: detect telomere units; convert all to kilobases (kb) using documented qPCR‑to‑kb factors; log every conversion in `logs/unit_conversion_log.csv`.  
    3. **Filtering**: retain only wild‑caught juvenile records; drop any with missing required fields.  
    4. **Merging**: join telomere data with lifespan, migration status, breeding latitude, body mass, and study identifiers on a case‑insensitive species name.  
    5. **Output**: write the final analysis‑ready table to `data/processed/merged_analysis.csv` (schema‑validated against `contracts/dataset.schema.yaml`).  
    6. **Auxiliary logs**: `logs/merge_stats.csv` (containing the proportion of successfully merged records), `logs/missing_data_log.csv` (species present in one source only), `logs/unconvertible_units.csv` (rows that could not be converted), `logs/duplicate_records.csv` (if any).  
  - **Verification**:  
    - `merged_analysis.csv` validates against the JSON schema (`python -m jsonschema -i data/processed/merged_analysis.csv contracts/dataset.schema.yaml`).  
    - `logs/merge_stats.csv` exists and contains a numeric value; an assert in the script ensures this proportion ≥ 0.90 (fulfils SC‑001).  
    - Unit tests `tests/test_clean.py` check that conversion factors are applied correctly and that all prohibited hard‑coded paths are absent.

---

## Phase 3 – Base Linear Mixed-Effects Model (LMM)  

- [ ] T005 Fit the base LMM model  
  - `code/04_fit_base_lmm.py` (Python driver) calls `code/R/01_fit_base_lmm.R` through `rpy2`. The R script fits a **Linear Mixed-Effects Model (LMM)** using the `lme4` package:  
    ```
    lifespan_days ~ telomere_length_kb + breeding_latitude + (1|species)
    ```
  - Results are appended as a single row to `results/model_summary.csv` with `model_type: "LMM_Base"`. If `n_species < 15`, the script writes `low_power_flag: true`, populates placeholder `null` values for coefficients, and logs the message `"Low Power: species-level inference unreliable"` to `logs/low_power_log.txt`.  
  - **Verification**:  
    - `results/model_summary.csv` validates against a finalized `contracts/model_output.schema.yaml`.  
    - The script asserts that `p_value_telomere` is compared to `alpha = 0.05` and writes a boolean `telomere_significant` flag.  
    - A human‑readable summary is written to `logs/base_model_fit.log`.

---

## Phase 4 – Interaction Model (Ecological Moderators)  

- [ ] T006 Fit the moderator‑augmented LMM model  
  - `code/05_fit_interaction_lmm.py` invokes `code/R/02_fit_interaction_lmm.R` (via `rpy2`). The R formula is:  
    ```
    lifespan_days ~ telomere_length_kb * migration_status + 
                    telomere_length_kb * breeding_latitude + (1|species)
    ```
  - Records with `migration_status == "Unknown"` are excluded from the interaction term estimation; the count of excluded records is written to `logs/interaction_exclusion_log.csv`.  
  - The resulting row (with `model_type: "LMM_Interaction"`) is appended to `results/model_summary.csv`.  
  - The script computes the AIC difference between the interaction and base models, writes the numeric value to `logs/aic_comparison.txt`, and updates the `delta_aic` field in the interaction row.  
  - **Verification**:  
    - `results/model_summary.csv` now contains exactly two rows (base + interaction) and passes schema validation.  
    - `logs/aic_comparison.txt` exists and contains a single floating‑point number.  
    - The interaction‑exclusion log lists the number of rows dropped and matches the count reported in the model summary.

---

## Phase 5 – Sensitivity & Power Analysis  

- [ ] T007 Perform LOOCV‑by‑species or jackknife‑by‑study sensitivity checks and estimate statistical power  
  - `code/06_sensitivity_power.py` reads `model_summary.csv` to obtain `n_species`.  
    - If `n_species ≥ 10`, it runs **leave‑one‑out cross‑validation (LOOCV) by species**: each iteration refits the base LMM on the dataset with one species removed, records `iteration_id`, `excluded_species`, `coefficient_telomere`, and `p_value_telomere`.  
    - If `n_species < 10`, it performs a **jackknife by study DOI** instead.  
  - The script also conducts a simulation‑based power analysis (1 000 replicates) matching the observed species count, random effect variance, and covariate structure, inserting a standardized telomere slope of 0.2. The proportion of simulations with `p < 0.05` is stored as `power_estimate`.  
  - Outputs: `results/sensitivity_log.csv`, `results/power_report.yaml`, and a log entry `logs/sensitivity_method.txt` describing the chosen method and justification.  
  - **Verification**:  
    - Both output files exist and conform to a finalized `contracts/model_output.schema.yaml`.  
    - The range of `coefficient_telomere` values in `sensitivity_log.csv` encloses the full‑sample coefficient from `model_summary.csv`.  
    - `power_report.yaml` contains a numeric `power_estimate` between 0 and 1.

---

## Phase 6 – Visualization  

- [ ] T008 Produce deterministic visual summaries  
  - `code/07_visualize.py` reads `results/model_summary.csv` and generates:  
    1. **Forest plot** of all fixed‑effect estimates with 95 % confidence intervals → `results/association_forest.png`.  
    2. **Moderator plot**: a grouped scatter of `lifespan_days` vs. `telomere_length_kb` with separate regression lines for “Migratory” and “Resident” species, plus a continuous latitude‑gradient plot → `results/moderator_plot.png`.  
  - After creation, the script computes SHA‑256 checksums for each PNG and records them in `logs/visualization_checksums.csv`. The visualisation code is seeded (`np.random.seed(42)`) to guarantee reproducibility.  
  - **Verification**:  
    - Both PNG files exist, are larger than 10 KB, and open without error.  
    - Re‑running the script on the same inputs reproduces identical checksum values (verified by a unit test in `tests/test_visualization.py`).

---

## Phase 7 – Testing Suite & Synthetic Validation  

- [ ] T009 Extend the automated test suite with synthetic benchmarks and power sanity checks  
  - Add `tests/test_model_synthetic.py` containing:  
    - `test_known_coefficients`: builds a synthetic dataset (seed = 42) with a pre‑specified telomere‑lifespan slope, runs the base LMM via the R script, and asserts that the reported `p_value_telomere` matches a manual OLS calculation (as an approximation for the fixed effect) within `1e‑6`.  
    - `test_null_relationship`: creates an uncorrelated synthetic dataset and asserts `p_value_telomere > 0.05`.  
  - Add `tests/test_power_estimate.py` that calls the power‑estimation routine and verifies the returned `power_estimate` lies in `[0, 1]`.  
  - Ensure all new tests are discovered by `pytest` and that the suite passes with exit code 0.  
  - **Verification**:  
    - Running `pytest -q` reports 0 failures and ≥ 3 new tests.  
    - The synthetic tests write no permanent artifacts outside `tmp/` directories.

---

## Phase 8 – Documentation & Paper‑Stage Hand‑off  

- [ ] T010 Write a reproducible quick‑start guide and hand‑off section  
  - `quickstart.md` (placed under `specs/001-telomere-lifespan-impact/`) contains:  
    1. The exact command sequence to run the full pipeline (ingestion → cleaning → base model → interaction model → sensitivity/power → visualisation).  
    2. Expected output file paths and their SHA‑256 checksums (generated by the first successful run).  
    3. Instructions for interpreting low‑power warnings, missing‑data logs, and unconvertible‑unit logs.  
    4. A “Paper‑Stage Hand‑off” subsection listing:  
       - Figures: `results/association_forest.png`, `results/moderator_plot.png`.  
       - Tables: `results/model_summary.csv`, `results/sensitivity_log.csv`, `results/power_report.yaml`.  
       - Limitations paragraph (observational data, power constraints, measurement heterogeneity).  
       - Suggested caption text for each figure/table.  
  - **Verification**:  
    - A fresh clone of the repository, after installing `requirements.txt` and `R/requirements_R.txt`, can follow the guide verbatim and reproduce identical checksums for all result artifacts (checked by a helper script `code/tests/test_quickstart_repro.py`).

---

## Phase 9 – Project State Hash Management  

- [ ] T011 Implement deterministic state‑hash updates  
  - Add `code/utils.py` with function `update_state_hashes()` that recursively walks `data/`, `results/`, and `logs/`, computes SHA‑256 for every file, and writes a mapping `relative_path → hash` to `state/projects/PROJ-055-investigating-the-impact-of-telomere-len.yaml`.  
  - Ensure **every** pipeline script (`02_ingest_data.py`, `03_clean_merge.py`, `04_fit_base_lmm.py`, `05_fit_interaction_lmm.py`, `06_sensitivity_power.py`, `07_visualize.py`) calls `utils.update_state_hashes()` as the final step.  
  - **Verification**:  
    - After any pipeline stage, `state/projects/PROJ-055-investigating-the-impact-of-telomere-len.yaml` exists and contains entries that exactly match the on‑disk SHA‑256 values.  
    - A verification script `tests/test_state_hashes.py` confirms the YAML matches current filesystem hashes.

---

### Dependency Mapping (summary)

| Specification Requirement | Satisfying Task(s) |
|---------------------------|--------------------|
| FR‑001, FR‑002, FR‑003    | T002, T003, T004   |
| FR‑004                    | T005               |
| FR‑005                    | T006               |
| FR‑006                    | T007               |
| FR‑007                    | T008               |
| FR‑008                    | T005, T006         |
| SC‑001                    | T004 (merge proportion artifact) |
| SC‑002                    | T005 (alpha‑threshold flag) |
| SC‑003                    | T006 (AIC difference) |
| SC‑004                    | T007 (coefficient stability) |
| SC‑005                    | T009 (power estimate) |
| US‑1, US‑2, US‑3          | T003, T004, T005‑T008 |

All tasks are ordered to respect data flow, write only to project‑owned paths, and avoid any synthetic data fabrication. The pipeline is fully deterministic, reproducible, and satisfies every functional and success‑criteria requirement from the specification.