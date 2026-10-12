# Tasks: The Impact of Digital Decluttering on Cognitive Performance and Well‑being  

**Input**: Design documents from `/specs/001-digital-decluttering-study/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `data‑model.md`, `contracts/`  

## Phase 1 – Project setup & early end‑to‑end run  

- [ ] T001.1 [P] Create the top‑level project directory tree  
  `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/{data/{raw,processed,compliance},code,tests,results,docs}`  
  *Verification*: `cat projects/PROJ-249-the-impact-of-digital-decluttering-on-co/structure.log` must list all directories.  

- [ ] T001.2 [P] Create `requirements.txt` with pinned versions of the scientific stack (`pandas`, `numpy`, `scipy`, `scikit‑learn`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`).  
  *Verification*: `pip install -r requirements.txt` succeeds without version conflicts.  

- [ ] T003 [P] Configure linting (`flake8`) and formatting (`black`) tools.  
  *Verification*: `flake8 .` and `black --check .` both exit with status 0.  

- [ ] T004 [P] Set up the data sub‑folders `data/raw/`, `data/processed/`, `data/compliance/`.  
  *Verification*: `ls data/` shows the three directories.  

## Phase 2 – Core infrastructure (blocking prerequisites)  

- [ ] T005 [US1] Implement **pseudonymous participant ID generator** and registration pipeline (`code/pipeline/register_participant.py`).  
  *Outputs*: `data/raw/participant_registry.csv` (columns `participant_id`, `recruitment_id`, `status`).  
  *Verification*: All IDs match regex `^P\d{3}$`; duplicate `recruitment_id`s raise `ValueError`.  

- [ ] T006 [US1] **OSF instrument verification** (`code/validation/verify_osf_instruments.py`).  
  *Steps*: download SART & Ospan v2.1+ to `data/raw/osf_instruments/`, compute SHA‑256, compare to reference hashes stored in `contracts/instrument_hashes.yaml`.  
  *Output*: `results/instrument_verification.json` with field `"status": "verified"` or `"failed"`.  
  *Verification*: Pipeline aborts with a clear exception if verification fails.  

- [ ] T007 [US1] **Synthetic baseline data generator** (`code/validation/synthetic_baseline.py`).  
  *Config*: `code/config/synthetic_data_config.yaml` (seed, means, stds for each metric).  
  *Outputs*: `data/raw/synthetic_baseline.csv` (columns `id,participant_id,phase,metric_type,value,timestamp,quality_flag`).  
  *Verification*: Running the script creates the CSV; a checksum file `data/raw/synthetic_baseline.sha256` is written; all metric values fall within psychometrically plausible ranges (e.g., SART commission errors > 0, PSS‑10 0‑40).  

- [ ] T008 [US1] **Monte Carlo power simulation** (`code/analysis/power_simulation.py`).  
  *Input*: synthetic baseline from T007.  
  *Procedure*: 1 000 iterations, effect size d = 0.5, bootstrap CI & Holm‑Bonferroni correction.  
  *Output*: `results/power_analysis.json` with keys `power_estimate` (float), `iterations` (int), `effect_size` (float).  
  *Verification*: JSON file exists and `power_estimate` is a number between 0 and 1.  

- [ ] T009 [US2] **Compliance‑log pipeline** (`code/compliance/parse_logs.py`, `code/compliance/rules_engine.py`, `code/validation/compliance_plausibility.py`).  
  *Inputs*: raw daily logs in `data/raw/compliance_logs/` (one CSV per participant).  
  *Outputs*:  
    - `data/compliance/aggregated_compliance.csv` (participant‑level weekly compliance score).  
    - `data/compliance/flags.json` containing flags for implausible entries and the edge‑case “0 minutes all 7 days”.  
  *Verification*: Unit tests in `tests/unit/` confirm that ≤30 min social‑media, `news_consumption=False`, `notifications_off=True` yields `is_compliant=True`; violations are flagged but not excluded.  

## Phase 3 – Baseline collection & data merging  

- [ ] T010 [US1] **Baseline data collection pipeline** (`code/pipeline/collect_baseline.py`).  
  *Workflow*: reads `data/raw/synthetic_baseline.csv`, registers participants (T005), validates instrument scores, writes `data/raw/baseline_raw.csv`.  
  *Verification*: `baseline_raw.csv` conforms to `contracts/dataset.schema.yaml` (checked by `tests/contract/test_baseline_schema.py`).  

- [ ] T011 [US3] **Merge baseline, post‑intervention, and compliance data; compute change scores** (`code/pipeline/merge_data.py`).  
  *Inputs*: `data/raw/baseline_raw.csv`, `data/raw/post_intervention_raw.csv` (to be supplied by the web interface), `data/compliance/aggregated_compliance.csv`.  
  *Outputs*:  
    - `data/processed/merged_data.csv` (long format, one row per metric per participant, with columns `participant_id, phase, metric_type, value`).  
    - `data/processed/change_scores.csv` (computed as `post‑baseline`).  
  *Verification*: Script aborts with a clear error if any required input file is missing; the resulting CSV passes schema validation (`contracts/dataset.schema.yaml`).  

## Phase 4 – Statistical analysis  

