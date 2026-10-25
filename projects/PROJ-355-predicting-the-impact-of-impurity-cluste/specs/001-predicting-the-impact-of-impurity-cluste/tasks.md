# Tasks: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, all contract schemas, and reviewer feedback.  
All paths are relative to the project root `projects/PROJ-355-predicting-the-impact-of-impurity-cluste/`.

---

## Phase 1 – Project scaffolding & first end‑to‑end run  

- [X] **T001** [P] **Create a strict `.gitignore`**  
  - **File**: `.gitignore`  
  - **Requirements**: Must contain **exactly** the three lines (in this order, no trailing spaces):  
    ```
    data/
    results/
    *.pyc
    __pycache__/
    ```  
  - **Verification**: `tests/unit/test_gitignore_strict.py` reads the file and asserts the exact line order and content.  

- [X] **T002** [P] **Write a strict `README.md`**  
  - **File**: `README.md`  
  - **Requirements**: Must contain the headings **exactly** as:  
    1. `# Project Title` – the project title from the spec.  
    2. `## Execution` – a one‑line command `python -m code.main`.  
    3. `## Data Provenance` – a paragraph citing the OQMD loader, documenting the Materials‑Project waiver, and stating that all raw data reside under `data/raw/`.  
    4. `## Research Question` – a concise restatement of the question from the spec.  
  - **Verification**: `tests/unit/test_readme_strict.py` checks for the four headings in order and the exact execution command string.  

- [ ] **T003** [US‑1] **Download bulk configuration records from OQMD with retry logic and record metadata**   <!-- FAILED-IN-EXECUTION: code/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download.py exit=1 -->
  - **Files**: `code/download.py`, `data/raw/oqmd_records/` (immutable JSON/CSV), `data/metadata.yaml`  
  - **Steps**:  
    1. Use `datasets.load_dataset("jablonkagroup/oqmd", name="raw_data", streaming=True)`.  
    2. Sample **exactly 600 records** (200 × Fe‑Cr, Ni‑Al, Cu‑Zn) using a fixed random seed (`seed=20231023`).  
    3. Implement up‑to‑3 retries on transient HTTP failures; on permanent failure log `[DATA_UNAVAILABLE]` and raise.  
    4. Record SHA‑256 checksums for every downloaded file, the sampling rule, and the Materials‑Project waiver (`materials_project_status: DATA_UNAVAILABLE`) in `data/metadata.yaml`.  
  - **Verification**: `tests/unit/test_download_retry.py` must pass; it checks the presence of the checksum map and the waiver field.  

- [ ] **T013** [US‑1] **Download bulk configuration records from Materials Project with retry logic and record metadata**   <!-- FAILED-IN-EXECUTION: code/download_mp.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_mp.py exit=1 -->
  - **Files**: `code/download_mp.py`, `data/raw/mp_records/` (immutable JSON/CSV), `data/metadata.yaml`  
  - **Steps**:  
    1. Use `pymatgen.ext.matproj.MPRester` (API key supplied via environment variable `MP_API_KEY`) to query the Materials Project for the same 600 compositions used for OQMD.  
    2. Implement up‑to‑3 retries on transient HTTP failures; on permanent failure log `[DATA_UNAVAILABLE]` and raise.  
    3. Record SHA‑256 checksums for every downloaded file and the source identifier (`materials_project_status: AVAILABLE`) in `data/metadata.yaml`.  
  - **Verification**: `tests/unit/test_download_mp.py` checks that the MP files exist, that checksums are recorded, and that the status field is `AVAILABLE`.  

