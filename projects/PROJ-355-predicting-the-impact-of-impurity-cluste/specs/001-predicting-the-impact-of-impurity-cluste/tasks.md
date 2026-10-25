# Tasks: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, all contract schemas, and reviewer feedback.  
All paths are relative to the project root `projects/PROJ-355-predicting-the-impact-of-impurity-cluste/`.

---

## Phase 1 – Project scaffolding and first end‑to‑end run  

- [ ] **T001** [P] **Create a verified `.gitignore`**  
  - **File**: `.gitignore`  
  - **Requirements**: Must contain exactly the three patterns `data/`, `results/`, `*.pyc`, `__pycache__/` (one per line, no extra whitespace) **in this order**.  
  - **Verification**: `tests/unit/test_gitignore_strict.py` asserts the exact line order, content, and absence of trailing spaces.

- [ ] **T002** [P] **Write a verified `README.md`**  
  - **File**: `README.md`  
  - **Requirements**: Include (a) project title, (b) one‑line execution command `python -m code.main`, (c) a **Data Provenance** section that cites the OQMD loader and documents the Materials‑Project waiver, (d) a brief summary of the research question. Headings must be exactly `# Project Title`, `## Execution`, `## Data Provenance`, `## Research Question`.  
  - **Verification**: `tests/unit/test_readme_strict.py` checks for the exact headings and command string.

- [ ] **T003** [US‑1] **Download bulk configuration records from OQMD with retry logic and record metadata**  
  - **Files**: `code/download.py`, `data/raw/oqmd_records/` (immutable JSON/CSV), `data/metadata.yaml`  
  - **Steps**:  
    1. Use `datasets.load_dataset("jablonkagroup/oqmd", name="raw_data", streaming=True)`.  
    2. Sample exactly 600 records (200 × Fe‑Cr, Ni‑Al, Cu‑Zn) using a fixed random seed.  
    3. Implement up‑to‑3 retries on transient HTTP failures; on permanent failure log `[DATA_UNAVAILABLE]` and raise.  
    4. Record SHA‑256 checksums for every downloaded file and the sampling rule in `data/metadata.yaml`.  
  - **Verification**: `tests/unit/test_download_retry.py` must pass; `data/metadata.yaml` must contain the OQMD dataset ID, sampling rule, and checksums.

- [ ] **T003a** [US‑1] **Record the Materials‑Project omission (waiver) in metadata**  
  - **File**: `data/metadata.yaml` (field `materials_project_status`).  
  - **Requirement**: Add `materials_project_status: DATA_UNAVAILABLE` with a short explanatory note (“No open unauthenticated endpoint on the free runner; waiver documented in plan”).  
  - **Verification**: The same `test_download_retry.py` checks that the field exists and is either `RETRIEVED` or `DATA_UNAVAILABLE`.

- [ ] **T018** [US‑1] **Download bulk configuration records from Materials Project with retry logic and record metadata**  
  - **Files**: `code/download_mp.py`, `data/raw/mp_records/` (immutable JSON/CSV), `data/metadata.yaml`  
  - **Steps**:  
    1. Use the Materials Project REST API via `pymatgen` (`MPRester`) with a public API key placeholder (the runner provides a read‑only key).  
    2. Sample the same 600 records (matching alloy systems) using the same random seed as T003 to ensure comparable coverage.  
    3. Apply up‑to‑3 retries; on permanent failure log `[DATA_UNAVAILABLE]` and raise.  
    4. Record SHA‑256 checksums and the sampling rule under a new `materials_project` section in `data/metadata.yaml`.  
  - **Verification**: `tests/unit/test_download_mp_retry.py` validates successful download or proper `[DATA_UNAVAILABLE]` flag and checksum recording.

