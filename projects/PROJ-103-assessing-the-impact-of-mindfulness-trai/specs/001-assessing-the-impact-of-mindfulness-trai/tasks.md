# Tasks: Assessing the Impact of Mindfulness Training on Default Mode Network Activity  

**Inputs**: `spec.md`, `plan.md`, data‑model, contracts, and any existing code.  
**Goal**: Deliver a reproducible end‑to‑end analysis that answers the research question while satisfying every functional requirement (FR‑001 – FR‑011) and success criterion (SC‑001 – SC‑006).  

---  

## Phase 1 – Project scaffolding & configuration  

- [ ] **T001** [USx?] Create the canonical project layout and core configuration files.  
  *Paths*: `code/`, `data/raw/`, `data/processed/`, `data/results/`, `docs/`, `code/config/settings.py`, `code/utils/seeding.py`.  
  *Verification*:  
  – Directory tree exists and contains an `__init__.py` in each package.  
  – `settings.py` defines keys for `dataset_paths`, `preprocessing_params`, `atlas_choice`, `motion_thresholds`, and `statistical_thresholds` with type hints.  
  – `seeding.py` pins NumPy, Python `random`, and (if used) PyTorch seeds; a unit test confirms deterministic output on two runs of a trivial NumPy operation.  

---  

## Phase 2 – Data acquisition & design verification  

- [ ] **T002** [USx?] Discover, download, and validate OpenNeuro datasets that contain **pre‑ and post‑mindfulness** resting‑state scans.  
  *Paths*: `code/datasets/openneuro_client.py`, `code/datasets/download_datasets.py`, `code/utils/gap_logging.py`, `data/raw/{dataset_id}/`, `data/metadata/{dataset_id}_metadata.json`, `docs/gaps.md`.  
  *Verification*:  
  – `openneuro_client.list_datasets()` returns a list of candidate IDs.  
  – For each candidate, `download_datasets.py` fetches the BIDS archive, writes a SHA‑256 checksum file, and records download timestamp.  
  – `verify_design.py` (implemented in `code/datasets/verify_design.py`) checks that each dataset has paired pre/post scans and contains mindfulness‑intervention metadata; datasets failing the check are logged via `gap_logging.py` into `docs/gaps.md` with reason “design_missing”.  
  – If fewer than **three** qualified mindfulness datasets are found, a warning is emitted and the pipeline proceeds **only with the available mindfulness datasets** (no substitution with unrelated resting‑state data).  

- [ ] **T017** [USx?] Implement `code/datasets/metadata_schema.py` to define and enforce the JSON schema for dataset metadata (matching `dataset.schema.yaml`).  
  *Verification*:  
  – Unit test validates a sample metadata file against the schema.  

- [X] **T018** [USx?] Implement `code/datasets/verify_design.py` that uses the schema from T017 to verify pre/post design and mindfulness metadata.  
  *Verification*:  
  – Script returns a boolean `design_verified` flag and writes a concise verification report per dataset.  

---  

## Phase 3 – Preprocessing  

- [ ] **T003** [USx?] Run fMRIPrep in Docker on every subject that passed design verification, producing standardized outputs.  
  *Paths*: `code/preprocessing/fmriprep_runner.py`, `data/processed/fmriprep_outputs/{subject_id}/`, `data/processed/preproc_metadata.json`.  
  *Verification*:  
  – For each subject, fMRIPrep generates a preprocessed BOLD image in MNI152 space, motion parameters, confound regressors, and an HTML QC report.  
  – `preproc_metadata.json` records `preprocessing_status` (“success”/“failed”), `motion_exclusion_flag` (translation > 3 mm or rotation > 3°), and timestamps.  
  – A unit test parses a sample HTML report to confirm the presence of motion summary tables.  

- [ ] **T016** [USx?] Implement `code/preprocessing/qc_parser.py` to extract motion metrics and other QC flags from fMRIPrep HTML reports.  
  *Verification*:  
  – Parser outputs a JSON summary that matches expectations for a known test subject.  

---  

