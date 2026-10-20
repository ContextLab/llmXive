# Tasks: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

**Inputs**: `spec.md`, `plan.md` (from `specs/001-the-impact-of-musical-training-on-functi/`), existing code and data‑model contracts, reviewer comments.

The following checklist implements the full research pipeline, from a reproducible synthetic run to real‑data execution and final results hand‑off. All tasks respect the memory ceiling (≤ 7 GB RAM), run on CPU‑only resources, and never fabricate data. Tasks are ordered to satisfy data‑flow dependencies.

---

## Phase 0 – Repair entry points and enable a reproducible synthetic run  

- [ ] T001 [US-1] Fix the four failing entry‑point scripts and document the runnable command in `specs/001-the-impact-of-musical-training-on-functi/quickstart.md`.  
  - **Files**: `code/main.py`, `code/data/run_synthetic_generator.py`, `code/data/real_ingest.py`, `code/run_quickstart_test.py`.  
  - **Requirements**:  
    - `code/main.py` must parse `--mode {synthetic,real}`, `--n-subjects`, `--seed`, and optional `--n-permutations`; `--help` displays all options.  
    - `code/data/run_synthetic_generator.py` must be executable as a script (`if __name__ == "__main__":`) and importable from the repository root.  
    - `code/data/real_ingest.py` must detect missing or inaccessible real datasets, print a clear “Data source unavailable” message, write a JSON status file (`data/logs/real_ingest_status.json`), and exit with status 0 – **no synthetic fallback**.  
    - `code/run_quickstart_test.py` must invoke `code/main.py --mode synthetic …`, verify that all expected output files exist, and assert that each JSON/CSV passes its schema (`*_schema.yaml`).  
  - **Verification**: Running each script individually returns the expected exit code (0 for success, 0 for the stub when no real data). `python code/run_quickstart_test.py` exits 0 and prints “Quickstart validation passed”.  

- [ ] T002 [US-1] Implement a synthetic verification cohort generator that produces a realistic but fully synthetic adolescent rs‑fMRI dataset.   <!-- FAILED-IN-EXECUTION: code/data/run_synthetic_generator.py exit=1 -->
  - **File**: `code/data/synthetic_generator.py` (invoked via `code/data/run_synthetic_generator.py`).  
  - **Behavior**:  
    - Generates `N=100` mock subjects (default) with balanced groups (≤ 75 per group) and the following attributes: `years_of_training` ~ Uniform(1, 10) for musicians, 0 for non‑musicians; `age` ~ N(15, 1); `sex` 50/50; `motion_score` ~ N(0.15, 0.05); `ses_score` ~ N(0, 1).  
    - Randomly injects 5 % missing `years_of_training` and 3 % corrupted NIfTI files (zero‑filled with an invalid header) to exercise exclusion logic.  
    - Writes mock NIfTI volumes (64³ Gaussian noise) under `data/raw/mock_nifti/<subject_id>.nii.gz`.  
    - Emits a subject table `data/processed/subjects.parquet` that conforms to `subject.schema.yaml`.  
    - Provides an optional flag `--inject-effect d=0.4` for later power‑simulation runs (no effect injected by default).  
  - **Verification**: `pytest code/tests/test_synthetic_generator.py` checks schema compliance, group balance, and that every musician has `years_of_training ≥ 1`.  

- [ ] T014 [US-1] Real‑data ingestion from the **ABCD Study** or **HCP‑Adolescents**.  
  - **File**: `code/data/real_ingest.py`.  
  - **Behavior**:  
    1. Reads environment variable `REAL_DATA_SOURCE` which must be set to either `ABCD` or `HCP`.  
    2. Uses the official data‑access SDKs (`abcd-data` for ABCD, `hcp` download utilities for HCP) to download resting‑state fMRI NIfTI files and the associated behavioral questionnaire containing musical‑training information.  
    3. Verifies download integrity via SHA‑256 checksums; aborts with a clear error if any file is missing or corrupted.  
    4. Parses the “Music Training” questionnaire to extract `years_of_training`; subjects with `years_of_training ≥ 1` are labeled `musician`, others `non_musician`.  
    5. Populates `data/processed/subjects.parquet` conforming to `subject.schema.yaml`.  
    6. Writes a detailed log to `data/logs/real_ingest.log` (download URLs, file counts, any missing columns).  
  - **Verification**: `pytest code/tests/test_real_ingest.py` ensures that when `REAL_DATA_SOURCE` is set, the script downloads ≥ 100 subjects, creates a valid subject table, and exits 0. If the variable is unset or the download fails, the script exits with a non‑zero code and a descriptive message.  