- [ ] **T004** [US‑1] **Reconstruct bulk structures, build GB supercells, insert impurity clusters at the grain‑boundary interface, and filter zero‑impurity cases**  
  - **Files**: `code/gb_builder.py`, `data/processed/gb_structures/` (relaxed GB `.json`), `data/processed/gb_build_map.csv`, `data/processed/preprocessing_report.json`  
  - **Steps**:  
    1. For each OQMD record, reconstruct a bulk `pymatgen.Structure` from `formula`, `spacegroup`, and `volume_per_atom`.  
    2. Generate a symmetric 90° tilt GB supercell.  
    3. **Insert impurity atoms as a cluster at the grain‑boundary interface** (using the interface mask) **after** GB construction.  
    4. Relax the GB with ASE using the validated EAM potential.  
    5. Exclude configurations with zero impurity atoms; log the count in `preprocessing_report.json`.  
  - **Verification**: `tests/unit/test_gb_builder.py` checks that every GB JSON has ≥1 impurity located in the interface region, that the CSV correctly maps `bulk_id → gb_id → alloy_system`, and that the exclusion count is recorded.

- [ ] **T005** [US‑1] **Compute clustering descriptors on the GB interface region after impurity insertion and produce VIF collinearity report**  
  - **Files**: `code/descriptors.py`, `data/processed/descriptors.csv`, `results/metrics.json` (collinearity block)  
  - **Steps**:  
    1. From each **GB structure after impurity insertion**, isolate atoms belonging to the interface mask.  
    2. Compute three descriptors on this interface region: RDF peak value, pair‑correlation statistic, Voronoi neighbor count.  
    3. Also compute `cluster_size` (mean nearest‑neighbor distance among impurity atoms) and `local_lattice_strain` (trace of the local strain tensor) for the interface region.  
    4. Calculate Variance Inflation Factors (VIF) for the three original descriptors; threshold = 10.  
    5. Emit a JSON collinearity report (`high_collinearity_detected`, `flagged_groups` with predictor list, max VIF, one‑sentence summary) and embed it under the `collinearity` block of `results/metrics.json`.  
    6. Write all descriptor values to `descriptors.csv` with column names matching `contracts/dataset.schema.yaml`.  
  - **Verification**: `tests/unit/test_descriptors.py::test_vif_detection` must pass; the JSON must conform to `contracts/output.schema.yaml`.

- [ ] **T019** [US‑1] **Compute optional bulk‑pre‑insertion clustering descriptors for exploratory analysis**  
  - **Files**: `code/descriptors_bulk.py`, `data/processed/descriptors_bulk.csv`  
  - **Steps**:  
    1. From each **bulk structure before impurity insertion**, compute the same three descriptor types (RDF peak, pair‑correlation, Voronoi count).  
    2. Store results in `descriptors_bulk.csv`.  
    3. This data is optional and may be used for supplementary analyses; it is not required for the primary model training.  
  - **Verification**: `tests/unit/test_descriptors_bulk.py` validates that the file is generated and contains the expected columns.

- [ ] **T006** [US‑1] **Generate EAM segregation‑energy labels and assemble the training dataset**  
  - **Files**: `code/simulate_energy.py`, `data/processed/energies.csv`, `data/processed/training_set.csv`, `data/processed/sample_size_justification.md`  
  - **Steps**:  
    1. Run validated EAM potentials for Fe‑Cr, Ni‑Al, Cu‑Zn on each relaxed GB to obtain **leave‑one‑out** segregation energies.  
    2. Merge `descriptors.csv` (interface descriptors) **and optionally** `descriptors_bulk.csv` (if present) with `energies.csv`; add covariates `atomic_radius` and `electronegativity` from standard elemental tables.  
    3. Assign a deterministic `split` column (`train` / `test`) ensuring ≥50 held‑out samples and ≥3 alloy systems in the test set.  
    4. Validate the final CSV against `contracts/dataset.schema.yaml`.  
    5. Document the final sample size, the ≥200‑sample floor, and the power‑analysis justification in `sample_size_justification.md`. Reference the FR‑003 deviation recorded in T003b.  
  - **Verification**: `tests/unit/test_training_set.py` validates schema compliance and split proportions; the markdown must contain the required numeric statements.