- [ ] **T004** [US‑1] **Reconstruct bulk structures, build grain‑boundary supercells, insert impurity clusters at the interface, and filter zero‑impurity cases**  
  - **Files**: `code/gb_builder.py`, `data/processed/gb_structures/` (relaxed GB `.json`), `data/processed/gb_build_map.csv`, `data/processed/preprocessing_report.json`  
  - **Steps**:  
    1. For each OQMD (and MP) record, reconstruct a bulk `pymatgen.Structure` from `formula`, `spacegroup`, and `volume_per_atom`.  
    2. Generate a symmetric 90° tilt GB supercell.  
    3. Insert **a cluster of impurity atoms** at the identified grain‑boundary interface (using the interface mask).  
    4. Relax the GB with ASE using the validated EAM potential.  
    5. Exclude configurations with zero impurity atoms; log the count in `preprocessing_report.json`.  
  - **Verification**: `tests/unit/test_gb_builder.py` asserts that every GB JSON contains ≥1 impurity located in the interface region, that the CSV correctly maps `bulk_id → gb_id → alloy_system`, and that the exclusion count is recorded.  

- [ ] **T005** [US‑1] **Compute interface‑post‑insertion clustering descriptors and VIF collinearity report**  
  - **Files**: `code/descriptors_interface.py`, `data/processed/descriptors_interface.csv`, `results/metrics.json` (collinearity block)  
  - **Steps**:  
    1. Load each **relaxed GB supercell** (post‑impurity insertion) from T004.  
    2. Restrict analysis to atoms belonging to the **grain‑boundary interface region** (using the interface mask).  
    3. For each impurity species present, compute the three required descriptors **within this interface region**:  
       - RDF peak value  
       - Pair‑correlation statistic  
       - Voronoi neighbor count  
    4. Assemble a CSV with columns matching `contracts/dataset.schema.yaml` (`rdf_peak_value`, `pair_corr_value`, `voronoi_count`, plus identifiers).  
    5. Calculate **Variance Inflation Factors (VIF)** for the three raw descriptors; threshold = 10.  
    6. Emit a JSON collinearity report containing `vif_threshold`, `vif_scores`, `high_collinearity_detected`, and `flagged_groups` (predictor list, max VIF, one‑sentence summary). Embed this report under the `collinearity` block of `results/metrics.json`.  
  - **Verification**: `tests/unit/test_descriptors_interface.py::test_vif_detection` must pass; the JSON must validate against `contracts/output.schema.yaml`.  

- [ ] **T006** [US‑1] **Generate EAM segregation‑energy labels and assemble the final training dataset**  
  - **Files**: `code/simulate_energy.py`, `data/processed/energies.csv`, `data/processed/training_set.csv`, `data/processed/sample_size_justification.md`  
  - **Steps**:  
    1. Run validated EAM potentials for Fe‑Cr, Ni‑Al, Cu‑Zn on each relaxed GB from T004 to obtain **leave‑one‑out** segregation energies.  
    2. Merge `descriptors_interface.csv` (interface descriptors) with `energies.csv`; add covariates `atomic_radius`, `electronegativity`, `local_lattice_strain`, and `cluster_size` (computed from impurity positions in the GB).  
    3. Assign a deterministic `split` column (`train` / `test`) ensuring **≥50 held‑out samples** and **≥3 alloy systems** represented in the test set.  
    4. Validate the final CSV against `contracts/dataset.schema.yaml`.  
    5. Document in `sample_size_justification.md` the total sample count (≥200), the power‑analysis target, and the achieved power (≥0.80). Reference FR‑003 and FR‑008.  
  - **Verification**: `tests/unit/test_training_set.py` checks schema compliance, split proportions, and that the markdown contains the required numeric statements.  

- [ ] **T014** [US‑1] **Validate EAM‑derived segregation energies against a DFT benchmark set**  
  - **Files**: `code/validate_potential.py`, `results/metrics.json` (eam_validation block)  
  - **Steps**:  
    1. Load a curated DFT benchmark dataset of segregation energies (sourced from Materials Project entries that include DFT‑computed GB segregation energies).  
    2. Match benchmark entries to the corresponding GB configurations in the training set via `gb_id`.  
    3. Compute the **Mean Absolute Error (MAE)** between EAM predictions and DFT values.  
    4. Populate the `eam_validation` block of `results/metrics.json` with `status: VALIDATED`, `n_benchmark`, `mae_eV`, `threshold_eV: 0.1`, and a brief note.  
    5. If fewer than 30 benchmark samples are found, raise an explicit error so the pipeline fails (no waiver).  
  - **Verification**: `tests/unit/test_eam_validation.py` ensures MAE ≤ 0.1 eV and that the JSON conforms to `contracts/output.schema.yaml`.  

