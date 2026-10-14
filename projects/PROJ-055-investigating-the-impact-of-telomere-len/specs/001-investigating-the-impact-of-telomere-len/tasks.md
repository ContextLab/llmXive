# Tasks: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations  

**Inputs**: `specs/001-telomere-lifespan-impact/spec.md`, `plan.md`, `data-model.md`, `contracts/`, prior task list and verifier feedback.

---

## Phase 0 – Reproducibility & Dependency Setup  

- [ ] T010 Create `code/requirements.txt` listing pinned Python dependencies (e.g., `pandas`, `numpy`, `requests`, `rpy2`, `matplotlib`, `seaborn`, `pytest`, `pyyaml`).  
  **Verification**:  
  - File exists and is non‑empty.  
  - `pip install -r code/requirements.txt` succeeds in a fresh virtual environment.  

- [ ] T011 Generate a lightweight R requirements file `code/R/requirements_R.txt` that records the versions of the R packages (`phylolm`, `ape`, `rotl`, `caper`) installed on‑the‑fly.  
  **Verification**:  
  - `code/R/requirements_R.txt` exists and contains at least one line (package name and version).  
  - A simple R script (`code/R/verify_requirements.R`) reads the file and confirms each listed package is installed; it exits with status 0.  

---

## Phase 1 – Configuration & End‑to‑End Warm‑up  

- [ ] T002 Create `code/config.yaml` documenting:  
  - Dryad base API endpoint and a **non‑empty** list of discovered dataset DOIs (`dataset_ids`).  
  - AnAge CSV download URL.  
  - Random seed (`42`) and analysis alpha (`0.05`).  
  - Any other global parameters (e.g., chunk size).  
  **Verification**:  
  - YAML parses without error and contains at least one DOI in `dataset_ids`.  
  - Both `code/02_ingest_data.py` and `code/03_clean_merge.py` import this file (e.g., `yaml.safe_load(open("code/config.yaml"))`) and contain **no hard‑coded URLs or seeds**.  

- [ ] T001 Implement the data‑ingestion and cleaning pipeline:  
  1. `code/02_ingest_data.py` reads `code/config.yaml`, downloads each Dryad DOI listed, and the AnAge CSV; writes raw files to `data/raw/` with accompanying SHA‑256 checksum files.  
  2. `code/03_clean_merge.py` reads the raw files, converts all telomere measurements to kilobases (using documented conversion factors), filters to wild‑caught juvenile records, and writes:  
     - `data/processed/telomere_standardized.csv` (unit‑standardised telomere data).  
     - `data/processed/merged_analysis.csv` (merged with migration status, body mass, etc.).  
  3. Logging: `logs/unconvertible_units.csv` (rows that could not be converted) and `logs/missing_data_log.csv` (species present in only one source).  
  **Verification**:  
  - All CSVs exist and are non‑empty.  
  - `merged_analysis.csv` validates against `contracts/dataset.schema.yaml`.  
  - The proportion of merged species ≥ 90 % of the union of source species (SC‑001) is computed and asserted in the script.  
  - Unit tests `tests/test_ingest.py` and `tests/test_clean.py` pass via `pytest`.  

- [ ] T000 Execute a minimal end‑to‑end run on a **sampled subset** (first 50 rows of each raw file) to produce:  
  - `data/processed/merged_analysis_sample.csv`  
  - `results/model_summary_sample.csv` (base PGLS on the sample)  
  - `results/association_forest_sample.png`  
  **Verification**:  
  - All three artifacts exist, pass schema validation (where applicable), and their SHA‑256 hashes are recorded in `logs/sample_run_checksums.csv`.  

---

## Phase 2 – Phylogeny Acquisition & Base Model  

- [ ] T003 Acquire a bird phylogeny and fit the base PGLS model:  
  - `code/04_fetch_phylogeny.py` extracts the unique species list from `data/processed/merged_analysis.csv`, queries the Open Tree of Life via the `rotl` R package, and saves the induced subtree to `data/phylogeny/bird_tree.nwk`.  
  - `code/04_model_pgls.py` (Python driver) calls `code/R/01_fit_pgls.R` through `rpy2` to fit `lifespan ~ telomere_length + body_mass + measurement_method`.  
  - Results are appended as a row to `results/model_summary.csv` conforming to `contracts/model_output.schema.yaml`.  
  - If `n_species < 15`, the script writes placeholder values, sets `low_power_flag: true`, and logs the reason to `logs/low_power_log.txt`.  
  **Verification**:  
  - Phylogeny file contains every species present in the merged dataset.  
  - `results/model_summary.csv` validates against the model schema.  
  - Script exits with status 0 and writes a human‑readable summary to `logs/model_fit_log.txt`.  
  - **Alpha‑threshold check**: the script asserts that `p_value_telomere` is compared to the α = 0.05 threshold; it logs a boolean `telomere_significant` flag indicating whether `p_value_telomere <= 0.05`.  

---

## Phase 3 – Sensitivity Checks  

- [ ] T004 Implement leave‑one‑out (LOOCV) or jackknife sensitivity analysis:  
  - `code/05_sensitivity.py` reads `results/model_summary.csv` to obtain `n_species`.  
  - If `n_species ≥ 10`, perform LOOCV; otherwise perform jackknife by study ID.  
  - Each iteration writes a row to `results/sensitivity_log.csv` with columns `iteration_id, excluded_species, coefficient_telomere, p_value`.  
  **Verification**:  
  - CSV exists, column order matches the documented schema.  
  - The range of `coefficient_telomere` values encloses the full‑sample coefficient from `results/model_summary.csv`.  

