# Tasks: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts (`*.schema.yaml`), reviewer feedback.  
All paths are relative to the project root `projects/PROJ-355-predicting-the-impact-of-impurity-cluste/`.

---

- [ ] T001 [P] [US-1] **Create a verifiable `.gitignore`**  
  - File: `.gitignore`  
  - Requirements: Must contain the patterns `data/`, `results/`, `*.pyc`, `__pycache__/`.  
  - Verification: `tests/unit/test_gitignore.py` asserts each pattern is present; the test must pass.

- [ ] T002 [P] [US-1] **Write a complete `README.md`**  
  - File: `README.md`  
  - Requirements: Include (a) project title, (b) one‑line execution command (`python -m code.main`), (c) data‑provenance section that cites the verified OQMD loader and documents the Materials Project deviation, (d) brief summary of the research question.  
  - Verification: `tests/unit/test_readme.py` checks for the required headings and strings; the test must pass.

- [ ] T003 [US-1] **Download bulk configuration records (OQMD) with retry logic and checksum verification**  
  - Files: `code/download.py`, `data/raw/oqmd_records/` (immutable JSON/CSV files), `data/metadata.yaml` (records dataset ID, sampling rule, SHA‑256 checksums).  
  - Steps:  
    1. Use the verified recipe `datasets.load_dataset("jablonkagroup/oqmd", name="raw_data")` with streaming.  
    2. Sample exactly 600 records (200 per alloy system Fe‑Cr, Ni‑Al, Cu‑Zn) using a fixed random seed.  
    3. Retry up to 3 times on transient failures; on permanent failure log `[DATA_UNAVAILABLE]` and raise.  
    4. Compute and record SHA‑256 checksums for all downloaded files in `data/metadata.yaml`.  
  - Verification: `tests/unit/test_download_retry.py` must pass; `data/metadata.yaml` must contain the OQMD dataset ID, sampling rule, and checksums for all raw files.

- [ ] T003a [US-1] **Attempt Materials Project bulk configuration download and record deviation status**  
  - Files: `code/download.py` (MP section), `data/metadata.yaml` (materials_project_status field).  
  - Steps:  
    1. Attempt to download Materials Project bulk structures using a verified public API endpoint (if one exists) or via `wget`/`curl` from a documented MP data repository.  
    2. Retry up to 3 times on transient failures.  
    3. If successful, store files in `data/raw/mp_records/` and record checksums in `data/metadata.yaml`.  
    4. If permanent failure (no verified endpoint available), log `[DATA_UNAVAILABLE]` and record `materials_project_status: DATA_UNAVAILABLE` in `data/metadata.yaml` with a brief explanation (e.g., "No open API endpoint; Materials Project requires authentication").  
  - Verification: `tests/unit/test_download_retry.py` must confirm that the MP section was attempted and that `data/metadata.yaml` contains the `materials_project_status` field with either `RETRIEVED` or `DATA_UNAVAILABLE`.

- [ ] T003b [US-1] **Document FR-003 deviation: segregation‑energy source limitation**  
  - Files: `data/metadata.yaml` (fr_003_deviation field).  
  - Steps:  
    1. Record in `data/metadata.yaml` that no verified open-access literature database of segregation‑energy measurements exists.  
    2. Document that segregation energies will be generated in‑house using validated EAM potentials (see T006), satisfying the intent of FR-003 (providing labeled segregation‑energy targets) while acknowledging the source limitation.  
    3. Include a note that this deviation is justified by the absence of a public literature database and is recorded per the Constitution's transparency principle.  
  - Verification: `data/metadata.yaml` must contain a `fr_003_deviation` field with the explanation; no synthetic/fabricated data is used in T006.

- [ ] T004 [US-1] **Reconstruct bulk structures, build GB supercells, insert impurities, and filter zero‑impurity cases**  
  - Files: `code/gb_builder.py`, `data/processed/gb_structures/` (relaxed GB `.json` files), `data/processed/gb_build_map.csv`.  
  - Steps:  
    1. For each OQMD record, reconstruct a bulk `pymatgen.Structure` from `formula`, `spacegroup`, and `volume_per_atom`.  
    2. Generate a symmetric 90° tilt grain‑boundary supercell, insert impurity atoms **as a pre‑existing bulk cluster** (i.e., before GB creation) and then place the GB.  
    3. Perform EAM relaxation with ASE.  
    4. Exclude configurations with zero impurity atoms; log the count in `data/processed/preprocessing_report.json`.  
  - Verification: `tests/unit/test_gb_builder.py` checks that every output GB has at least one impurity and that the mapping CSV correctly links `bulk_id` → `gb_id` → `alloy_system`.

