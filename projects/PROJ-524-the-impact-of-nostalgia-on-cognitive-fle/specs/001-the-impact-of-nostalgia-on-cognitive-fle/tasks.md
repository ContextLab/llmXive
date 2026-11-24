# Tasks: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

**Inputs**: `spec.md`, `plan.md`, existing code and data directories, reviewer feedback, and the requirement that the study be a deterministic simulation (no real WCST‑nostalgia dataset exists).

## Phase 1 – Setup and first end‑to‑end analysis (simulation‑first)

- [ ] **T001** [US1][FR‑004][FR‑005] **Update specification to match the methodological plan**  
  - Edit `specs/001-nostalgia-cognitive-flexibility/spec.md`  
    - Change **FR‑004** wording from “Cohen’s d” to **“Hedges’ g (bias‑corrected, non‑pooled variance)”**.  
    - Change **FR‑005** borderline band to **corrected p ∈ [0.020, 0.030]** (±0.005 around the Bonferroni‑corrected α = 0.025).  
    - Add a short rationale paragraph referencing the plan’s “kick‑back notes”.  
  - **Verification**: `grep "Hedges' g" spec.md` and `grep "\[0\.020, 0\.030\]" spec.md` succeed; unit test `tests/unit/test_spec_updates.py` checks that the rationale paragraph is present.

- [ ] **T002** [US1][FR‑001][FR‑006] **Deterministic simulation data generator**  
  - Implement `code/ingestion.py` with a `generate_simulated_wcst(seed=42, n_per_group=128)` function that creates a CSV `data/raw/simulated_dataset.csv` containing the columns required by `contracts/dataset.schema.yaml` (including optional `MMSE`, `education_years`, `gender`).  
  - Write accompanying `data/raw/metadata.json` with keys: `"simulation_mode": true`, `"seed": 42`, `"generated_rows": 256`, and a SHA‑256 checksum of the CSV.  
  - **Verification**: Running `python -m code.ingestion` produces the two files; a pytest `test_simulation_output` checks row count, age ≥ 65, and reproducible seed.

- [ ] **T003** [FR‑001][FR‑006] **Checksum recording and stimulus integrity stub**  
  - Add utility `code/utils.py` that computes SHA‑256 for any file and writes a manifest `data/raw/checksums.json` (entries for `simulated_dataset.csv` and any placeholder stimulus files under `data/stimuli/`).  
  - If `data/stimuli/` is empty, write `{ "status": "absent" }` and log a warning in `data/raw/metadata.json`.  
  - **Verification**: `tests/unit/test_checksums.py` confirms the manifest contains a matching hash for the CSV.

- [ ] **T004** [US1][FR‑001][FR‑006] **Cleaning and validation of the simulated dataset**  
  - Implement `code/cleaning.py` with `clean_dataset(input_path, output_path)` that:
    1. Loads `data/raw/simulated_dataset.csv`.  
    2. Filters out rows where `age` < 65 or missing (FR‑001).  
    3. Filters out rows with missing `perseverative_errors` or `categories_completed`.  
    4. If the `MMSE` column exists, excludes rows where `MMSE` < 24 (FR‑006) and records a flag `has_mmse: true` in `data/processed/mmse_flag.json`; otherwise sets `has_mmse: false`.  
    5. Writes the cleaned file to `data/processed/cleaned_dataset.csv` and an exclusion summary to `data/processed/exclusion_log.json`.  
  - **Verification**: Unit tests `test_clean_age_filter` and `test_clean_mmse_filter` pass; the exclusion log totals equal the number of dropped rows.

## Phase 2 – Complete the study and validate its evidence

- [ ] **T005** [US2][FR‑002][FR‑003][FR‑004] **Statistical analysis pipeline**  
  - Implement `code/analysis.py` with `run_welch_analysis(clean_path, out_path)` that:
    1. Reads `data/processed/cleaned_dataset.csv`.  
    2. Splits by `stimulus_type` (nostalgia vs. control).  
    3. For each outcome (`perseverative_errors`, `categories_completed`):
       - Performs Welch’s independent‑samples t‑test (`scipy.stats.ttest_ind(..., equal_var=False)`).  
       - Computes **Hedges’ g** with 95 % confidence intervals (bias‑corrected).  
    4. Applies **Bonferroni correction** across the two outcomes (α = 0.025).  
    5. Flags “sensitive” when a corrected p‑value falls in **[0.020, 0.030]** (FR‑005).  
    6. Writes a list of result objects to `data/results/statistical_report.json` conforming to `contracts/output.schema.yaml` and sets `"validity_status": "simulation"`.  
  - **Verification**: Integration test `tests/integration/test_analysis.py` checks that the JSON file contains exactly two entries, each with non‑null fields and the correct `significance_status` values.