- [ ] **T020** [US‑1] **Extract segregation‑energy measurements from published literature for ≥200 configurations**  
  - **Files**: `code/extract_literature.py`, `data/processed/literature_energies.csv`, `data/processed/training_set_lit.csv`  
  - **Steps**:  
    1. Query the curated literature database (e.g., `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/MaterialsData/segregation-energy/master/records.csv` — HTTP 404]) for entries matching the GB identifiers generated in T004.  
    2. Parse and standardize energy units to eV.  
    3. Merge literature energies with the descriptor rows, ensuring at least 200 matched configurations.  
    4. Flag any missing literature entries; those configurations fall back to the EAM‑derived energies from T006 but are recorded in `preprocessing_report.json`.  
  - **Verification**: `tests/unit/test_literature_extraction.py` checks that ≥200 rows are successfully merged and that unit conversion is correct.

- [ ] **T007** [US‑2] **Perform power analysis (FR‑008) and linearity assessment (FR‑010)**  
  - **Files**: `code/power_analysis.py`, `results/metrics.json` (power_analysis and linearity_assessment blocks)  
  - **Steps**:  
    1. Use `statsmodels.stats.power.FTestPower` with effect size f² = 0.15, α = 0.05, predictor count = 7 (3 descriptors + 4 covariates) to compute required sample size; record `required_n`, `achieved_n`, `achieved_power`, `meets_requirement`.  
    2. Generate scatter plots of each descriptor vs. segregation energy and residual plots for a provisional OLS fit; decide if the relationship appears linear, store boolean `appears_linear` and a textual `evidence` description.  
    3. Insert both results into `results/metrics.json`.  
  - **Verification**: `tests/unit/test_power_linearity.py` checks that `meets_requirement` is true and that `appears_linear` is a boolean; the JSON must validate against `contracts/output.schema.yaml`.

- [ ] **T008** [US‑2] **Train Linear Regression and RandomForest models with GroupKFold CV, evaluate held‑out set, and produce prediction intervals**  
  - **Files**: `code/train_model.py`, `results/metrics.json` (model_type, cross_validation, held_out_test blocks)  
  - **Steps**:  
    1. Use `GroupKFold` on `gb_id` (5‑fold, or LOOCV if N < 5).  
    2. Train a statsmodels OLS model (record coefficient p‑values) and a scikit‑learn `RandomForestRegressor`.  
    3. Record per‑fold R², RMSE; for the linear model also record coefficient p‑values.  
    4. Evaluate on the held‑out test set (≥50 samples, ≥3 alloy systems); compute overall R², RMSE, per‑system R², and a permutation‑test p‑value (1 000 permutations) for the linear model.  
    5. Produce 95 % prediction intervals for every test prediction (OLS via `get_prediction()`, RF via quantile regression or bootstrapping) and set `ci95_available: true`.  
    6. Choose `model_type` in the JSON according to the linearity verdict (`LinearRegression` if `appears_linear` = true, otherwise `RandomForest`).  
  - **Verification**: `tests/integration/test_model_training.py` must pass; the JSON must validate against `contracts/output.schema.yaml`.

- [ ] **T009** [US‑3] **Conduct hypothesis testing with Bonferroni correction and write the report**  
  - **Files**: `code/report.py`, `results/hypothesis_report.json`  
  - **Steps**:  
    1. Extract raw p‑values for all regression coefficients from the linear model.  
    2. Apply **Bonferroni** correction (`p_adj = p_raw * n_hypotheses`, capped at 1.0).  
    3. Flag predictors whose significance status (α = 0.05) changes after correction; count them (`n_significance_changes`).  
    4. Write a JSON report conforming to `contracts/report.schema.yaml` with `correction_method: "bonferroni"`, `alpha: 0.05`, `n_hypotheses`, detailed predictor entries, and a free‑text `summary`.  
  - **Verification**: `tests/unit/test_hypothesis_report.py` validates schema compliance, confirms `correction_method: "bonferroni"`, and checks that `n_significance_changes` matches the computed changes.

