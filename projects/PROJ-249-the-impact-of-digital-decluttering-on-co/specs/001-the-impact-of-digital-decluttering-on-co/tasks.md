# Tasks: The Impact of Digital Decluttering on Cognitive Performance and Well‑being  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/`, original research idea, and reviewer feedback.  
The goal is to implement a reproducible, end‑to‑end pipeline that evaluates the **associational** effect of a one‑week digital declutter on sustained attention, working memory, stress, and mood, while explicitly acknowledging practice‑effect and control‑group limitations. All functional requirements (FR‑001 – FR‑011) and success criteria (SC‑001 – SC‑005) must be satisfied and verifiable by automated tests.

---

## Phase 0 – Pilot Validation (pre‑recruitment)

- [ ] T000 **Pilot validation of SART and Ospan timing (n = 5).**  
  *Create a tiny live pilot, record raw trial‑level responses, and verify that all response times fall within 100 ms – 5000 ms and that SART accuracy ≥ 50 % (low‑attention flag otherwise).*  
  **File path(s)**: `data/raw/pilot/`, `code/tests/test_pilot.py`  
  **Verification**: `pytest code/tests/test_pilot.py` must pass and the pilot files must validate against `contracts/dataset.schema.yaml`.

---

## Phase 1 – Setup, Data Collection, and Early End‑to‑End Run  

### Project scaffolding  

- [ ] T001 **Create project layout, pin dependencies, and write configuration.**  
  *Create required directories (`code/scoring/`, `code/analysis/`, `code/compliance/`, `code/viz/`, `code/validation/`, `code/pipeline/`, `code/tests/`, `data/raw/`, `data/processed/`, `data/results/`, `figures/`).*  
  **File path(s)**: (directory creation), `code/requirements.txt`, `code/config/study_config.yaml`, `quickstart.md` (updated with exact command).  
  **Verification**: `pytest tests/integration/test_layout.py` confirms directories exist; `pip install -r code/requirements.txt` succeeds without conflicts.

### Participant recruitment & instrument delivery  

- [ ] T001b **Implement web‑based participant recruitment and pseudonymous ID generation (FR‑001).**  
  *Develop a minimal Flask endpoint `code/recruitment/app.py` that registers a new participant, assigns an ID matching `^P\\d{3}$`, stores optional demographics, and writes a row to `data/raw/participants.csv`.*  
  **File path(s)**: `code/recruitment/app.py`, `data/raw/participants.csv`  
  **Verification**: `tests/integration/test_recruitment.py` confirms ID format and CSV entry.

- [ ] T001c **Build web interface for SART and Ospan delivery (FR‑002).**  
  *Create `code/web/tasks/sart_ospan.py` that downloads the OSF task code (verified via checksum), serves the tasks, records raw trial‑level responses, and writes CSVs (`data/raw/trial_level/sart_trials_<pid>.csv`, `data/raw/trial_level/ospan_trials_<pid>.csv`).*  
  **File path(s)**: `code/web/tasks/sart_ospan.py`, `data/raw/trial_level/`  
  **Verification**: `tests/integration/test_task_delivery.py` ensures files are created and conform to `contracts/dataset.schema.yaml`.

- [ ] T001d **Create web pages for PSS‑10 and PANAS questionnaires (FR‑003).**  
  *Implement `code/web/questionnaires/pss_panas.py` that serves the questionnaires, collects raw responses, and writes `data/raw/questionnaire_responses.csv`.*  
  **File path(s)**: `code/web/questionnaires/pss_panas.py`, `data/raw/questionnaire_responses.csv`  
  **Verification**: `tests/integration/test_questionnaire.py` validates the CSV against `contracts/dataset.schema.yaml`.

- [ ] T001e **Develop daily compliance‑logging UI (FR‑004).**  
  *Provide `code/web/compliance/compliance_ui.py` where participants submit daily logs (social media minutes, news consumption, notifications off). Logs are stored as one CSV per participant per day under `data/raw/compliance_logs/`.*  
  **File path(s)**: `code/web/compliance/compliance_ui.py`, `data/raw/compliance_logs/`  
  **Verification**: `tests/integration/test_compliance_ui.py` checks that submitted logs validate against `contracts/compliance.schema.yaml`.