## Phase 4 – ROI extraction (DMN)  

- [ ] **T005** [USx?] Extract mean time‑series from the DMN nodes defined by the **AAL atlas** (PCC, mPFC, IPL, angular_gyrus) in MNI152 space.  
  *Paths*: `code/analysis/extract_dmn_timeseries.py`, `data/processed/roi_masks/aal_{node}.nii.gz`, `data/processed/timeseries/{subject_id}_{scan}_dmn.tsv`.  
  *Verification*:  
  – All four canonical DMN nodes have corresponding AAL mask files (`aal_PCC.nii.gz`, etc.).  
  – Each TSV contains the same number of time points as the preprocessed BOLD volume (verified by length column).  
  – A test confirms that a subject flagged for motion exclusion is omitted from the output directory.  

---  

## Phase 5 – Connectivity & effect‑size computation  

- [ ] **T006** [USx?] Compute Pearson correlation matrices for every subject‑scan, apply Fisher‑z transformation with AR(1) pre‑whitening, and store results adhering to `connectivity.schema.yaml`.  
  *Paths*: `code/analysis/compute_connectivity.py`, `data/results/connectivity/{subject_id}_{scan}_matrix.json`.  
  *Verification*:  
  – Each JSON file validates against the schema (fields: `subject_id`, `scan_type`, `node_pair`, `pearson_corr`, `fisher_z`, `time_series_length`, etc.).  
  – A unit test on a synthetic time‑series verifies that the AR(1) residual is computed and that Fisher‑z values lie within the expected range.  

- [ ] **T007** [USx?] Perform paired statistical testing (pre vs post) across subjects for every node‑pair, calculate Cohen’s d effect sizes, and obtain bootstrapped 95 % confidence intervals (10 000 iterations).  
  *Paths*: `code/analysis/paired_effects.py`, `data/results/effect_sizes.csv`.  
  *Verification*:  
  – CSV columns: `node_pair`, `cohen_d`, `ci_lower`, `ci_upper`, `p_value`.  
  – A test checks that the bootstrapped CI width shrinks with increasing sample size on a simulated dataset.  

- [ ] **T008** [USx?] Apply Network‑Based Statistic (NBS) correction (primary threshold *t* ≥ 3.1, component‑wise FWE α = 0.05) to the paired‑test results and annotate significance.  
  *Paths*: `code/analysis/nbs_correction.py`, `data/results/nbs_corrected.csv`.  
  *Verification*:  
  – `nbs_corrected.csv` includes `nbs_p_value` and `nbs_significant` columns for each connection.  
  – Running the script on a small benchmark dataset reproduces the reference NBS output (checked against a stored fixture).  

---  

## Phase 6 – Sensitivity & power analyses  

- [ ] **T009** [USx?] Conduct a motion‑threshold sensitivity analysis (2 mm, 3 mm, 4 mm) and document how exclusion rates and effect‑size estimates vary.  
  *Paths*: `code/analysis/motion_sensitivity.py`, `docs/motion_sensitivity_report.md`.  
  *Verification*:  
  – Report contains a table of exclusion counts per threshold and a plot of Cohen’s d versus threshold.  

- [ ] **T010** [USx?] Run a post‑hoc power analysis (statsmodels `TTestPower`) using the observed pooled effect size; also provide an a‑priori power calculation assuming Cohen’s d = 0.5.  
  *Paths*: `code/analysis/power_analysis.py`, `docs/power_analysis_report.md`.  
  *Verification*:  
  – Report states the achieved power (≥ 0.80 target) and the required sample size for the assumed effect size.  

---  

## Phase 7 – Cross‑dataset meta‑analysis (when possible)  

- [ ] **T011** [USx?] If ≥ 3 qualified mindfulness datasets are available, perform a random‑effects meta‑analysis of the node‑pair effect sizes using R `metafor`; otherwise produce a single‑dataset summary.  
  *Paths*: `code/analysis/metafor_wrapper.R`, `code/analysis/meta_analysis.py`, `data/results/meta_analysis_{node_pair}.csv`, `figures/forest_{node_pair}.png`.  
  *Verification*:  
  – For each node‑pair, the CSV contains `pooled_effect`, `pooled_ci_lower`, `pooled_ci_upper`, `i_squared`, `q_test_p`.  
  – Forest plots are generated and saved to `figures/`.  
  – When fewer than three datasets exist, the script writes a clear warning to the log and skips pooling.  