- [ ] T012 [US3] **Primary bootstrap analysis** (`code/analysis/run_bootstrap.py`).  
  *Input*: `data/processed/change_scores.csv`.  
  *Procedure*: 10 000 resamples per metric, compute mean change and 95 % CI.  
  *Output*: `data/processed/bootstrap_results.json` (per‑metric `mean_change`, `ci_lower`, `ci_upper`).  
  *Verification*: JSON file exists; a sanity‑check test confirms CI bounds enclose the empirical mean.  

- [ ] T013 [US3] **Convergence detection & fallback Wilcoxon test** (`code/analysis/convergence_detector.py` + `code/analysis/wilcoxon_fallback.py`).  
  *Trigger*: If `run_bootstrap.py` writes a `bootstrap_status.json` flag `convergence_failed`.  
  *Output*: `data/processed/fallback_results.json` with Wilcoxon `p_value` and effect direction.  
  *Verification*: Unit test `tests/unit/test_fallback_trigger.py` forces a failure and checks that the fallback file is produced.  

- [ ] T014 [US3] **Effect‑size calculation & Holm‑Bonferroni correction** (`code/analysis/effect_sizes.py` & `code/analysis/holm_bonferroni.py`).  
  *Inputs*: bootstrap (or fallback) results.  
  *Outputs*: `results/statistical_summary.json` conforming to `contracts/analysis.schema.yaml` (includes `method_used`, `effect_size_cohen_d`, `p_value_corrected`).  
  *Verification*: A schema validation test (`tests/contract/test_analysis_schema.py`) passes; corrected p‑values are ≤ 0.05 for at least one metric when the simulated data contains a true effect.  

## Phase 5 – Visualization & reporting  

- [ ] T015 [US3] **Generate figures** (`code/viz/generate_plots.py`).  
  *Outputs*: `figures/boxplot_<metric>.png` and `figures/change_distribution_<metric>.png` for all four outcomes.  
  *Verification*: Files exist and are non‑empty PNGs; a quick‑look test confirms image dimensions ≥ 400 px.  

- [ ] T016 [US3] **Compile final study report** (`code/report/generate_report.py`).  
  *Sections*:  
    1. Summary of methods (links to `quickstart.md`).  
    2. Power‑analysis summary (from T008).  
    3. Sensitivity‑analysis discussion (FR‑011).  
    4. Statistical summary table (from T014).  
    5. Figures (from T015).  
    6. Quality‑report (data‑quality flags, dropout & attention‑check warnings).  
    7. Reproducibility manifest (see T017).  
  *Output*: `results/final_report.md`.  
  *Verification*: End‑to‑end test `tests/integration/test_end_to_end_pipeline.py` runs the full pipeline on synthetic data and asserts that `final_report.md` contains the headings “Statistical Summary”, “Power Analysis”, and “Quality Report”.  

- [ ] T017 [US3] **Create reproducibility manifest** (`code/utils/generate_manifest.py`).  
  *Contents*: random seed values, SHA‑256 checksums of all raw input files, `requirements.txt` hash, and software version snapshot.  
  *Output*: `results/reproducibility_manifest.json`.  
  *Verification*: Manifest is validated by `tests/unit/test_manifest_schema.py`.  

## Phase 6 – Data‑quality & edge‑case handling (cross‑cutting)  

- [ ] T018 [US3] **Dropout handling** (`code/pipeline/handle_dropouts.py`).  
  *Logic*: participants missing post‑intervention data are excluded from paired tests but retained in `data/processed/descriptive_baseline.csv`.  
  *Output*: `data/processed/exclusions.json` listing IDs with reason `missing_post_data`.  

- [ ] T019 [US3] **Attention‑check validation** (`code/validation/attention_check.py`).  
  *Rule*: SART accuracy < 50 % → flag as `low_quality`; flagged IDs are appended to `exclusions.json` with reason `low_sart_accuracy`.  

- [ ] T020 [US2] **Extreme compliance case flag** (enhancement to `code/validation/compliance_plausibility.py`).  
  *Rule*: if a participant reports `social_media_minutes == 0` for all 7 days, add flag `extreme_compliance` to `data/compliance/flags.json` but do **not** exclude from analysis.  

## Phase 7 – Review & polish (already verified)  

- [ ] T021 [P] Write `README.md` with installation, data‑generation, and analysis‑pipeline sections.  
- [ ] T022 [P] Write `quickstart.md` with a step‑by‑step command‑line guide.  
- [ ] T023 [P] Refactor `code/scoring/` and `code/analysis/` to keep cyclomatic complexity < 10 (unit‑test coverage ≥ 90 %).  
- [ ] T024 [P] Performance optimisation of bootstrap loops (vectorised NumPy implementation) achieving ≥ 20 % runtime reduction (measured on CI).  
- [ ] T025 [P] Run end‑to‑end reproducibility check (`quickstart.md` script) and confirm that a fresh checkout produces identical `final_report.md` and `statistical_summary.json`.  

---  

**Note** – All unchecked tasks above (T007‑T020) have been reopened or added to address the verification failures reported for `T009`, `T010`, and `T031`. The duplicate task identifier `T039` has been removed; the remaining visualisation task (`T015`) retains the original functionality.
