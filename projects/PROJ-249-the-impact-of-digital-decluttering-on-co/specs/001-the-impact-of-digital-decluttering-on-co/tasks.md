# Tasks: The Impact of Digital Decluttering on Cognitive Performance and Well‑being  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/`, original research idea, and reviewer feedback.  
The goal is to implement a reproducible, end‑to‑end pipeline that evaluates the **associational** effect of a one‑week digital declutter on sustained attention, working memory, stress, and mood, respecting all functional requirements (FR‑001 – FR‑011) and success criteria (SC‑001 – SC‑005).

---  

## Phase 0 – Pilot Validation (pre‑recruitment)

- [ ] T000 [US1] **Pilot validation of SART and Ospan timing (n = 5).**  
  *Create a tiny live or simulated pilot, record raw trial‑level responses, and verify that all response times fall within 100 ms – 5000 ms and that SART accuracy ≥ 50 % (low‑attention flag otherwise).*  
  **File path(s)**: `data/raw/pilot/`, `code/tests/test_pilot.py`  
  **Verification**: `pytest code/tests/test_pilot.py` must pass and the pilot files must validate against `contracts/dataset.schema.yaml`.  

---  

## Phase 1 – Setup & Data Collection  

- [ ] T001 [P1] **Create project layout (directories).**  
  *Create required directories (`code/scoring/`, `code/analysis/`, `code/compliance/`, `code/viz/`, `code/validation/`, `code/pipeline/`, `code/tests/`, `data/raw/`, `data/processed/`, `data/results/`, `figures/`).*  
  **File path(s)**: (directory creation, no file)  
  **Verification**: Presence of directories verified by integration test `tests/integration/test_layout.py`.

- [ ] T013 [P1] **Pin dependencies in `requirements.txt`.**  
  *Write `code/requirements.txt` with exact version pins for all packages used in the pipeline.*  
  **File path(s)**: `code/requirements.txt`  
  **Verification**: `pip install -r code/requirements.txt` succeeds without version conflicts.

- [ ] T014 [P1] **Create study configuration file.**  
  *Write `code/config/study_config.yaml` containing seed = 42, n_participants = 80, bootstrap_resamples = 10000, practice_effect_grid = [0.0,0.2,0.4].*  
  **File path(s)**: `code/config/study_config.yaml`  
  **Verification**: Config file parses without error using `yaml.safe_load`.

- [ ] T015 [P1] **Verify end‑to‑end run captures log and status.**  
  *Execute `python -m code.pipeline.run_all --config code/config/study_config.yaml` and ensure `data/results/pipeline.log` ends with `STATUS: SUCCESS`.*  
  **File path(s)**: `data/results/pipeline.log`  
  **Verification**: Integration test `tests/integration/test_full_run.py` checks log termination.

- [ ] T001a [P1] **Implement web‑based participant recruitment and pseudonymous ID generation (FR‑001).**  
  *Develop a minimal Flask/Django endpoint `code/recruitment/app.py` that registers a new participant, assigns an ID matching pattern `^P\\d{3}$`, stores demographics, and returns the ID.*  
  *Persist registrations to `data/raw/participants.csv` (schema validated by `contracts/dataset.schema.yaml`).*  
  **File path(s)**: `code/recruitment/app.py`, `data/raw/participants.csv`  
  **Verification**: Integration test `tests/integration/test_recruitment.py` confirms ID format and CSV entry.

- [ ] T001b [P2] **Build web interface for SART and Ospan delivery (FR‑002).**  
  *Create `code/web/tasks/sart_ospan.py` exposing routes to serve the OSF task code (downloaded & checksum‑validated) and record raw trial‑level responses.*  
  *Responses are saved under `data/raw/trial_level/` as CSV files (`sart_trials_*.csv`, `ospan_trials_*.csv`).*  
  **File path(s)**: `code/web/tasks/sart_ospan.py`, `data/raw/trial_level/`  
  **Verification**: `tests/integration/test_task_delivery.py` ensures files are created and conform to `contracts/dataset.schema.yaml`.

- [ ] T001c [P3] **Create web pages for PSS‑10 and PANAS questionnaires (FR‑003).**  
  *Implement `code/web/questionnaires/pss_panas.py` serving the questionnaires, collecting raw responses, and writing them to `data/raw/questionnaire_responses.csv`.*  
  **File path(s)**: `code/web/questionnaires/pss_panas.py`, `data/raw/questionnaire_responses.csv`  
  **Verification**: `tests/integration/test_questionnaire.py` validates CSV schema.

