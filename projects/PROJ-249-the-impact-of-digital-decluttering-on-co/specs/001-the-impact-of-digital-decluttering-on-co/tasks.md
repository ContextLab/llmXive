# Tasks: The Impact of Digital Decluttering on Cognitive Performance and Well‑being

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, the three JSON‑schema contracts, the original idea, and the latest reviewer feedback.  
The goal is to produce a fully reproducible end‑to‑end pipeline that runs on the seeded simulation, generates real‑world‑shaped artefacts, validates every file against its schema, and records all checksums and logs required by the constitution.

---

- [ ] **T001** [P] [US1] Establish project layout, configuration, pinned dependencies, and checksum manifest; produce a successful end‑to‑end run log as evidence.  
  - Create the directory tree `code/`, `code/scoring/`, `code/analysis/`, `code/compliance/`, `code/viz/`, `code/tests/`, `data/raw/`, `data/processed/`, `data/results/`, `figures/`.  
  - Write `code/config/study_config.yaml` with the keys `seed`, `n_participants`, `dropout_rate`, `effect_sizes`, `practice_effect_grid`, `bootstrap_resamples`, `start_date`, `pilot_n`.  
  - Write `code/requirements.txt` (pinned versions) and `quickstart.md` documenting the command  
    ```bash
    python -m code.pipeline.run_all --config code/config/study_config.yaml
    ```  
  - Initialise `data/checksums.sha256` (empty file).  
  - **Verification**: Run the documented command on a fresh clone; capture the full stdout/stderr into `data/results/run_log.txt`. The log must end with the line `STATUS: SUCCESS`. Add `run_log.txt` to `data/checksums.sha256`. A passing `pytest -q` run (including the sanity test in `code/tests/test_quickstart.py`) is also recorded in the log.

- [ ] **T002** [US1] Implement instrument scoring functions with OSF‑reference logic and synthetic pilot check.  
  - Files: `code/scoring/sart.py`, `code/scoring/ospan.py`, `code/scoring/pss10.py`, `code/scoring/panas.py`.  
  - Unit tests in `code/tests/test_scoring.py` cover range bounds, low‑attention flagging, and a synthetic pilot of 5 participants generated from the config.  
  - **Verification**: `pytest code/tests/test_scoring.py` passes; scoring functions return values that satisfy the `contracts/dataset.schema.yaml` when applied to the trial‑level files produced by T003.

- [ ] **T003** [US1] Generate deterministic seeded study simulation and produce raw artefacts; validate schema, checksums, and smoke results.  
  - Implement `code/validation/simulate_study.py` that reads `code/config/study_config.yaml` and creates:  
    * `data/raw/participants.csv` (Participant registry, IDs `P001` …).  
    * `data/raw/trial_level/sart_trials.csv` and `data/raw/trial_level/ospan_trials.csv` (per‑trial response data).  
    * `data/raw/simulated_measurements.csv` (scored single‑value records conforming to `contracts/dataset.schema.yaml`).  
    * `data/raw/compliance_logs/` directory with one CSV per participant following `contracts/compliance.schema.yaml`.  
  - Append SHA‑256 digests for every new file to `data/checksums.sha256`.  
  - Run the scoring functions (T002) on the trial files to produce `data/raw/simulated_measurements.csv`.  
  - Generate a thin “smoke” analysis output `data/results/smoke_results.json` containing one entry per metric (SART, Ospan, PSS‑10, PANAS‑PA, PANAS‑NA) with realistic mean‑change values derived from the simulation.  
  - **Verification**:  
    * `jsonschema.validate` against `contracts/dataset.schema.yaml` for every row in `simulated_measurements.csv`.  
    * `jsonschema.validate` against `contracts/analysis.schema.yaml` for each object in `smoke_results.json`.  
    * `sha256sum -c data/checksums.sha256` returns no errors.  
    * A pytest suite `code/tests/test_simulation.py` checks deterministic IDs, value ranges, and that the smoke file contains the required fields.

- [ ] **T004** [US2] Implement the compliance‑log pipeline and validation.  
  - `code/compliance/parse_logs.py` reads all CSVs under `data/raw/compliance_logs/`, enforces the plausibility rule `0 ≤ social_media_minutes ≤ 1440`, derives `is_compliant` (`social_media_minutes ≤ 30` **and** `news_consumption == False` **and** `notifications_off == True`).  
  - Outputs: `data/processed/aggregated_compliance.csv` (one row per participant with weekly compliance %), `data/processed/compliance_flags.json` (participants flagged for implausible entries or extreme “0‑minute all‑7‑days” case).  
  - Append both files to `data/checksums.sha256`.  
  - **Verification**: `pytest code/tests/test_compliance.py` covers compliant, non‑compliant, out‑of‑range, and extreme cases; checksum verification passes.

- [ ] **T005** [US3] Merge raw measurements with compliance, handle drop‑outs, and compute change scores.  
  - `code/pipeline/merge_data.py` performs:  
    * Join `data/raw/simulated_measurements.csv` with `data/processed/aggregated_compliance.csv` on `participant_id`.  
    * Exclude participants lacking a post‑intervention record (drop‑out) from paired analyses, but retain their baseline rows in `data/processed/descriptive_baseline.csv`.  
    * Apply low‑attention flags from T002 (SART accuracy < 50 %).  
    * Write `data/processed/exclusions.json` (reason for each exclusion).  
    * Compute `post − baseline` for every metric and write `data/processed/change_scores.csv`.  
  - Append the three new files to `data/checksums.sha256`.  
  - **Verification**: `pytest code/tests/test_merge.py` asserts correct exclusion logic, correct arithmetic for change scores, and that missing files raise an explicit error (no silent fallback). Checksum validation succeeds.