- [ ] **T006** [US3][FR‑005] **Threshold‑sweep sensitivity analysis**  
  - Implement `code/sensitivity.py` with `run_sensitivity(report_path, out_path)` that loads the raw p‑values from `statistical_report.json` and evaluates significance at thresholds **0.01**, **0.025**, and **0.05** (Bonferroni‑corrected).  
  - Produce `data/results/sensitivity_report.json` – an array of objects `{ "outcome": "...", "threshold": ..., "significance_status": "significant"/"non‑significant" }`.  
  - Also add a top‑level flag `"is_sensitive_to_threshold": true` if any outcome’s corrected p‑value lies in the borderline band.  
  - **Verification**: Unit test `test_sensitivity_band` asserts that the flag is true for the seeded data (by construction).

- [ ] **T007** [FR‑007] **Runtime monitoring wrapper**  
  - Add `code/runtime_monitor.py` exposing `monitor(func, *args, **kwargs)` which records wall‑clock time; if total runtime > 6 hours (21 600 s) it logs a warning `WARN_RUNTIME_EXCEEDED` and appends the message to `data/results/runtime_log.json` while still returning the original result.  
  - Modify `code/main.py` to invoke the full pipeline (`ingestion → cleaning → analysis → sensitivity`) through this monitor.  
  - **Verification**: Mocked test `tests/unit/test_runtime_monitor.py` forces a long runtime and checks that the warning appears in the JSON log.

- [ ] **T008** [FR‑001–FR‑006] **Contract validation of all output artifacts**  
  - Extend `tests/contract/validate_output.py` to iterate over `data/results/*.json` and validate each against `contracts/output.schema.yaml` using `jsonschema.validate`.  
  - Write a summary `data/results/schema_validation_log.json` with `"passed": true` and timestamps.  
  - **Verification**: Running `pytest -k validation` yields success; the log file is non‑empty.

- [ ] **T012** [US2][FR‑004] **A priori power analysis and documentation**  
  - Implement `code/power_analysis.py` that computes the required sample size per group for a two‑sample Welch test given effect size d = 0.5, α = 0.05, power = 0.80 (using `statsmodels.stats.power.TTestIndPower`).  
  - Record the calculated n per group and the rationale (including the seed and simulation assumptions) in `data/raw/power_analysis.json` and append a summary to `data/raw/metadata.json`.  
  - **Verification**: Unit test `test_power_calculation` checks that the reported n matches the analytical result (≈128) and that the JSON file exists.

- [ ] **T013** [US2][FR‑002] **Covariate‑adjusted linear model**  
  - Extend `code/analysis.py` with `run_adjusted_model(clean_path, out_path)` that fits an OLS model predicting each outcome from `stimulus_type` plus covariates `education_years` and `gender`.  
  - Record adjusted effect size, standard error, and p‑value in a new entry of `statistical_report.json` with `"adjustment_status": "adjusted"`.  
  - **Verification**: Integration test `tests/integration/test_adjusted_model.py` validates that the adjusted entry exists and conforms to the output schema.

- [ ] **T014** [US1][FR‑001] **Generate and archive raw WCST trial‑by‑trial logs**  
  - Enhance `code/ingestion.py` to also produce `data/raw/trial_logs/` containing one CSV per participant (named `<participant_id>_trials.csv`) with simulated trial‑by‑trial data (e.g., trial number, stimulus presented, response correctness).  
  - Update `data/raw/metadata.json` with a pointer to the logs directory and compute a SHA‑256 manifest `data/raw/trial_logs_checksums.json`.  
  - **Verification**: Unit test `test_trial_logs_presence` confirms that for every participant a corresponding trial‑log file exists and that its checksum matches the manifest.

- [ ] **T015** [FR‑001] **Fix ingestion script failure (T101)**  
  - Debug and correct `code/ingestion.py` so that the script runs without error, properly writes the simulated dataset and associated metadata, and returns exit code 0.  
  - Add a regression test `tests/unit/test_ingestion_success.py` that invokes the module and asserts the existence of `data/raw/simulated_dataset.csv` and a zero exit status.  
  - **Verification**: CI step runs the test and ensures the script completes successfully.

- [ ] **T011** [US1–US3] **Full re‑run from a clean workspace and provenance archiving**  
  - Add a `make clean` target (or equivalent script) that deletes `data/raw/*`, `data/processed/*`, and `data/results/*`.  
  - Run the complete pipeline on a fresh clone, ensuring all pytest suites pass.  
  - Record SHA‑256 hashes of every artifact under `data/` into a new archive file `state/archive/<timestamp>.yaml`.  
  - **Verification**: CI step `test_full_reproducibility` asserts that after the clean‑run the hashes recorded in the archive match the freshly computed hashes.