- [ ] T001d [P2] **Develop daily compliance‑logging UI (FR‑004).**  
  *Provide `code/web/compliance/compliance_ui.py` where participants submit daily logs (social media minutes, news consumption, notifications off).*  
  *Logs are saved as one CSV per participant per day under `data/raw/compliance_logs/`.*  
  **File path(s)**: `code/web/compliance/compliance_ui.py`, `data/raw/compliance_logs/`  
  **Verification**: `tests/integration/test_compliance_ui.py` checks that submitted logs validate against `contracts/compliance.schema.yaml`.

- [ ] T002 [P1] [US1] **Implement scoring functions for all four instruments with quality‑flag logic.**  
  *Add `code/scoring/sart.py`, `code/scoring/ospan.py`, `code/scoring/pss10.py`, `code/scoring/panas.py` that follow the OSF v2.1+ reference algorithms.*  
  *Each function returns a numeric score and a `quality_flag` (`valid`, `low_attention`, `missing`).*  
  *SART: flag `low_attention` when accuracy < 50 %; all tasks enforce response‑time limits 100 ms – 5000 ms (FR‑009).*  
  **File path(s)**: `code/scoring/*.py`, `code/tests/test_scoring.py`  
  **Verification**: `pytest code/tests/test_scoring.py` must pass and the produced rows must validate against `contracts/dataset.schema.yaml`.

- [ ] T003 [P2] **Simulate a complete study dataset for early testing (development‑only).**  
  *`code/validation/simulate_study.py` (seed = 42) creates:*  
    - `data/raw/participants_simulated.csv` (IDs = P001‑P080).  
    - `data/raw/trial_level/sart_trials_sim.csv` & `ospan_trials_sim.csv`.  
    - `data/raw/simulated_measurements.csv` with baseline & post records (including `quality_flag`).  
    - `data/raw/compliance_logs_sim/` with seven daily CSVs per participant.  
  **File path(s)**: `code/validation/simulate_study.py`, `data/raw/*sim*`  
  **Verification**: Running the script produces the files; subsequent tasks consume them.

- [ ] T016 [P2] **Generate SHA‑256 checksums for all raw artifacts.**  
  *`code/validation/generate_checksums.py` writes `data/checksums.sha256` containing a line `<hash>  <relative_path>` for each file under `data/raw/`.*  
  **File path(s)**: `code/validation/generate_checksums.py`, `data/checksums.sha256`  
  **Verification**: `sha256sum -c data/checksums.sha256` exits with all OK.

- [ ] T017 [P2] **Produce a smoke‑analysis result for the simulated dataset.**  
  *`code/validation/produce_smoke_results.py` runs the full analysis pipeline on the simulated data and writes `data/results/smoke_results.json` conforming to `contracts/analysis.schema.yaml`.*  
  **File path(s)**: `code/validation/produce_smoke_results.py`, `data/results/smoke_results.json`  
  **Verification**: `pytest code/tests/test_smoke_analysis.py` validates JSON schema compliance.

- [ ] T004 [P2] [US2] **Process daily compliance logs, enforce plausibility, and produce aggregated compliance output.**  
  *Implement `code/compliance/compute_compliance.py` (exposed as module `code.compliance.compute_compliance`).*  
  *The script loads all CSVs from `data/raw/compliance_logs/`, validates each row against `contracts/compliance.schema.yaml` (any out‑of‑range value raises an exception – no silent correction).*
  *Derive `is_compliant = (social_media_minutes ≤ 30) ∧ (news_consumption == False) ∧ (notifications_off == True)`.*
  *Flag participants whose **entire** 7‑day record reports 0 minutes as “extreme” (retain them).*
  *Write `data/processed/aggregated_compliance.csv` (one row per participant) and `data/processed/compliance_flags.json` containing any flagged cases.*  
  **File path(s)**: `code/compliance/compute_compliance.py`, `data/processed/aggregated_compliance.csv`, `data/processed/compliance_flags.json`  
  **Verification**: `pytest code/tests/test_compliance.py` must pass; executing `python -m code.compliance.compute_compliance` must exit 0 and its stdout (including a summary of flagged cases) appended to `data/results/pipeline.log`.

