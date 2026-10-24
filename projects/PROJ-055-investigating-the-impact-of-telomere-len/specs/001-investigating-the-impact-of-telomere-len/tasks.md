# Tasks: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations  

**Inputs**: `specs/001-telomere-lifespan-impact/spec.md`, `plan.md`, `data-model.md`, `contracts/`, prior task list and verifier feedback.

## Phase 0 – Dependency Specification  

- [ ] T001 [P] Create reproducible dependency manifests   <!-- FAILED-IN-EXECUTION: code/R/verify_requirements.R exit=-1 --> <!-- FAILED-IN-EXECUTION: code/R/verify_requirements.sh exit=127 --> <!-- FAILED-IN-EXECUTION: code/R/verify_requirements.R exit=-1 -->
  - **Python**: `code/requirements.txt` listing pinned versions of `pandas`, `numpy`, `requests`, `rpy2`, `matplotlib`, `seaborn`, `pytest`, `pyyaml`, `tqdm`.  
  - **R**: `code/R/requirements_R.txt` containing package names and versions for `lme4`, `lmerTest`, `ggplot2`, `patchwork`, `performance`.  
  - **Verification**:  
    - Both files exist and are non‑empty.  
    - `pip install -r code/requirements.txt` succeeds in a fresh virtual environment.  
    - Running `Rscript code/R/verify_requirements.R` exits with status 0, confirming all listed R packages are installed.

## Phase 1 – Data Discovery, Configuration & Ingestion  

- [ ] T002 [US-1] Populate a complete configuration file with real Dryad DOIs  
  - Create `code/config.yaml` containing required keys (`dryad_api_base`, `dataset_ids`, `anage_url`, `random_seed`, `alpha`, `chunk_size`).  
  - **Important**: `dataset_ids` **must be a non‑empty list** of real, publicly resolvable Dryad DOIs (e.g., `["[UNRESOLVED-CLAIM: 10.5061/dryad.abc123 — HTTP 404]", "[UNRESOLVED-CLAIM: 10.5061/dryad.def456 — HTTP 404]"]`).  
  - Implement `code/01_discover_data.py` that queries the Dryad API for datasets containing the keyword “telomere”, validates each DOI resolves (HTTP 200), and writes the list to `config.yaml`. Run this script to auto‑populate `dataset_ids`.  
  - Ensure `code/02_ingest_data.py` and `code/03_clean_merge.py` import the configuration via `yaml.safe_load(open("code/config.yaml"))` and contain **no** hard‑coded URLs or seeds.  
  - **Verification**:  
    - `config.yaml` parses without error and `dataset_ids` contains at least one real DOI.  
    - Executing `python code/01_discover_data.py` updates the file (or confirms existing IDs).  
    - Static analysis (`grep -R "http"`) on `code/02_ingest_data.py` and `code/03_clean_merge.py` returns no matches for literal URLs or numeric seeds.  

- [ ] T003 [US-1] Implement robust data‑ingestion pipeline  
  - `code/02_ingest_data.py` reads `config.yaml`, streams each DOI listed under `dataset_ids` using `requests`, writes raw CSVs to `data/raw/` preserving original filenames, and creates a SHA‑256 checksum file `data/raw/<filename>.sha256`.  
  - The script also downloads the AnAge CSV (or BirdLife fallback) to `data/raw/anage_lifespan.csv` with its checksum.  
  - All downloads must raise an exception on failure (no synthetic fallback).  
  - **Verification**:  
    - After execution, every expected raw file exists and its `.sha256` file is non‑empty.  
    - `sha256sum -c data/raw/*.sha256` passes.  
    - Unit tests `tests/test_ingest.py` assert the number of downloaded files equals `len(dataset_ids) + 1`.  

## Phase 2 – Cleaning, Standardisation & Merging  

- [ ] T004 [US-1] Build a full cleaning & merge workflow  
  - `code/03_clean_merge.py` reads raw CSVs, validates taxonomy via OpenTree, converts telomere units to kb, filters to wild‑caught juveniles, merges with lifespan and covariates, and writes `data/processed/merged_analysis.csv`.  
  - Generates logs: `logs/unit_conversion_log.csv`, `logs/merge_stats.csv`, `logs/missing_data_log.csv`, `logs/unconvertible_units.csv`, `logs/duplicate_records.csv`.  
  - **Verification**:  
    - `merged_analysis.csv` validates against `contracts/dataset.schema.yaml`.  
    - `logs/merge_stats.csv` reports a merge proportion ≥ 0.90 (fulfills SC‑001).  
    - Unit tests `tests/test_clean.py` check conversion correctness and absence of hard‑coded paths.  

## Phase 3 – Base Linear Mixed‑Effects Model (LMM)  

- [ ] T005 Fit the base LMM model  
  - `code/04_fit_base_lmm.py` (Python driver) calls `code/R/01_fit_base_lmm.R` via `rpy2`. The R script fits: `lifespan_days ~ telomere_length_kb + breeding_latitude + (1|species)`.  
  - Results appended to `results/model_summary.csv` with `model_type: "LMM_Base"`. If `n_species < 15`, writes `low_power_flag: true` and logs `"Low Power: species-level inference unreliable"` to `logs/low_power_log.txt`.  
  - **Verification**:  
    - `results/model_summary.csv` validates against `contracts/model_output.schema.yaml`.  
    - Script asserts `p_value_telomere` compared to `alpha = 0.05` and writes `telomere_significant` boolean.  
    - Human‑readable summary in `logs/base_model_fit.log`.  

## Phase 4 – Interaction Model (Ecological Moderators)  

