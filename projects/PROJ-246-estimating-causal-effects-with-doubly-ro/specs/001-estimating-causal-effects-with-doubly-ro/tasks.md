# Tasks: Estimating Causal Effects with Doubly Robust Methods on Observational Data

**Inputs**: `spec.md`, `plan.md`, reviewer comments, existing source layout, contracts, and data‑model definitions.

The following checklist implements the full research pipeline, from a reproducible end‑to‑end run on a small synthetic dataset to the complete Monte‑Carlo study, meta‑regression, and hand‑off.  All tasks are unchecked; completed tasks will be checked automatically by the platform when their verification steps succeed.

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run a minimal, fully reproducible pipeline on a tiny synthetic dataset and confirm that the true ATE is computed correctly. |
|------|--------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T001** [P] Update `spec.md`  
  - Correct the feature‑branch name (`001-gene-regulation` → `001-estimating-causal-effects-with-doubly-ro`).  
  - Refine **User Story 1** acceptance: the true ATE must be *analytically* computed (or via a high‑precision Monte‑Carlo reference) and verified against the analytical value within a tolerance of **0.001**.  
  - **Verification**: `pytest tests/unit/test_spec_updates.py` checks that the branch name matches the spec filename and that the tolerance clause contains “analytically computed”.

- [ ] **T002** [P] Implement DGP generator `src/dgp.py`  
  - Provide functions `generate_data(config: SimulationConfig) -> pd.DataFrame` and `compute_true_ate(config: SimulationConfig) -> float`.  
  - Use `pyDOE2` to draw covariates, define treatment assignment via a logistic propensity, and outcome via the non‑linear DGP $Y = \sin(X_1) + X_2^2 + \epsilon$.  
  - **Verification**: `tests/unit/test_dgp.py` asserts that for a fixed seed the true ATE matches the analytical expression within `1e‑3`.

- [ ] **T003** [P] Add `quickstart.md` with a runnable command  
  - Command example: `python -m src.cli --config config/example.yaml`.  
  - The example config runs `N=500`, uses the *correct* outcome and propensity models, and writes results to `data/results/example_estimation.csv`.  
  - **Verification**: Running the command produces the CSV file and the script prints “✅ end‑to‑end run successful”.

- [ ] **T004** [P] Implement AIPW estimator `src/estimators/aipw.py`  
  - Function `fit_aipw(outcome_model, propensity_model, X, T, Y) -> EstimationResult`.  
  - Supports plugging any model wrapper from `src/models/`.  
  - Clips propensity scores to `[0.01, 0.99]`.  
  - **Verification**: `tests/unit/test_aipw.py` fits a linear outcome & logistic propensity on a synthetic linear DGP and checks that `|bias| < 0.01` and that 95% CIs are computed with correct coverage for the true value.

- [ ] **T005** [P] Build single‑replication driver `src/simulation.py`  
  - Loads a `SimulationConfig`, calls `generate_data`, fits AIPW, computes bias, CI, coverage, and writes a single `EstimationResult` record to `data/interim/estimation_results_{hash}.parquet`.  
  - Validates the record against `contracts/estimation_result.schema.yaml`.  
  - **Verification**: `tests/unit/test_simulation_driver.py` runs one replication and asserts the parquet file exists and conforms to the schema.

---

## Phase 2 – Complete the study and validate its evidence  

| Goal | Execute the full misspecification grid, aggregate metrics, perform meta‑regression, and produce visual diagnostics while respecting the CI runner limits. |
|------|-----------------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T006** [P] Create model wrappers in `src/models/`  
  - **Outcome models**: `nonlinear_correct`, `quadratic`, `interaction_omitted`.  
  - **Propensity models**: `logistic_correct`, `logistic_misspecified`, `logistic_interaction_heavy`.  
  - Each wrapper implements `fit(X, T/Y)` and `predict(X)`.  
  - **Verification**: `tests/unit/test_model_wrappers.py` fits each wrapper on a tiny dataset and checks that predictions are numeric and that misspecified wrappers deliberately omit the intended terms.

- [ ] **T007** [P] Implement grid orchestration in `src/simulation.py`  
  - Loops over outcome‑model × propensity‑model × sample‑size (`{500, 1000, 2000}`) and runs **1 000** Monte‑Carlo replications per cell.  
  - Streams each `EstimationResult` to `data/interim/estimation_results_{cell_hash}.parquet` (no in‑memory accumulation).  
  - Logs progress, runtime, and peak memory (via `psutil`).  
  - **Verification**: After a short “smoke‑run” with `replications=10` the script produces 9 parquet files and a `data/processed/memory_report.json` showing peak ≤ 7 GB.