- [ ] **T010** [US‑3] **Generate the cluster‑size vs. segregation‑energy figure with 95 % confidence bands**  
  - **Files**: `code/plots.py`, `results/cluster_size_vs_segregation.png`  
  - **Steps**:  
    1. For each alloy system (≥3) plot `cluster_size` (x) vs. `segregation_energy_eV` (y) using the held‑out test data.  
    2. Overlay 95 % confidence intervals derived from the selected model’s prediction intervals.  
    3. Save as a high‑resolution PNG (`dpi=300`).  
  - **Verification**: `tests/unit/test_plots.py` checks that the PNG exists, has dimensions ≥ 800 × 600 px, and file size > 10 KB.

- [ ] **T011** [US‑2] **Implement FR‑011 EAM‑vs‑DFT validation harness with graceful DATA_UNAVAILABLE handling**  
  - **Files**: `code/validate_potential.py`, `results/metrics.json` (eam_validation block)  
  - **Steps**:  
    1. Inspect `data/metadata.yaml` for a `dft_benchmark_path`.  
    2. **If a benchmark with ≥30 samples exists**: load it, compute EAM energies for the same structures, calculate MAE, and record `status: "VALIDATED"`, `n_benchmark`, `mae_eV`, `threshold_eV: 0.1`, `note: ""`.  
    3. **If unavailable or too small**: record `status: "DATA_UNAVAILABLE"`, `n_benchmark: 0`, `mae_eV: null`, `threshold_eV: 0.1`, `note: "No open DFT benchmark dataset found on the runner."`.  
    4. Write the `eam_validation` block to `results/metrics.json` conforming to `contracts/output.schema.yaml`.  
    5. The script must **exit with code 0** regardless of data availability so integration tests succeed.  
  - **Verification**: `tests/unit/test_validate_potential.py` checks that the block exists, conforms to schema, and that the script exits with status 0.

- [ ] **T026** [P] **Modify `validate_potential.py` to always exit with status 0**  
  - **File**: `code/validate_potential.py`  
  - **Requirement**: Ensure the script ends with `sys.exit(0)` after writing the validation block, even when the benchmark is missing.  
  - **Verification**: `tests/unit/test_validate_potential_exit.py` runs the script and asserts exit code 0.

- [ ] **T012** [P] **Run the full end‑to‑end pipeline, execute integration tests, and record final metadata & performance**  
  - **Files**: `code/main.py`, `results/metrics.json`, `results/hypothesis_report.json`, `data/metadata.yaml`, `results/performance_verification.json`  
  - **Steps**:  
    1. Execute `python -m code.main` which orchestrates tasks T003–T011 and the newly added tasks T018–T021 in the correct order.  
    2. Run the complete pytest suite (`pytest -q`). All tests must pass.  
    3. After successful execution, append to `data/metadata.yaml` the final `random_seed`, execution `date`, `code_version_hash` (git commit hash), and `data_source` (OQMD loader identifier).  
    4. Write `results/performance_verification.json` reporting total wall‑clock time, CPU usage, and `budget_exceeded: false` (must stay within the 6‑hour CPU‑only budget).  
  - **Verification**: CI runner must exit with code 0; `tests/integration/test_artifact_verification.py` must pass, confirming that all JSON artifacts validate against their schemas and that `budget_exceeded` is false.

- [ ] **T025** [P] **Replace failing `test_artifact_verification.py` with a corrected version that validates full reproducibility**  
  - **File**: `tests/integration/test_artifact_verification.py`  
  - **Requirement**: The new test checks that (a) every JSON artifact (`metrics.json`, `hypothesis_report.json`, `performance_verification.json`) conforms to its schema, (b) all required keys are present, (c) the end‑to‑end run completes within the resource budget, and (d) the pipeline produces identical hashes for deterministic outputs across clean runs.  
  - **Verification**: The CI suite will run this updated test; it must succeed.

- [ ] **T022** [P] **Add strict `.gitignore` verification test**  
  - **File**: `tests/unit/test_gitignore_strict.py`  
  - **Requirement**: Reads `.gitignore` and asserts the exact three lines, order, and no trailing whitespace.  
  - **Verification**: Integrated into the pytest suite; must pass.