- [ ] **T007** [US‑2] **Perform power analysis (FR‑008) and linearity assessment (FR‑010)**  
  - **Files**: `code/power_analysis.py`, `results/metrics.json` (power_analysis and linearity_assessment blocks)  
  - **Steps**:  
    1. Use `statsmodels.stats.power.FTestPower` with effect size f² = 0.15, α = 0.05, predictor count = 7 (3 descriptors + 4 covariates) to compute `required_n`. Record `required_n`, `achieved_n` (from the training set), `achieved_power`, and `meets_requirement`.  
    2. Fit a provisional OLS model on the training data, generate scatter plots of each descriptor vs. segregation energy and residual plots.  
    3. Based on visual diagnostics, set `appears_linear` (boolean) and a concise `evidence` string describing the assessment.  
    4. Insert both results into `results/metrics.json`.  
  - **Verification**: `tests/unit/test_power_linearity.py` ensures `meets_requirement` is true, `appears_linear` is a boolean, and the JSON validates against `contracts/output.schema.yaml`.  

- [ ] **T008** [US‑2] **Train Linear Regression and RandomForest models with GroupKFold CV, evaluate held‑out set, and produce prediction intervals**  
  - **Files**: `code/train_model.py`, `results/metrics.json` (model_type, cross_validation, held_out_test blocks)  
  - **Steps**:  
    1. Use `GroupKFold` on `gb_id` (5‑fold, or LOOCV if N < 5).  
    2. Train a statsmodels OLS model (record coefficient p‑values) **if** `appears_linear` from T007 is true; otherwise train a scikit‑learn `RandomForestRegressor`.  
    3. Record per‑fold R², RMSE; for the linear model also record coefficient p‑values.  
    4. Evaluate on the held‑out test set (≥50 samples, ≥3 alloy systems) → compute overall R², RMSE, per‑system R², and a permutation‑test p‑value (1 000 permutations) for the linear model.  
    5. Generate 95 % prediction intervals for every test prediction (OLS via `get_prediction()`, RF via quantile regression/bootstrapping) and set `ci95_available: true`.  
    6. Populate `model_type` in the JSON as `"LinearRegression"` or `"RandomForest"` according to the linearity verdict.  
  - **Verification**: `tests/integration/test_model_training.py` must pass; the JSON must validate against `contracts/output.schema.yaml`.  

- [ ] **T009** [US‑3] **Conduct hypothesis testing with Bonferroni correction and write the JSON report**  
  - **Files**: `code/report.py`, `results/hypothesis_report.json`  
  - **Steps**:  
    1. Extract raw p‑values for all regression coefficients from the linear model (only generated if linear model is selected).  
    2. Apply **Bonferroni** correction (`p_adj = min(p_raw * n_hypotheses, 1.0)`).  
    3. For each predictor, flag whether significance (α = 0.05) changes after correction; count these changes as `n_significance_changes`.  
    4. Write a JSON report conforming to `contracts/report.schema.yaml` with `correction_method: "bonferroni"`, `alpha: 0.05`, `n_hypotheses`, detailed predictor entries, the change count, and a free‑text `summary`.  
  - **Verification**: `tests/unit/test_hypothesis_report.py` validates schema compliance, confirms the correction method, and checks that `n_significance_changes` matches the computed changes.  

