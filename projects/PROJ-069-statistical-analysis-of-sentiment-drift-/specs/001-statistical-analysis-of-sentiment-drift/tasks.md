---
description: "Task list for Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions"
---

# Tasks: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

**Input**: Design documents from `/specs/001-sentiment-drift/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`  

**Tests**: Test tasks are included where the specification explicitly requests verification.  

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format
`- [ ] T### [P?] [Story] description – **file(s)**`

- **[P]** – can run in parallel (different files, no dependencies)  
- **[Story]** – US1, US2, or US3 (corresponds to the user story)  
- **file(s)** – exact path(s) affected by the task  

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Initialize project directory structure (`code/`, `data/raw/`, `data/processed/`, `data/metadata/`, `results/`, `tests/`, `artifacts/`, `docs/`, `scripts/`) – **file(s)**: `scripts/init_dirs.sh`
- [ ] T002 Create `code/requirements.txt` with pinned dependencies (`pandas`, `numpy`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `requests`, `datasets`, `fredapi`, `pygdelt`, `nbformat`, `nbconvert`, `ruff`, `black`) – **file(s)**: `code/requirements.txt`
- [ ] T003 Initialize a Python 3.10 virtual environment in `venv/` and install the dependencies – **file(s)**: `scripts/create_venv.sh`
- [ ] T004 Configure linting (`ruff`) and formatting (`black`) tools – **file(s)**: `.ruff.toml`, `pyproject.toml`
- [ ] T005 Create concrete JSON Schema definitions for `TimeSeries`, `ModelResult`, and `RecessionPeriod` – **file(s)**: `code/contracts/timeseries_schema.json`, `code/contracts/model_result_schema.json`, `code/contracts/recession_period_schema.json`
- [ ] T006 Implement `code/update_state.py` to compute SHA‑256 hashes for **each** artifact in `data/`, `code/`, and `results/` and write per‑file checksums to `state/projects/...yaml` – **file(s)**: `code/update_state.py`
- [ ] T007 Create `.env.example` with placeholders for `FRED_API_KEY` and `HF_TOKEN` – **file(s)**: `.env.example`
- [ ] T075 Create a real `.env` file from `.env.example` (to be populated by the researcher) and verify that `code/data_ingestion.py` reads API keys from it – **file(s)**: `.env`, `tests/integration/test_env_loading.py`
- [ ] T074 Verify that a real `.env` file is populated from `.env.example` and that `code/data_ingestion.py` reads API keys from it – **file(s)**: `.env`, `tests/integration/test_env_loading.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that must be complete before any user story can start  

- [ ] T008 Create `code/data_ingestion.py` skeleton with wrappers for the FRED API (`fredapi.Fred`) and the HuggingFace dataset loader – **file(s)**: `code/data_ingestion.py`
- [ ] T009 Create `code/preprocessing.py` skeleton for resampling, linear interpolation, and stationarity‑related diagnostics – **file(s)**: `code/preprocessing.py`
- [ ] T010 Create `code/modeling.py` skeleton for ADF, Johansen, VAR/VECM fitting, and Granger causality – **file(s)**: `code/modeling.py`
- [ ] T011 Create `code/validation.py` skeleton for Moving Block Bootstrap (MBB) and sensitivity analysis – **file(s)**: `code/validation.py`
- [ ] T012 Create `code/visualization.py` skeleton for time‑series plots, NBER recession shading, impulse‑response functions, and heatmaps – **file(s)**: `code/visualization.py`
- [ ] T013 Run a pilot sensitivity sweep on a small sample to determine concrete masking proportions and the acceptable absolute p‑value shift threshold; write these values to `code/config.yaml` as `sensitivity_masking_proportions` and `p_value_shift_threshold` – **file(s)**: `code/config.yaml`
- [ ] T014 [P] Contract test for `TimeSeries` schema – **file(s)**: `tests/contract/test_timeseries_schema.py`
- [ ] T015 [P] Contract test for `ModelResult` schema – **file(s)**: `tests/contract/test_model_result_schema.py`
- [ ] T016 [P] Contract test for `RecessionPeriod` schema – **file(s)**: `tests/contract/test_recession_period_schema.py`
- [ ] T017 [P] Verify that per‑file checksums are recorded after each data download – **file(s)**: `tests/integration/test_checksum_recording.py`
- [ ] T062 Add per‑file checksum generation for raw data files (e.g., `data/raw/*.csv`) and record them in the state file – **file(s)**: `code/update_state.py`, `tests/integration/test_raw_checksum.py`
- [ ] T067 Validate that `code/preprocessing.py` writes `TimeSeries` objects conforming to the schema – **file(s)**: `tests/contract/test_timeseries_output.py`
- [ ] T068 Validate that `code/modeling.py` writes `ModelResult` objects conforming to the schema – **file(s)**: `tests/contract/test_model_result_output.py`
- [ ] T069 Validate that `code/visualization.py` writes `RecessionPeriod` objects conforming to the schema – **file(s)**: `tests/contract/test_recession_period_output.py`

**Checkpoint**: Foundational work complete → user‑story implementation can begin.

---

## Phase 3: User Story 1 – Data Acquisition, Alignment, and Preprocessing (Priority: P1) 🎯 MVP  

**Goal**: Ingest historical sentiment and macro‑economic data, align to **quarterly** frequency (core requirement) and also produce a **monthly** version for bootstrap validation, handling missing data via documented linear interpolation.

**Independent Test**: Running the ingestion and preprocessing scripts must produce `data/processed/aligned_quarterly.csv` (quarterly) and `data/processed/aligned_monthly.csv` (monthly) with the required completeness and logging.

### Tests (optional – write first, ensure they fail)

- [ ] T018 [P] [US1] Contract test for `aligned_quarterly.csv` schema – **file(s)**: `tests/contract/test_timeseries_schema_quarterly.py`
- [ ] T018b [P] [US1] Contract test for `aligned_monthly.csv` schema – **file(s)**: `tests/contract/test_timeseries_schema_monthly.py`
- [ ] T019 [P] [US1] Integration test for the full data‑alignment pipeline – **file(s)**: `tests/integration/test_data_alignment.py`
- [ ] T020 [P] [US1] Unit tests for interpolation methods (linear vs forward‑fill) – **file(s)**: `tests/unit/test_interpolation.py`
- [ ] T065 Compute data completeness (percentage of non‑missing points) after interpolation and assert ≥ 95 % – **file(s)**: `code/preprocessing.py`, `tests/contract/test_data_completeness.py`
- [ ] T070 [P] Contract test that data completeness ≥ 95 % – **file(s)**: `tests/contract/test_data_completeness.py`

### Implementation

- [ ] T021 [US1] Download quarterly GDP (`FRED/GDP`) via the FRED API; store raw CSV in `data/raw/fred_gdp.csv` – **file(s)**: `code/data_ingestion.py`, `data/raw/fred_gdp.csv`
- [ ] T022 [US1] Download unemployment (`FRED/UNRATE`) via the FRED API; store raw CSV in `data/raw/fred_unrate.csv` – **file(s)**: `code/data_ingestion.py`, `data/raw/fred_unrate.csv`
- [ ] T023 [US1] Download consumer‑confidence series (`FRED/CONSUMER_CONF`) via the FRED API; store raw CSV in `data/raw/fred_consumer_confidence.csv` – **file(s)**: `code/data_ingestion.py`, `data/raw/fred_consumer_confidence.csv`
- [ ] T024 [US1] Download the HuggingFace sentiment dataset `snap-cornell/twitter-roberta-base-sentiment-dataset`; store as `data/raw/sentiment_hf.csv` – **file(s)**: `code/data_ingestion.py`, `data/raw/sentiment_hf.csv`
- [ ] T025 [US1] Resample daily sentiment to **monthly** positive/negative/neutral ratios, store as `data/processed/aligned_monthly.csv`.  
- [ ] T061 [US1] Aggregate the monthly sentiment ratios to **quarterly** frequency (average of the three months in each quarter) and merge with macro series, apply **linear interpolation** for any missing macro values (only if missing rate ≤ 5 %). Log the interpolation method and percentage imputed in `data/processed/data_quality_log.json`; output final quarterly dataset as `data/processed/aligned_quarterly.csv`. – **file(s)**: `code/preprocessing.py`, `data/processed/aligned_quarterly.csv`, `data/processed/data_quality_log.json`
- [ ] T026 [US1] Compute per‑month sentiment sample size; flag months where sample size < 100 tweets or average confidence < 0.7 as low‑confidence; propagate these flags to the quarterly aggregation (exclude flagged months from quarterly averages) and record flags in `data/processed/data_quality_log.json`. – **file(s)**: `code/preprocessing.py`, `data/processed/data_quality_log.json`
- [ ] T027 [US1] Verify that `aligned_quarterly.csv` contains **no missing values** after interpolation; raise an exception if any remain. – **file(s)**: `code/preprocessing.py`
- [ ] T058 [P] Verify that `code/preprocessing.py` raises an exception when missing values remain after interpolation – **file(s)**: `code/preprocessing.py`, `tests/unit/test_missing_values_exception.py`

**Checkpoint**: User Story 1 functional and independently testable.

---

## Phase 4: User Story 2 – Statistical Modeling, Stationarity Testing, Causal Inference & Validation (Priority: P2)

**Goal**: Run stationarity diagnostics, select optimal lag order, fit VAR or VECM on the **quarterly** series, perform Granger causality tests, and validate results with Moving Block Bootstrap (using the **monthly** series) and out‑of‑sample recession hold‑outs.

**Independent Test**: Execution of `code/modeling.py` and `code/validation.py` must produce `results/model_stats.json`, `results/validation_stats.json`, and `results/holdout_validation.json` with all required statistics.

### Tests (optional)

- [ ] T028 [P] [US2] Contract test for `model_stats.json` schema – **file(s)**: `tests/contract/test_model_results_schema.py`
- [ ] T029 [P] [US2] Integration test for the full Granger‑causality pipeline – **file(s)**: `tests/integration/test_granger_causality.py`
- [ ] T030 [P] [US2] Unit tests for ADF and Johansen implementations – **file(s)**: `tests/unit/test_stationarity.py`
- [ ] T031 [P] Contract test that all Granger‑causality p‑values are < 0.05 – **file(s)**: `tests/contract/test_granger_significance.py`
- [ ] T032 [P] Contract test that data completeness ≥ 95 % – **file(s)**: `tests/contract/test_data_completeness.py`
- [ ] T069 [P] Contract test for `ModelResult` schema compliance – **file(s)**: `tests/contract/test_model_result_output.py`

### Implementation

- [ ] T033 [US2] **Out‑of‑sample validation**: Using `data/metadata/recession_periods.json` (produced by T045) hold out all months belonging to each NBER‑defined recession period, re‑fit the quarterly VAR/VECM on the remaining data, forecast the held‑out months, compute RMSE and coverage; store results in `results/holdout_validation.json`. – **file(s)**: `code/validation.py`, `results/holdout_validation.json`
- [ ] T034 [US2] Implement Augmented Dickey‑Fuller (ADF) test for each series; if a series remains non‑stationary after first differencing, automatically apply a log or Box‑Cox transformation; write ADF results to `results/adf_results.json`. – **file(s)**: `code/modeling.py`, `results/adf_results.json`
- [ ] T035 [US2] Implement the Johansen cointegration test; **prioritize the Trace statistic** for rank selection; write results to `results/cointegration.json`. – **file(s)**: `code/modeling.py`, `results/cointegration.json`
- [ ] T036 [US2] Determine the optimal lag length via Akaike Information Criterion (AIC) for the chosen model (VAR or VECM); write the selected lag to `results/lag_selection.json`. – **file(s)**: `code/modeling.py`, `results/lag_selection.json`
- [ ] T037 [US2] Fit the appropriate model (VAR if no cointegration, VECM otherwise) using the lag order from T036; serialize the fitted model to `results/model_fit.pkl` and record summary statistics in `results/model_stats.json`. – **file(s)**: `code/modeling.py`, `results/model_fit.pkl`, `results/model_stats.json`
- [ ] T038 [US2] Run Granger‑causality F‑tests for all direction pairs; append p‑values and F‑statistics to `results/model_stats.json`. – **file(s)**: `code/modeling.py`, `results/model_stats.json`
- [ ] T039 [US2] Implement Moving Block Bootstrap (MBB) **on the monthly dataset** (`data/processed/aligned_monthly.csv`) with **block length = 1 month**, 1 000 iterations, and a convergence check (CI width stabilises < 1 % over three successive runs); calculate 95 % confidence intervals and verify CI width ≤ 20 % of the original point estimate; write outcomes to `results/validation_stats.json`. – **file(s)**: `code/validation.py`, `results/validation_stats.json`
- [ ] T040 [US2] Validate sentiment drift against NBER recession dates (using `data/metadata/recession_periods.json` from T045); compare drift onset timing with recession start/end and store results in `results/drift_nber_validation.json`. – **file(s)**: `code/validation.py`, `results/drift_nber_validation.json`
- [ ] T041 [US2] Compute Variance Inflation Factor (VIF) for GDP and Unemployment; write VIF values to `results/vif_report.json` and note joint‑relationship interpretation. – **file(s)**: `code/modeling.py`, `results/vif_report.json`
- [ ] T042 [US2] Execute the sensitivity analysis defined in `code/config.yaml`; for each masking proportion, randomly mask data, re‑interpolate, re‑run the full modeling pipeline, and record absolute p‑value shifts; **assert that every shift ≤ `p_value_shift_threshold` (0.01)**; write summary to `results/sensitivity_analysis.json`. – **file(s)**: `code/validation.py`, `results/sensitivity_analysis.json`

**Checkpoint**: User Story 2 functional and independently testable.

---

## Phase 5: User Story 3 – Visualization, Robustness Validation, and Reporting (Priority: P3)

**Goal**: Produce publication‑ready visualizations, embed all results in a reproducible Jupyter notebook, and generate a final PDF report.

**Independent Test**: The notebook `notebooks/analysis_master.ipynb` runs from start to finish without errors and produces the expected figures in `artifacts/figures/` and the PDF `artifacts/report.pdf`.

### Tests (optional)

- [ ] T043 [P] Contract test for figure‑metadata schema (recession shading, URLs/DOIs) – **file(s)**: `tests/contract/test_figure_metadata.py`
- [ ] T044 [P] Integration test that the full pipeline (ingestion → modeling → validation → visualization) produces a runnable notebook – **file(s)**: `tests/integration/test_full_pipeline.py`
- [ ] T071 [P] Integration test that the master notebook runs end‑to‑end without error – **file(s)**: `tests/integration/test_notebook_execution.py`

### Implementation

- [ ] T045 [US3] Fetch official NBER recession dates from the verified CSV source `https://raw.githubusercontent.com/datasets/nber-business-cycle-dating/master/data/nber-cycles.csv`; store as `data/metadata/recession_periods.json` and compute a checksum – **file(s)**: `code/visualization.py`, `data/metadata/recession_periods.json`
- [ ] T046 [US3] Implement time‑series plots of sentiment, GDP, and unemployment with recession shading; save PNG and PDF versions to `artifacts/figures/time_series.png` (and `.pdf`) – **file(s)**: `code/visualization.py`, `artifacts/figures/time_series.png`
- [ ] T047 [US3] Implement impulse‑response function (IRF) plots for each variable pair and cross‑correlation heatmaps; store in `artifacts/figures/irf_*.png` and `artifacts/figures/cross_corr_heatmap.png` – **file(s)**: `code/visualization.py`, `artifacts/figures/irf_sentiment_gdp.png`, `artifacts/figures/cross_corr_heatmap.png`
- [ ] T048 [US3] Assemble the master notebook `notebooks/analysis_master.ipynb` that sequentially runs all scripts, displays figures, and includes narrative text; embed dataset URLs, DOIs, and configuration details in a metadata cell – **file(s)**: `notebooks/analysis_master.ipynb`
- [ ] T049 [US3] Convert the notebook to a PDF report `artifacts/report.pdf` using `nbconvert` with a custom LaTeX template that preserves figure captions and recession shading – **file(s)**: `artifacts/report.pdf`
- [ ] T050 [US3] Update the project state file (`state/projects/...yaml`) with hashes of all final artifacts (`aligned_quarterly.csv`, `model_stats.json`, `validation_stats.json`, `report.pdf`, etc.) – **file(s)**: `code/update_state.py`, `state/projects/...yaml`
- [ ] T052 [P] Refactor code for readability and performance: enforce lint (`ruff`), formatting (`black`), and run a benchmark script (`scripts/performance_benchmark.sh`) ensuring total runtime < 4 h and peak memory < 5 GB – **file(s)**: `scripts/performance_benchmark.sh`, `code/`
- [ ] T053 [P] Add comprehensive edge‑case unit tests (`tests/unit/test_edge_cases.py`) covering API failures, non‑stationary fallback paths, extreme missing‑data scenarios, and collinearity diagnostics – **file(s)**: `tests/unit/test_edge_cases.py`
- [ ] T054 [P] Create quick‑start validation script `scripts/quickstart.sh` that clones the repo, installs dependencies, runs the full pipeline, and checks that all expected artifacts exist; add integration test `tests/integration/test_quickstart.sh` – **file(s)**: `scripts/quickstart.sh`, `tests/integration/test_quickstart.sh`
- [ ] T055 [P] Verify that `.env` is populated from `.env.example` and that `code/data_ingestion.py` reads API keys from it – **file(s)**: `.env.example`, `tests/integration/test_env_loading.py`
- [ ] T056 [P] Verify that the virtual environment (`venv/`) is created and that `pip freeze` matches `code/requirements.txt` – **file(s)**: `scripts/create_venv.sh`, `tests/integration/test_venv_creation.py`
- [ ] T057 [P] Verify that `code/config.yaml` contains the keys `sensitivity_masking_proportions` and `p_value_shift_threshold` – **file(s)**: `code/config.yaml`, `tests/unit/test_config_values.py`
- [ ] T058 [P] Verify that `code/preprocessing.py` raises an exception when missing values remain after interpolation – **file(s)**: `code/preprocessing.py`, `tests/unit/test_missing_values_exception.py`
- [ ] T059 [P] Verify that the master notebook runs end‑to‑end without error (re‑uses T071) – **file(s)**: `tests/integration/test_notebook_execution.py`
- [ ] T060 [P] Verify that all generated figures include recession shading and that the final PDF report metadata lists all dataset URLs/DOIs – **file(s)**: `tests/contract/test_figure_metadata.py`

**Checkpoint**: All deliverables for User Story 3 are generated and reproducible.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Final refinements that affect the whole project.

- [ ] T051 [P] Update documentation in `docs/data_sources.md` to include a full bibliography of dataset URLs, DOIs, and citation information – **file(s)**: `docs/data_sources.md`
- [ ] T052 [P] Refactor code for readability and performance: enforce lint (`ruff`), formatting (`black`), and run a benchmark script (`scripts/performance_benchmark.sh`) ensuring total runtime < 4 h and peak memory < 5 GB – **file(s)**: `scripts/performance_benchmark.sh`, `code/`
- [ ] T053 [P] Add comprehensive edge‑case unit tests (`tests/unit/test_edge_cases.py`) covering API failures, non‑stationary fallback paths, extreme missing‑data scenarios, and collinearity diagnostics – **file(s)**: `tests/unit/test_edge_cases.py`
- [ ] T054 [P] Create quick‑start validation script `scripts/quickstart.sh` that clones the repo, installs dependencies, runs the full pipeline, and checks that all expected artifacts exist; add integration test `tests/integration/test_quickstart.sh` – **file(s)**: `scripts/quickstart.sh`, `tests/integration/test_quickstart.sh`
- [ ] T055 [P] Verify that `.env` is populated from `.env.example` and that `code/data_ingestion.py` reads API keys from it – **file(s)**: `.env.example`, `tests/integration/test_env_loading.py`
- [ ] T056 [P] Verify that the virtual environment (`venv/`) is created and that `pip freeze` matches `code/requirements.txt` – **file(s)**: `scripts/create_venv.sh`, `tests/integration/test_venv_creation.py`
- [ ] T057 [P] Verify that `code/config.yaml` contains the keys `sensitivity_masking_proportions` and `p_value_shift_threshold` – **file(s)**: `code/config.yaml`, `tests/unit/test_config_values.py`
- [ ] T058 [P] Verify that `code/preprocessing.py` raises an exception when missing values remain after interpolation – **file(s)**: `code/preprocessing.py`, `tests/unit/test_missing_values_exception.py`
- [ ] T059 [P] Verify that the master notebook runs end‑to‑end without error (re‑uses T071) – **file(s)**: `tests/integration/test_notebook_execution.py`
- [ ] T060 [P] Verify that all generated figures include recession shading and that the final PDF report metadata lists all dataset URLs/DOIs – **file(s)**: `tests/contract/test_figure_metadata.py`