- [ ] T003 [US-1] Build the preprocessing pipeline that filters, matches, and audits the synthetic (or real) cohort.  
  - **File**: `code/data/preprocess.py`.  
  - **Steps**:  
    1. Load `subjects.parquet`.  
    2. Apply the strict **≥ 1 year** musician cutoff; treat subjects with exactly 0 years (even if they self‑report “some experience”) as non‑musicians.  
    3. Exclude subjects with missing `years_of_training` or corrupted NIfTI files (log counts).  
    4. Perform propensity‑score nearest‑neighbor matching (caliper = 0.2 SD) on age, sex, motion_score, and ses_score.  
    5. Compute standardized mean differences (SMD) for each covariate; if any SMD ≥ 0.1, residualize those covariates from the connectivity matrices downstream.  
    6. Halt with a clear error “Sample Size Insufficient” if either group contains < 50 subjects after matching.  
  - **Outputs**:  
    - `data/processed/subjects_cleaned.parquet` (matched, filtered).  
    - `data/logs/exclusion_report.txt`.  
    - `data/processed/matching_balance_report.csv` (SMD values).  
  - **Verification**: `pytest code/tests/test_preprocess.py` asserts ≥ 90 % of final subjects have valid labels, that the SMD report is generated, and that the script aborts correctly when a group falls below 50.  

- [ ] T004 [US-2] Compute per‑subject functional connectivity matrices and derive network‑level metrics.  
  - **Files**: `code/analysis/atlas.py`, `code/analysis/connectivity.py`, `code/analysis/network_metrics.py`.  
  - **Process**:  
    1. Load the Schaefer‑200 atlas (bundled CSV).  
    2. For each subject, extract ROI time‑courses from the NIfTI, compute Pearson correlation, apply Fisher‑r‑to‑z transformation, and store a symmetric matrix (`z_matrix`) in `data/processed/connectivity/<subject_id>.json` (validated against `connectivity.schema.yaml`).  
    3. Map ROIs to the three target networks (auditory, motor, executive) and compute mean intra‑network Fisher‑z connectivity; store as `data/processed/network_metrics/<subject_id>.json` (validated against `network_metric.schema.yaml`).  
  - **Verification**: `pytest code/tests/test_connectivity.py` checks matrix symmetry, zero diagonal, and that each network metric file contains exactly the three networks with correct ROI indices.  

- [ ] T005 [P] Implement strict memory‑usage enforcement for all pipeline stages.  
  - **File**: `code/utils/memory_monitor.py`.  
  - **Features**:  
    - Monitors peak RAM via `psutil`.  
    - If a step exceeds 7 GB, automatically switches to streaming mode (e.g., `datasets.load_dataset(..., streaming=True)`) or deterministic sub‑sampling (recorded in `data/logs/memory_subsampling.log`).  
    - If memory cannot be reduced, aborts with “Memory limit exceeded – pipeline stopped”.  
  - **Verification**: `pytest code/tests/test_memory_monitor.py` runs a synthetic 8 GB matrix workload and confirms that sub‑sampling is triggered and final peak RAM ≤ 7 GB.  

- [ ] T006 [US-2] Run the full synthetic pipeline and validate that every artifact is produced and schema‑compliant.  
  - **Command**: `python code/main.py --mode synthetic --n-subjects 100 --seed 42`.  
  - **Post‑run**: Execute `python code/run_quickstart_test.py`.  
  - **Verification**: The quickstart test must exit 0, and a summary log `data/logs/quickstart_success.txt` is written.  

