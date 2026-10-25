# Tasks: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts (`*.schema.yaml`), reviewer feedback.  
All paths are relative to the project root `projects/PROJ-355-predicting-the-impact-of-impurity-cluste/`.

---

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] **T001** [P] **Create a verifiable `.gitignore`**  
  - **File**: `.gitignore`  
  - **Requirements**: Must contain the exact lines `data/`, `results/`, `*.pyc`, `__pycache__/`.  
  - **Verification**: `tests/unit/test_gitignore.py` asserts each pattern is present; the test must pass.

- [ ] **T002** [P] **Write a complete `README.md`**  
  - **File**: `README.md`  
  - **Requirements**: Include (a) project title, (b) one‑line execution command `python -m code.main`, (c) a *Data Provenance* section that cites the verified OQMD loader and documents the Materials‑Project waiver, (d) a brief summary of the research question.  
  - **Verification**: `tests/unit/test_readme.py` checks for the required headings and strings; the test must pass.

- [ ] **T003** [US‑1] **Download bulk configuration records (OQMD) with retry logic and checksum verification**  
  - **Files**: `code/download.py`, `data/raw/oqmd_records/` (immutable JSON/CSV), `data/metadata.yaml` (dataset ID, sampling rule, SHA‑256 checksums).  
  - **Steps**:  
    1. Use `datasets.load_dataset("jablonkagroup/oqmd", name="raw_data", streaming=True)`.  
    2. Sample exactly 600 records (200 × Fe‑Cr, Ni‑Al, Cu‑Zn) with a fixed random seed.  
    3. Retry up to 3 times on transient failures; on permanent failure log `[DATA_UNAVAILABLE]` and raise.  
    4. Record SHA‑256 checksums for every downloaded file in `data/metadata.yaml`.  
  - **Verification**: `tests/unit/test_download_retry.py` must pass; `data/metadata.yaml` must contain the OQMD dataset ID, sampling rule, and checksums.

- [ ] **T003a** [US‑1] **Record Materials‑Project omission (waiver) in metadata**  
  - **File**: `data/metadata.yaml` (field `materials_project_status`).  
  - **Steps**: Add `materials_project_status: DATA_UNAVAILABLE` with a short explanatory note (“No open unauthenticated endpoint on the free runner; waiver documented in plan”).  
  - **Verification**: `tests/unit/test_download_retry.py` confirms the field exists and is either `RETRIEVED` or `DATA_UNAVAILABLE`.

- [ ] **T003b** [US‑1] **Record FR‑003 deviation (EAM‑generated energies) in metadata**  
  - **File**: `data/metadata.yaml` (field `fr_003_deviation`).  
  - **Steps**: Document that no public segregation‑energy database exists and that energies will be generated in‑house with validated EAM potentials.  
  - **Verification**: The field must be present and contain a non‑empty explanation; `tests/unit/test_metadata_fields.py` (if present) will check it.

- [ ] **T004** [US‑1] **Reconstruct bulk structures, build GB supercells, insert pre‑existing bulk impurity clusters, and filter zero‑impurity cases**  
  - **Files**: `code/gb_builder.py`, `data/processed/gb_structures/` (relaxed GB `.json`), `data/processed/gb_build_map.csv`.  
  - **Steps**:  
    1. For each OQMD record, reconstruct a bulk `pymatgen.Structure` from `formula`, `spacegroup`, and `volume_per_atom`.  
    2. Insert impurity atoms **as a bulk cluster** *before* grain‑boundary construction.  
    3. Generate a symmetric 90° tilt grain‑boundary supercell, relax with ASE using the validated EAM potential.  
    4. Exclude configurations with zero impurity atoms; log the count in `data/processed/preprocessing_report.json`.  
  - **Verification**: `tests/unit/test_gb_builder.py` checks that every output GB has ≥1 impurity, that the CSV correctly maps `bulk_id → gb_id → alloy_system`, and that the exclusion count is recorded.

- [ ] **T005** [US‑1] **Compute clustering descriptors on the *bulk* configuration (pre‑insertion) and generate VIF collinearity report**  
  - **Files**: `code/descriptors.py`, `data/processed/descriptors.csv`, `results/metrics.json` (collinearity block).  
  - **Steps**:  
    1. From each **bulk structure before impurity insertion**, compute three descriptors: RDF peak value, pair‑correlation statistic, Voronoi neighbor count.  
    2. Also compute `cluster_size` (mean nearest‑neighbor distance among impurity atoms) and `local_lattice_strain` (trace of the local strain tensor) for later use.  
    3. Calculate Variance Inflation Factors (VIF) for the three original descriptors; threshold = 10.  
    4. Emit a JSON collinearity report (`high_collinearity_detected`, `flagged_groups` with predictor list, max VIF, one‑sentence summary) and embed it under the `collinearity` block of `results/metrics.json`.  
    5. Write all descriptor values to `data/processed/descriptors.csv` with column names matching `contracts/dataset.schema.yaml`.  
  - **Verification**: `tests/unit/test_descriptors.py::test_vif_detection` must pass; the JSON report must conform to `contracts/output.schema.yaml`; every descriptor must be derived from the bulk (pre‑insertion) structure.