- [ ] **T006** [US3] Run primary statistical analysis with bootstrap, fallback, effect sizes, and Holm‑Bonferroni correction.  
  - Implement `code/analysis/run_analysis.py` which reads `data/processed/change_scores.csv` and:  
    * For each metric, perform 10 000 bootstrap resamples to obtain mean change and 95 % CI.  
    * If bootstrap fails to converge (e.g., zero variance), fall back to a Wilcoxon signed‑rank test (per FR‑006 amendment).  
    * Compute Cohen’s d with 95 % CI.  
    * Apply Holm‑Bonferroni correction across the five hypothesis tests (SART, Ospan, PSS‑10, PANAS‑PA, PANAS‑NA).  
    * Write `data/results/statistical_summary.json` conforming to `contracts/analysis.schema.yaml`.  
  - Append the JSON file to `data/checksums.sha256`.  
  - **Verification**: `pytest code/tests/test_analysis.py` includes a known‑effect simulation where corrected p < 0.05 and a null‑effect simulation where it does not; schema validation passes; CI bounds contain the empirical mean; correction applied to exactly five tests.

- [ ] **T007** [US1] Run Monte‑Carlo power simulation to estimate required sample size.  
  - `code/analysis/power_simulation.py` reads `code/config/study_config.yaml`, repeats the full analysis pipeline 1 000 times with effect size d = 0.5, and records the proportion of simulations achieving Holm‑Bonferroni‑corrected significance.  
  - Output `data/results/power_analysis.json` with keys `power_estimate`, `iterations`, `effect_size`, and `required_n_for_80pct_power`.  
  - Append the file to `data/checksums.sha256`.  
  - **Verification**: `pytest code/tests/test_power.py` checks reproducibility (fixed seed) and that the JSON contains all required keys; checksum validation succeeds.

- [ ] **T008** [US3] Add sensitivity and robustness checks, documenting limitations.  
  - `code/analysis/sensitivity.py` performs three sub‑analyses:  
    1. Re‑run primary analysis excluding participants with compliance < 50 %.  
    2. Apply the practice‑effect grid `[0.0, 0.2, 0.4]` SD to SART and Ospan scores, re‑estimate effects, and report how conclusions shift.  
    3. Write a markdown report `data/results/sensitivity_report.md` that explains the self‑report compliance limitation (FR‑011) and the absence of a control condition (per reviewer comment).  
  - Write `data/results/sensitivity_analysis.json` summarising the three scenarios (effect sizes, p‑values, whether each meets SC‑001–SC‑004).  
  - Append both new artefacts to `data/checksums.sha256`.  
  - **Verification**: `pytest code/tests/test_sensitivity.py` asserts the exact three‑value grid is used, that low‑compliance participants are filtered correctly, and that the markdown file contains the required limitation discussion; checksum validation passes.

- [ ] **T009** [US3] Generate figures directly from validated outputs.  
  - `code/viz/generate_plots.py` reads `data/processed/change_scores.csv` and `data/results/statistical_summary.json` and produces:  
    * `figures/change_distribution_SART.png`, `figures/change_distribution_Ospan.png`, `figures/change_distribution_PSS-10.png`, `figures/change_distribution_PANAS-PA.png`, `figures/change_distribution_PANAS-NA.png` (histograms of change scores).  
    * `figures/effect_sizes_forest.png` (forest plot with CIs for all five metrics).  
  - Append all PNGs to `data/checksums.sha256`.  
  - **Verification**: `pytest code/tests/test_viz.py` checks that each PNG file exists, is non‑empty, and that the plotted values match those in `statistical_summary.json`; checksum validation succeeds.

- [ ] **T010** [P] [US3] Compile the final results report and perform a full checksum re‑verification.  
  - Write `data/results/final_report.md` that:  
    * Summarises methods (scoring, bootstrap, Holm‑Bonferroni over five tests, power analysis, sensitivity checks).  
    * Presents a table of change‑score statistics (mean ± CI, corrected p, Cohen’s d) linking each number to the corresponding entry in `statistical_summary.json`.  
    * Embeds all figures generated in T009.  
    * Evaluates each success criterion SC‑001 – SC‑005 in the **association** framing (effect size ≥ 0.2 and Holm‑Bonferroni‑corrected p < 0.05).  
    * Includes a “Paper‑stage handoff” section that lists required manuscript sections, figure/table numbers, and the location of the JSON summary for downstream authors.  
  - Re‑run `sha256sum -c data/checksums.sha256` and capture the output in `data/results/checksum_verification.log`; the log must end with `ALL CHECKSUMS VERIFIED`.  
  - **Verification**: `pytest code/tests/test_end_to_end.py` runs the command from `quickstart.md` on a clean checkout, asserts that `final_report.md` contains the required sections, that every statistic matches the JSON, and that the checksum verification log reports success.

--- 

**Dependency matrix**

| Requirement | Covered by task(s) |
|-------------|-------------------|
| FR‑001 – FR‑003 (recruitment, scoring) | T001, T002, T003 |
| FR‑004 – FR‑010 (compliance, change scores, validation) | T004, T005, T006 |
| FR‑011 (sensitivity) | T008 |
| SC‑001 – SC‑005 (effect‑size, significance, correction) | T006, T007, T008, T010 |
| Data‑model & contracts | T002, T003, T004, T005, T006, T008 |
| Reproducibility (seed, checksum, log) | T001, T003, T004, T005, T006, T007, T008, T009, T010 |

All tasks respect the data‑flow ordering: layout → scoring → simulation → compliance → merge → analysis → power → sensitivity → visualisation → final report.