- [ ] T006 Fit the moderator‑augmented LMM model  
  - `code/05_fit_interaction_lmm.py` invokes `code/R/02_fit_interaction_lmm.R`. Formula: `lifespan_days ~ telomere_length_kb * migration_status + telomere_length_kb * breeding_latitude + (1|species)`.  
  - Excludes rows with `migration_status == "Unknown"` from interaction estimation; logs count to `logs/interaction_exclusion_log.csv`.  
  - Appends row with `model_type: "LMM_Interaction"` to `results/model_summary.csv`.  
  - Computes ΔAIC vs. base model, writes to `logs/aic_comparison.txt`, updates `delta_aic` field.  
  - **Verification**:  
    - `results/model_summary.csv` contains exactly two rows and passes schema validation.  
    - `logs/aic_comparison.txt` contains a single float.  
    - Interaction‑exclusion log matches count reported in model summary.  

## Phase 5 – Sensitivity & Power Analysis  

- [ ] T007 Perform LOOCV‑by‑species or jackknife‑by‑study sensitivity checks and estimate statistical power  
  - `code/06_sensitivity_power.py` reads `model_summary.csv` for `n_species`.  
  - If `n_species ≥ 10`, runs LOOCV by species; otherwise jackknife by study DOI. Records `iteration_id`, `excluded_unit`, `coefficient_telomere`, `p_value_telomere` to `results/sensitivity_log.csv`.  
  - Conducts 1 000 simulation‑based power analyses with standardized telomere slope = 0.2, stores `power_estimate` in `results/power_report.yaml`.  
  - Writes method justification to `logs/sensitivity_method.txt`.  
  - **Verification**:  
    - Output files exist and conform to schemas.  
    - Range of `coefficient_telomere` in `sensitivity_log.csv` encloses full‑sample coefficient.  
    - `power_report.yaml` contains numeric `power_estimate` between 0 and 1.  

## Phase 6 – Visualization  

- [ ] T008 Produce deterministic visual summaries  
  - `code/07_visualize.py` reads `results/model_summary.csv` and creates:  
    1. Forest plot → `results/association_forest.png`.  
    2. Moderator plot (grouped scatter for migration status and latitude gradient) → `results/moderator_plot.png`.  
  - Computes SHA‑256 checksums for each PNG and records in `logs/visualization_checksums.csv`. Uses fixed random seed for reproducibility.  
  - **Verification**:  
    - Both PNGs exist, > 10 KB, open without error.  
    - Re‑running the script yields identical checksums (asserted in `tests/test_visualization.py`).  

## Phase 7 – Testing Suite & Synthetic Validation  

- [ ] T009 Extend the automated test suite with synthetic benchmarks and power sanity checks  
  - Add `tests/test_model_synthetic.py` with `test_known_coefficients` and `test_null_relationship` using seeded synthetic data.  
  - Add `tests/test_power_estimate.py` verifying `power_estimate` in `[0,1]`.  
  - Ensure `pytest -q` reports ≥ 3 new tests and 0 failures.  

## Phase 8 – Documentation & Paper‑Stage Hand‑off  

- [ ] T010 Write a reproducible quick‑start guide and hand‑off section  
  - `quickstart.md` under `specs/001-telomere-lifespan-impact/` lists full command sequence, expected output paths with SHA‑256 checksums, interpretation of warnings, and a “Paper‑Stage Hand‑off” subsection enumerating figures, tables, limitations, and suggested captions.  
  - **Verification**:  
    - A fresh clone can follow the guide verbatim and reproduce identical checksums for all result artifacts (validated by `code/tests/test_quickstart_repro.py`).  

## Phase 9 – Project State Hash Management  

- [ ] T011 Implement deterministic state‑hash updates and pass verification  
  - Refactor `code/utils.py` to provide `update_state_hashes(root_paths: List[str]) -> dict` that walks `data/`, `results/`, and `logs/`, computes SHA‑256 for every file, and writes a mapping `relative_path: hash` to `state/projects/PROJ-055-investigating-the-impact-of-telomere-len.yaml`.  
  - Ensure **all** pipeline scripts (`02_ingest_data.py`, `03_clean_merge.py`, `04_fit_base_lmm.py`, `05_fit_interaction_lmm.py`, `06_sensitivity_power.py`, `07_visualize.py`) invoke `utils.update_state_hashes([...])` as their final step.  
  - Update the verification script `code/R/verify_renv.py` so that it checks the YAML file exists and that each recorded hash matches the on‑disk file (using `hashlib.sha256`) and exits with status 0.  
  - **Verification**:  
    - After any pipeline stage, the state YAML exists and contains entries that exactly match current file hashes.  
    - Running `Rscript code/R/verify_renv.py` exits with status 0.  

## Dependency Mapping (summary)

| Specification Requirement | Satisfying Task(s) |
|---------------------------|--------------------|
| FR‑001, FR‑002, FR‑003    | T002, T003, T004   |
| FR‑004                    | T005               |
| FR‑005                    | T006               |
| FR‑006                    | T007               |
| FR‑007                    | T008               |
| FR‑008                    | T005, T006         |
| SC‑001                    | T004 (merge proportion) |
| SC‑002                    | T005 (alpha‑threshold) |
| SC‑003                    | T006 (ΔAIC) |
| SC‑004                    | T007 (coefficient stability) |
| SC‑005                    | T009 (power estimate) |
| US‑1, US‑2, US‑3          | T003, T004, T005‑T008 |

All tasks respect data flow, write only to project‑owned directories, and avoid synthetic data fabrication. The pipeline is fully deterministic, reproducible, and satisfies every functional and success‑criteria requirement from the specification.  