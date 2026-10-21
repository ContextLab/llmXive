# Tasks: The Impact of Digital Decluttering on Cognitive Performance and Well‑being

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/`, and the original research idea.  
The goal is to implement a reproducible pipeline that evaluates the **associational** (not causal) relationship between a one‑week digital declutter and cognitive/affective outcomes in a within‑subject pre/post design, per the Causal Interpretation Disclaimer in `plan.md`.

## Phase 0: Pilot Validation (pre‑recruitment)

- [ ] T000 [US1] Run a pre‑study pilot validation of SART and Ospan timing with **n=5** participants.  
  - Simulate 5 participants (or run a tiny live pilot) and record raw trial‑level responses.  
  - Verify that all response times are within **100 ms – 5000 ms**.  
  - Ensure that **SART accuracy ≥ 50 %**; flag any participant failing this as low‑attention.  
  - **Verification**: `pytest code/tests/test_pilot.py` must pass, confirming timing constraints and that the pilot data conform to `contracts/dataset.schema.yaml`. The pilot data are stored under `data/raw/pilot/` and are **not** used for the main analysis.

## Phase 1: Setup and First End‑to‑End Analysis  

- [ ] T001 [US1] Establish project layout, pinned dependencies, and create configuration files.  
  - Create the directory tree (`code/scoring/`, `code/analysis/`, `code/compliance/`, `code/viz/`, `code/validation/`, `code/pipeline/`, `code/tests/`, `data/raw/`, `data/processed/`, `data/results/`, `figures/`).  
  - Write `code/requirements.txt` (pinned versions) and `code/config/study_config.yaml` containing at least `seed: 42`, `n_participants: 80`, `bootstrap_resamples: 10000`, `practice_effect_grid: [0.0, 0.2, 0.4]`.  
  - **Verification**: Run `ls` or a simple script to confirm that all directories exist and that the two config files are present; capture the output in `data/results/pipeline.log`. The log must contain the line `SETUP: COMPLETE`.

- [ ] T002 [US1] Implement scoring functions for all four instruments and include quality‑flag logic.  
  - Add `code/scoring/sart.py`, `code/scoring/ospan.py`, `code/scoring/pss10.py`, `code/scoring/panas.py` following the OSF v2.1+ reference algorithms.  
  - Each scorer must output a single numeric score and a `quality_flag` (`valid`, `low_attention`, `missing`). For SART, flag `low_attention` when accuracy < 50 %; for all tasks, enforce response‑time limits 100 ms – 5000 ms (FR‑009).  
  - **Verification**: `pytest code/tests/test_scoring.py` must pass, confirming that (i) scores are numeric, (ii) quality flags are correctly assigned, and (iii) the resulting rows conform to `contracts/dataset.schema.yaml`.

- [ ] T003 [US1] Generate a deterministic seeded study simulation, validate raw artifacts, and produce a smoke‑results file.  
  - Implement `code/validation/simulate_study.py` (seeded with `np.random.seed(42)`) to create:  
    * `data/raw/participants.csv` (pseudonymous IDs `P001`‑`P080`).  
    * `data/raw/trial_level/sart_trials.csv` and `data/raw/trial_level/ospan_trials.csv` containing raw trial‑level responses.  
    * `data/raw/simulated_measurements.csv` with one row per participant per metric, already scored and annotated with `quality_flag` so that it **conforms** to `contracts/dataset.schema.yaml`.  
    * `data/raw/compliance_logs/` directory with seven daily CSV files per participant that satisfy `contracts/compliance.schema.yaml`.  
  - Implement `code/validation/generate_checksums.py` to compute SHA‑256 digests for **all** files under `data/raw/` and write `data/checksums.sha256` (format: `<hash>  <relative_path>`).  
  - Implement `code/validation/produce_smoke_results.py` that reads the simulated measurements, runs the bootstrap analysis (10 000 resamples) on the synthetic data, and writes `data/results/smoke_results.json` containing one entry per metric (SART, Ospan, PSS‑10, PANAS‑PA, PANAS‑NA) that matches `contracts/analysis.schema.yaml`.  
  - Add an entry‑point script `code/validation/run_all.py` that sequentially executes the three scripts above.  
  - **Verification**: Running `python -m code.validation.run_all` must (a) validate every generated file against its JSON‑Schema and print `PASS: <filename>` for each, (b) execute `sha256sum -c data/checksums.sha256` and print `OK` for every file, (c) pretty‑print the contents of `data/results/smoke_results.json`. All three sections must be captured in `data/results/pipeline.log` after the pipeline run.

- [ ] T004 [US2] Process daily compliance logs, enforce plausibility, and produce aggregated compliance output.  
  - Implement `code/compliance/compute_compliance.py` (exposed as a module `code.compliance.compute_compliance`). It must:  
    * Load all CSVs from `data/raw/compliance_logs/`.  
    * Validate each row against `contracts/compliance.schema.yaml`; any out‑of‑range value (e.g., `social_media_minutes` < 0 or > 1440) must raise an exception and abort – no silent correction.  
    * Derive `is_compliant` = (`social_media_minutes` ≤ 30) ∧ (`news_consumption` is False) ∧ (`notifications_off` is True).  
    * Flag participants whose **entire** 7‑day record is `0` minutes as “extreme” but retain them in the output.  
    * Write `data/processed/aggregated_compliance.csv` (one row per participant) and `data/processed/compliance_flags.json` containing any flagged cases.  
  - **Verification**: `pytest code/tests/test_compliance.py` must pass, and a direct execution `python -m code.compliance.compute_compliance` must exit with status 0 and append its stdout (including any flagged‑case summary) to `data/results/pipeline.log`.

- [ ] T005 [US3] Merge baseline/post measurements with compliance data, handle attrition, and compute change scores.  
  - Implement `code/pipeline/merge_data.py` (exposed as `code.pipeline.merge_data`). It must:  
    * Join `data/raw/simulated_measurements.csv` with `data/processed/aggregated_compliance.csv` on `participant_id`.  
    * Detect participants missing any **post‑intervention** record; exclude them from paired statistical tests but retain their baseline rows in `data/processed/descriptive_baseline.csv`.  
    * Compute `post – baseline` for each metric and write `data/processed/change_scores.csv` (columns: `participant_id`, `metric_type`, `change`).  
    * Preserve timestamps and quality flags for reproducibility.  
  - **Verification**: `pytest code/tests/test_merge.py` must confirm correct arithmetic, proper dropout exclusion, and schema‑compliant output. Direct execution `python -m code.pipeline.merge_data` must exit 0 and its summary (number of participants kept, number dropped) must be appended to `data/results/pipeline.log`.

- [ ] T006 [US3] Perform primary statistical analysis with bootstrapping and Holm‑Bonferroni correction.  
  - Implement `code/analysis/run_analysis.py` that reads `data/processed/change_scores.csv`. For each of the five metrics it must:  
    * Perform 10 000‑sample bootstrap of the mean change, yielding 95 % CI.  
    * Run Shapiro‑Wilk; if **p < 0.05**, fall back to Wilcoxon signed‑rank (method = “wilcoxon”). Otherwise use the bootstrap method (method = “bootstrap”).  
    * Compute Cohen’s d with its 95 % CI.  
    * After all metrics are processed, apply the Holm‑Bonferroni step‑down procedure to the uncorrected p‑values and store corrected values.  
    * Write `data/results/statistical_summary.json` containing one object per metric that conforms exactly to `contracts/analysis.schema.yaml`.  
  - **Verification**: `pytest code/tests/test_analysis.py` must verify (i) corrected p‑values are ≥ uncorrected, (ii) bootstrap CIs enclose the empirical mean, and (iii) the JSON file validates against the schema. Successful execution of `python -m code.analysis.run_analysis` must also be logged in `data/results/pipeline.log`.

- [ ] T007 [US3] Run a Monte‑Carlo power simulation to justify the planned sample size.  
  - Implement `code/analysis/power_simulation.py` which repeats the full analysis pipeline on synthetic data 1 000 times at an effect size `d = 0.5`. Use the same seed (`42`) for reproducibility.  
  * Record the proportion of simulations where all four primary outcomes achieve Holm‑Bonferroni‑corrected significance (p < 0.05).  
  * Output `data/results/power_analysis.json` with keys `power_estimate` (float) and `required_n_for_80pct_power` (int).  
  - **Verification**: `pytest code/tests/test_power.py` checks that the JSON contains both keys and that the values are deterministic given the seed.

- [ ] T008 [US3] Conduct sensitivity analyses addressing reviewer concerns about practice effects and self‑report bias.  
  - Implement `code/analysis/sensitivity.py` which:  
    * Re‑runs the primary analysis after excluding participants whose compliance percentage < 50 % (self‑report quality check).  
    * Simulates practice‑effect inflation by adding Gaussian noise with SD values from `practice_effect_grid` (0.0, 0.2, 0.4) to the baseline SART and Ospan scores, re‑computes change scores, and records how effect sizes shift.  
    * Writes a narrative `data/results/sensitivity_report.md` that (a) describes the limitation of self‑reported compliance (FR‑011), (b) presents the grid results, and (c) reiterates the associative framing per the disclaimer.  
    * Writes `data/results/sensitivity_analysis.json` summarizing the effect‑size changes for each grid value.  
  - **Verification**: `pytest code/tests/test_sensitivity.py` must confirm the grid is applied correctly and that the markdown report contains the required sections. Execution `python -m code.analysis.sensitivity` must exit 0 and its concise stdout be appended to `data/results/pipeline.log`.

- [ ] T009 [US3] Generate all required visualizations from validated outputs.  
  - Implement `code/viz/generate_plots.py` that reads `data/results/statistical_summary.json` and `data/processed/change_scores.csv`. It must produce:  
    * Histogram PDFs for change scores of each metric (`figures/hist_<metric>.png`).  
    * A forest plot of Cohen’s d with 95 % CIs (`figures/effect_sizes_forest.png`).  
    * A compliance‑distribution bar chart (`figures/compliance_bar.png`).  
  - **Verification**: `pytest code/tests/test_viz.py` asserts that each expected PNG file exists, has non‑zero size, and that the plotted numeric values match those in `statistical_summary.json`. Successful execution `python -m code.viz.generate_plots` must be logged.

- [ ] T010 [US3] Compile the final associative report, perform a final checksum verification, and hand off to the paper pipeline.  
  - Write `data/results/final_report.md` that includes:  
    * A methods section referencing the exact script versions and config used.  
    * A results table mirroring `statistical_summary.json` (mean ± CI, corrected p, Cohen’s d).  
    * All figures produced in T009 embedded via markdown image links.  
    * A discussion that explicitly frames findings as **associational**, acknowledges practice‑effect possibilities (per reviewer), and documents the self‑report limitation (FR‑011).  
    * A “Paper‑stage handoff” subsection mapping each JSON key to the intended manuscript table/figure.  
  - Run `sha256sum -c data/checksums.sha256` again and write the verification output to `data/results/checksum_verification.log`. Append a line `REPORT: COMPLETE` to `data/results/pipeline.log`.  
  - **Verification**: `pytest code/tests/test_end_to_end.py` must (i) re‑run the `quickstart.md` command, (ii) confirm that every statistic in `final_report.md` matches the source JSON, and (iii) check that `checksum_verification.log` ends with `OK`. The pipeline log must contain the final `REPORT: COMPLETE` marker.

- [ ] T011 [US3] End‑to‑end reproducibility verification.  
  - Execute the full pipeline after all previous tasks have succeeded: `python -m code.pipeline.run_all --config code/config/study_config.yaml`.  
  - Verify that `data/results/pipeline.log` exists, contains the `STATUS: SUCCESS` line, and that all expected output artifacts (`statistical_summary.json`, plots, final report, etc.) are present.  
  - **Verification**: `pytest code/tests/test_full_run.py` asserts that the log ends with `STATUS: SUCCESS` and that the artifact hash manifest matches the recorded checksums.

## Phase 2: Complete the study and validate its evidence  

*(Tasks T004‑T010 already listed above; ordering respects data flow.)*

## Phase 3: Reproducible results and paper handoff  

(Tasks T009, T010, and T011 already cover generation of reproducible artefacts and the handoff; no additional tasks are required in this phase.)

## Dependencies and requirement coverage  

| Specification Requirement | Covered by Task(s) | Verification |
|---------------------------|--------------------|--------------|
| FR‑001 – participant IDs | T003, T004 | schema validation of `participants.csv` |
| FR‑002 / FR‑003 – SART & Ospan scoring | T002, T003 | `test_scoring.py` |
| FR‑004 – daily compliance logging | T004 | `test_compliance.py` |
| FR‑005 – change‑score calculation | T005 | `test_merge.py` |
| FR‑006 – bootstrap primary, Wilcoxon fallback | T006 | `test_analysis.py` |
| FR‑007 – Cohen’s d with CI | T006 | `test_analysis.py` |
| FR‑008 – Holm‑Bonferroni | T006 | `test_analysis.py` |
| FR‑009 – pilot validation of task timing | T000, T002, T003 | `test_pilot.py` |
| FR‑010 – plausibility of compliance entries | T004 | `test_compliance.py` |
| FR‑011 – sensitivity to self‑report bias | T008 | `test_sensitivity.py` |
| SC‑001 – SC‑005 (success criteria) | T006, T009, T010 | final report & statistical summary |
| Reproducibility (checksums, logs) | T001, T003, T010, T011 | pipeline log checks |

**Execution order (data‑flow respected)**:  
T000 → T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011.  

All tasks are unchecked pending successful implementation and verification.  