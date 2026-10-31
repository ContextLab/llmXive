# Tasks: Investigating the Relationship Between Brain Network Dynamics and Creative Problem Solving

**Input**: Design documents from `/specs/518-brain-dynamics-creativity/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY where defined by spec acceptance criteria.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- Paths are relative to the project directory (`projects/PROJ-518-investigating-the-relationship-between-b/`). Source lives in `code/`, tests in `code/tests/`, results in `data/interim/` and `docs/outputs/`.

## Completed work (preserved — verified by prior review receipts)

- [X] T002 Pinned dependencies in `requirements.txt` (nilearn, networkx, scikit-learn, numpy, pandas, matplotlib, scipy, brainconn, statsmodels).
- [X] T005 `code/config.py` with `WINDOW_SIZES = [20,30,40]`, `STEP = 5`, `FWE_METHOD`, and `validate_fwe_config()`.
- [X] T006 `code/utils/logging.py` `log_exclusion(reason, subject_id)` writing CSV rows to `data_exclusion_log.txt` with standardized reason codes (`MISSING_SCAN`, `MISSING_SCORE`, `HIGH_MOTION`).

**Note (T007 correction, retained)**: The earlier `code/utils/versioning.py` task that wrote artifact hashes into `state/projects/...yaml` has been removed; hashing now only updates `data/checksums.json`. No task may write to `state/` — platform state is owned by the platform.

## Phase 1: Setup and first end-to‑to‑end analysis on real data

- [~] T101 US4 **Implement CAQ availability validation with a single, shared error class.**
  *Description*: In `code/data/loader.py`, implement `validate_caq_availability(behavioral_json)` that parses the HCP behavioral metadata for the CAQ field. Define the error class ONCE in `code/errors.py` (`DataMissingCreativityError`) and import it in both `loader.py` and `code/main.py::run_validation()`. When CAQ is missing or null for all participants, raise `DataMissingCreativityError("DATA_MISSING_CREATIVITY")` and have `run_validation()` catch it, log the missing field name, and call `sys.exit(1)`. When CAQ is present, proceed without error.
  *Deliverables*: `code/errors.py`, updated `code/data/loader.py`, updated `code/main.py`.
  *Verification*: `pytest code/tests/contract/test_loader.py` — tests import `DataMissingCreativityError` from `code.errors` and assert both the pass‑through case (valid JSON with CAQ) and the halt case (missing CAQ → exit code 1, error code `DATA_MISSING_CREATIVITY` logged). Satisfies FR‑011 / US‑4.

- [ ] T102 US1 **Fetch real HCP resting‑state fMRI and behavioral data from OpenNeuro.** <!-- FAILED-IN-EXECUTION: code/data/run_fetch.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/run_fetch.py exit=1 -->
  *Description*: Implement `fetch_hcp_data(subject_id)` in `code/data/loader.py` that downloads each subject's resting‑state fMRI (CIFTI) and behavioral JSON from the canonical HCP S1200 OpenNeuro mirror (`https://openneuro.org/datasets/ds003189`). Write raw files to `data/raw/hcp_{subject_id}/`. The loader MUST fail loudly: if the real fetch fails, raise — NO synthetic fallback. Record SHA‑256 checksums of all raw files in `data/checksums.json`. Additionally, generate a manifest file `data/raw/manifest.json` listing all downloaded subject IDs. Define the sampled subject list via a constant `SAMPLE_SUBJECT_IDS` in `code/config.py` (e.g., first 1000 IDs from the manifest or a fixed‑seed random sample). 
  *Deliverables*: populated `data/raw/hcp_{subject_id}/`, `data/checksums.json`, `data/raw/manifest.json`, and `code/config.py` constant.
  *Verification*: `pytest code/tests/unit/test_loader_fetch.py` asserting downloaded files exist, are non‑empty, match recorded checksums, and that a fetch failure raises an exception. Satisfies FR‑009 provenance and Constitution VI.