- [ ] T007 [US-2] Perform edge‑wise between‑group comparisons and Network‑Based Statistic (NBS).  
  - **File**: `code/analysis/stats.py`.  
  - **Methods**:  
    - Welch’s t‑test for every edge within the auditory, motor, and executive networks (using residualized matrices if SMD ≥ 0.1).  
    - Benjamini‑Hochberg FDR correction (FR‑003).  
    - Compute Cohen’s d and bootstrap 95 % confidence intervals (FR‑007).  
    - Run permutation‑based NBS (1 000 permutations, primary thresholds t = 1.8, 2.0, 2.5) and output the largest connected component size and its FWER‑corrected p‑value (FR‑008, SC‑001).  
  - **Outputs**: `data/results/statistical_results.csv` (validated against `statistical_result.schema.yaml`) and `data/results/nbs_components.json` (validated against `network_component.schema.yaml`).  
  - **Verification**: `pytest code/tests/test_stats.py` confirms that t‑statistics match `scipy.stats.ttest_ind(..., equal_var=False)` to ≤ 1e‑6, that q‑values are monotonic, and that an NBS component file is written.  

- [ ] T008 [US-3] Correlate connectivity strength with years of musical training (musicians only) and run a sensitivity analysis on significance thresholds and on the musician definition (≥ 3 years).  
  - **Files**: `code/analysis/correlation.py`, `code/analysis/sensitivity.py`.  
  - **Correlation**:  
    - For each connection, compute Pearson (or Spearman if normality fails) correlation between `years_of_training` and the Fisher‑z edge weight across musicians.  
    - Apply BH‑FDR, report r, p, q, effect size (r‑derived d), and 95 % CI (FR‑004, SC‑002).  
  - **Sensitivity**:  
    - Sweep the significance threshold across {0.01, 0.05, 0.10} and record the count of significant connections (SC‑003).  
    - Additionally, re‑run the correlation using a stricter musician definition (≥ 3 years) to assess construct validity (addresses reviewer concern about low‑bar cutoff).  
  - **Outputs**: `data/results/correlation_results.csv`, `data/results/sensitivity_analysis.csv`.  
  - **Verification**: `pytest code/tests/test_correlation.py` checks that only musician rows are used, that runtime ≤ 5 min (asserted via a timer), and that the “low‑stability” flag is set when the 95 % CI includes zero at the 0.01 threshold. `pytest code/tests/test_sensitivity.py` validates the threshold‑sweep counts and the ≥ 3‑year re‑analysis.  

- [ ] T009 Validate statistical machinery on null data and estimate detection power.  
  - **Procedure**:  
    1. Run the synthetic generator with `--inject-effect` **disabled** (null cohort). Verify false‑positive rates for group tests, NBS, and correlations are at the nominal level (≈ 0.05).  
    2. Run the generator with `--inject-effect d=0.4` (medium effect) and repeat the full analysis to estimate empirical power (≥ 0.80 for d = 0.5, ≥ 0.70 for d = 0.3).  
  - **Outputs**: `data/results/validation_checks.csv` (false‑positive rates) and `data/results/power_simulation.csv` (detection rates per effect size).  
  - **Verification**: `pytest code/tests/test_validation.py` confirms that the null run yields ≤ 0.07 false‑positive proportion and that the power run reports the expected detection percentages.  

- [ ] T010 Record total runtime and peak memory usage for the entire pipeline.  
  - **Implementation**: Extend `code/utils/memory_monitor.py` to write a summary row to `data/results/verification_run_summary.csv` after the pipeline finishes (including wall‑clock time).  
  - **Verification**: `pytest code/tests/test_run_summary.py` checks that the CSV contains columns `stage`, `peak_ram_gb`, `elapsed_seconds` and that all RAM entries are ≤ 7 GB (SC‑004).  

- [ ] T011 Build the Single Source of Truth (SSoT) results file.  
  - **File**: `code/analysis/aggregate_results.py`.  
  - **Action**: Collate group‑comparison statistics, NBS component summary, correlation results, sensitivity tables, and runtime logs into `data/results/results_summary.csv` (FR‑010). Ensure one‑row‑per‑connection format with clear identifiers.  
  - **Verification**: `pytest code/tests/test_aggregate.py` reads the summary and cross‑checks that every entry matches the source CSV/JSON files.  