- [ ] **T008** [P] Compute aggregated metrics `src/analysis/aggregate.py`  
  - Reads all interim parquet files, groups by `{outcome_model, propensity_model, sample_size}` and calculates: `mean_bias`, `se_bias`, `coverage_rate`.  
  - Writes `data/processed/aggregated_metrics.parquet`.  
  - **Verification**: `tests/unit/test_aggregation.py` asserts that for ALL correctly specified cells ≥ 95 % of replications have `bias < 0.05` (SC‑001) and that the empirical coverage probability matches the nominal 0.95 level within tolerance (SC‑003).

- [ ] **T009** [P] Perform meta‑regression `src/analysis/meta_regression.py`  
  - Fits an ANOVA‑style linear model with categorical factors `outcome_model`, `propensity_model`, and their interaction on the bias values.  
  - Stores coefficients, standard errors, and p‑values in `data/processed/meta_regression_results.yaml`.  
  - **Verification**: `tests/unit/test_meta_regression.py` runs the routine on two datasets: one where the interaction is zero (p > 0.05) and one where a strong interaction is injected, asserting the p-value < 0.05 (SC‑002).

- [ ] **T010** [P] Generate heat‑map visualizations `src/analysis/visualizations.py`  
  - Creates a bias heatmap for each sample size, saved as `figures/bias_heatmap_N{size}.png`.  
  - Highlights cells with bias > 0.1 in red.  
  - **Verification**: `tests/unit/test_visualizations.py` confirms that the PNG file exists, has dimensions ≥ 600 px, and that the red overlay appears for at least one cell.

- [ ] **T011** [P] Add memory‑usage monitoring (already logged in T007) and produce a summary report  
  - `data/processed/memory_report.json` contains `peak_memory_gb`, `total_runtime_seconds`, and a boolean `within_limits`.  
  - **Verification**: `tests/unit/test_memory_report.py` asserts `within_limits` is `true` for the smoke‑run.

- [ ] **T012** [P] Validate contracts and schema conformity  
  - Run `pytest tests/contract/test_estimation_result_schema.py` to ensure every `EstimationResult` written by the pipeline validates against `contracts/estimation_result.schema.yaml`.  
  - Update the schema only if a new field is introduced (none expected).  
  - **Verification**: CI passes the contract tests without errors.

- [ ] **T015** [P] Implement data checksumming utility `src/utils/checksum.py`  
  - Provide a utility to compute SHA-256 checksums for all files under `data/` and write them to a `data/checksums.json` manifest.  
  - **Verification**: `pytest tests/unit/test_checksum.py` confirms SHA-256 hashes are correctly calculated and recorded for a sample file.

- [ ] **T016** [P] Update project state map `src/utils/state_manager.py`  
  - Implement a function to sync the `data/checksums.json` manifest into the `state/projects/PROJ-246-estimating-causal-effects-with-doubly-ro.yaml` `artifact_hashes` map.  
  - **Verification**: `pytest tests/unit/test_state_manager.py` asserts that the state YAML contains updated hashes for all artifacts produced in Phase 2.

---

## Phase 3 – Reproducible results and paper hand‑off  

| Goal | Produce a concise, verifiable methods/results record and guarantee that the whole pipeline can be re‑run from a single config file. |
|------|------------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T013** [P] Draft `research.md` (methods & results)  
  - Summarize the DGP, model families, grid layout, and key quantitative findings: mean bias per cell, interaction‑term estimate (with p‑value), coverage rates, and memory/runtime statistics.  
  - Embed links to the concrete artifacts: `data/processed/aggregated_metrics.parquet`, `data/processed/meta_regression_results.yaml`, and `figures/*.png`.  
  - **Verification**: Run `python -m src.analysis.verify_research_claims` which parses `research.md` and asserts all linked files exist and contain the claimed values.

- [ ] **T014** [P] Add a full‑pipeline CI step to `/.github/workflows/ci.yml` (managed by the platform)  
  - The step runs `python -m src.cli --config config/full_study.yaml` and, after completion, executes `pytest` to confirm all verification scripts succeed.  
  - Update `quickstart.md` to point to `config/full_study.yaml` for the official reproducible run.  
  - **Verification**: Running the CI workflow on a fresh runner finishes with all tasks marked “✅” and the final artifact hash matches the one recorded in `state/project_artifacts.yaml`.

---

## Dependency / Requirement Mapping  

| Spec / FR ID | Covered by Task(s) |
|--------------|--------------------|
| FR‑001 | T002, T003 |
| FR‑002 | T004, T006 |
| FR‑003 | T007 |
| FR‑004 | T005, T008 |
| FR‑005 | T009 |
| FR‑06 | T010 |
| FR‑007 | T004 (CI), T008 (coverage) |
| SC‑001 | T008 |
| SC‑002 | T009 |
| SC‑003 | T008 |
| SC‑004 | T007, T011 |
| SC‑005 | T002 |
| Constitution III | T015 |
| Constitution V | T016 |

All scientific requirements from the specification are represented by at least one task, and the ordering respects data flow: data generation → model fitting → estimation → aggregation → analysis → visualization → reporting.