- [ ] T103 US1 **Implement subject filtering with standardized exclusion logging.**
  *Description*: Implement `filter_subjects(manifest, behavioral)` in `code/data/loader.py` that (a) skips subjects whose resting‑state scan is unavailable (`MISSING_SCAN`), (b) excludes subjects with missing behavioral/creativity scores (`MISSING_SCORE`), and (c) flags and omits subjects with mean framewise displacement > 0.5 mm in > 20 % of volumes (`HIGH_MOTION`). All decisions are written via `log_exclusion` to `data/interim/data_exclusion_log.txt`. Output the included‑subject table to `data/interim/included_subjects.csv` with columns `subject_id, age, sex, education, creativity_score, rest_fmri_path`. Relies on the manifest produced by T102.
  *Verification*: `pytest code/tests/unit/test_filter_subjects.py` with fixtures covering all three edge cases, asserting correct exclusion codes and that the run does not abort on a missing scan. Satisfies FR‑009 and all three spec edge cases.

- [ ] T104 US1 **Repair and run fMRI preprocessing.** <!-- FAILED-IN-EXECUTION: code/data/run_preprocess.py exit=-1 (TIMEOUT) --> <!-- FAILED-IN-EXECUTION: code/data/run_preprocess.py exit=1 -->
  *Description*: Fix the failing `code/data/run_preprocess.py` (previous exit=1). `preprocess_fmri` in `code/data/preprocess.py` performs motion correction, spatial normalization, and band‑pass filtering 0.01–0.1 Hz, writing output to `data/processed/fmri_clean/{subject_id}.nii.gz` (canonical path per data‑model; rename any legacy `data/processed/{subject_id}_preprocessed.nii.gz` outputs and update downstream references). Process subjects one at a time with memory‑mapped arrays to stay under 7 GB RAM.
  *Deliverables*: `data/processed/fmri_clean/{subject_id}.nii.gz` for every included subject.
  *Verification*: `python code/data/run_preprocess.py` exits 0; `pytest code/tests/unit/test_preprocess.py` asserting each output file exists, is loadable via `nilearn`, and has the expected affine/shape. Satisfies FR‑001.

- [ ] T105 US1 **Compute sliding‑window connectivity, static strength, and flexibility with consensus clustering.**
  *Description*: In `code/analysis/connectivity.py`, compute sliding‑window functional connectivity (window 30 s default, step 5 s) and per‑participant `static_connectivity_strength` (mean |r| of the full‑window static matrix, FR‑012). In `code/analysis/dynamics.py`, apply Louvain community detection **with consensus clustering** (using the `brainconn` library) per window, build the module‑allegiance matrix, compute whole‑brain flexibility (proportion of community changes per ROI, averaged), and implement the phase‑randomized null model producing `null_flexibility_mean` and `excess_flexibility = observed − null`. Write one row per subject to `data/interim/flexibility_metrics.csv` with all fields required by `contracts/flexibility_metric.schema.yaml`.
  *Verification*: `pytest code/tests/unit/test_flexibility_schema.py` validating each row against the schema; unit tests `test_calculate_flexibility_averages` (hand‑computable toy connectivity matrices) and seed‑reproducibility of the null model. Satisfies FR‑002, FR‑003, FR‑004, FR‑012.

- [ ] T106 US1 **Fit the OLS regression using network_flexibility as predictor and produce the primary result.**
  *Description*: In `code/analysis/statistics.py`, fit `creativity_score ~ network_flexibility + age + sex + education + static_connectivity_strength` (FR‑005, predictor now matches the spec). Compute the Pearson r and two‑tailed p‑value between `network_flexibility` and creativity, ΔR² (full − static‑only baseline) formatted to ≥ 4 decimal places, and 95 % CIs for the flexibility coefficient. Write `data/interim/results.csv` **exactly matching** `contracts/regression_result.schema.yaml` (columns: `model_id, coefficient_flexibility, p_value_flexibility, r_squared, delta_r_squared, permutation_p_value, ci_lower, ci_upper, window_length, n_samples`). The `coefficient_flexibility` field stores the beta for `network_flexibility`. 
  *Verification*: `pytest code/tests/unit/test_fit_regression_coefficients.py` (synthetic design matrix with known solution) and `pytest code/tests/integration/test_regression_summary.py` validating the CSV against the YAML contract and checking 4‑decimal ΔR² precision. Satisfies FR‑005, SC‑001, SC‑003.