- [ ] T005 [US-1] [US-2] **Compute clustering descriptors from the GB interface region and generate VIF collinearity report**  
  - Files: `code/descriptors.py`, `data/processed/descriptors.csv`, `results/metrics.json` (collinearity block).  
  - Steps:  
    1. From the **interface region** (atoms within 3 Ångströms of the GB plane) of each **relaxed GB structure** (post‑EAM relaxation), compute three descriptors: RDF peak value, pair‑correlation statistic, and Voronoi neighbor count. Also compute `cluster_size` (mean nearest‑neighbor distance among interface impurities) and `local_lattice_strain` (trace of the local strain tensor around the interface).  
    2. Calculate Variance Inflation Factors (VIF) for the three original descriptors (RDF peak, pair-correlation, Voronoi count); threshold VIF = 10.  
    3. Emit a JSON collinearity report (`high_collinearity_detected`, `flagged_groups` with predictor list, max VIF, one‑sentence summary) and embed it under the `collinearity` block in `results/metrics.json`.  
    4. Write all descriptor values to `data/processed/descriptors.csv` with columns matching `contracts/dataset.schema.yaml`.  
  - Verification: `tests/unit/test_descriptors.py::test_vif_detection` must pass; the JSON report must conform to `contracts/output.schema.yaml`; every descriptor must be computed only from interface atoms.

- [ ] T006 [US-2] **Generate EAM segregation‑energy labels and assemble the training dataset**  
  - Files: `code/simulate_energy.py`, `data/processed/energies.csv`, `data/processed/training_set.csv`, `data/processed/sample_size_justification.md`.  
  - Steps:  
    1. Run validated EAM potentials for the three alloy systems (Fe‑Cr, Ni‑Al, Cu‑Zn) on each GB structure to obtain segregation energies (leave‑one‑out).  
    2. Merge `descriptors.csv` with `energies.csv`, add covariates `atomic_radius` and `electronegativity` from standard elemental tables, and assign a deterministic `split` column (`train`/`test`) ensuring ≥50 held‑out samples and ≥3 alloy systems in the test set.  
    3. Validate the final CSV against `contracts/dataset.schema.yaml`.  
    4. Document the final sample size, the 200‑sample floor, and the power‑analysis justification in `sample_size_justification.md`. Reference the FR-003 deviation record from T003b.  
  - Verification: `tests/unit/test_training_set.py` validates schema compliance and split proportions; the justification markdown must contain the required numeric statements.

- [ ] T007 [US-2] **Perform power analysis (FR‑008) and linearity assessment (FR‑010)**  
  - Files: `code/power_analysis.py`, `results/metrics.json` (power_analysis and linearity_assessment blocks).  
  - Steps:  
    1. Using `statsmodels.stats.power.FTestPower`, compute required sample size for effect size f² = 0.15, α = 0.05, and predictor count = 12 (matching the 12 columns in the training-set schema: rdf_peak_value, pair_corr_value, voronoi_count, cluster_size, local_lattice_strain, atomic_radius, electronegativity, impurity_species, alloy_system, bulk_id, gb_id, sample_id). Record `required_n`, `achieved_n`, `achieved_power`, `meets_requirement`.  
    2. Generate scatter plots of each descriptor vs. segregation energy and residual plots for a provisional OLS fit; store a boolean `appears_linear` and a textual `evidence` description.  
    3. Insert both results into `results/metrics.json`.  
  - Verification: `tests/unit/test_power_linearity.py` checks that `meets_requirement` is true and that `appears_linear` is a boolean.

- [ ] T008 [US-2] **Train Linear Regression and RandomForest models with GroupKFold CV, evaluate held‑out set, and produce prediction intervals**  
  - Files: `code/train_model.py`, `results/metrics.json` (model_type, cross_validation, held_out_test blocks).  
  - Steps:  
    1. Use `GroupKFold` on `gb_id` (5‑fold, or LOOCV if N < 5) to train both a statsmodels OLS model (record p‑values) and a scikit‑learn `RandomForestRegressor`.  
    2. Record per‑fold R², RMSE, and for the linear model also coefficient p‑values.  
    3. Evaluate on the held‑out test set (≥50 samples, ≥3 alloy systems); compute overall R², RMSE, per‑system R², and a permutation‑test p‑value (1 000 permutations) for the linear model.  
    4. Produce 95 % prediction intervals for every test prediction (OLS via `get_prediction()`, RF via quantile regression or bootstrapping) and set `ci95_available: true`.  
    5. Choose `model_type` in the JSON according to the linearity verdict (`LinearRegression` if `appears_linear` true, otherwise `RandomForest`).  
  - Verification: `tests/integration/test_model_training.py` must pass; the JSON must validate against `contracts/output.schema.yaml`.