- [ ] T005 [P2] [US3] **Merge baseline/post measurements with compliance data, handle attrition, and compute change scores.**  
  *Implement `code/pipeline/merge_data.py` (module `code.pipeline.merge_data`).*  
  *Join `data/raw/simulated_measurements.csv` (or real `data/raw/measurement_records.csv` when available) with `data/processed/aggregated_compliance.csv` on `participant_id`.*  
  *Detect participants missing any post‑intervention record; exclude them from paired statistical tests but retain their baseline rows in `data/processed/descriptive_baseline.csv`.*  
  *Compute `post – baseline` for each metric, write `data/processed/change_scores.csv` (columns: `participant_id`, `metric_type`, `change`).*  
  *Preserve original timestamps and `quality_flag` for reproducibility.*  
  **File path(s)**: `code/pipeline/merge_data.py`, `data/processed/descriptive_baseline.csv`, `data/processed/change_scores.csv`  
  **Verification**: `pytest code/tests/test_merge.py` must confirm correct arithmetic, proper dropout handling, and schema‑compliant output; running `python -m code.pipeline.merge_data` must exit 0 and its summary (participants kept / dropped) appended to `data/results/pipeline.log`.

- [ ] T006 [P3] [US3] **Perform primary statistical analysis with bootstrap, fallback Wilcoxon, Cohen’s d, and Holm‑Bonferroni correction.**  
  *Implement `code/analysis/run_analysis.py` that reads `data/processed/change_scores.csv`.*  
  *For each of the four outcome metrics:*  
    – Perform 10 000‑sample bootstrap of the mean change → 95 % CI.  
    – Run Shapiro‑Wilk; if p < 0.05, fall back to Wilcoxon signed‑rank **but still report Cohen’s d** (rank‑biserial is *not* used, complying with FR‑007).  
    – Compute Cohen’s d with bias‑corrected 95 % CI.  
  *After processing all metrics, apply Holm‑Bonferroni step‑down to the uncorrected p‑values.*  
  *Write `data/results/statistical_summary.json` containing one object per metric that conforms exactly to `contracts/analysis.schema.yaml`.*  
  **File path(s)**: `code/analysis/run_analysis.py`, `data/results/statistical_summary.json`  
  **Verification**: `pytest code/tests/test_analysis.py` must verify corrected p‑values ≥ uncorrected, CI containment, and schema compliance; executing `python -m code.analysis.run_analysis` must log its progress to `data/results/pipeline.log`.

- [ ] T012 [P3] **Verify success‑criterion thresholds (SC‑001 – SC‑004).**  
  *Create `code/tests/test_success_criteria.py` that loads `data/results/statistical_summary.json` and asserts for each metric:*  
    – `p_value_corrected < 0.05` **and** `effect_size_cohen_d >= 0.2`.  
  *If any metric fails, the test fails, making the success criteria enforceable.*  
  **File path(s)**: `code/tests/test_success_criteria.py`  
  **Verification**: `pytest code/tests/test_success_criteria.py` must pass for the study to be accepted.

- [ ] T007 [P3] **Monte‑Carlo power simulation to justify the planned sample size.**  
  *Implement `code/analysis/power_simulation.py` that repeats the full analysis pipeline on synthetic data 1 000 times with effect size d = 0.5 (seed = 42).*  
  *Record the proportion of simulations where **all four primary outcomes** achieve Holm‑Bonferroni‑corrected significance (p < 0.05). Also compute the smallest N that yields ≥ 80 % power (by incremental search).*  
  *Write `data/results/power_analysis.json` with keys `power_estimate` (float) and `required_n_for_80pct_power` (int).*  
  **File path(s)**: `code/analysis/power_simulation.py`, `data/results/power_analysis.json`  
  **Verification**: `pytest code/tests/test_power.py` must confirm both keys exist and values are deterministic given the seed.

- [ ] T008 [P3] **Sensitivity analyses for practice effects and self‑report compliance bias.**  
  *Implement `code/analysis/sensitivity.py` that:*  
    – Re‑runs the primary analysis after **excluding** participants whose overall compliance percentage < 50 % (self‑report quality check).  
    – Simulates practice‑effect inflation by adding Gaussian noise (SD = 0.0, 0.2, 0.4) to baseline SART and Ospan scores (grid `practice_effect_grid` from the config), recomputes change scores, and records how effect sizes shift.  
    – Writes a narrative `data/results/sensitivity_report.md` describing the limitation (FR‑011), presenting the grid results, and reiterating the associative framing.  
    – Writes `data/results/sensitivity_analysis.json` summarizing effect‑size changes for each grid value.  
  **File path(s)**: `code/analysis/sensitivity.py`, `data/results/sensitivity_report.md`, `data/results/sensitivity_analysis.json`  
  **Verification**: `pytest code/tests/test_sensitivity.py` must confirm the grid is applied correctly and that the markdown contains required sections; execution `python -m code.analysis.sensitivity` must exit 0 and its concise stdout be appended to `data/results/pipeline.log`.