- [ ] T107 US3 **Run the permutation test and fill the empirical p‑value.**
  *Description*: Implement the vectorized permutation test in `code/analysis/statistics.py`: 10 000 shuffles of the creativity‑score vector (seed 42) preserving the `network_flexibility` vector, returning the two‑tailed empirical p‑value. Apply the family‑wise error correction (max‑T or Bonferroni) **to the ROI‑wise correlations computed by T118**. Write `data/interim/permutation_results.csv` (single row: `empirical_p_value`) and back‑fill `permutation_p_value` into `data/interim/results.csv`.
  *Verification*: `pytest code/tests/unit/test_permutation.py::test_empirical_p_value_present` and `test_permutation_seed_reproducibility` (two runs with seed 42 give identical p‑values). Satisfies FR‑006, FR‑007.

- [ ] T108 US3 **Run the window‑length sensitivity sweep.**
  *Description*: Re‑run connectivity + flexibility + correlation for window lengths {20, 30, 40} s (step 5 s), reusing the per‑window recomputation in `code/analysis/connectivity.py`. This task **must run after T107** because it requires the permutation p‑values to be populated. Write `data/interim/sensitivity_summary.csv` with columns `window_length, correlation_coefficient, p_value, permutation_p_value, n_samples` — one row per window length, all values non‑null.
  *Verification*: `pytest code/tests/unit/test_analysis.py::test_sensitivity_csv_schema` asserting three rows (20/30/40) with non‑null numeric values, validated against `contracts/sensitivity_summary.schema.yaml`. Satisfies FR‑010, SC‑002, SC‑005.

- [ ] T109 US2 **Generate all diagnostic visualisations.**
  *Description*: In `code/viz/plots.py`: (a) `plot_flexibility_vs_creativity` — scatter with regression line and 95 % confidence band, saved as `docs/outputs/flexibility_vs_creativity.png`; (b) `plot_residuals` — residuals‑vs‑fitted plot saved as `docs/outputs/model_residuals.png`; (c) QQ‑plot saved as `docs/outputs/model_qq.png`. All PNGs must be ≤ 5 MB (compress and raise `RuntimeError` on failure).
  *Verification*: `pytest code/tests/unit/test_plots.py` asserting all three files exist, are non‑empty PNGs, and are ≤ 5 MB, executed after the T106 model fit. Satisfies FR‑008, SC‑004.

- [ ] T110 **Run the full pipeline end‑to‑end and verify reproducibility.**
  *Description*: Execute `python code/main.py` from validation through visualisation in one run. Then, in a fresh virtualenv with `requirements.txt` installed, re‑run the documented quickstart workflow and record the log to `docs/outputs/quickstart_run_log.txt`. Compute SHA‑256 checksums of **all raw data files** (as listed in `data/raw/manifest.json`) and of **derived CSV artifacts** (`data/interim/*.csv`) and assert they match entries in `data/checksums.json` using the script `code/utils/verify_checksums.py`. Also run a memory/profile run on a 10‑subject subset, write `docs/outputs/profiling_report.txt` containing measured memory usage (< 7 GB) and per‑subject mean runtime; extrapolate full‑run runtime by `mean_runtime_per_subject × target_N` and assert the projection is < 6 h. 
  *Verification*: `pytest code/tests/integration/` passes; checksum assertion script exits 0; profiling report present with measured values and documented projection method. Satisfies the plan's performance goals and Constitution I/III.

- [ ] T111 [P] **Code quality and dependency checks.**
  *Description*: Run `black` on all `code/` files; ensure `flake8 code/` exits 0; run a dependency security audit on `requirements.txt` and record results in `docs/outputs/dependency_audit.txt`.
  *Verification*: `flake8 code/` exit code 0; audit report file exists and is non‑empty.
  *Dependency*: **depends_on: T107, T108, T109** (run after all new code is final).

## Phase 2: Results handoff

