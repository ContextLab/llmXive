# Tasks: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

**Input**: `spec.md`, `plan.md`, existing research artifacts.  
**Goal**: Produce a fully reproducible end‑to‑end analysis that satisfies every functional requirement in the specification, using only real data and real computation.

---

## Phase 1 – Project scaffolding (foundational, must be completed before any user‑story work)

- [ ] **T001** [P] Create the canonical project directories (`src/`, `tests/`, `specs/`) and add a minimal `README.md` documenting the layout.  
  *Verification*: `tree -L 2` shows the three top‑level folders and the README file.

- [ ] **T002** [ P ] Add linting/formatting configuration (`pyproject.toml` with **ruff** and **black** settings, plus a `.ruff.toml` if desired) and commit a CI‑compatible `ruff check` command.  
  *Verification*: Running `ruff check .` returns “0 errors”.

- [ ] **T003** [ P ] Create an environment‑management stub: an example `.env.example` describing required variables (`DATA_ROOT`, `OPENNEURO_TOKEN`), and a tiny helper module `src/utils/config.py` that loads the file and provides defaults.  
  *Verification*: Importing `src.utils.config` prints the resolved configuration without raising.

- [ ] **T004** [ P ] Add the dataset and output JSON‑Schema contracts required by the spec:  
  - `specs/001-investigating-the-relationship-between-b/contracts/dataset.schema.yaml`  
  - `specs/001-investigating-the-relationship-between-b/contracts/output.schema.yaml`  
  *Verification*: `jsonschema.validate(example.json, schema.yaml)` succeeds for a provided example.

- [ ] **T005** [ P ] Implement Pydantic models for `Subject`, `ConnectivityMatrix`, `NetworkMetrics`, and `BehavioralScore` in `src/models/schemas.py`.  
  *Verification*: Unit tests in `tests/contract/test_schemas.py` pass.

- [ ] **T006** [ P ] Configure basic logging (`src/utils/logging.py`) with reproducibility metadata (seed, timestamps, package versions).  
  *Verification*: Log file contains the required fields.

- [ ] **T007** [ P ] Add contract‑validation tests (`tests/contract/test_schemas.py`, `tests/contract/test_data_schema.py`, `tests/contract/test_results_schema.py`).  
  *Verification*: All contract tests run and succeed.

---

## Phase 2 – User Story 1: Data acquisition & preprocessing (Priority P1)

- [ ] **T008** [US1] Implement `src/data/download.py` to **stream** the OpenNeuro ds000233 metadata, verify that the BMRQ column exists, and download for a given subject ID: the raw rs‑fMRI NIfTI file and the behavioral CSV. Compute SHA‑256 checksums and abort loudly if the BMRQ column is missing.  
  *Verification*: Running `python -m src.data.download --subject 001` creates `data/raw/001/func.nii.gz` and `data/raw/001/behav.csv`; checksum files are written; the script exits with a non‑zero code if BMRQ is absent.

- [ ] **T009** [US1] When a missing BMRQ is detected, generate a **Data Gap Report** (`data/data_gap_report.md`) that lists the missing variable and terminates with exit code 1.  
  *Verification*: The report file is created and contains a clear statement of the missing column; the process exits with status 1.

- [ ] **T010** [US1] Implement `src/data/preprocess.py` – a thin wrapper that calls **fMRIPrep** in CPU‑only mode on a single subject (dry‑run for CI). The script must:  
  1. Run fMRIPrep with motion correction and band‑pass filtering (0.01–0.1 Hz).  
  2. Compute mean Framewise Displacement (FD).  
  3. Write a run‑log JSON (`data/preprocessing/run_log.json`) containing the subject ID, FD value, and a pass/fail flag.  
  *Verification*: After execution, `run_log.json` exists, contains `"fd_mean": <float>`, and `"motion_excluded": true/false` as appropriate.

- [ ] **T011** [US1] Add **motion‑exclusion logic** to `src/data/preprocess.py`: if `fd_mean > 0.5 mm` the subject is flagged as excluded and the run‑log records `"motion_excluded": true`. Down‑stream scripts must respect this flag.  
  *Verification*: For a subject with artificially high FD (e.g., by passing `--fd 0.6`), the log shows `"motion_excluded": true` and downstream tasks skip that subject.

- [ ] **T012** [US1] Implement `src/analysis/connectivity.py` to load the **Schaefer‑200** atlas, extract the preprocessed time‑series, compute a **Pearson correlation matrix** (200 × 200), enforce symmetry, set the diagonal to 1.0, and save as `data/connectivity/<subject>_matrix.npy`.  
  *Verification*: The saved NumPy array passes a sanity‑check script that confirms symmetry (`np.allclose(m, m.T)`) and `np.allclose(np.diag(m), 1.0)`.

---

## Phase 3 – User Story 2: Graph‑metric calculation & dataset merging (Priority P2)