---  

## Phase 8 – Reporting & reproducibility  

- [ ] **T012** [USx?] Assemble the final methods / results manuscript sections, ensuring associational framing (no causal language) and transparent documentation of dataset gaps, motion exclusion rates, and power considerations.  
  *Paths*: `docs/final_report.md`, `figures/` (all generated plots), `data/results/summary_table.csv`.  
  *Verification*:  
  – A linter scans `final_report.md` for prohibited causal verbs (e.g., “causes”, “leads to”) and fails if any are found.  
  – All tables and figures referenced in the manuscript exist and match the underlying result files.  

- [ ] **T013** [USx?] Run the full end‑to‑end pipeline on a minimal test dataset (e.g., a single OpenNeuro subject) to produce a complete set of outputs (`connectivity`, `effect_sizes`, `nbs_corrected`, `meta_analysis` if applicable). Record the execution log and verify that every schema validation passes.  
  *Paths*: `scripts/run_full_pipeline.sh`, `logs/full_pipeline_test.log`.  
  *Verification*:  
  – The script exits with status 0.  
  – `log` contains timestamps for each stage and a final “pipeline completed successfully” message.  
  – All generated JSON/CSV files validate against their respective schemas.  

- [ ] **T014** [USx?] Implement a fabrication‑guard utility that scans all result files for synthetic‑data markers (`random.*`, `mock_`, `synthetic_`) and raises an error if any are found.  
  *Paths*: `code/utils/fabrication_guard.py`, `tests/unit/test_fabrication_guard.py`.  
  *Verification*:  
  – Unit test feeds a deliberately fabricated file and asserts that the guard raises `FabricationError`.  

- [ ] **T015** [USx?] Generate a reproducibility checklist report summarizing Docker image hash, random‑seed values, data‑checksum records, and software version pins.  
  *Paths*: `docs/reproducibility_checklist.md`.  
  *Verification*:  
  – The checklist includes SHA‑256 of the fMRIPrep Docker image, the exact `settings.py` version, and the `requirements.txt` hash.  

---  

## Phase 9 – Additional supporting tasks  

- [ ] **T019** [USx?] Create `code/utils/gap_logging.py` to provide a simple logger that appends dataset‑gap messages to `docs/gaps.md`.  
  *Verification*:  
  – Unit test confirms that calling `log_gap('ds001234', 'design_missing')` writes the correct line to `docs/gaps.md`.  

- [ ] **T044** [USx?] Add unit test suite `tests/unit/test_connectivity.py` to validate JSON output against `connectivity.schema.yaml` and check basic statistical sanity (e.g., correlation bounds).  
  *Verification*:  
  – Test runs with a small synthetic connectivity file and passes.  

---  

### Dependency ordering  

1. **T001** → foundational layout.  
2. **T002** → needs layout; uses `gap_logging.py` (T019).  
3. **T017**, **T018** → schema & design verification scripts (used by T002).  
4. **T003** → requires downloaded data (T002).  
5. **T016** → QC parser for fMRIPrep (used by T003).  
6. **T005** → needs successful preprocessing (T003).  
7. **T006** → needs ROI time‑series (T005).  
8. **T007**, **T008**, **T009**, **T010** → need connectivity matrices (T006).  
9. **T011** → needs effect‑size table (T008) and at least three qualified datasets (verified in T002).  
10. **T012** → aggregates all prior results.  
11. **T013** → validates the whole chain on a minimal dataset.  
12. **T014**, **T015** → run after any result files exist.  

---  

*All tasks are designed to run on the free‑tier CI (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h).  No GPU resources are required; every method is CPU‑tractable or falls back to a lightweight alternative where explicitly permitted.*  