- [ ] **T010** [US‑3] **Generate the cluster‑size vs. segregation‑energy figure with 95 % confidence bands**  
  - **Files**: `code/plots.py`, `results/cluster_size_vs_segregation.png`  
  - **Steps**:  
    1. For each alloy system (≥3) plot `cluster_size` (x) vs. `segregation_energy_eV` (y) using the held‑out test data.  
    2. Overlay 95 % confidence intervals derived from the selected model’s prediction intervals.  
    3. Save as a high‑resolution PNG (`dpi=300`, minimum dimensions 800 × 600 px, file size > 10 KB).  
  - **Verification**: `tests/unit/test_plots.py` checks existence, dimensions, and file size thresholds.  

- [ ] **T011** [S] **Run the full end‑to‑end pipeline, execute the full pytest suite, and record final metadata & performance verification**  
  - **Files**: `code/main.py`, `results/metrics.json`, `results/hypothesis_report.json`, `data/metadata.yaml`, `results/performance_verification.json`  
  - **Steps**:  
    1. Execute `python -m code.main` which orchestrates tasks T003–T010 in the correct order.  
    2. Run the complete pytest suite (`pytest -q`). All tests must pass.  
    3. After successful execution, append to `data/metadata.yaml` the final `random_seed`, execution `date`, `code_version_hash` (git commit hash), and `data_source` (OQMD loader identifier).  
    4. Write `results/performance_verification.json` reporting total wall‑clock time, CPU usage, and `budget_exceeded: false` (must stay within the 6‑hour CPU‑only budget).  
  - **Verification**: CI must exit with code 0; `tests/integration/test_artifact_verification.py` must succeed, confirming schema compliance and budget adherence.  

- [ ] **T012** [S] **Archive all provenance artifacts for external audit**  
  - **Files**: `archive/project_snapshot.tar.gz`, `data/metadata.yaml` (checksum entry)  
  - **Steps**:  
    1. Create a deterministic tarball containing `code/`, `data/`, `results/`, `spec.md`, `plan.md`, and `tasks.md` with fixed ordering and timestamps.  
    2. Compute its SHA‑256 checksum and record it under `archive_checksum` in `data/metadata.yaml`.  
  - **Verification**: `tests/unit/test_archive_integrity.py` checks that the tarball includes all required paths and that its checksum matches the recorded value.  

---  

### Dependency / Requirement Coverage Map  

| Spec / Success‑Criteria ID | Satisfying Task(s) |
|----------------------------|--------------------|
| **FR‑001** (OQMD & MP download) | T003, **T013** |
| **FR‑002** (Clustering descriptors) – now **interface‑post‑insertion** | **T005** |
| **FR‑003** (≥200 labeled configs) | T006 |
| **FR‑004a / FR‑004b** (Regression models) | T008 |
| **FR‑005** (Multiple‑comparison correction) | T009 |
| **FR‑007 / FR‑012** (VIF collinearity) | T005 |
| **FR‑008** (Power analysis) | T007 |
| **FR‑009** (Cluster‑size plot) | T010 |
| **FR‑010** (Linearity assessment) | T007 |
| **FR‑011** (EAM‑vs‑DFT validation) | **T014** |
| **FR‑012** (VIF report) | T005 |
| **SC‑001 – SC‑006** | T006, T007, T008, T009, T010, **T014** |
| **US‑1** | T003, T013, T004, T005, T006 |
| **US‑2** | T007, T008 |
| **US‑3** | T009, T010 |
| **T011** & **T012** orchestrate and archive all prior artifacts.  

---  

### Notes on Reviewer Feedback  

- Descriptor computation now occurs **after impurity insertion within the GB interface** (T005).  
- Materials Project data are now sourced (T013), satisfying Constitution Principle VI.  
- EAM‑vs‑DFT validation (T014) removes the previous waiver and provides the required MAE metric (SC‑006).  
- Parallel‑safe tags removed from T011 and T012 to avoid race conditions; T012 now explicitly depends on completion of T011.  
- All other tasks retain their original IDs and ordering, preserving downstream references.  

---  

*All tasks are unchecked (`[ ]`). Once implemented, each will be marked complete by the verifier after the associated test passes.*  