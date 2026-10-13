# Tasks: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

**Inputs**: `specs/001-telomere-lifespan-impact/spec.md`, `plan.md`, `data-model.md`, `contracts/`, prior task list and verifier rejections.

## Phase 0: Reproducibility setup

- [ ] T010 [P?] Create `code/requirements.txt` listing pinned Python dependencies (e.g., pandas, numpy, requests, rpy2, matplotlib, seaborn, pytest, pyyaml).  
  **Verification**: File exists, is non‑empty, and `pip install -r code/requirements.txt` succeeds in a fresh virtual environment.

- [ ] T011 [P?] Create `code/R/renv.lock` (or top‑level `renv.lock`) pinning R packages `phylolm`, `ape`, `rotl`, `caper`.   <!-- FAILED-IN-EXECUTION: code/R/verify_renv.py exit=1 -->
  **Verification**: File exists and `R -e "renv::restore()"` restores the packages without error.

## Phase 1: Configuration (must precede ingestion)

- [ ] T002 [US1] Implement environment configuration `code/config.yaml` documenting Dryad/AnAge endpoints, dataset IDs, random seed(s), and the alpha threshold (0.05).  
  **Verification**: `code/config.yaml` is valid YAML and is read by `02_ingest_data.py` and `03_clean_merge.py` (no hard‑coded URLs or seeds in those scripts).

## Phase 2: Data ingestion & cleaning (produces canonical files)

- [ ] T001 [US1] Complete the data ingestion and cleaning pipeline:
  1. `code/02_ingest_data.py` downloads raw CSVs from Dryad (using dataset IDs from `config.yaml`) and the AnAge longevity table, writes raw files under `data/raw/` with SHA256 checksums.
  2. `code/03_clean_merge.py`:
     - Standardises all telomere length measurements to kilobases (kb) using documented conversion factors.
     - Filters to wild‑caught, juvenile records only.
     - Writes the intermediate, unit‑standardised file `data/processed/telomere_standardized.csv`.
     - Merges with ecological covariates (migration status, body mass) to produce the final analysis dataset `data/processed/merged_analysis.csv`, adhering to `contracts/dataset.schema.yaml` (no duplicate `species_id`).
     - Logs unconvertible rows to `logs/unconvertible_units.csv` and unmatched species to `logs/missing_data_log.csv`.
  3. **Verification**:
     - Both CSVs exist and are non‑empty.
     - Schema validation against `contracts/dataset.schema.yaml` passes.
     - The proportion of merged species ≥ 90 % of the union of source species (SC‑001 threshold) is reported and asserted.
     - `utils.py` records SHA256 hashes of all newly written files and updates `state/projects/PROJ-055-investigating-the-impact-of-telomere-len.yaml` via its helper (no direct task writes to `state/`).
     - Unit tests are placed in the root `tests/` directory:
       - `tests/test_ingest.py::test_dryad_download`
       - `tests/test_clean.py::test_unit_conversion`
       - `tests/test_clean.py::test_species_merge`
     - Running `pytest` passes.

## Phase 3: Phylogeny acquisition and base model fitting

- [ ] T003 [US2] Implement the base PGLS model:
  - `code/04_model_pglS.py` extracts the unique species list from `data/processed/merged_analysis.csv`, fetches the matching bird phylogeny via the Open Tree of Life (`rotl`), and saves it as `data/phylogeny/bird_tree.tre`.
  - Calls the R script `code/R/01_fit_pglS.R` via `rpy2` to fit a Phylogenetic Generalized Least Squares model.
  - **Always** writes a row to `results/model_summary.csv` that conforms to `contracts/model_output.schema.yaml`.  
    - If `n_species < 15`, the row contains placeholder numeric values (e.g., `0.0`) with `low_power_flag: true` and a brief explanation logged in `logs/low_power_log.txt`.  
    - Otherwise, real estimates (including `fixed_effect_telomere`, `p_value_telomere`, `phylogenetic_lambda`, `aic_score`, `n_species`, `low_power_flag: false`, `power_estimate`) are recorded.
  - **Verification**: Script exits with status 0, the tree file contains every species present in the merged analysis, and `results/model_summary.csv` validates against the schema.

