# Tasks: The Impact of Musical Training on Functional Connectivity in Adolescent Brains  

**Inputs**: `spec.md`, `plan.md` (from `specs/001-musical-training-connectivity/`)  

---

## Phase 0 – Project scaffolding, synthetic verification mode, and real‑data ingestion  

- [ ] T001 **Document project layout and quick‑start command**   <!-- FAILED-IN-EXECUTION: code/run_quickstart_test.py exit=5 -->
  *Creates* `README.md` and `quickstart.md` that describe the directory structure, required Python version, and the command `python -m code.main --mode verification`.  
  *Verification*: `pytest tests/unit/test_quickstart.py` passes; the README lists all top‑level folders (`code/`, `data/`, `tests/`).  

- [ ] T002 **Synthetic data generator** – `code/data/synthetic_generator.py`   <!-- FAILED-IN-EXECUTION: code/data/run_synthetic_generator.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/run_synthetic_generator.py exit=1 -->
  Generates a balanced synthetic cohort (≈75 musicians, ≈75 non‑musicians) with realistic confound distributions and writes:  
  - `data/raw/mock_nifti/` (mock NIfTI files)  
  - `data/processed/subjects.parquet` (behavioural table).  
  *Verification*: `pytest tests/unit/test_synthetic_generator.py` confirms schema compliance (subject.schema.yaml) and that every musician has `years_of_training ≥ 1`.  

- [ ] T003 **Main entry‑point wiring** – `code/main.py`   <!-- FAILED-IN-EXECUTION: code/main.py exit=2 -->
  Adds CLI options `--mode verification` (synthetic) and `--mode analysis` (real data). Calls the appropriate pipeline modules.  
  *Verification*: Running `python -m code.main --mode verification` produces the three verification‑mode CSVs listed in T101‑T106 without error.  

- [ ] T111 **Real‑data ingestion (ABCD/HCP‑Adolescents)** – `code/data/real_ingest.py`   <!-- FAILED-IN-EXECUTION: code/data/real_ingest.py exit=1 -->
  Implements a compliant access workflow to download/restoring resting‑state fMRI NIfTI files and accompanying behavioral CSVs from the ABCD Study or HCP‑Adolescents.  
  *Outputs*:  
  - `data/raw/fmri/` (raw NIfTI files)  
  - `data/raw/behavioural/subjects_raw.csv` (metadata including musical training history).  
  *Verification*: `pytest tests/integration/test_real_ingest.py` checks that the download succeeded, that the CSV contains the required columns, and that at least 50 subjects per group are present; otherwise raises `DataAccessError('Insufficient Data for Power')`.  

---

## Phase 1 – Data ingestion & preprocessing (US‑1)  

- [ ] T101 **US1 – Preprocess subjects & produce validation reports**  
  *File*: `code/data/preprocess.py`  
  *Inputs*: `data/raw/behavioural/subjects_raw.csv` (real) or synthetic `subjects.parquet`.  
  *Outputs*:  
  - `data/processed/subjects_cleaned.csv` (columns: `subject_id,group,years_of_training,age,sex,motion_score,ses_score`)  
  - `data/processed/dataset_validity_report.csv` (`metric,value` including `valid_subjects_percentage`). The report now includes a quantitative target: `valid_subjects_percentage >= 90`.  
  - `data/processed/matching_balance_report.csv` (`variable,pre_mean,post_mean,diff,p_value` for age, sex, motion_score, ses_score).  
  *Verification*: `pytest tests/integration/test_ingestion.py` checks file existence, column names, that the validity percentage meets the ≥ 90 % threshold, and that **all** rows labelled “musician” have `years_of_training ≥ 1` while “non_musician” rows have `years_of_training == 0`.  