- [ ] T112 **Document artifacts and write the results handoff for the paper stage.**
  *Description*: Update `README.md` with a table of every generated artifact (path, columns, units, FR/SC satisfied). Populate `specs/518-brain-dynamics-creativity/research.md` with a concise methods/results account programmatically linked to the actual CSV and PNG artifacts — report the real measured r, p‑values, ΔR², and sensitivity table, describing negative findings and limitations honestly (including the construct‑validity caveat that CAQ measures creative achievement, not divergent thinking, and the post‑hoc power analysis). Document the paper‑stage handoff: paper layout, PDF compilation, and publication requirements live in the subsequent paper pipeline and are not duplicated here.
  *Verification*: Every artifact path referenced in `research.md` exists on disk; no hand‑typed statistics (all values traceable to `data/interim/*.csv`). 

- [ ] T113 **Update the data‑model to reflect canonical artifact locations and checksum scope.**
  *Description*: Edit `specs/518-brain-dynamics-creativity/data-model.md` so the file table lists `data/processed/fmri_clean/{id}.nii.gz` and `data/interim/results.csv` as canonical outputs, and clarify that `data/checksums.json` now records checksums for both raw files and derived CSV artifacts. Remove the obsolete statement about `code/utils/versioning.py` updating `state/projects/...yaml`. 
  *Verification*: File‑table paths match the outputs present in `data/` after T110; checksum scope description aligns with T122.

## New supplemental tasks (addressing uncovered concerns)

- [ ] T114 **Update data‑model versioning constraint.**
  *Description*: Edit `specs/518-brain-dynamics-creativity/data-model.md` to remove the stale clause that `code/utils/versioning.py` updates `state/projects/...yaml`. Replace it with a note that artifact hashes are recorded only in `data/checksums.json`. 
  *Verification*: The data‑model no longer mentions writes to `state/`; consistency check against tasks passes.

- [ ] T115 **Implement consensus clustering in dynamics step.**
  *Description*: In `code/analysis/dynamics.py`, integrate `brainconn` consensus clustering to obtain stable community assignments across sliding windows before computing flexibility. Ensure the algorithm uses the default resolution γ = 1.0 and is deterministic given a fixed random seed. 
  *Verification*: `pytest code/tests/unit/test_consensus_clustering.py` validates that consensus clusters are reproducible and that flexibility values differ from plain Louvain as expected.

- [ ] T116 **Generate manifest.json listing all downloaded subjects.**
  *Description*: Extend T102 (or as a separate lightweight step) to write `data/raw/manifest.json` containing an array of subject IDs and basic metadata (paths to fMRI files, behavioral JSON). This file serves as the authoritative source for downstream tasks. 
  *Verification*: `pytest code/tests/unit/test_manifest_generation.py` checks the JSON structure and that it lists exactly the subjects fetched by T102.

- [ ] T117 **Define sampled subject list.**
  *Description*: In `code/config.py`, add a constant `SAMPLE_SUBJECT_IDS` that is populated at runtime by reading `data/raw/manifest.json` and selecting either the first 1000 IDs or a fixed‑seed random sample of size 1000. Document the sampling rule in the config file. 
  *Verification*: `pytest code/tests/unit/test_sampling_rule.py` confirms that the list length is 1000 and that the selection is reproducible across runs.

- [ ] T118 **Compute ROI‑wise correlations and apply FWE correction.**
  *Description*: Add a new module `code/analysis/roi_correlation.py` that, for each ROI, computes the Pearson correlation between `network_flexibility` (or ROI‑specific flexibility if desired) and `creativity_score`. Collect all ROI‑wise p‑values and apply the family‑wise error method specified in `code/config.py` (max‑T or Bonferroni). Write `data/interim/roi_correlations.csv` with columns `roi, r, p_value, fwe_corrected_p`. T107 will consume this file to perform the final FWE step. 
  *Verification*: `pytest code/tests/unit/test_roi_correlation_fwe.py` validates that the output file exists, contains one row per ROI, and that corrected p‑values are ≤ 1 and appropriately adjusted.