- [ ] **T006** [US‑2] **Generate EAM segregation‑energy labels and assemble the training dataset**  
  - **Files**: `code/simulate_energy.py`, `data/processed/energies.csv`, `data/processed/training_set.csv`, `data/processed/sample_size_justification.md`.  
  - **Steps**:  
    1. Run validated EAM potentials for Fe‑Cr, Ni‑Al, Cu‑Zn on each relaxed GB to obtain **leave‑one‑out** segregation energies.  
    2. Merge `descriptors.csv` with `energies.csv`; add covariates `atomic_radius` and `electronegativity` from standard elemental tables.  
    3. Assign a deterministic `split` column (`train` / `test`) ensuring ≥50 held‑out samples and ≥3 alloy systems in the test set.  
    4. Validate the final CSV against `contracts/dataset.schema.yaml`.  
    5. Document the final sample size, the ≥200‑sample floor, and the power‑analysis justification in `sample_size_justification.md`. Reference the FR‑003 deviation recorded in T003b.  
  - **Verification**: `tests/unit/test_training_set.py` validates schema compliance and split proportions; the markdown must contain the required numeric statements.

- [ ] **T007** [US‑2] **Perform power analysis (FR‑008) and linearity assessment (FR‑010)**  
  - **Files**: `code/power_analysis.py`, `results/metrics.json` (power_analysis and linearity_assessment blocks).  
  - **Steps**:  
    1. Using `statsmodels.stats.power.FTestPower`, compute required sample size for effect size f² = 0.15, α = 0.05, predictor count = 7 (the three descriptors + four covariates). Record `required_n`, `achieved_n`, `achieved_power`, `meets_requirement`.  
    2. Generate scatter plots of each descriptor vs. segregation energy and residual plots for a provisional OLS fit; store a boolean `appears_linear` and a textual `evidence` description.  
    3. Insert both results into `results/metrics.json`.  
  - **Verification**: `tests/unit/test_power_linearity.py` checks that `meets_requirement` is true and that `appears_linear` is a boolean; the JSON must validate against `contracts/output.schema.yaml`.

- [ ] **T008** [US‑2] **Train Linear Regression and RandomForest models with GroupKFold CV, evaluate held‑out set, and produce prediction intervals**  
  - **Files**: `code/train_model.py`, `results/metrics.json` (model_type, cross_validation, held_out_test blocks).  
  - **Steps**:  
    1. Use `GroupKFold` on `gb_id` (5‑fold, or LOOCV if N < 5) to train:  
       - a statsmodels OLS model (record coefficient p‑values),  
       - a scikit‑learn `RandomForestRegressor`.  
    2. Record per‑fold R², RMSE, and for the linear model also coefficient p‑values.  
    3. Evaluate on the held‑out test set (≥50 samples, ≥3 alloy systems); compute overall R², RMSE, per‑system R², and a permutation‑test p‑value (1 000 permutations) for the linear model.  
    4. Produce 95 % prediction intervals for every test prediction (OLS via `get_prediction()`, RF via quantile regression or bootstrapping) and set `ci95_available: true`.  
    5. Choose `model_type` in the JSON according to the linearity verdict (`LinearRegression` if `appears_linear` = true, otherwise `RandomForest`).  
  - **Verification**: `tests/integration/test_model_training.py` must pass; the JSON must validate against `contracts/output.schema.yaml`.

- [ ] **T009** [US‑3] **Conduct hypothesis testing with Bonferroni correction and write the report**  
  - **Files**: `code/report.py`, `results/hypothesis_report.json`.  
  - **Steps**:  
    1. Extract raw p‑values for all regression coefficients from the linear model.  
    2. If more than one hypothesis, apply **Bonferroni** correction (`p_adj = p_raw * n_hypotheses`, capped at 1.0).  
    3. Flag predictors whose significance status (α = 0.05) changes after correction; count them (`n_significance_changes`).  
    4. Write a JSON report conforming to `contracts/report.schema.yaml` with `correction_method: "bonferroni"`, `alpha: 0.05`, `n_hypotheses`, detailed predictor entries, and a free‑text `summary`.  
  - **Verification**: `tests/unit/test_hypothesis_report.py` validates schema compliance, confirms `correction_method: "bonferroni"`, and checks that `n_significance_changes` matches the computed changes.

- [ ] **T010** [US‑3] **Generate the cluster‑size vs. segregation‑energy figure with 95 % confidence bands**  
  - **Files**: `code/plots.py`, `results/cluster_size_vs_segregation.png`.  
  - **Steps**:  
    1. For each alloy system (≥3) plot `cluster_size` (x‑axis) vs. `segregation_energy_eV` (y‑axis) using the held‑out test data.  
    2. Overlay 95 % confidence intervals derived from the selected model’s prediction intervals.  
    3. Save as a high‑resolution PNG (`dpi=300`).  
  - **Verification**: `tests/unit/test_plots.py` checks that the PNG exists, has dimensions ≥ 800 × 600 px, and file size > 10 KB (ensuring it is not a placeholder).

