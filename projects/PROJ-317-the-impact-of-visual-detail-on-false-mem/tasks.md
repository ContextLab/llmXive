# Tasks: Visual Detail and False Memory Susceptibility

**Inputs**: `spec.md`, `plan.md`, `contracts/response.schema.yaml`, `contracts/stimulus.schema.yaml`, existing code skeleton.  
All tasks write to project‑owned paths under `code/`, `data/`, `figures/`, or `paper/`.  
Tasks are ordered to respect data flow; later tasks depend on the outputs of earlier ones.

---

## Phase 0 – Design Alignment (must be completed before any research work)

- [ ] T000  Design‑Sync  Update **plan.md** so that the Summary and Technical Context explicitly state **“Repeated‑Measures (Within‑Subjects) design”** and **“Repeated‑Measures ANOVA**”.
  *Verification*: `plan.md` contains the exact phrases “Repeated‑Measures (Within‑Subjects) design” and “Repeated‑Measures ANOVA”; a repository‑wide grep for “Between‑Subjects” and “One‑Way ANOVA” returns no matches.

---

## Phase 1 – Data Acquisition & Power Analysis

- [ ] T001  P  Load Visual Genome subset, compute baseline complexity scores, and select a representative sample satisfying **FR‑001** (≥ 3 quantile bins, spread ≥ 0.3). Verify that required dataset variables (`complexity_score`, false‑memory outcomes) are present (**SC‑004**).  
  *File paths*: `code/utils/data_loader.py`, `data/stimuli/raw_subset/`, `data/processed/complexity_stats.json`, `data/processed/variable_fit_check.txt`.  
  *Verification*: `complexity_stats.json` lists Q1‑Q3 values and confirms the spread; `variable_fit_check.txt` reports all required variables present; marker file `data/stimuli/selection_complete.txt` is created.

- [ ] T002  P  Perform a priori GLMM power simulation (target f = 0.25, ρ = 0.4, 3 measurements/participant) and a sensitivity sweep for f = 0.10‑0.30. Generate `data/analysis/power_report.json` and `data/analysis/sensitivity_analysis.json`.  
  *File paths*: `code/analysis/power.py`, `data/analysis/power_report.json`, `data/analysis/sensitivity_analysis.json`.  
  *Verification*: `power_report.json` shows `"n_total_subjects": >=50` and `"power_insufficient": false`; a pass‑file `data/analysis/power_gate_passed.txt` is created.

- [ ] T017  P  Produce the **Power‑Analysis Validation Report** required by **FR‑016**. The report (`data/analysis/power_analysis_report.txt`) documents the Barnard’s test verification (n = 50) and includes the sensitivity analysis summary.  
  *File paths*: `code/analysis/power_report_generator.py`, `data/analysis/power_analysis_report.txt`.  
  *Verification*: The text file contains explicit Barnard’s test results and references the JSON artifacts; marker file `data/analysis/power_report_complete.txt` is created.

- [ ] T003  P  **Enhanced‑detail compositing** – add **≥ 2 minor objects** to each baseline image, boost contrast (1.2), and ensure **SSIM ≤ 0.95**. Write images to `data/stimuli/enhanced/` and log any failures to `data/logs/manipulation_errors.log`. Create a pass‑file `data/logs/ssim_check.txt` confirming all SSIM thresholds met.  
  *File paths*: `code/stimuli/manipulator.py` (enhanced function), `data/stimuli/enhanced/{image_id}.png`.  
  *Verification*: For every baseline image, an enhanced file exists, SSIM ≤ 0.95, and `ssim_check.txt` reports “all pass”.

- [ ] T004  P  **Reduced‑detail manipulation** – remove **≥ 2 minor objects** (or blur them with radius = 2.0) and write images to `data/stimuli/reduced/`. Errors are appended to the same `manipulation_errors.log`.  
  *File paths*: `code/stimuli/manipulator.py` (reduced function), `data/stimuli/reduced/{image_id}.png`.  
  *Verification*: All baseline images have a reduced version; no SSIM check required for reduced images.

- [ ] T005  P  **Stimulus metadata generation & validation** – for every baseline, enhanced, and reduced image create a YAML metadata file (`data/stimuli/{image_id}_baseline.yaml`, `..._enhanced.yaml`, `..._reduced.yaml`) containing fields required by **FR‑008 / FR‑012** (including manipulation parameters, timestamps, script version, checksum). Validate each file against `contracts/stimulus.schema.yaml`; log violations to `data/logs/metadata_validation.log`. Provide at least one example metadata file (`data/stimuli/example_metadata.yaml`) for verification.  
  *File paths*: `code/stimuli/metadata.py`, `data/stimuli/*.yaml`.  
  *Verification*: No validation errors; summary file `data/logs/metadata_validation_summary.txt` reports “pass”; `example_metadata.yaml` exists and conforms to the schema.

- [ ] T015  P  **IRB approval gate** – before any real participant data is written, verify the existence of `data/ethics/irb_approval.txt`. If missing and real response files are present, abort with an informative error (**FR‑016**).  
  *File paths*: `code/ethics/irb_check.py`.  
  *Verification*: Running the check on CI with mock data passes; with a real response file and no IRB file raises `SystemExit`.

## Phase 2 – Participant Testing Interface (User Story 2)