### Scoring functions  

- [ ] T002 **Implement scoring functions for SART, Ospan, PSS‑10, and PANAS with quality‑flag logic (FR‑002, FR‑003, FR‑009).**  
  *Add modules `code/scoring/sart.py`, `code/scoring/ospan.py`, `code/scoring/pss10.py`, `code/scoring/panas.py` that follow OSF v2.1+ reference algorithms. Each returns a numeric score and a `quality_flag` (`valid`, `low_attention`, `missing`). SART flags `low_attention` when accuracy < 50 %; all tasks enforce response‑time limits 100 ms – 5000 ms.*  
  **File path(s)**: `code/scoring/*.py`, `code/tests/test_scoring.py`  
  **Verification**: `pytest code/tests/test_scoring.py` must pass; scored rows must validate against `contracts/dataset.schema.yaml`.

### Simulated dataset generation & validation  

- [~] T003a **Generate a fully‑scored simulated study dataset (baseline & post) for early testing.**  
  *Run `code/validation/simulate_study.py` (seed = 42) to create:*  
  - `data/raw/participants_simulated.csv` (IDs P001‑P080).  
  - `data/raw/trial_level/sart_trials_sim.csv` & `ospan_trials_sim.csv`.  
  - `data/raw/measurement_records_sim.csv` containing baseline and post records for all four metrics, each with a `quality_flag`.  
  - `data/raw/compliance_logs_sim/` with seven daily CSVs per participant.  
  **File path(s)**: `code/validation/simulate_study.py`, `data/raw/*sim*`  
  **Verification**: Script runs without error and prints a summary; `ls data/raw/*sim*` shows the expected files.

- [ ] T003b **Validate the simulated measurement records against `contracts/dataset.schema.yaml`.**   <!-- FAILED-IN-EXECUTION: code/validation/validate_schema.py exit=1 -->
  *Execute `code/validation/validate_schema.py --schema contracts/dataset.schema.yaml --data data/raw/measurement_records_sim.csv`. Any violation must raise an exception (no silent correction).*  
  **File path(s)**: `code/validation/validate_schema.py` (shared validator)  
  **Verification**: `pytest code/tests/test_simulated_schema.py` asserts successful validation.

- [~] T003c **Generate SHA‑256 checksums for all simulated raw artifacts and verify inclusion.**  
  *Run `code/validation/generate_checksums.py` targeting `data/raw/` (including simulated files). The script writes `data/checksums.sha256` with a line `<hash>  <relative_path>` for every file.*  
  **File path(s)**: `code/validation/generate_checksums.py`, `data/checksums.sha256`  
  **Verification**: `sha256sum -c data/checksums.sha256` exits with all OK; `tests/integration/test_checksum.py` checks that the manifest contains entries for at least five simulated files.

- [ ] T003d **Produce a smoke‑analysis result on the simulated dataset and confirm values.**   <!-- FAILED-IN-EXECUTION: code/validation/produce_smoke_results.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/validation/produce_smoke_results.py exit=1 -->
  *Run `code/validation/produce_smoke_results.py` which invokes the full analysis pipeline on the simulated data and writes `data/results/smoke_results.json`.*  
  *After generation, a quick sanity check confirms that each metric’s `mean_change` is a finite number and that `method_used` is either `"bootstrap"` or `"wilcoxon"`.*  
  **File path(s)**: `code/validation/produce_smoke_results.py`, `data/results/smoke_results.json`  
  **Verification**: `pytest code/tests/test_smoke_analysis.py` validates JSON against `contracts/analysis.schema.yaml` and asserts non‑null numeric fields.

### Initial pipeline sanity check (Post-Simulation)