- [ ] T012 Generate primary figures for reporting.  
  - **Files**: `code/analysis/plot_connectivity.py`, `code/analysis/plot_nbs.py`.  
  - **Outputs**:  
    - `data/results/fig_connectivity_heatmap.png` – group‑mean Fisher‑z matrices side‑by‑side.  
    - `data/results/fig_nbs_component.png` – graph visualisation of the largest NBS component (edges coloured by effect size).  
  - **Verification**: `pytest code/tests/test_visuals.py` re‑creates each figure and asserts that the MD5 hash matches a stored reference (ensuring reproducibility).  

- [ ] T013 Write the methods/results manuscript draft and final hand‑off documentation.  
  - **Files**: `specs/001-the-impact-of-musical-training-on-functi/research.md`, `specs/001-the-impact-of-musical-training-on-functi/quickstart.md`.  
  - **Content**:  
    - Detailed description of each pipeline stage, including the repaired entry points, synthetic data generation, matching strategy, and statistical methods.  
    - Explicit note that the original “musical aptitude” variable is unavailable in the current datasets and therefore omitted (addressing reviewer dan‑rockmore).  
    - Discussion of the musician‑definition sensitivity analysis (≥ 1 year vs ≥ 3 years) per reviewer eric‑kandel.  
    - **Important**: The final manuscript must be based on real‑data results; synthetic runs are only for unit‑testing (addressing FR‑011 enforcement).  
    - Statement that FR‑001’s real‑data clause and FR‑011’s real‑data validation are fulfilled by the real‑data ingestion (T014) and validation (T015) tasks.  
    - Links to all primary artifacts (`results_summary.csv`, figures, logs) and the exact reproducible command (`python code/main.py --mode synthetic …` for testing, `python code/main.py --mode real …` for final analysis).  
  - **Verification**: `pytest code/tests/test_documentation.py` checks that the draft contains the required disclaimer, references all artifact paths, and that no placeholder tags (e.g., `[Reviewer: …]`) remain.  

- [ ] T015 Validate the full analysis pipeline on real data using permutation testing.  
  - **Files**: `code/main.py` (run with `--mode real`), `code/analysis/validation_real.py`.  
  - **Procedure**:  
    1. After successful `real_ingest.py` and preprocessing, run the entire analysis (connectivity, stats, correlation, NBS) on the real cohort.  
    2. Perform permutation testing (e.g., 1 000 label permutations) for the primary group comparison to assess family‑wise error.  
    3. Summarize permutation p‑value distribution and report empirical false‑positive rate in `data/results/real_validation.csv`.  
  - **Verification**: `pytest code/tests/test_validation_real.py` ensures that the permutation file is generated, contains ≥ 1 000 permutations, and that the empirical type‑I error is ≤ 0.07.  

- [ ] T016 Audit behavioral predictor schema for musical aptitude.  
  - **File**: `code/analysis/aptitude_audit.py`.  
  - **Behavior**: Checks the loaded behavioral questionnaire for a validated “musical aptitude” field. If absent, logs a clear warning in `data/logs/aptitude_audit.txt` and records that the analysis proceeds without this variable, satisfying Principle VII.  
  - **Verification**: `pytest code/tests/test_aptitude_audit.py` confirms that the audit runs without error and that the warning is present when the field is missing.  

## Dependency mapping (requirement → task)

| Requirement | Task(s) |
|-------------|---------|
| FR‑001 (real‑data clause) | T014 (real ingestion) |
| FR‑002 | T004 |
| FR‑003, FR‑007, FR‑008, SC‑001 | T007 |
| FR‑004, SC‑002 | T008 |
| FR‑005, SC‑003 | T008 (sensitivity) |
| FR‑006, SC‑004 | T005, T010 |
| FR‑009 | T003 (matching & residualization) |
| FR‑010 | T011 |
| FR‑011 (real‑data validation) | T015 |
| SC‑005 (≥ 90 % valid labels) | T003 |
| Reviewer‑raised musician‑definition concern | T008 (≥ 3 year sensitivity) |
| Reviewer‑raised missing “musical aptitude” | T016 (audit) |
| Reviewer‑raised data‑source mismatch | T014 updated to ABCD/HCP |

**Execution order**: T001 → T002 → T014 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T015 → T016.  

All tasks write only to project‑owned directories (`code/`, `data/`, `specs/…`). No task creates or modifies platform state files. This checklist satisfies the specification, addresses reviewer feedback, and provides a complete, reproducible end‑to‑end analysis pipeline.  