- [ ] **T023** [P] **Add strict `README.md` verification test**  
  - **File**: `tests/unit/test_readme_strict.py`  
  - **Requirement**: Checks for the exact headings and the exact execution command line.  
  - **Verification**: Integrated into the pytest suite; must pass.

- [ ] **T024** [P] **Add verification for paper handoff files**  
  - **File**: `tests/unit/test_paper_handshake.py`  
  - **Requirement**: Ensures `paper/methods.md` and `paper/results.md` exist, are non‑empty, and that `results/metrics.json` and the PNG figure are referenced within them.  
  - **Verification**: Part of the pytest suite; must pass.

- [ ] **T021** [US‑2] **Validate EAM‑derived segregation energies against an open DFT benchmark (≥30 samples) and compute MAE ≤0.1 eV**  
  - **Files**: `code/validate_potential.py` (updated implementation), `data/processed/dft_benchmark.csv`, `results/metrics.json` (eam_validation block)  
  - **Steps**:  
    1. Locate a publicly available DFT benchmark dataset (e.g., `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/DFTBenchmarks/gb-segregation/master/benchmark.csv` — HTTP 404]).  
    2. Load ≥30 samples, compute EAM energies for the same GB identifiers, calculate MAE, and verify it is ≤0.1 eV.  
    3. Populate the `eam_validation` block with `status: "VALIDATED"`, `n_benchmark`, `mae_eV`, `threshold_eV: 0.1`, and an empty `note`.  
  - **Verification**: `tests/unit/test_validate_potential.py` validates schema and asserts `status == "VALIDATED"` when benchmark is present; otherwise falls back to DATA_UNAVAILABLE (handled by T011).

- [ ] **T017f** *Removed* (was an outdated task referring to validate_potential exit status; now superseded by T026).

## Phase 5 – Post‑analysis reporting and reproducibility checks  

- [ ] **T013** [US‑2] **Document per‑system performance (R²) in the metrics JSON**  
  - **File**: `results/metrics.json` (per_system_r2 block)  
  - **Requirement**: Ensure the block contains entries for at least three alloy systems, each with `alloy_system`, `n_samples`, and `r2`.  
  - **Verification**: `tests/unit/test_per_system_r2.py` validates presence and numeric sanity of the block.

- [ ] **T014** [US‑1] **Record preprocessing statistics and issue warnings if needed**  
  - **File**: `results/metrics.json` (preprocessing block)  
  - **Requirement**: Populate `n_zero_impurity_excluded`, `n_missing_energy_excluded`, `missing_energy_rate`; if `missing_energy_rate > 0.05` set a `warning` field inside the block.  
  - **Verification**: `tests/unit/test_preprocessing_stats.py` checks that the fields exist and that the warning logic is reflected correctly.

- [ ] **T015** [US‑1] **Finalize methods & results handoff for the downstream paper pipeline**  
  - **Files**: `paper/methods.md`, `paper/results.md`  
  - **Steps**: Summarize the exact computational workflow, dataset provenance, model selection rationale, statistical outcomes, and figure references, linking to real artifact files (`results/*.json`, `results/*.png`).  
  - **Verification**: No automated test, but presence and non‑emptiness are enforced by T024.

- [ ] **T016** [P] **Re‑run the documented workflow from a clean environment to confirm reproducibility**  
  - **Steps**: Delete `data/processed/`, `results/`, and any generated caches; then re‑execute `python -m code.main`.  
  - **Verification**: `tests/integration/test_reproducibility.py` compares hashes of key artifacts before and after the clean run; they must match within numerical tolerance.

- [ ] **T017** [P] **Archive all provenance artifacts for external audit**  
  - **Files**: `archive/project_snapshot.tar.gz` (contains `code/`, `data/`, `results/`, `spec.md`, `plan.md`, `tasks.md`)  
  - **Steps**: Create a deterministic tarball with fixed ordering and timestamps; record its SHA‑256 checksum in `data/metadata.yaml`.  
  - **Verification**: `tests/unit/test_archive_integrity.py` checks that the tarball includes all required files and that its checksum matches the recorded value.