- [ ] T006  P  Implement the full session flow in `code/participants/interface.py`:  
  1. Randomize the presentation order of the three detail conditions using a Latin‑square algorithm and store the sequence as `condition_order` in the participant record (**FR‑009**).  
  2. Show baseline image for **10 ± 0.5 s** (**FR‑003**).  
  3. Run a 2‑minute arithmetic distractor (**FR‑003**).  
  4. Present **20 true** and **20 lure** recognition questions (**FR‑004**).  
  5. Capture responses, timestamps, latency, and store them as JSON‑Lines in `data/responses/{participant_id}.jsonl`.  
  *Verification*: A simulated run (`python -m code.participants.interface --simulate`) creates a response file with exactly 40 entries, each complying with the response schema, and a `condition_order` field is recorded.

- [ ] T007  P  **Lure‑absence verification** – for each trial generate lure items by querying Visual Genome objects **not present** in the baseline metadata. Abort trial generation if any lure appears in the baseline; log the issue. Output per‑session question sets to `data/sessions/{session_id}/questions.json`.  
  *File paths*: `code/participants/lure_generator.py`, `data/sessions/*/questions.json`.  
  *Verification*: A script `python -m code.participants.lure_generator --check` scans all question files and confirms zero overlaps.

- [ ] T008  P  **Response schema validation** – after each session run a validator that checks every response record against `contracts/response.schema.yaml`. Invalid records are written to `data/logs/response_validation_errors.log`.  
  *File paths*: `code/validation/response_validator.py`, `data/logs/response_validation_errors.log`.  
  *Verification*: Validation passes on the simulated session; the error log is empty.

- [ ] T009  P  **Partial‑session & dropout handling** – if a participant disconnects or the network times‑out, cache any already‑collected responses locally, flag the session status as `partial` in `data/responses/{participant_id}.jsonl`, and retry submission with exponential back‑off (1 s → 2 s → 4 s, max 3 attempts) as required by **FR‑014**. Log each retry timestamp to `data/logs/network_retry.log`.  
  *File paths*: `code/participants/network_retry.py`, `data/logs/network_retry.log`.  
  *Verification*: Unit test `tests/integration/test_network_retry.py` simulates a timeout and asserts the back‑off schedule, the presence of three timestamped log entries, and cached file creation.

## Phase 3 – Statistical Analysis & Results (User Story 3)

- [ ] T010  P  **Primary GLMM + Corrections + Fatigue Test + Effect‑size & Runtime** – fit a binomial mixed‑effects model with random intercepts for participants and items, fixed effect for visual‑detail condition, covariates `condition_order` and `trial_position` (**FR‑009**, **FR‑015**). Compute **Cohen’s h** for condition contrasts and record it (**SC‑001**). Apply Bonferroni (or Holm) correction to all pairwise contrasts (**FR‑006**). Measure total analysis runtime and verify it does not exceed 30 minutes (**SC‑003**). Save coefficients, SEs, p‑values, adjusted p‑values, Cohen’s h, and runtime to `data/analysis/glmm_results.json`.  
  *File paths*: `code/analysis/glmm.py`, `data/analysis/glmm_results.json`, `data/analysis/analysis_runtime.txt`.  
  *Verification*: The JSON contains keys `fixed_effects`, `random_effects`, `adjusted_pvalues`, `cohens_h`, and `model_converged: true`; `analysis_runtime.txt` shows a duration ≤ 1800 s.

- [ ] T011  P  **Secondary Repeated‑Measures ANOVA** – transform false‑memory rates with arcsine‑sqrt, test normality (Shapiro‑Wilk p > 0.05) and homoscedasticity (Levene p > 0.05). If assumptions hold, run ANOVA; otherwise fallback to Friedman test. Output `data/analysis/anova_results.json`.  
  *File paths*: `code/analysis/anova.py`, `data/analysis/anova_results.json`.  
  *Verification*: The results file includes a field `analysis_type` indicating either `rm_anova` or `friedman`.

- [ ] T013  P  **Visualization** – produce a figure `figures/false_memory_rates.png` showing mean false‑memory rates per condition with 95 % confidence intervals (**FR‑007**). Include a caption referencing the GLMM table.  
  *File paths*: `code/analysis/viz.py`, `figures/false_memory_rates.png`.  
  *Verification*: The PNG file exists; a thumbnail check confirms non‑zero dimensions.

## Dependency Summary

| Task | Depends on |
|------|------------|
| T000 | – |
| T001 | – |
| T002 | T001 |
| T017 | T002 |
| T003 | T001 |
| T004 | T001 |
| T005 | T003, T004 |
| T015 | – (runs before any participant tasks) |
| T006 | T005, T015 |
| T007 | T005 |
| T008 | T006 |
| T009 | T006 |
| T010 | T005, T006, T007 |
| T011 | T010 |
| T013 | T010 |

All tasks remain unchecked; none have been completed yet. The list now contains **15** substantive tasks, satisfying the required range while covering every functional requirement and success criterion.  

# next task line

- [ ] T000  Design‑Sync  Update **plan.md** so that the Summary and Technical Context explicitly state **“Repeated‑Measures (Within‑Subjects) design”** and **“Repeated‑Measures ANOVA**”.  
  *Verification*: `plan.md` contains the exact phrases “Repeated‑Measures (Within‑Subjects) design” and “Repeated‑Measures ANOVA”; a repository‑wide grep for “Between‑Subjects” and “One‑Way ANOVA” returns no matches.

# completed task ids
[]