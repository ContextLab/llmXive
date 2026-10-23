# Tasks: Estimating Causal Effects with Doubly Robust Methods on Observational Data

**Inputs**: `spec.md`, `plan.md`, reviewer comments, existing source layout, contracts, and data‑model definitions.

The checklist below implements the full research pipeline, from a reproducible end‑to‑end run on a tiny synthetic dataset to the complete Monte‑Carlo study, meta‑regression, visual diagnostics, and a paper‑stage hand‑off.  
All tasks are unchecked; the platform will automatically check a task when its verification steps succeed.

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run a minimal, fully reproducible pipeline on a small synthetic dataset and confirm that the true ATE is computed analytically within the required tolerance. |
|------|--------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T001** [P] [US1] **Update `spec.md`** – correct the feature‑branch name (`001-gene-regulation` → `001-estimating-causal-effects-with-doubly-ro`) and refine User Story 1’s acceptance criterion so that *the calculated true ATE must be analytically computable and match the theoretical expectation within a tolerance of 0.001*.  
  - **Path**: `specs/001-estimating-causal-effects-with-doubly-ro/spec.md`  
  - **Verification**: `pytest tests/unit/test_spec_updates.py` checks that the branch name matches the spec folder and that the tolerance clause contains the phrase “analytically computable … within 0.001”.

- [ ] **T002** [P] [US1] **Implement DGP generator and true‑ATE calculator** – create `src/dgp.py` with functions `generate_data(config: SimulationConfig) -> pd.DataFrame` and `compute_true_ate(config: SimulationConfig) -> float`. Use `pyDOE2` for covariates, a logistic propensity that includes the `X₁·X₂` interaction, and the non‑linear outcome  
  \[
  Y = \sin(X_1) + X_2^2 + 0.3\,X_1X_2 + 0.5\,T + \varepsilon .
  \]  
  - **Path**: `src/dgp.py`  
  - **Verification**: `tests/unit/test_dgp.py` asserts that for a fixed seed the true ATE returned by `compute_true_ate` matches the analytic value within `1e‑3`.

- [ ] **T003** [P] [US1] **Add `quickstart.md` with an executable CLI command** – document a command that runs a minimal end‑to‑end example (`N=500`, correct outcome & propensity models) and writes the result to `data/results/example_estimation.csv`.  
  - **Path**: `docs/quickstart.md`  
  - **Verification**: Running the documented command (`python -m src.cli --config config/example.yaml`) creates the CSV file and prints “✅ end‑to‑end run successful”.

- [ ] **T004** [P] [US2] **Implement the AIPW estimator** – create `src/estimators/aipw.py` with function `fit_aipw(outcome_model, propensity_model, X, T, Y) -> EstimationResult`. The implementation must  
  1. fit the supplied outcome and propensity wrappers,  
  2. clip propensity scores to `[0.01, 0.99]`,  
  3. compute the AIPW estimate, its standard error, a 95 % CI, bias, and coverage flag.  
  - **Path**: `src/estimators/aipw.py`  
  - **Verification**: `tests/unit/test_aipw.py` fits a linear outcome & correctly specified logistic propensity on a synthetic linear DGP and checks that `|bias| < 0.01` and that the CI covers the true ATE in ≥ 95 % of 200 bootstrap replications.

---

## Phase 2 – Complete the study and validate its evidence  

| Goal | Execute the full misspecification grid, aggregate metrics, perform meta‑regression, generate visual diagnostics, and confirm that the pipeline respects the GitHub‑Actions runtime & memory limits. |
|------|-----------------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T005** [P] [US2] **Create model wrappers** – add `src/models/outcome.py` and `src/models/propensity.py` exposing classes `NonlinearCorrect`, `QuadraticMissingSine`, `InteractionOmitted` (outcome) and `LogisticCorrect`, `LogisticMisspecified`, `LogisticInteractionHeavy` (propensity). Each class implements `fit(X, y)` / `fit(X, T)` and `predict(X)`.  
  - **Path**: `src/models/` (both files)  
  - **Verification**: `tests/unit/test_model_wrappers.py` fits each wrapper on a tiny dataset, checks that predictions are numeric, and confirms that misspecified wrappers deliberately omit the intended terms (e.g., no sine term for `QuadraticMissingSine`).

- [ ] **T006** [P] [US2] **Build single‑replication driver** – extend `src/simulation.py` with a function that (1) loads a `SimulationConfig`, (2) calls `generate_data`, (3) runs `fit_aipw`, (4) computes bias/coverage, and (5) writes a single `EstimationResult` record to  
  `data/interim/estimation_results_{hash}.parquet`. The record must validate against `contracts/estimation_result.schema.yaml`.  
  - **Path**: `src/simulation.py`  
  - **Verification**: `tests/unit/test_simulation_driver.py` runs one replication and asserts that the parquet file exists, contains the required columns, and passes schema validation.

- [ ] **T007** [P] [US2] **Orchestrate the full misspecification grid** – in `src/simulation.py` add a grid loop over  
  *outcome_model* × *propensity_model* × *sample_size* (`{500, 1000, 2000}`) and execute **1 000 Monte‑Carlo replications per cell**. Results are streamed to per‑cell parquet files `data/interim/estimation_results_{cell_hash}.parquet` (no in‑memory accumulation). Use `psutil` to log peak RAM and total runtime; abort with a clear error if peak RAM > 7 GB.  
  - **Path**: `src/simulation.py` (grid function)  
  - **Verification**: A smoke‑run with `replications=10` creates 9 parquet files and a `data/processed/memory_report.json` showing `peak_memory_gb ≤ 7`. `tests/integration/test_grid_smoke.py` checks these conditions.