- [ ] T009 [US-3] **Conduct hypothesis testing, apply Benjamini‑Hochberg FDR correction, and write the report**  
  - Files: `code/report.py`, `results/hypothesis_report.json`.  
  - Steps:  
    1. Extract raw p‑values for all regression coefficients from the linear model.  
    2. If more than one hypothesis, apply **Benjamini‑Hochberg FDR correction** (not Bonferroni); compute adjusted p‑values.  
    3. Flag predictors whose significance status changes after correction; count them (`n_significance_changes`).  
    4. Write a JSON report conforming to `contracts/report.schema.yaml` with `correction_method: "fdr-bh"`, `alpha: 0.05`, `n_hypotheses`, detailed predictor entries, and a free‑text `summary`.  
  - Verification: `tests/unit/test_hypothesis_report.py` validates schema compliance, confirms `correction_method: "fdr-bh"` is set, and verifies that `n_significance_changes` matches the computed changes.

- [ ] T010 [US-3] **Generate the cluster‑size vs. segregation‑energy figure with 95 % confidence bands**  
  - Files: `code/plots.py`, `results/cluster_size_vs_segregation.png`.  
  - Steps:  
    1. For each alloy system (≥3), plot `cluster_size` on the x‑axis and `segregation_energy_eV` on the y‑axis using the held‑out test data.  
    2. Overlay 95 % confidence intervals derived from the chosen model's prediction intervals.  
    3. Save as a high‑resolution PNG (`dpi=300`).  
  - Verification: `tests/unit/test_plots.py` checks that the PNG exists, has the correct dimensions, and that the file size > 10 KB (ensuring it is not an empty placeholder).

- [ ] T011a [US-2] **Implement FR-011 EAM-vs-DFT validation harness**  
  - Files: `code/validate_potential.py`, `results/metrics.json` (eam_validation block).  
  - Steps:  
    1. Check if a verified DFT benchmark dataset is available (injected by the execution stage or specified in `data/metadata.yaml`).  
    2. **If available and ≥30 samples**: load the benchmark, compute EAM energies for the same structures, compute MAE between EAM and DFT predictions, and check if MAE ≤ 0.1 eV per FR-011. Record `status: "VALIDATED"`, `n_benchmark: <count>`, `mae_eV: <value>`, and set `note` to an empty string or brief confirmation.  
    3. **If unavailable or <30 samples**: record `status: "DATA_UNAVAILABLE"`, `n_benchmark: 0`, `mae_eV: null`, and include a `note` explaining that no verified open DFT benchmark exists (or that the available benchmark is too small).  
    4. Write the `eam_validation` block to `results/metrics.json` conforming to `contracts/output.schema.yaml`. This task is **mandatory and non-optional**; the eam_validation block must be present in every run.  
  - Verification: `tests/unit/test_validate_potential.py` checks that the eam_validation block is present and conforms to schema; the block must contain either `status: "VALIDATED"` with MAE ≤ 0.1 eV or `status: "DATA_UNAVAILABLE"` with a clear explanation in the `note` field.

- [ ] T012 **Run full end‑to‑end pipeline, execute integration tests, and record final metadata**  
  - Files: `code/main.py`, `results/metrics.json`, `results/hypothesis_report.json`, `data/metadata.yaml`, `results/performance_verification.json`.  
  - Steps:  
    1. Execute `python -m code.main` which orchestrates tasks T003–T011a in order.  
    2. Run the full pytest suite (`pytest -q`). All tests must pass.  
    3. After a successful run, append to `data/metadata.yaml` the final `random_seed`, execution `date`, `code_version_hash` (git commit hash), and `data_source` (OQMD loader identifier).  
    4. Write a performance summary (`results/performance_verification.json`) reporting total wall‑clock time, CPU usage, and confirmation that the job stayed within the 6‑hour CPU‑only budget.  
  - Verification: The CI runner must finish with exit code 0; the performance JSON must contain `budget_exceeded: false`.

--- 

**Dependency map**

| Task | Depends on |
|------|------------|
| T001, T002 | – (independent) |
| T003, T003a, T003b | – (independent data-acquisition tasks) |
| T004 | T003, T003a |
| T005 | T004 |
| T006 | T005, T003b |
| T007 | T006 |
| T008 | T007 |
| T009 | T008 |
| T010 | T008 |
| T011a | T006 |
| T012 | All previous tasks (T003–T011a) |

All tasks are unchecked (`- [ ]`) to allow fresh execution and verification.