- [ ] T102 **US2 – Load bundled Schaefer‑400 atlas**  
  *File*: `code/analysis/atlas.py` (loads `data/atlas/schaefer_400.csv` shipped with the repo).  
  *Outputs*: `data/atlas/schaefer_400.csv` (columns: `roi_id,x,y,z,network`) and a checksum entry in `data/checksums.txt`.  
  *Verification*: `pytest tests/unit/test_atlas_load.py` asserts the file has 400 rows, that the checksum matches, and that network names are limited to the expected set.  

- [ ] T112 **US2 – Compute functional connectivity matrices** – `code/analysis/connectivity.py`  
  Loads preprocessed fMRI time‑series (using the atlas from T102) for each subject, computes Pearson correlation matrices, applies Fisher’s r‑to‑z transformation, and saves:  
  - `data/processed/connectivity_matrices.npy` (shape: `N_subjects × n_rois × n_rois`).  
  *Verification*: `pytest tests/unit/test_connectivity.py` confirms the output shape matches the number of subjects and ROIs, that matrices are symmetric with zeros on the diagonal, and that a spot‑check correlation reproduces `numpy.corrcoef`.  

- [ ] T103 **US2 – Derive network‑level metrics**  
  *File*: `code/analysis/networks.py` (loads `data/processed/connectivity_matrices.npy` and the atlas from T102).  
  *Output*: `data/processed/network_metrics.csv` (`subject_id,network,mean_connectivity`).  
  *Verification*: `pytest tests/integration/test_network_metrics.py` confirms every `network` value is one of `auditory`, `motor`, `executive` and that rows = subjects × 3.  

---

## Phase 2 – Core statistical analysis (US‑2)  

- [ ] T104 **US2 – Group‑wise edge‑wise Welch’s t‑tests & BH‑FDR**  
  *File*: `code/analysis/stats.py` (Welch’s t‑test, Benjamini‑Hochberg correction, Cohen’s d, 1 000 bootstrap CIs).  
  *Outputs*:  
  - `data/processed/connectivity_results.csv` (`connection_id,t_stat,p_value,q_value,effect_size,ci_lower,ci_upper`).  
  - `data/processed/nbs_results.csv` (`component_id,size_edges,p_value_fwer`).  
  *Verification*: Spot‑check on a random edge reproduces `scipy.stats.ttest_ind(..., equal_var=False)` to ≤ 1e‑6; `pytest tests/unit/test_stats.py` validates column names, that q‑values are computed with BH, and does **not** require any edge to survive the threshold (the test simply ensures the file is well‑formed).  

- [ ] T105 **US3 – Correlation of connectivity with years of training (musician‑only)**  
  *File*: `code/analysis/correlation.py` (Pearson; falls back to Spearman if normality fails; BH‑FDR).  
  *Output*: `data/processed/correlation_results.csv` (`connection_id,r_value,p_value,q_value,effect_size,ci_lower,ci_upper,stability_flag`).  
  *Verification*: `pytest tests/integration/test_correlation.py` checks that `stability_flag` is `"low"` whenever the 95 % CI of the effect size includes zero and that the number of musician rows matches `subjects_cleaned.csv`.  

- [ ] T106 **US3 – Sensitivity analysis over FDR thresholds**  
  *File*: `code/analysis/sensitivity.py` (sweeps q‑thresholds = 0.01, 0.05, 0.10).  
  *Output*: `data/processed/sensitivity_analysis.csv` (`threshold,significant_count,percentage_reduction`).  
  *Verification*: `pytest tests/unit/test_sensitivity.py` recomputes counts from `connectivity_results.csv` and asserts the reduction formula matches the recorded values.  

---

## Phase 3 – Full verification run & validation checks  

- [ ] T107 **Run end‑to‑end verification pipeline (null‑first cohort)**  
  *Command*: `python -m code.main --mode verification`.  
  *Output*: `data/results/verification_run_summary.csv` (`metric,value,unit`) containing peak RAM (from `utils/memory_monitor.py`), total runtime, and a statement that no edge survived BH‑FDR (q < 0.05) and NBS p‑value > 0.05.  
  *Verification*: Values in the summary are programmatically read back and compared to the actual logs; `pytest tests/integration/test_full_run.py` must pass.  