- [ ] T119 **Implement checksum verification script.**
  *Description*: Create `code/utils/verify_checksums.py` that reads `data/checksums.json` and asserts that every listed file (both raw and derived CSVs) exists and matches its stored SHA‑256 hash. Exit with code 0 on success, non‑zero on mismatch. 
  *Verification*: `pytest code/tests/integration/test_verify_checksums.py` runs the script on a known‑good repository and expects exit 0; a manipulated file triggers a failure.

- [ ] T120 **Write provenance file for raw data source.**
  *Description*: After T102 completes, generate `data/raw/provenance.yaml` documenting: (a) the exact OpenNeuro dataset URL, (b) download date, (c) software versions used for fetching (e.g., `requests` version), (d) the HCP‑MMP atlas version employed downstream. This satisfies Constitution VI. 
  *Verification*: `pytest code/tests/unit/test_provenance.yaml` checks the file exists and contains required fields.

- [ ] T121 **Perform post‑hoc power analysis and document justification.**
  *Description*: Using the final sample size (`n_samples` from `data/interim/results.csv`), compute the achieved statistical power to detect a correlation of r = 0.15 at α = 0.05 (e.g., via `statsmodels.stats.power.CorrelationPower`). Write the result to `docs/outputs/power_analysis.txt` and reference it in `research.md`. This addresses the spec’s power assumption. 
  *Verification*: `pytest code/tests/unit/test_power_analysis.py` confirms the file is created and contains a numeric power estimate ≥ 0.80 (or flags if not).

- [ ] T122 **Clarify checksum registry scope in data‑model.**
  *Description*: Edit `specs/518-brain-dynamics-creativity/data-model.md` to state explicitly that `data/checksums.json` records SHA‑256 hashes for **both** raw data files and derived CSV artifacts (`data/interim/*.csv`). This resolves the mismatch with T110. 
  *Verification*: The updated data‑model description matches the behavior of the checksum verification script (T119) and the end‑to‑end reproducibility check (T110).

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command |
| :--- | :--- | :--- |
| FR-011 / US‑4 (CAQ validation, `DATA_MISSING_CREATIVITY`) | T101 | `pytest code/tests/contract/test_loader.py` |
| FR-009 (exclusion logging; real‑data fetch provenance) | T102, T103, T120 | `pytest code/tests/unit/test_filter_subjects.py`; `data/checksums.json` |
| FR-001 (preprocessing) | T104 | `python code/data/run_preprocess.py` |
| FR-002, FR-003, FR-004, FR-012 (connectivity, Louvain, flexibility, static strength) | T105, T115 | `pytest code/tests/unit/test_flexibility_schema.py` |
| FR-005 / US‑1, SC-001, SC-003 (OLS, ΔR², Pearson r) | T106 | `pytest code/tests/integration/test_regression_summary.py` |
| FR-006, FR-007 / US‑3 (permutation, FWE) | T107, T118 | `pytest code/tests/unit/test_permutation.py` |
| FR-010 / US‑3, SC-002, SC-005 (sensitivity sweep) | T108 | `pytest code/tests/unit/test_analysis.py::test_sensitivity_csv_schema` |
| FR-008 / US‑2, SC-004 (plots) | T109 | `pytest code/tests/unit/test_plots.py` |
| Reproducibility, performance, constitution I/III | T110 | `pytest code/tests/integration/`; checksum script; profiling report |
| Paper handoff, Principle IV | T112, T113 | artifact‑path audit of `research.md` |
| Versioning & state consistency | T114, T122 | data‑model no longer mentions state writes |
| Consensus clustering implementation | T115 | `pytest code/tests/unit/test_consensus_clustering.py` |
| ROI‑wise correlation & FWE | T118 | `pytest code/tests/unit/test_roi_correlation_fwe.py` |
| Checksum verification script | T119 | `pytest code/tests/integration/test_verify_checksums.py` |
| Power analysis justification | T121 | `pytest code/tests/unit/test_power_analysis.py` |

**Execution order** (respecting data flow):  
T101 → T102 → T116 → T117 → T103 → T104 → T105 → T115 → T106 → T107 → T118 → T108 → T109 → T110 → T111 → T112 → T113 → T114 → T122 → T119 → T120 → T121.  

All tasks respect the required dependencies and produce verifiable artifacts.  

# End of tasks.md