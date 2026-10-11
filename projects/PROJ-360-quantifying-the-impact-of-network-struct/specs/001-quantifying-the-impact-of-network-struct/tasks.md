# Tasks: Quantifying the Impact of Network Structure on Heat Diffusion in Crystalline Solids

**Input**: Design documents from `/specs/001-network-structure-thermal-conductivity/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks where explicitly requested in the feature specification.

## Phase 1 – Setup and first end‑to‑end analysis  

**Goal**: Establish a runnable pipeline on a small real input before expanding to the full study.

- [ ] T001 [P] Create directory `data/raw/cif/` – ensures a place for downloaded CIF files.  
- [ ] T002 [P] Create directory `data/processed/networks/` – stores atomic network graph objects.  
- [ ] T003 [P] Create directories `data/processed/`, `models/`, `results/`, `code/` – project‑level folder layout.  
- [ ] T004 [P] Initialise a Python 3.11 project with pinned dependencies (`pymatgen`, `networkx`, `scikit-learn`, `pandas`, `requests`, `numpy`, `statsmodels`) – `code/requirements.txt`.  
- [ ] T005 [P] Add a minimal `quickstart.md` stub (to be expanded later) – `specs/001-network-structure-thermal-conductivity/quickstart.md`.  

## Phase 2 – Foundational (blocking prerequisites)

**Purpose**: Core utilities that must exist before any user‑story work can start.

- [ ] T006 [P] Implement `code/utils.py` with:
  - deterministic seed pinning,
  - exponential‑backoff retry helper,
  - a simple logger wrapper.  
- [ ] T007 [P] Add `code/config.py` defining a `Config` class that loads the Materials Project API key from `MATERIALS_PROJECT_API_KEY` and stores a fixed random‑seed dictionary.  
- [ ] T008 [P] Create `data/metadata.yaml` schema to record download timestamps, material IDs, and SHA‑256 checksums for raw CIFs and derived artifacts.  

## Phase 3 – User Story 1: Download & construct atomic networks (Priority P1)

**Goal**: Obtain ≥ 50 CIF files, build corresponding atomic‑network graphs, and validate basic structure.

- [ ] T009 [US1] `code/download.py` – query the Materials Project API for materials that have a thermal‑conductivity tensor, download CIFs to `data/raw/cif/`, compute SHA‑256 checksums, and write entries to `data/metadata.yaml`.  
- [ ] T036a [US1] Verify that **≥ 50** CIF files were successfully downloaded in `data/raw/cif/`. Fail the pipeline if the count is lower.  
- [ ] T010 [US1] `code/construct_network.py` – parse each CIF with `pymatgen`, create bonds using covalent‑radius + tolerance, apply progressive fallback cut‑offs (4.0 Å → 4.5 Å), and build a `networkx.Graph`.  
- [ ] T011 [US1] Save each graph as a pickle file in `data/processed/networks/` (filename `<material_id>.pkl`).  
- [ ] T012 [US1] `code/validate_graphs.py` – verify every graph has ≥ 2 nodes and ≥ 1 edge; log and skip any material that remains disconnected after fallbacks.  

## Phase 4 – User Story 2: Compute metrics & correlate with thermal conductivity (Priority P2)

**Goal**: Derive ≥ 3 network metrics per material, merge physical descriptors, and perform correlation analysis with proper multiple‑testing correction.

- [ ] T013 [US2] `code/compute_metrics.py` – for each validated graph compute:
  - average degree,
  - average shortest‑path length on the largest connected component (NaN if fully disconnected),
  - global clustering coefficient,
  and also extract unit‑cell volume, atom count, and mean atomic mass via `pymatgen`.  
  Output a consolidated `data/processed/metrics.csv` containing all columns required by `metrics.schema.yaml`.  
- [ ] T014 [US2] `code/analyze.py` – load `metrics.csv`, apply a Shapiro‑Wilk normality test; if any variable is non‑normal (p < 0.05) apply a log‑transformation and write the transformed table to `data/processed/metrics_transformed.csv`.  
- [ ] T015 [US2] Compute Pearson and Spearman correlation coefficients between each network metric and the scalar thermal conductivity (mean of kₓ,k_y,k_z). Store raw results in `results/correlations_raw.json`.  
- [ ] T015b [US2] Validate `results/correlations_raw.json` against `contracts/correlation.schema.yaml`.  
- [ ] T016 [US2] Apply Bonferroni correction across the three metric‑conductivity tests; write results to `results/correlations.json` conforming to `correlation.schema.yaml`.  
- [ ] T017 [US2] Log the final sample size; if n < 50 emit a warning in `results/power_analysis.log`.  

## Phase 5 – User Story 3: Train predictive model & validate (Priority P3)

**Goal**: Build a linear regression model using VIF‑filtered features and evaluate via k‑fold cross‑validation.

- [ ] T018 [US3] Calculate Variance Inflation Factor for all candidate features (network metrics + physical descriptors) from `metrics.csv`; drop any feature with VIF ≥ 5 and write the retained list to `data/processed/filtered_features.csv`.  
- [ ] T019 [US3] Train a `LinearRegression` model on the filtered feature set to predict scalar thermal conductivity; serialize the model to `models/thermal_predictor.pkl`.  
- [ ] T020 [US3] Perform stratified k‑fold cross‑validation (default k = 5; if n < 10 use `k = min(n‑1, 2)`) by binning the target into 5 quantile bins for stratification. Compute R² and RMSE for each fold and aggregate mean ± std. Save to `results/model_performance.json` per `model_performance.schema.yaml`.  
- [ ] T021 [US3] Generate a residual plot (predicted vs. actual thermal conductivity) for the baseline model and save as `results/model_residuals.png`.  
- [ ] T032 [US3] Perform a robustness regression using VIF‑filtered metrics **and** physical descriptors; record R², RMSE, and coefficients in `results/robustness_check.json`.  
- [ ] T032b [US3] Verify that `results/robustness_check.json` contains the keys `r2`, `rmse`, and `coefficients` with appropriate value types.  
- **New** - [ ] T032c [US3] Add JSON schema `specs/001-quantifying-the-impact-of-network-struct/contracts/robustness_check.schema.yaml` defining the required structure of `results/robustness_check.json` (fields: `r2` [number], `rmse` [number], `coefficients` [object] mapping feature names to numbers).  
- **New** - [ ] T032d [US3] Add a contract‑test task that validates `results/robustness_check.json` against the newly created `robustness_check.schema.yaml` using the existing schema‑validation utilities.  

## Phase 6 – Report generation & hand‑off

**Goal**: Produce a reproducible report that contains all required sections and verification artefacts.

- [ ] T022 [US3] `code/report.py` – read `model_performance.json` and `correlations.json`, embed tables/figures, and insert the mandatory “Limitations” paragraph verbatim:  
  > This study is observational. Correlations do not imply causality. The thermal conductivity tensor was reduced to a scalar by averaging principal components, which may obscure anisotropic effects.  
  Additionally, add a paragraph summarizing the sample size (`n = <value>`) and whether a power‑warning was triggered. Write the markdown report to `results/final_report.md`.  

## Phase 7 – Polish, documentation & robustness checks  

- [ ] T028 Update `quickstart.md` – add a concise “Run the full pipeline” command block and a verification step:  
  ```bash
  python -m code.download
  python -m code.construct_network
  python -m code.compute_metrics
  python -m code.analyze
  python -m code.report
  ```  
  Then state: *“Verify the report contains the mandatory Limitations paragraph by grepping for the exact sentence.”*  
  **File**: `specs/001-quantifying-the-impact-of-network-struct/quickstart.md`.  
- [ ] T023 [P] Verify that `results/final_report.md` contains the exact “Limitations” text (string match).  
- [ ] T024 Run the full pipeline end‑to‑end (`code/download.py → code/construct_network.py → code/compute_metrics.py → code/analyze.py → code/report.py`) and confirm that all artefacts (`data/processed/metrics.csv`, `results/correlations.json`, `results/model_performance.json`, `results/final_report.md`) exist and pass their respective schema checks.  
- [ ] T036 Verify that the **final processed dataset** (`data/processed/metrics.csv`) contains **≥ 50** materials; fail if the count is lower.  
- [ ] T037 Measure total runtime of the full pipeline (from start of `code/download.py` to completion of `code/report.py`). Fail if runtime exceeds **6 hours** (21600 seconds).  

## Phase 8 – Final verification & hand‑off to paper stage  

- [ ] T034 Update `quickstart.md` (from T028) with a link to `results/final_report.md` and a short “Expected outcome” description (e.g., “A PDF‑compatible markdown report containing correlation tables, model performance metrics, and the mandatory Limitations section”).  
- [ ] T035 Run the verification suite (`pytest`) to ensure all contract schemas are satisfied and that the three pending artefacts (`quickstart.md`, `results/robustness_check.json`, `results/model_residuals.png`) are present and non‑empty.  

### Dependency summary

| Requirement | Satisfying task(s) |
|-------------|-------------------|
| FR‑001 (download ≥ 50 CIFs) | T009, T036a |
| FR‑002 (bond detection with fallbacks) | T010, T011 |
| FR‑003 (compute ≥ 3 metrics) | T013 |
| FR‑004 (Pearson & Spearman correlations) | T015 |
| FR‑005 (Bonferroni correction) | T016 |
| FR‑006 (train linear regression) | T019 |
| FR‑007 (k‑fold CV) | T020 |
| FR‑008 (Limitations section) | T022 |
| FR‑009 (VIF filtering) | T018 |
| FR‑010 (power‑size warning) | T017, T022 |
| SC‑003 (≥ 50 materials) | T036a, T036 |
| SC‑005 (≤ 6 h runtime) | T037 |
| US‑1, 2, 3 coverage | T009‑T021 |
| Review‑driven robustness | T032, T032b, T032c, T032d |
| Documentation hand‑off | T028, T034, T035 |

All previously checked tasks remain unchanged; pending tasks have been clarified, safety‑tagged, and new verification steps added to satisfy every panel concern.  