- [ ] T108 **Independent validation checks (edge cases & stress test)**  
  *Sub‑tasks*:  
  1. **Stress test** – inject a known effect into a synthetic cohort and confirm NBS detects a component (size > null).  
  2. **Corrupted NIfTI handling** – feed a truncated file, verify the subject is skipped and the error is logged without crash.  
  3. **Insufficient‑sample halt** – run `--mode analysis` on a dataset with < 50 subjects per group and assert a `DataAccessError('Insufficient Data for Power')` is raised.  
  *Output*: `data/results/validation_checks.csv` summarising each sub‑test outcome (`test_name,status,notes`).  
  *Verification*: `pytest tests/integration/test_validation_checks.py` confirms all three behaviours occur as specified.  

---

## Phase 4 – Results visualisation & tables (US‑2 & US‑3)  

- [ ] T109 **Generate figures and summary tables**  
  *Files*: `code/visualization/plot_connectivity.py`, `code/visualization/plot_nbs.py`.  
  *Outputs*:  
  - `data/results/fig_connectivity_heatmap.png` (group‑mean z‑matrix heatmaps).  
  - `data/results/fig_nbs_component.png` (graph of the largest NBS component).  
  - `data/results/table_group_comparison.csv` (derived from `connectivity_results.csv`).  
  - `data/results/table_correlation.csv` (derived from `correlation_results.csv`).  
  - `data/results/table_sensitivity.csv` (derived from `sensitivity_analysis.csv`).  
  *Verification*: Re‑running the plotting scripts on the CSVs reproduces identical PNGs (pixel‑wise hash check) and CSVs match the source files column‑wise (`pytest tests/unit/test_visuals.py`).  

---

## Phase 5 – Documentation hand‑off to paper pipeline  

- [ ] T110 **Write methods & results narrative; update quick‑start**  
  *Files*: `research.md`, `quickstart.md`.  
  *Content*:  
  - Precise description of each pipeline stage, the synthetic‑verification results, and an explicit statement that **scientific conclusions require a verified real ABCD/HCP‑Adolescents dataset (FR‑001)**; the synthetic mode is only for pipeline validation.  
  - Commands to reproduce the verification run and the validation checks from a clean checkout.  
  *Verification*: `pytest tests/integration/test_documentation.py` parses the markdown and confirms that every referenced artifact path exists and that the “Verification Mode” disclaimer is present.  

---

## Dependencies & requirement coverage  

| Requirement | Task(s) that satisfy it |
|-------------|------------------------|
| FR‑001 / US‑1 | T111 (real data ingestion) → T101 (preprocessing) |
| FR‑002 / US‑2 | T112 (connectivity computation) |
| FR‑003 / US‑2 | T104 (Welch’s t‑test, **BH** FDR) |
| FR‑004 / US‑3 | T105 (correlation) |
| FR‑005 / US‑3 | T106 (threshold sensitivity) |
| FR‑006 / SC‑004 | T107 (memory & runtime monitoring) |
| FR‑007 / SC‑001‑SC‑003 | T104 (effect sizes, CIs), T105 (effect sizes, CIs), T106 (significant‑count table) |
| FR‑008 | T104 (NBS component) |
| FR‑009 | T101 (propensity‑score matching **and** regression residualisation) |
| SC‑005 | T101 (valid_subjects_percentage ≥ 90 %) |
| Edge‑case handling | T108 (corrupted file, insufficient sample) |
| Documentation hand‑off | T110 |

All tasks respect data‑flow ordering: real ingestion → preprocessing → atlas load → connectivity → network metrics → statistical testing → correlation → sensitivity → full run → validation → visualisation → write‑up.  

---  

*End of `tasks.md`.* 