- [ ] **T008** [P] [US3] **Aggregate metrics per configuration** – implement `src/analysis/aggregate.py` that reads all interim parquet files, groups by `{outcome_model, propensity_model, sample_size}`, and computes  
  * mean bias,  
  * standard error of mean bias,  
  * empirical coverage rate,  
  * (later) interaction term placeholder.  
  Results are written to `data/processed/aggregated_metrics.parquet` and must conform to `contracts/aggregated_metrics.schema.yaml`.  
  - **Path**: `src/analysis/aggregate.py`  
  - **Verification**: `tests/unit/test_aggregation.py` asserts that for every cell where either the outcome **or** propensity model is correctly specified, ≥ 95 % of replications have `bias < 0.05` (SC‑001) and that the coverage rate is within 0.03 of the nominal 0.95 (SC‑003).

- [ ] **T009** [P] [US3] **Perform categorical meta‑regression** – add `src/analysis/meta_regression.py` which fits an ANOVA‑style OLS model  
  ```
  bias ~ C(outcome_model) + C(propensity_model) + C(outcome_model):C(propensity_model)
  ```  
  using HC3 robust SEs. Store the full coefficient table (estimates, robust SEs, p‑values) in `data/processed/meta_regression_results.yaml`.  
  - **Path**: `src/analysis/meta_regression.py`  
  - **Verification**: `tests/unit/test_meta_regression.py` runs the routine on two synthetic datasets (one with a known zero interaction, one with a strong injected interaction) and checks that the interaction p‑value is > 0.05 in the former and < 0.05 in the latter (SC‑002).

- [ ] **T010** [P] [US3] **Generate bias heat‑maps** – implement `src/analysis/visualizations.py` to produce, for each sample size, a heat‑map PNG `figures/bias_heatmap_N{size}.png` where cell colour reflects mean bias magnitude and cells with bias > 0.1 are highlighted in red.  
  - **Path**: `src/analysis/visualizations.py` and `figures/` output directory  
  - **Verification**: `tests/unit/test_visualizations.py` confirms that each PNG exists, has dimensions ≥ 600 px, and that at least one cell is coloured red (bias > 0.1).

- [ ] **T011** [P] [US4] **Produce memory & runtime summary** – after the grid finishes, write `data/processed/memory_report.json` containing `peak_memory_gb`, `total_runtime_seconds`, and a boolean `within_limits` (true if peak ≤ 7 GB and runtime ≤ 6 h).  
  - **Path**: `data/processed/memory_report.json` (generated by the grid driver)  
  - **Verification**: `tests/unit/test_memory_report.py` runs a short grid (10 replications per cell) and asserts `within_limits == true`.

- [ ] **T012** [P] **Validate contracts & schema conformity** – run the contract test suite to ensure every artifact written by the pipeline validates against its YAML schema. No schema changes are expected.  
  - **Path**: `tests/contract/` (existing)  
  - **Verification**: `pytest -q tests/contract/` must exit with zero failures.

---

## Phase 3 – Reproducible results and paper hand‑off  

| Goal | Produce a concise, verifiable methods‑and‑results record and guarantee that the whole pipeline can be re‑run from a single configuration file. |
|------|------------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T013** [P] **Draft `research.md` (methods & results)** – summarize the DGP, model families, grid layout, and key quantitative findings: mean bias per cell, interaction‑term estimate (with p‑value), coverage rates, and memory/runtime statistics. Embed hyperlinks to the concrete artifacts (`data/processed/aggregated_metrics.parquet`, `data/processed/meta_regression_results.yaml`, `figures/*.png`).  
  - **Path**: `docs/research.md`  
  - **Verification**: `python -m src.analysis.verify_research_claims docs/research.md` parses the markdown, loads the linked files, and asserts that the reported numbers match the stored values.

- [ ] **T014** [P] **Add a reproducible CI step (managed by the platform)** – update the workflow configuration (`.github/workflows/ci.yml`) to run the full study via `python -m src.cli --config config/full_study.yaml`, then execute the full test suite (including contract and verification tests). Also point `quickstart.md` to `config/full_study.yaml` for the official reproducible run.  
  - **Path**: `.github/workflows/ci.yml` and `docs/quickstart.md` (updated link)  
  - **Verification**: A fresh GitHub Actions run finishes with all tasks marked “✅” and the final artifact hash recorded in `state/project_artifacts.yaml`.

---

## Dependency / Requirement Mapping  

| Spec / FR ID | Covered by Task(s) |
|--------------|--------------------|
| FR‑001 | T002, T003 |
| FR‑002 | T004, T005 |
| FR‑003 | T007 |
| FR‑004 | T006, T008 |
| FR‑005 | T009 |
| FR‑006 | T010 |
| FR‑007 | T004 (CI‑based CI), T008 (coverage) |
| SC‑001 | T008 |
| SC‑002 | T009 |
| SC‑003 | T008 |
| SC‑004 | T007, T011 |
| SC‑005 | T002 |
| Constitution III | T012 |
| Constitution V | T012 |

All scientific requirements from the specification are represented, and task ordering respects the data flow: data generation → model fitting → estimation → aggregation → analysis → visualization → reporting.
