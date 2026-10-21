# Tasks: Statistical Analysis of Publicly Available Election Poll Aggregates  

**Input**: `specs/001-statistical-poll-aggregation/spec.md`, `plan.md`, existing research and data‑model artifacts, contracts.  

The checklist follows the platform‑required format. Checked boxes (`[X]`) indicate work that has already been verified; unchecked boxes (`[ ]`) are pending or have been reopened for correction. Tasks are ordered to respect data flow and scientific dependencies.

---  

## Phase 0 – Project foundation (setup & tooling)

- [ ] T001 Establish core source layout – create `src/` package with sub‑modules `data/`, `models/`, `evaluation/`, `utils/`.  
  - **Verification**: `tree -L 2 src/` shows the expected directories and an empty `__init__.py` in each.

- [X] T002 Create `requirements.txt` pinned to exact versions (pandas, numpy, scipy, pymc v5, arviz, requests, pyyaml, statsmodels, pytest) and implement `src/utils/config.py` to pin global random seeds for `numpy`, `random`, and `PyMC` to ensure absolute reproducibility (Constitution I).  
  - **Verification**: `pip install -r requirements.txt` succeeds; `src/utils/config.py` contains a `set_seed()` function that is called at the start of all scripts.

- [ ] T003 Add linting and formatting configuration files (`.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) and ensure they are invoked by the CI workflow.  
  - **File paths**: `.ruff.toml`, `.flake8`, `pyproject.toml` (project root).  
  - **Verification**: Running `ruff .` and `black --check .` passes; CI logs show lint step executed.

- [ ] T004 Create the data‑storage hierarchy `data/raw/`, `data/processed/`, and the project‑state folder `state/projects/`; add a small `README.md` in each to prove existence.  
  - **File paths**: `data/raw/README.md`, `data/processed/README.md`, `state/projects/README.md`.  
  - **Verification**: `ls data/raw/ data/processed/ state/projects/` lists the directories and their README files.

- [X] T005 Add the two data‑validation schemas (`dataset.schema.yaml`, `forecast.schema.yaml`) under `specs/001-statistical-poll-aggregation/contracts/` and ensure they are syntactically valid JSON‑Schema documents.  
  - **File paths**: `specs/001-statistical-poll-aggregation/contracts/dataset.schema.yaml`, `specs/001-statistical-poll-aggregation/contracts/forecast.schema.yaml`.  
  - **Verification**: `yamllint` reports no errors; a Python script validates a dummy CSV against each schema using `jsonschema`.

---  

## Phase 1 – Data acquisition & harmonization (User Story 1, P1)

- [ ] T006 Implement `src/data/download.py` to fetch all poll CSVs from FiveThirtyEight (`https://projects.fivethirtyeight.com/polls/`) **and** RealClearPolitics repositories, and official election‑outcome data. Store raw files under `data/raw/`. Immediately after download, compute SHA-256 checksums for all raw files and record them in `state/projects/PROJ-206-statistical-analysis.yaml` (Constitution III).   <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 -->
  - **Verification**: After running `python -m src.data.download`, `data/raw/` contains poll files from both sources and outcomes; the state YAML contains checksum entries for every raw file.

- [ ] T007 Implement `src/data/harmonize.py` to (a) read the raw CSVs, (b) normalise dates, (c) bin polls into ISO‑week intervals, (d) attach a placeholder `historical_rmse` column (to be filled later), and (e) write `data/processed/poll_data_cleaned.csv` with columns `date,pollster,vote_share,sample_size,historical_rmse,week_bin`.  
  - **Verification**: The CSV has no duplicate `(pollster, date)` rows, all `vote_share` values are between 0‑100, and the file validates against `dataset.schema.yaml`.

- [ ] T008 Implement `src/data/weights.py` to compute out‑of‑sample historical RMSE per pollster using only earlier election cycles; write `data/processed/historical_weights.csv`. Pollsters lacking history receive the median RMSE of all pollsters.  
  - **Verification**: Each pollster appears once with a non‑negative RMSE; a unit test checks the median‑imputation rule.

- [ ] T009 Embed data‑sufficiency checks in `src/data/harmonize.py` (FR‑008, FR‑010):  
  • Warn if < 5 polls are present within the 30‑day window before an election week.  
  • Abort with an error if the total poll count across all cycles is < 500.  
  - **Verification**: Running the script on a deliberately small subset triggers the warning/error messages as expected; a flag file `data/processed/insufficient.flag` is created on warning.

---  

## Phase 2 – Frequentist aggregation (User Story 2, P2)

- [ ] T010 Implement `src/models/frequentist.py` with two public functions:  
  • `simple_average(df)` – arithmetic mean of `vote_share` per `week_bin`.  
  • `weighted_average(df, weights_df)` – inverse‑RMSE weighted mean, normalising weights to sum = 1.0.  
  The script writes `data/processed/frequentist_forecasts.csv` containing `week_bin`, `simple_avg_forecast`, `weighted_avg_forecast`.  
  - **Verification**: Spot‑checking a week with three polls reproduces the manual calculation; the file validates against `forecast.schema.yaml`.

- [ ] T011 Add metric utilities in `src/evaluation/metrics.py` to compute RMSE and MAE for the frequentist forecasts against the official outcomes; write a JSON summary `data/processed/frequentist_metrics.json`.  
  - **Verification**: The JSON contains keys `rmse_simple`, `mae_simple`, `rmse_weighted`, `mae_weighted` with numeric values; a unit test asserts they lie within plausible ranges for the 2020 cycle.

- [ ] T012 Write unit tests `tests/unit/test_frequentist.py` covering: single‑poll weeks, missing weight entries, and correct normalisation.  
  - **Verification**: `pytest -q` reports all tests passing.

---  

## Phase 3 – Bayesian hierarchical modeling & evaluation (User Story 3, P3)

- [ ] T013 Implement `src/models/bayesian.py` using PyMC v5:  
  • Static parameter hierarchical model (per Plan Complexity Tracking) to estimate latent preference.  
  • Observation model `poll_{i,t} ~ Normal(θ_t, τ_i²)` where `τ_i` combines reported margin‑of‑error and a pollster‑specific variance component.  
  • NUTS sampler with 1 000 warm‑up and 2 000 draws, CPU‑only (`device="cpu"`).  
  Output posterior draws and point forecasts (`posterior_mean`) plus 95 % credible intervals to `data/processed/bayesian_forecasts.csv`.  
  - **Verification**: The trace shows `r_hat` ≤ 1.05 for all parameters; the CSV includes `week_bin`, `bayesian_forecast`, `ci_lower`, `ci_upper`.

- [ ] T014 Add convergence validation in `src/models/bayesian.py`: if any `r_hat` > 1.05, raise a descriptive `RuntimeError` and abort.  
  - **Verification**: Artificially forcing divergence triggers the error and logs the offending parameters.

- [ ] T015 Extend `src/evaluation/metrics.py` with `calculate_coverage(forecast_df, outcomes_df)` that computes the proportion of weeks where the true outcome falls inside the 95 % credible interval; also perform a binomial test against the null hypothesis of 0.95 coverage. Write results to `data/processed/bayesian_coverage.json`.  
  - **Verification**: The JSON contains `coverage_rate` ≥ 0.90 for the 2020 cycle and a `p_value` ≥ 0.05.

- [ ] T016 Implement Hierarchical Meta-Analysis of errors in `src/evaluation/meta_analysis.py` (replacing DM tests per Plan Complexity Tracking); produce `data/processed/meta_analysis_results.csv` with columns `method_a`, `method_b`, `stat`, `p_adj`.  
  - **Verification**: Running the script on the three forecast series yields a file where all `p_adj` values are reported; permutation count is 1 000.

- [ ] T017 Add unit tests `tests/unit/test_bayesian.py` that (a) run the model on a tiny synthetic dataset (≤ 5 polls) to verify convergence logic, and (b) check that `calculate_coverage` returns 1.0 when the synthetic truth equals the posterior mean.  
  - **Verification**: All tests pass under `pytest`.

---  

## Phase 4 – State tracking, reproducibility & runtime limits

- [ ] T018 Implement `src/utils/state.py` with a `record_hash(filepath: str)` function that (a) computes the SHA‑256 hash of the given file, (b) writes/updates `state/projects/PROJ-206-statistical-analysis.yaml` with an `artifact_hashes` map entry, and (c) returns the hash.  
  - **Verification**: After calling `record_hash` on any processed file, the YAML contains a correct hash entry.

- [ ] T019 Instrument all data‑processing scripts (`download.py`, `harmonize.py`, `weights.py`, `frequentist.py`, `bayesian.py`, `metrics.py`, `meta_analysis.py`) to call `src.utils.state.record_hash(filepath)` after each successful write, thereby updating the project‑state YAML.  
  - **Verification**: After a full pipeline run, `state/projects/PROJ-206-statistical-analysis.yaml` contains hash entries for every file in `data/processed/`.

- [ ] T020 Create the pipeline orchestrator `src/main.py` that sequentially runs:  
  1. `src.data.download`  
  2. `src.data.harmonize` (checks sufficiency flags)  
  3. `src.data.weights`  
  4. `src.models.frequentist`  
  5. `src.models.bayesian`  
  6. `src.evaluation.metrics` (frequentist & Bayesian)  
  7. `src.evaluation.meta_analysis`  
  The script respects the `insufficient.flag` and aborts downstream steps when raised.  
  - **Verification**: Executing `python -m src.main` runs the full end‑to‑end pipeline without missing‑module errors; on insufficient data it exits cleanly with an explanatory message.

- [ ] T021 Add a lightweight timing wrapper in `src/main.py` that records wall‑clock time for the whole run and logs it; CI must assert the total runtime is < 4 h on the standard 2‑core runner (NFR‑001).  
  - **Verification**: Sample CI run reports `Total runtime: 3h 42m`; the log entry appears in `logs/run.log`.

---  

## Phase 5 – Documentation, results & handoff

- [ ] T022 Write `quickstart.md` with a single command (`python -m src.main`) and a short description of required environment variables, expected runtime, and where to find results (`data/processed/` and `figures/`).  
  - **Verification**: A new contributor can follow the guide on a fresh runner and reproduce the full analysis.

- [ ] T023 Draft `research.md` summarising the mathematical formulation of all three methods, the rationale for the static Bayesian model, the Hierarchical Meta-Analysis, and a discussion of limitations. MUST include an explicit verification check ensuring findings are framed as predictive accuracy and associational uncertainty, NOT causal voter influence (FR-007).  
  - **Verification**: The file is linked from `README.md` and passes a spell‑check CI step; a reviewer confirms no causal language is used.

- [ ] T024 Generate final result artifacts:  
  • Table `tables/forecast_accuracy.csv` containing RMSE and MAE for each method per election cycle.  
  • Figure `figures/forecast_comparison.png` visualising point forecasts and 95 % credible intervals against actual outcomes.  
  - **Verification**: Files exist, are non‑empty, open without error, and a checksum entry is added to the state YAML.

- [ ] T025 Provide an end‑to‑end integration test `tests/integration/test_pipeline.py` that runs `src.main` and then asserts the presence of all expected output files (`poll_data_cleaned.csv`, `frequentist_forecasts.csv`, `bayesian_forecasts.csv`, `meta_analysis_results.csv`, `forecast_accuracy.csv`, `forecast_comparison.png`).  
  - **Verification**: CI reports the integration test passes.

---  

### Dependency & execution order summary

1. **Foundation** – T001, T002, T003, T004, T005.  
2. **Data ingestion** – T006 → T007 → T008 (sufficiency) → T009 (gating).  
3. **Frequentist** – T010 → T011 → T012.  
4. **Bayesian** – T013 → T014 → T015 → T016 → T017.  
5. **State & reproducibility** – T018 → T019 → T020 → T021.  
6. **Documentation & handoff** – T022 → T023 → T024 → T025.  

All pending tasks (`[ ]`) are ready to be implemented in the next development sprint. Once each task is completed and its verification passes, the corresponding box should be checked.