- [ ] **T013** [US2] Implement `src/analysis/graph_metrics.py` to compute, for each subject’s connectivity matrix:  
  - Global efficiency, modularity, participation coefficient.  
  - Network‑specific efficiencies for **DMN**, **Salience**, and **Visual** (using Schaefer label sets).  
  - Edge‑level strengths (flattened upper‑triangle).  
  The script must also calculate **VIF** for all predictors; if any VIF > 5, apply a **PCA** (retain components explaining ≥ 95 % variance) and store the transformed features. Output files:  
  - `data/metrics/<subject>_metrics.json` (raw metrics)  
  - `data/vif_report.json` (global VIF values)  
  - `data/metrics/<subject>_metrics_pca.json` (if PCA applied)  
  *Verification*: JSON files validate against `output.schema.yaml`; VIF report contains numeric entries; PCA file exists when needed.

- [ ] **T014** [US2] Implement `src/analysis/merge.py` to **join** the per‑subject metric files with the behavioral data (BMRQ, age, sex, FD) while:  
  1. Excluding any subject flagged `motion_excluded` or missing BMRQ.  
  2. Writing the final analysis table to `data/merged_dataset.csv`.  
  3. Adding a summary line (printed to console) reporting the final **sample size (N)** and the distribution (mean ± SD) of BMRQ scores.  
  *Verification*: The CSV contains only subjects that pass all inclusion criteria; the header includes all required columns; a quick‑look script prints `N = <int>` and `BMRQ mean = …`.

- [ ] **T015** [US2] Perform a **power analysis** (Task 3.1) inside `src/analysis/stats.py`: given the current `N`, compute achieved power for detecting an effect size `r = 0.20` at `α = 0.05`. Write `data/power_gate_status.json` (`{"status":"pass","achieved_power":0.87}`) and, if power < 0.80, also generate `data/power_failure_report.md` explaining the shortfall.  
  *Verification*: The JSON file exists and matches the schema; the CI step aborts with a non‑zero exit code when status is `"fail"`.

---

## Phase 4 – User Story 3: Statistical modelling & hypothesis testing (Priority P3)

- [ ] **T016** [US3] In `src/analysis/stats.py`, implement **partial correlation** between each network metric and the BMRQ total score, controlling for age, sex, and FD. Apply **FDR correction** (q < 0.05) across all tests. Save results to `data/analysis_results.csv` adhering to `output.schema.yaml`.  
  *Verification*: The CSV validates against the output schema; a column `significant` is `True` only when the FDR‑adjusted p‑value < 0.05.

- [ ] **T017** [US3] Also in `src/analysis/stats.py`, fit a **regularized linear regression** (Ridge + Lasso) with **5‑fold cross‑validation** to predict BMRQ scores from the full set of predictors. Output:  
  - `data/regression_cv_results.json` (mean R², per‑fold R², selected coefficients)  
  - `data/null_model_results.json` (intercept‑only baseline R²)  
  *Verification*: Both JSON files exist; the CV results show an R² > baseline; the null‑model file contains `"r2": 0.0` (or the appropriate baseline value).

- [ ] **T018** [US3] Create visualisations in `src/analysis/visualize.py`:  
  1. Scatter plot of **predicted vs. actual** BMRQ scores (with regression line and annotated R²).  
  2. Bar chart of the **most predictive network metrics** (absolute coefficient magnitude).  
  Save figures to `figures/scatter_pred_actual.png` and `figures/metric_importance.png`.  
  *Verification*: Both PNG files are generated; a quick‑view script can open them without error.

---

## Phase 5 – Quick‑start & reproducibility hand‑off

- [ ] **T019** [ P ] Update `quickstart.md` with a single command that runs the full pipeline on a **single subject** (dry‑run mode) and produces the end‑to‑end artefacts (`data/connectivity`, `data/metrics`, `data/analysis_results.csv`).  
  *Verification*: Executing the command on the CI runner completes in < 15 min and all expected files appear.

- [ ] **T020** [ P ] Add a **reproducibility checklist** to `README.md` linking to the schema validation commands, the environment file, and the CI badge.  
  *Verification*: The checklist items are all “✅” after a fresh clone and `make test`.

---

### Dependency & execution order summary

| Phase | Prerequisite | Main output |
|------|---------------|-------------|
| 1 – Scaffolding | – | Directory tree, lint config, `.env.example`, schema files |
| 2 – Data acquisition | Phase 1 | `data/raw/<subj>/func.nii.gz`, `behav.csv`, `run_log.json` |
| 3 – Connectivity | Phase 2 | `data/connectivity/<subj>_matrix.npy` |
| 4 – Graph metrics & merge | Phase 3 | `data/metrics/*.json`, `data/merged_dataset.csv` |
| 5 – Power gate | Phase 4 | `data/power_gate_status.json` (must be `"pass"` to continue) |
| 6 – Statistics & viz | Phase 5 | `analysis_results.csv`, regression JSONs, figures |
| 7 – Quick‑start | All above | `quickstart.md` command runs end‑to‑end on N=1 |

All tasks marked **[P]** can run in parallel where their file targets differ; tasks with a **[USx]** label must respect the data‑flow dependencies shown above.

--- 

*All unchecked tasks are pending implementation; checked tasks have been verified to meet their respective verification criteria.*