- [ ] T009 [P3] **Generate all required visualizations from validated outputs.**  
  *Implement `code/viz/generate_plots.py` that reads `data/results/statistical_summary.json` and `data/processed/change_scores.csv`.*  
  *Produce:*  
    – Histogram PDFs for change scores of each metric (`figures/hist_<metric>.png`).  
    – Forest plot of Cohen’s d with 95 % CIs (`figures/effect_sizes_forest.png`).  
    – Bar chart of compliance distribution (`figures/compliance_bar.png`).  
  *Save PNGs under `figures/`.*  
  **File path(s)**: `code/viz/generate_plots.py`, `figures/*.png`  
  **Verification**: `pytest code/tests/test_viz.py` asserts each expected PNG exists, is non‑zero size, and that plotted numeric values match those in `statistical_summary.json`; running the script must be logged in `data/results/pipeline.log`.

---  

## Phase 2 – Results & Paper Hand‑off  

- [ ] T010 [P3] **Compile the final associative report.**  
  *Create `data/results/final_report.md` containing:*  
    – Methods section referencing exact script versions and the config file.  
    – Results table mirroring `statistical_summary.json` (mean ± CI, corrected p, Cohen’s d).  
    – All figures (embedded via markdown image links).  
    – Discussion that explicitly frames findings as **associational**, acknowledges practice‑effect possibilities, and documents self‑report limitations (FR‑011).  
    – “Paper‑stage handoff” subsection mapping each JSON key to the intended manuscript table/figure.  
  **File path(s)**: `data/results/final_report.md`  
  **Verification**: `pytest code/tests/test_report.py` checks that every statistic in the markdown matches the source JSON.

- [ ] T010b [P3] **Re‑run checksum verification and log hand‑off.**  
  *Execute `sha256sum -c data/checksums.sha256` and write the full output to `data/results/checksum_verification.log`.*  
  *Append a line `REPORT: COMPLETE` to `data/results/pipeline.log`.*  
  **File path(s)**: `data/results/checksum_verification.log`, `data/results/pipeline.log`  
  **Verification**: `grep "OK" data/results/checksum_verification.log` must succeed; `grep "REPORT: COMPLETE" data/results/pipeline.log` must succeed.

- [ ] T011 [P3] **End‑to‑end reproducibility verification.**  
  *Execute the full pipeline from scratch:* `python -m code.pipeline.run_all --config code/config/study_config.yaml`.  
  *Confirm that `data/results/pipeline.log` exists, ends with `STATUS: SUCCESS`, and that all expected artifacts (`statistical_summary.json`, all PNGs, `final_report.md`, etc.) are present.*  
  **File path(s)**: `data/results/pipeline.log`, `data/results/*`, `figures/*`  
  **Verification**: `pytest code/tests/test_full_run.py` asserts the log ends with `STATUS: SUCCESS`, that artifact hashes match `data/checksums.sha256`, and that no unexpected files are generated.

---  

### Dependency & Requirement Mapping  

| Spec Requirement | Covered by Task(s) | Verification |
|------------------|--------------------|--------------|
| FR‑001 (IDs) | T001a | schema validation of `participants.csv` |
| FR‑002 / FR‑003 (SART, Ospan, PSS‑10, PANAS) | T001b, T001c, T002 | `test_scoring.py`, UI integration tests |
| FR‑004 (Compliance logging) | T001d, T004 | `test_compliance.py` |
| FR‑005 (Change scores) | T005 | `test_merge.py` |
| FR‑006 (Bootstrap / Wilcoxon) | T006 | `test_analysis.py` |
| FR‑007 (Cohen’s d) | T006 (Cohen’s d only) | `test_analysis.py` |
| FR‑008 (Holm‑Bonferroni) | T006 | `test_analysis.py` |
| FR‑009 (Pilot timing) | T000, T002 | `test_pilot.py` |
| FR‑010 (Compliance plausibility) | T004 | `test_compliance.py` |
| FR‑011 (Sensitivity to self‑report) | T008 | `test_sensitivity.py` |
| SC‑001 – SC‑004 (Success criteria) | T012 | `test_success_criteria.py` |
| All other FRs & SCs | Various tasks above | Corresponding test suites |

All tasks are currently unchecked; completing each will satisfy the specification, address the reviewer’s concerns about practice effects and causal framing, and produce a fully reproducible research pipeline.  

---  

*All tasks respect data‑flow ordering: T000 → T001 → T013 → T014 → T015 → T001a‑T001d → T002 → T003 → T016 → T017 → T004 → T005 → T006 → T012 → T007 → T008 → T009 → T010 → T010b → T011.*  

---  

# End of tasks.md