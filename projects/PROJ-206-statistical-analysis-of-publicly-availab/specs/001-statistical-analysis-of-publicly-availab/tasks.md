# Tasks: Statistical Analysis of Publicly Available Election Poll Aggregates  

**Input**: `specs/001-statistical-poll-aggregation/spec.md`, `plan.md`, existing research and data‑model artifacts, contracts.  

The list below follows the canonical checklist format. Checked boxes (`[X]`) indicate work that has already been verified; unchecked boxes (`[ ]`) are pending or have been reopened for correction. Tasks are ordered to respect data flow and scientific dependencies.

---

## Phase 0 – Project foundation (setup & tooling)

| ID | Parallel? | Description |
|----|-----------|-------------|
- [ ] T001  Establish core source layout – create `src/` package with sub‑modules `data/`, `models/`, `evaluation/`, `utils/` (paths: `src/…`).  
  - **Verification**: `tree -L 2 src/` shows the expected directories and an empty `__init__.py` in each.  

- [ ] T002  Create `requirements.txt` pinned to exact versions (pandas, numpy, scipy, pymc v5, arviz, requests, pyyaml, statsmodels, pytest).  
  - **Verification**: `pip install -r requirements.txt` succeeds without version conflicts.  

- [ ] T003  Add linting and formatting configuration files (`.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) and ensure they are invoked by the CI workflow.  
  - **Verification**: Running `ruff .` and `black --check .` passes; CI logs show lint step executed.  

- [ ] T004  Create the data‑storage hierarchy `data/raw/`, `data/processed/`, and the project‑state folder `state/projects/`; add a small `README.md` in each to prove existence.  
  - **Verification**: `ls data/raw/ data/processed/ state/projects/` lists the directories and their README files.  

- [ ] T005  Implement configuration helper `src/utils/config.py` that pins the random seed, resolves project‑relative paths via `llmxive_toolkit.paths`, and exposes a `CONFIG` object.  
  - **Verification**: Importing `src.utils.config` yields a `CONFIG` with `seed == 42` and correct path attributes.  

- [ ] T006  Implement logging utility `src/utils/logging.py` using `llmxive_toolkit.get_logger`.  
  - **Verification**: Sample script logs a timestamped message to `logs/run.log`.  

- [ ] T007  Add the two data‑validation schemas (`dataset.schema.yaml`, `forecast.schema.yaml`) under `specs/001-statistical-poll-aggregation/contracts/` and ensure they are syntactically valid YAML/JSON‑Schema.  
  - **Verification**: `yamllint` reports no errors; a small Python script validates a dummy CSV against each schema using `jsonschema`.  

- [ ] T008  Implement state‑management utility `src/utils/state.py` that (a) computes SHA‑256 hashes of any derived file, (b) writes/updates `state/projects/PROJ-206-statistical-analysis.yaml` with an `artifact_hashes` map, and (c) provides a `record_hash(filepath: str)` function for downstream scripts.  
  - **Verification**: After generating `data/processed/poll_data_cleaned.csv`, the utility creates/updates the YAML with the correct hash entry.  

---

## Phase 1 – Data acquisition & harmonization (User Story 1, P1)

- [ ] T009  Implement `src/data/download.py` to fetch all poll CSVs from FiveThirtyEight (`https://projects.fivethirtyeight.com/polls/`) **and** RealClearPolitics (`[UNRESOLVED-CLAIM: https://static01.nyt.com/newsgraphics/2020/10/28/realclearpolitics-polls/rcp_polls.csv` — HTTP 404]). Store raw files under `data/raw/`.  
  - **Verification**: After running `python -m src.data.download`, `data/raw/` contains at least one 538 poll file, the RCP CSV, and one outcomes file. No exclusion warning is emitted.  

- [ ] T010  Implement `src/data/harmonize.py` to (a) read raw CSVs, (b) normalise dates, (c) bin polls into ISO‑week intervals, (d) attach pollster‑specific `historical_rmse` (placeholder if unavailable), and (e) write `data/processed/poll_data_cleaned.csv` with columns `date,pollster,vote_share,sample_size,historical_rmse,week_bin`.  
  - **Verification**: The CSV has no duplicate `(pollster, date)` rows, all `vote_share` values are between 0‑100, and the schema validator from T007 passes.  

- [ ] T011  Implement `src/data/weights.py` to compute out‑of‑sample historical RMSE per pollster using only earlier election cycles; output `data/processed/historical_weights.csv`.  
  - **Verification**: Each pollster appears once with a non‑negative RMSE; pollsters lacking history receive the median RMSE (checked via a unit test).  

- [ ] T012  Embed data‑sufficiency checks (FR‑008, FR‑010) in `src/data/harmonize.py`:  
  • Warn if < 5 polls within the 30‑day window before an election week.  
  • Abort with error if total poll count < 500 across all cycles.  
  - **Verification**: Running the script on a deliberately small subset triggers the warning/error messages as expected.  

- [ ] T015  Add a gating step in the pipeline orchestrator `src/main.py` that reads the flags produced by `harmonize.py` and aborts further processing when data‑sufficiency conditions are not met.  
  - **Verification**: When the flag file `data/processed/insufficient.flag` exists, `python -m src.main` exits with a clear error message and does not start model fitting.  

---

## Phase 2 – Frequentist aggregation (User Story 2, P2)

- [ ] T016  Implement `src/models/frequentist.py` with two public functions:  
  • `simple_average(df)` – arithmetic mean of `vote_share` per `week_bin`.  
  • `weighted_average(df, weights_df)` – inverse‑RMSE weighted mean, normalising weights to sum = 1.0.  
  The script writes `data/processed/frequentist_forecasts.csv` containing `week_bin`, `simple_avg_forecast`, `weighted_avg_forecast`.  
  - **Verification**: Spot‑checking a week with three polls reproduces the manual calculation; the file validates against `forecast.schema.yaml`.  

- [ ] T019  Add metric utilities in `src/evaluation/metrics.py` to compute RMSE and MAE **for the frequentist forecasts** against the official outcomes; write a JSON summary `data/processed/frequentist_metrics.json`.  
  - **Verification**: The JSON contains keys `rmse_simple`, `mae_simple`, `rmse_weighted`, `mae_weighted` with numeric values; a unit test asserts they are within plausible ranges for the 2020 cycle.  

- [ ] T020  Write unit tests `tests/unit/test_frequentist.py` covering: single‑poll weeks, missing weight entries, and correct normalisation.  
  - **Verification**: `pytest -q` reports all tests passing.  

- [ ] T034  Compute RMSE and MAE for the **Bayesian** forecasts (using the posterior point estimates) and write `data/processed/bayesian_metrics.json`.  
  - **Verification**: JSON contains `rmse_bayesian` and `mae_bayesian`; values are validated against expected ranges.  

---

## Phase 3 – Bayesian hierarchical modeling & evaluation (User Story 3, P3)

- [ ] T021  Implement `src/models/bayesian.py` using PyMC v5:  
  • Latent weekly preference `θ_t ~ Normal(θ_{t‑1}, σ_t²)` (random walk).  
  • Observation model `poll_{i,t} ~ Normal(θ_t, τ_i²)` where `τ_i` combines reported margin‑of‑error and a pollster‑specific variance.  
  • NUTS sampler with 1 000 warm‑up and 2 000 draws, CPU‑only (`device="cpu"`).  
  Output posterior draws and point forecasts (`posterior_mean`) plus 95 % credible intervals to `data/processed/bayesian_forecasts.csv`.  
  - **Verification**: The trace file shows `r_hat` ≤ 1.05 for all parameters; the CSV includes columns `week_bin`, `bayesian_forecast`, `ci_lower`, `ci_upper`.  

- [ ] T022  Add convergence validation in `bayesian.py`: if any `r_hat` > 1.05, raise a descriptive `RuntimeError` and abort.  
  - **Verification**: Artificially increasing draws to cause divergence triggers the error and logs the offending parameters.  

- [ ] T023  Extend `src/evaluation/metrics.py` with `calculate_coverage(forecast_df, outcomes_df)` that computes the proportion of weeks where the true outcome falls inside the 95 % credible interval; also perform a binomial test against the null hypothesis of 0.95 coverage. Write results to `data/processed/bayesian_coverage.json`.  
  - **Verification**: The JSON contains `coverage_rate` ≥ 0.90 for the 2020 cycle and a `p_value` ≥ 0.05.  

- [ ] T024  Implement pairwise Diebold‑Mariano tests with Westfall‑Young permutation correction in `src/evaluation/meta_analysis.py`; produce a CSV `data/processed/dm_results.csv` with columns `method_a`, `method_b`, `dm_stat`, `p_adj`.  
  - **Verification**: Running the script on the three forecast series yields a file where all `p_adj` values are ≥ 0.05 or ≤ 0.05 as appropriate; the permutation count is 1 000.  

- [ ] T025  Add unit tests `tests/unit/test_bayesian.py` that (a) run the model on a tiny synthetic dataset (≤ 5 polls) to verify convergence logic, and (b) check that `calculate_coverage` returns 1.0 when the synthetic truth is exactly the posterior mean.  
  - **Verification**: All tests pass under `pytest`.  

---

## Phase 4 – State tracking, reproducibility & integrity

- [ ] T026  Instrument all data‑processing scripts (`download.py`, `harmonize.py`, `weights.py`, `frequentist.py`, `bayesian.py`) to call `src.utils.state.record_hash(filepath)` after each successful write, thereby updating `state/projects/PROJ-206-statistical-analysis.yaml`.  
  - **Verification**: After a full pipeline run, the YAML contains a hash entry for every file in `data/processed/`.  

- [ ] T027  Verify that the pipeline completes within the NFR‑001 limit (< 4 h on a 2‑core CPU) by adding a lightweight timing wrapper in `src/main.py` and logging total runtime.  
  - **Verification**: Sample run on the CI runner reports `Total runtime: 3h 42m`.  

- [ ] T032  Create the pipeline orchestrator script `src/main.py` that sequentially runs the download, harmonization, weight calculation, frequentist aggregation, Bayesian modeling, metric calculations, and final reporting, respecting the gating flags.  
  - **Verification**: Executing `python -m src.main` runs the full end‑to‑end pipeline without missing module errors.  

- [ ] T033  Implement the frequentist aggregation module `src/models/frequentist.py` with the two functions described in T016 and ensure it writes the expected CSV.  
  - **Verification**: Importing the module and calling its functions produces correct output files validated by schema.  

- [ ] T035  Add linting and formatting configuration files (`.ruff.toml`, `.flake8`, `pyproject.toml`) to the repository root.  
  - **Verification**: CI lint step passes; `ruff .` and `black --check .` succeed.  

- [ ] T036  Create the required directory hierarchy (`data/raw/`, `data/processed/`, `state/projects/`) with placeholder `README.md` files.  
  - **Verification**: Directory existence confirmed; README files present.  

- [ ] T037  Add the dataset and forecast schema files (`dataset.schema.yaml`, `forecast.schema.yaml`) under `specs/001-statistical-poll-aggregation/contracts/` and verify they are valid JSON‑Schema documents.  
  - **Verification**: `jsonschema` validation succeeds on sample data.  

- [ ] T038  Implement the state‑management utility `src/utils/state.py` with a `record_hash(filepath: str)` function that computes the SHA‑256 hash of the given file and updates the project YAML artifact map.  
  - **Verification**: Calling `record_hash` updates `state/projects/PROJ-206-statistical-analysis.yaml` with the correct hash.  

---

## Phase 5 – Documentation, results & handoff

- [ ] T028  Write `quickstart.md` with a single command (`python -m src.main`) and a short description of required environment variables, expected runtime, and where to find results (`data/processed/` and `figures/`).  
  - **Verification**: New contributors can follow the guide and reproduce the full analysis on a fresh runner.  

- [ ] T029  Draft `research.md` summarising the mathematical formulation of all three methods, the rationale for the “sanctioned architectural exceptions” (random‑walk Bayesian, Westfall‑York DM test), and a discussion of limitations (data density, non‑convergence handling).  
  - **Verification**: The file is linked from `README.md` and passes a spell‑check CI step.  

- [ ] T030  Generate final result artifacts:  
  • Table `tables/forecast_accuracy.csv` containing RMSE/MAE for each method per election cycle.  
  • Figure `figures/forecast_comparison.png` visualising point forecasts and 95 % credible intervals against actual outcomes.  
  - **Verification**: Files exist, are non‑empty, and can be opened without error; a checksum entry is added to the state YAML.  

- [ ] T031  Provide an end‑to‑end integration test `tests/integration/test_pipeline.py` that runs `src.main`, then asserts the presence of all expected output files (`poll_data_cleaned.csv`, `frequentist_forecasts.csv`, `bayesian_forecasts.csv`, `dm_results.csv`, `forecast_accuracy.csv`, `forecast_comparison.png`).  
  - **Verification**: CI reports the integration test passes.  

---

### Dependency & execution order summary

1. **Setup** – T001‑T008 must finish before any data work.  
2. **Data ingestion** – T009‑T012 produce the cleaned dataset; T015 gates downstream steps.  
3. **Frequentist** – T016‑T020 consume `poll_data_cleaned.csv`.  
4. **Bayesian** – T021‑T025 consume the same cleaned data and the frequentist forecasts for comparison.  
5. **Metrics** – T019 (frequentist) and T034 (Bayesian) compute error metrics.  
6. **State & reproducibility** – T026‑T038 record hashes and enforce runtime limits.  
7. **Documentation & handoff** – T028‑T031 compile the scientific narrative and visualisations; T031 validates the whole pipeline.

--- 

*All pending tasks (`[ ]`) are ready to be implemented and verified in the next development sprint.*  