## Phase 4: Sensitivity analysis (aligned with data model)

- [ ] T004 [US2] Implement leave‑one‑out / jackknife sensitivity:
  - New script `code/04_sensitivity.py` (invoked by `04_model_pglS.py` or run independently) performs LOOCV when `n_species >= 10`; otherwise performs jackknife by study.
  - Writes `results/sensitivity_log.csv` with exactly the columns defined by the `SensitivityLog` entity:
    `iteration_id, excluded_species, coefficient_telomere, p_value`.
  - **Verification**: CSV exists, column order matches the schema, and the range of `coefficient_telomere` values encloses the full‑sample coefficient from `results/model_summary.csv`.

## Phase 5: Moderator interaction model

- [ ] T013 [US3] Create `code/R/03_fit_moderator.R` containing a PGLS model with formula `lifespan ~ telomere_length * migration_status`. The script header records the formula, data source, and version information.  
  **Verification**: File exists and is syntactically valid R code.

- [ ] T005 [US3] Extend `code/04_model_pglS.py` to invoke `code/R/03_fit_moderator.R` after the base model, and append a `PGLS_Interaction` row to `results/model_summary.csv` with all required fields (including interaction coefficient, its p‑value, AIC, and `low_power_flag: false`).  
  **Verification**: `results/model_summary.csv` now contains two rows (base and interaction) and both rows validate against the schema; the AIC difference is computed and recorded.

## Phase 6: Visualization (deterministic reproducibility)

- [ ] T006 [US2] Complete `code/05_visualize.py`:
  - Generates a forest plot `results/association_forest.png` from all rows in `model_summary.csv`.
  - Generates a grouped scatter plot `results/moderator_plot.png` showing lifespan vs. telomere length with separate regression lines for “Migratory” and “Resident” species.
  - After creation, computes SHA256 checksums of both PNGs and records them in `logs/visualization_checksums.csv`.
  - **Verification**: Both PNG files exist, are > 10 KB, are readable image files, and on a repeat run their SHA256 hashes match the recorded values (ensuring deterministic output).

## Phase 7: Model testing and power estimation

- [ ] T007 [US2][US3] Extend `code/tests/test_model.py`:
  - Add a deterministic synthetic dataset test (seed = 42) that verifies the telomere coefficient p‑value matches a manual OLS calculation within 1e‑6.
  - Add a synthetic uncorrelated dataset test expecting a p‑value > 0.05.
  - Incorporate a power‑estimate calculation (Cohen’s d = 0.5, α = 0.05) into `04_model_pglS.py`; the resulting value is written to the `power_estimate` column of `results/model_summary.csv`.
  - **Verification**: `pytest` passes; `power_estimate` is populated and lies in the interval [0, 1].

## Phase 8: Quickstart and paper‑stage handoff

- [ ] T008 [P] Write `quickstart.md` in `specs/001-investigating-the-impact-of-telomere-len/`:
  - Document the exact command sequence (`python code/02_ingest_data.py`, `python code/03_clean_merge.py`, `python code/04_model_pglS.py`, `python code/05_visualize.py`).
  - List expected output artifacts with their SHA256 checksums.
  - Explain handling of low‑power flags, exclusion logs, and the observational (non‑causal) framing.
  - **Verification**: A fresh run following only this guide reproduces identical SHA256 hashes for all result files.

- [ ] T009 Document the paper‑stage handoff within `quickstart.md` (figures, tables, limitations).  
  **Verification**: Section present and clearly lists required items for the downstream paper pipeline.

## Phase 9: State hash management

- [ ] T012 [P] Verify that `utils.py` implements a function (e.g., `update_state_hashes()`) that records SHA256 hashes of every file written to `data/`, `results/`, and `logs/` into `state/projects/PROJ-055-investigating-the-impact-of-telomere-len.yaml`.  
  **Verification**: After any pipeline step, the state YAML contains matching hashes for all newly created artifacts (no direct task writes to `state/`; the helper is invoked by the pipeline scripts).