---

## Phase 4 – Moderator Interaction Model  

- [ ] T013 Create the interaction‑model R script `code/R/03_fit_moderator.R` containing:  
  - Formula `lifespan ~ telomere_length * migration_status + body_mass + measurement_method`.  
  - Header comments documenting data source, R package versions, and git commit hash.  
  **Verification**:  
  - File exists and `Rscript -e "source('code/R/03_fit_moderator.R')"` runs without syntax errors (it may exit early if `n_species < 30`).  

- [ ] T005 Extend `code/04_model_pgls.py` to invoke the moderator script after the base model and append a second row (`model_type: "PGLS_Interaction"`) to `results/model_summary.csv`.  
  - The row must include `fixed_effect_migration`, `interaction_effect`, `p_value_interaction`, updated `aic_score`, and `low_power_flag` (false when `n_species ≥ 30`).  
  - Compute and record the AIC difference between the two models in `logs/aic_comparison.txt`.  
  **Verification**:  
  - `results/model_summary.csv` now contains exactly two rows (base and interaction) that each validate against the model schema.  
  - The AIC difference file exists and contains a numeric value.  

---

## Phase 5 – Visualization  

- [ ] T006 Complete `code/06_visualize.py` to generate:  
  - Forest plot `results/association_forest.png` from all rows in `model_summary.csv`.  
  - Grouped scatter plot `results/moderator_plot.png` showing lifespan vs. telomere length with separate regression lines for “Migratory” and “Resident” species (using the interaction model coefficients).  
  - After creation, compute SHA‑256 checksums and store them in `logs/visualization_checksums.csv`.  
  **Verification**:  
  - Both PNG files exist, are > 10 KB, and can be opened by standard image viewers.  
  - Re‑running the script on the same inputs reproduces identical SHA‑256 hashes (deterministic output).  

---

## Phase 6 – Model Testing & Power Estimation  

- [ ] T007 Expand the test suite (`tests/`) with deterministic synthetic checks:  
  - `tests/test_model_synthetic.py::test_known_coefficients` builds a synthetic dataset (seed = 42) with a pre‑specified telomere‑lifespan slope, runs the base PGLS via the R script, and asserts that the reported `p_value_telomere` matches a manual OLS calculation within `1e‑6`.  
  - `tests/test_model_synthetic.py::test_null_relationship` creates an uncorrelated synthetic dataset and asserts `p_value_telomere > 0.05`.  
  - `tests/test_power_estimate.py` calls the power‑estimation routine (R `pwr` simulation) and verifies that the returned `power_estimate` lies in `[0,1]`.  
  - The power estimate is written to the `power_estimate` column of each model row in `results/model_summary.csv`.  
  **Verification**:  
  - `pytest` passes all new tests.  
  - `results/model_summary.csv` contains a non‑null `power_estimate` between 0 and 1 for both models.  

---

## Phase 7 – User‑Facing Documentation & Paper Handoff  

- [ ] T008 Write `quickstart.md` (placed in `specs/001-telomere-lifespan-impact/`) that:  
  - Lists the exact command sequence (`python code/02_ingest_data.py`, `python code/03_clean_merge.py`, `python code/04_model_pgls.py`, `python code/06_visualize.py`).  
  - Shows expected output file paths and their SHA‑256 checksums (generated by the first successful run).  
  - Explains how low‑power flags, missing‑data logs, and unconvertible‑unit logs are handled.  
  **Verification**:  
  - A fresh clone of the repository, after installing `requirements.txt`, can follow the guide verbatim and reproduce identical checksums for all result artifacts.  

- [ ] T009 Add a “Paper‑Stage Hand‑off” section to `quickstart.md` that enumerates:  
  - Figures (`association_forest.png`, `moderator_plot.png`).  
  - Tables (`model_summary.csv`, `sensitivity_log.csv`).  
  - Limitations paragraph (low power, observational nature, construct‑validity mitigations).  
  - Suggested caption text for each figure/table.  
  **Verification**:  
  - Section is present, clearly titled, and contains all items required by the downstream paper pipeline.  

---

## Phase 8 – State‑Hash Management  

- [ ] T012 Ensure `code/utils.py` provides a function `update_state_hashes()` that:  
  - Recursively computes SHA‑256 hashes for every file under `data/`, `results/`, and `logs/`.  
  - Writes a mapping of relative paths to hashes into `state/projects/PROJ-055-investigating-the-impact-of-telomere-len.yaml`.  
  - Is invoked automatically at the end of each pipeline script (ingestion, cleaning, modeling, visualization).  
  **Verification**:  
  - After any pipeline step, the state YAML contains entries matching the on‑disk hashes (validated by a small helper script `code/tests/test_state_hashes.py`).  

---  

### Dependency Mapping (summary)

| Requirement | Satisfying Task(s) |
|-------------|-------------------|
| FR‑001, FR‑002, FR‑003 | T002, T001 |
| FR‑004 | T003 |
| FR‑005 | T013, T005 |
| FR‑006 | T004 |
| FR‑007 | T006 |
| SC‑001 | T001 (merged‑species proportion) |
| SC‑002 | T003 (alpha‑threshold check) |
| SC‑003 | T005 (AIC difference) |
| SC‑004 | T004 (coefficient stability) |
| SC‑005 | T007 (power estimate) |

---  

*All tasks are ordered to respect data flow; no task writes to `state/` directly (handled by `utils.py`).*  