- [ ] T001a **Run a full end‑to‑end pipeline on the current (empty) data to produce a successful log.**  
  *Execute `python -m code.pipeline.run_all --config code/config/study_config.yaml` on the empty `data/raw/` (expected to abort with a clear validation error). Capture the error output and the resulting `results/pipeline.log`. Then, after populating minimal valid data (produced in T003a), re‑run the pipeline and capture a successful log.*  
  **File path(s)**: `results/pipeline.log` (both failure and success runs).  
  **Verification**: The success run ends with a line `STATUS: SUCCESS`; `tests/integration/test_full_run.py` asserts this line exists.

### Compliance processing  

- [ ] T004 **Process daily compliance logs, enforce plausibility, and produce aggregated compliance output (FR‑010).**  
  *Implement `code/compliance/compute_compliance.py` (module `code.compliance.compute_compliance`). The script:*  
  1. Loads all CSVs from `data/raw/compliance_logs/` (or the simulated counterpart).  
  2. Validates each row against `contracts/compliance.schema.yaml`; any out‑of‑range value raises an exception (no silent fallback).  
  3. Derives `is_compliant = (social_media_minutes ≤ 30) ∧ (news_consumption == False) ∧ (notifications_off == True)`.  
  4. Flags participants whose **entire** 7‑day record reports 0 minutes as “extreme” (retain them).  
  5. Writes `data/processed/aggregated_compliance.csv` (one row per participant) and `data/processed/compliance_flags.json` (list of extreme cases).  
  **File path(s)**: `code/compliance/compute_compliance.py`, `data/processed/aggregated_compliance.csv`, `data/processed/compliance_flags.json`  
  **Verification**: `pytest code/tests/test_compliance.py` must pass; running `python -m code.compliance.compute_compliance` exits with code 0 and appends a concise summary to `results/pipeline.log`.

### Data merging & change‑score computation  

- [ ] T005 **Merge baseline/post measurements with compliance data, handle attrition, and compute change scores (FR‑005).**  
  *Implement `code/pipeline/merge_data.py` (module `code.pipeline.merge_data`). The script:*  
  1. Loads `data/raw/measurement_records.csv` (or the simulated `measurement_records_sim.csv`).  
  2. Joins with `data/processed/aggregated_compliance.csv` on `participant_id`.  
  3. Detects participants missing any post‑intervention record; excludes them from paired tests but writes their baseline rows to `data/processed/descriptive_baseline.csv`.  
  4. Computes `change = post_value – baseline_value` for each metric, producing `data/processed/change_scores.csv` (columns: `participant_id`, `metric_type`, `change`).  
  5. Preserves original timestamps and `quality_flag` for reproducibility.  
  **File path(s)**: `code/pipeline/merge_data.py`, `data/processed/descriptive_baseline.csv`, `data/processed/change_scores.csv`  
  **Verification**: `pytest code/tests/test_merge.py` confirms correct arithmetic, proper dropout handling, and schema‑compliant output; `python -m code.pipeline.merge_data` exits with code 0 and logs summary to `results/pipeline.log`.

### Primary statistical analysis  

- [ ] T006 **Perform primary statistical analysis with bootstrap, fallback Wilcoxon, Cohen’s d, and Holm‑Bonferroni correction (FR‑006, FR‑007, FR‑008).**  
  *Implement `code/analysis/run_analysis.py` that reads `data/processed/change_scores.csv`.*  
  *For each of the four outcome metrics:*  
  1. Perform 10 000‑sample bootstrap of the mean change → 95 % CI.  
  2. Run Shapiro‑Wilk; if `p < 0.05`, fall back to Wilcoxon signed‑rank **but still report** Cohen’s d (bias‑corrected 95 % CI).  
  3. Compute Cohen’s d (or rank‑biserial if Wilcoxon fallback is used, per FR‑007).  
  4. After all metrics, apply Holm‑Bonferroni step‑down to the uncorrected p‑values.  
  5. Write `data/results/statistical_summary.json` containing one object per metric that conforms exactly to `contracts/analysis.schema.yaml`.  
  **File path(s)**: `code/analysis/run_analysis.py`, `data/results/statistical_summary.json`  
  **Verification**: `pytest code/tests/test_analysis.py` checks corrected p‑values ≥ uncorrected, CI containment, and schema compliance; execution logs are appended to `results/pipeline.log`.