- [ ] **T011** [US‑2] **Implement FR‑011 EAM‑vs‑DFT validation harness (graceful DATA_UNAVAILABLE handling)**  
  - **Files**: `code/validate_potential.py`, `results/metrics.json` (eam_validation block).  
  - **Steps**:  
    1. Inspect `data/metadata.yaml` for a `dft_benchmark_path`.  
    2. **If a benchmark with ≥30 samples is present**: load it, compute EAM energies for the same structures, calculate MAE, and record `status: "VALIDATED"`, `n_benchmark`, `mae_eV`, `threshold_eV: 0.1`, `note: ""`.  
    3. **If unavailable or too small**: record `status: "DATA_UNAVAILABLE"`, `n_benchmark: 0`, `mae_eV: null`, `threshold_eV: 0.1`, `note: "No open DFT benchmark dataset found on the runner."`.  
    4. Write the `eam_validation` block to `results/metrics.json` conforming to `contracts/output.schema.yaml`.  
    5. The script must **exit with code 0** regardless of data availability so that the integration test passes.  
  - **Verification**: `tests/unit/test_validate_potential.py` checks that the `eam_validation` block exists, conforms to schema, and that the script exits with status 0.

- [ ] **T012** **Run full end‑to‑end pipeline, execute integration tests, and record final metadata**  
  - **Files**: `code/main.py`, `results/metrics.json`, `results/hypothesis_report.json`, `data/metadata.yaml`, `results/performance_verification.json`.  
  - **Steps**:  
    1. Execute `python -m code.main` which orchestrates tasks T003–T011 in the correct order.  
    2. Run the complete pytest suite (`pytest -q`). All tests must pass.  
    3. After a successful run, append to `data/metadata.yaml` the final `random_seed`, execution `date`, `code_version_hash` (git commit hash), and `data_source` (OQMD loader identifier).  
    4. Write `results/performance_verification.json` reporting total wall‑clock time, CPU usage, and a flag `budget_exceeded: false` confirming the job stayed within the 6‑hour CPU‑only budget.  
  - **Verification**: CI runner must exit with code 0; the performance JSON must contain `budget_exceeded: false` and be validated by `tests/integration/test_artifact_verification.py`.

---

## Phase 2 – Complete the study and validate its evidence  

- [ ] **T013** **Cross‑system performance reporting**  
  - **File**: `results/metrics.json` (per_system_r2 block).  
  - **Steps**: Ensure that `per_system_r2` contains entries for at least three alloy systems, each with `alloy_system`, `n_samples`, and `r2`.  
  - **Verification**: `tests/unit/test_per_system_r2.py` validates presence and numeric sanity of the block.

- [ ] **T014** **Document preprocessing statistics and warnings**  
  - **File**: `results/metrics.json` (preprocessing block).  
  - **Steps**: Populate `n_zero_impurity_excluded`, `n_missing_energy_excluded`, and `missing_energy_rate`. Emit a warning if `missing_energy_rate > 0.05`.  
  - **Verification**: `tests/unit/test_preprocessing_stats.py` checks that the fields exist and that the warning logic is correctly reflected in the JSON.

- [ ] **T015** **Final methods & results handoff for paper pipeline**  
  - **Files**: `paper/methods.md`, `paper/results.md`.  
  - **Steps**: Summarize the exact computational workflow, dataset provenance, model selection rationale, statistical outcomes, and figure references, linking to the real artifact files (`results/*.json`, `results/*.png`).  
  - **Verification**: Manual reviewer check; no automated test required but the files must be present for downstream paper generation.

---

## Phase 3 – Reproducible results and paper handoff  

- [ ] **T016** **Re‑run documented workflow from scratch on a clean environment**  
  - **Steps**: Delete `data/processed/`, `results/`, and any generated caches; then execute `python -m code.main` again. Verify that the same outputs (hashes, JSON values, PNG) are reproduced within numerical tolerance.  
  - **Verification**: `tests/integration/test_reproducibility.py` compares hashes of key artifacts before and after the clean run.

- [ ] **T017** **Archive all provenance artifacts for external audit**  
  - **Files**: `archive/` (tarball containing `code/`, `data/`, `results/`, `spec.md`, `plan.md`, `tasks.md`).  
  - **Steps**: Create a reproducible archive `archive/project_snapshot.tar.gz` with deterministic ordering and timestamps.  
  - **Verification**: `tests/unit/test_archive_integrity.py` checks that the tarball contains all required files and that its SHA‑256 checksum matches the value recorded in `data/metadata.yaml`.

---

**Dependency map**

| Task | Depends on |
|------|------------|
| T001, T002 | – |
| T003, T003a, T003b | – |
| T004 | T003, T003a |
| T005 | T004 |
| T006 | T005, T003b |
| T007 | T006 |
| T008 | T007 |
| T009 | T008 |
| T010 | T008 |
| T011 | T006 |
| T012 | T003–T011 (all) |
| T013 | T008 |
| T014 | T004, T006 |
| T015 | T012, T009, T010 |
| T016 | T012 |
| T017 | T012, T016 |

All tasks are unchecked (`- [ ]`) to allow fresh execution and verification.