- [ ] T006a **Verify family-wise error rate control (SC-005).**  
  *Implement `code/tests/test_fwer.py` that loads `data/results/statistical_summary.json` and asserts that p-values were corrected using the Holm-Bonferroni method (e.g., by verifying the step-down logic against the uncorrected p-values).*  
  **File path(s)**: `code/tests/test_fwer.py`  
  **Verification**: `pytest code/tests/test_fwer.py` must pass.

### Success‑criterion enforcement  

- [ ] T007 **Verify that all success‑criterion thresholds (SC‑001 – SC‑004) are met.**  
  *Create `code/tests/test_success_criteria.py` that loads `data/results/statistical_summary.json` and asserts for each metric:*  
  - `p_value_corrected < 0.05` **and** `effect_size_cohen_d >= 0.2`.  
  *If any metric fails, the test fails, making the criteria enforceable.*  
  **File path(s)**: `code/tests/test_success_criteria.py`  
  **Verification**: `pytest code/tests/test_success_criteria.py` must pass for the study to be accepted.

### Power simulation (FR‑011)  

- [ ] T008 **Monte‑Carlo power simulation to justify the planned sample size.**  
  *Implement `code/analysis/power_simulation.py` that repeats the full analysis pipeline on synthetic data 1 000 times with effect size `d = 0.5` (seed = 42). The script records the proportion of simulations where **all four** primary outcomes achieve Holm‑Bonferroni‑corrected significance (`p < 0.05`). It also performs an incremental search to find the smallest `N` yielding ≥ 80 % power.*  
  *Write `data/results/power_analysis.json` with keys `power_estimate` (float) and `required_n_for_80pct_power` (int).*  
  **File path(s)**: `code/analysis/power_simulation.py`, `data/results/power_analysis.json`  
  **Verification**: `pytest code/tests/test_power.py` confirms both keys exist and values are deterministic given the seed.

### Sensitivity analyses (practice effects & compliance bias)  

- [ ] T009 **Sensitivity analyses for practice effects and self‑report compliance bias (FR‑011).**  
  *Implement `code/analysis/sensitivity.py` that:*  
  1. Re‑runs the primary analysis after **excluding** participants whose overall compliance percentage < 50 % (self‑report quality check).  
  2. Simulates practice‑effect inflation by adding Gaussian noise (SD = 0.0, 0.2, 0.4) to baseline SART and Ospan scores (grid `practice_effect_grid` from the config), recomputes change scores, and records how effect sizes shift.  
  3. Writes a narrative `results/sensitivity_report.md` describing the limitation, presenting the grid results, and reiterating the associative framing.  
  4. Writes `results/sensitivity_analysis.json` summarizing effect‑size changes for each grid value.  
  **File path(s)**: `code/analysis/sensitivity.py`, `results/sensitivity_report.md`, `results/sensitivity_analysis.json`  
  **Verification**: `pytest code/tests/test_sensitivity.py` confirms the grid is applied correctly and that the markdown contains required sections; execution logs are appended to `results/pipeline.log`.

### Visualizations  

- [ ] T010 **Generate all required visualizations from validated outputs (FR‑011).**  
  *Implement `code/viz/generate_plots.py` that reads `data/results/statistical_summary.json` and `data/processed/change_scores.csv`.*  
  *Produce:*  
  - Histogram PDFs for change scores of each metric (`figures/hist_<metric>.png`).  
  - Forest plot of Cohen’s d with 95 % CIs (`figures/effect_sizes_forest.png`).  
  - Bar chart of compliance distribution (`figures/compliance_bar.png`).  
  **File path(s)**: `code/viz/generate_plots.py`, `figures/*.png`  
  **Verification**: `pytest code/tests/test_viz.py` asserts each expected PNG exists, is non‑zero size, and that plotted numeric values match those in `statistical_summary.json`; script execution is logged.

### Final report & explicit limitation discussion  

- [ ] T011 **Compile the final associative report, explicitly acknowledging design limitations.**  
  *Create `data/results/final_report.md` containing:*  
  1. **Methods** – references exact script versions, config file, and simulated vs. real data handling.  
  2. **Results** – a table mirroring `statistical_summary.json` (mean ± CI, corrected p, Cohen’s d).  
  3. **Figures** – embed all PNGs via markdown image links.  
  4. **Discussion** – explicitly state that the within‑subject pre/post design lacks a control group, that SART/Ospan are practice‑sensitive, and that observed changes are **associational** only. Summarize the sensitivity‑analysis findings (practice‑effect grid) and the self‑report compliance limitation (FR‑011).  
  5. **Paper‑stage handoff** – map each JSON key to the intended manuscript table/figure.  
  **File path(s)**: `data/results/final_report.md`  
  **Verification**: `pytest code/tests/test_report.py` checks that every statistic in the markdown matches the source JSON and that the discussion section contains the required limitation statements.

### Reproducibility & handoff verification  

- [ ] T012 **Run full pipeline from scratch and verify reproducibility (Phase 2 handoff).**  
  *Execute `python -m code.pipeline.run_all --config code/config/study_config.yaml` on the **real** (or simulated) dataset.*  
  *Confirm that `results/pipeline.log` ends with `STATUS: SUCCESS` and that all expected artifacts (`statistical_summary.json`, all PNGs, `final_report.md`, `checksum_verification.log`) are present.*  
  *Re‑run checksum verification (`sha256sum -c data/checksums.sha256`) and write the full output to `data/results/checksum_verification.log`; append `REPORT: COMPLETE` to `pipeline.log`.*  
  **File path(s)**: `results/pipeline.log`, `data/results/checksum_verification.log`, `data/results/final_report.md`, `figures/*`  
  **Verification**: `pytest code/tests/test_full_run.py` asserts the log ends with `STATUS: SUCCESS`, that artifact hashes match the manifest, and that no unexpected files are generated.

---

## Dependency & Requirement Mapping  

| Spec Requirement | Covered by Task(s) | Verification |
|------------------|--------------------|--------------|
| FR‑001 (IDs) | T001b | `test_recruitment.py` |
| FR‑002 / FR‑003 (SART, Ospan, PSS‑10, PANAS) | T001c, T001d, T002 | `test_scoring.py`, UI integration tests |
| FR‑004 (Compliance logging) | T001e, T004 | `test_compliance.py` |
| FR‑005 (Change scores) | T005 | `test_merge.py` |
| FR‑006 (Bootstrap / Wilcoxon) | T006 | `test_analysis.py` |
| FR‑007 (Effect size) | T006 | `test_analysis.py` |
| FR‑008 (Holm‑Bonferroni) | T006, T006a | `test_analysis.py`, `test_fwer.py` |
| FR‑009 (Pilot timing) | T000 | `test_pilot.py` |
| FR‑010 (Compliance plausibility) | T004 | `test_compliance.py` |
| FR‑011 (Sensitivity) | T008, T009 | `test_power.py`, `test_sensitivity.py` |
| SC‑001 – SC‑004 (Success criteria) | T007 | `test_success_criteria.py` |
| SC-005 (FWER control) | T006a | `test_fwer.py` |
| All other FRs & SCs | Distributed across tasks above | Corresponding test suites |

All tasks respect data‑flow ordering:  

`T000 → T001 → T001b‑T001e → T002 → T003a‑T003d → T001a → T004 → T005 → T006 → T006a → T007 → T008 → T009 → T010 → T011 → T012`.

---  

*All tasks remain unchecked until their respective verification steps succeed. Completing each will satisfy the specification, address reviewer concerns about practice effects and lack of a control condition, and produce a fully reproducible research pipeline.*