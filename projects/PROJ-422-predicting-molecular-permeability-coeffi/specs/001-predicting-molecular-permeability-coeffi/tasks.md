# Tasks: Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets  

**Inputs**: `spec.md`, `plan.md`, existing project skeleton under `code/` and `data/`, and the contracts in `specs/001‑predicting‑molecular‑permeability‑coeffi/`.  

The list follows the platform‑provided template (research → validation → hand‑off).  All tasks are written as markdown check‑boxes with the canonical `- [ ] T### [P?] [USx?] …` format.  Completed tasks are marked `[X]`.  Unchecked tasks must be implemented; checked tasks are retained only if they still satisfy the specification after the revisions below.

---  

## Phase 0 – Project bootstrap (shared infrastructure)

- [ ] **T001** Create `setup_dirs.sh` – a bash script that creates the nine required directories under the project root (`code/data`, `code/models`, `code/analysis`, `data/raw`, `data/processed`, `data/interim`, `results`, `tests/unit`, `tests/integration`).  
  *Verification*: `bash setup_dirs.sh && test -d code/data && test -d code/models && … && echo "All directories exist"`.

- [ ] **T002** Initialize a Python 3.11 virtual environment and pin all dependencies in `requirements.txt` (including `rdkit`, `torch`, `torch‑geometric`, `scikit‑learn`, `shap`, `gnnexplainer`, `pandas`, `datasets`, `statsmodels`).  
  *Verification*: `pip install -r requirements.txt && pip check`.

- [ ] **T003** Add `pyproject.toml` with `ruff` linting configuration and a `.black` config file.  
  *Verification*: `ruff check . && black --check .`.

- [ ] **T003a** Add `code/generate_config.py` that writes `config.yaml` containing **only** the two configurable thresholds required by the spec:  
  ```yaml
  validation:
    bias_threshold: 0.85          # Pearson‑r absolute value above which a bias warning is raised (FR‑013)
    retention_threshold: 0.95     # Minimum proportion of valid molecules required (FR‑011)
  ```  
  *Verification*: `python code/generate_config.py && grep -E "bias_threshold|retention_threshold" config.yaml`.

---  

## Phase 1 – Foundational scaffolding (blocks all user‑story work)

- [ ] **T004** Implement `code/utils/logging.py` – a thin wrapper around `llmxive_toolkit.get_logger` that provides `log_metric(name, value)` and `log_error(msg)`.  
  *Verification*: unit test `tests/unit/test_logging.py` passes.

- [ ] **T005** Skeleton `code/data/download.py` – define class `DataLoader` with methods `fetch_dataset(source: str) -> str` and `verify_checksum(file_path: str) -> None`.  No real download logic yet.  
  *Verification*: unit test `tests/unit/test_download_skeleton.py` passes.

- [ ] **T006** Skeleton `code/data/preprocess.py` – define class `MoleculeProcessor` with `parse_smiles(smiles: str) -> Mol` and `calculate_descriptors(mol: Mol) -> dict`.  
  *Verification*: unit test `tests/unit/test_preprocess_skeleton.py` passes.

- [ ] **T007** Skeleton `code/data/split.py` – define `stratified_split(df: pd.DataFrame, stratify_col: str) -> Tuple[pd.DataFrame, pd.DataFrame]` and `random_split(df: pd.DataFrame)`.  
  *Verification*: unit test `tests/unit/test_split_skeleton.py` passes.

- [ ] **T008** Skeleton `code/models/gnn.py` – define `MPNN` class inheriting from `torch.nn.Module` with a stub `forward(self, batch)`.  
  *Verification*: unit test `tests/unit/test_gnn_skeleton.py` passes.

- [ ] **T009** Skeleton `code/models/rf.py` – define `train_random_forest(X, y) -> RandomForestRegressor` and `predict(model, X) -> np.ndarray`.  
  *Verification*: unit test `tests/unit/test_rf_skeleton.py` passes.

- [ ] **T010** Skeleton `code/analysis/evaluate.py` – define `calculate_metrics(y_true, y_pred) -> dict` and `paired_ttest(errors_a, errors_b) -> dict`.  
  *Verification*: unit test `tests/unit/test_evaluate_skeleton.py` passes.

- [ ] **T011** Skeleton `code/analysis/explain.py` – define `explain_rf(model, X) -> dict` and `explain_gnn(model, graph_batch) -> dict`.  
  *Verification*: unit test `tests/unit/test_explain_skeleton.py` passes.

- [ ] **T012** Create empty test modules `tests/unit/test_preprocess.py` and `tests/integration/test_pipeline.py` (scaffolding for later implementation).  

---  

## Phase 2 – User Story 1: Data ingestion, preprocessing, and split  

**Goal**: Obtain a real public dataset, parse SMILES, compute the exact descriptor set, build graph objects, enforce data‑integrity and bias checks, and produce a single unified processed CSV plus train/test splits.

- [ ] **T013** Implement `code/data/download.py` → `DataLoader.fetch_dataset()` that iterates over the **verified** Hugging‑Face IDs listed below, downloads each with checksum verification, and stops at the first dataset that (a) contains a `smiles` column and (b) contains **any** of the target columns `["permeability", "logP_exp", "PC", "p_logP"]`.  
  ```python
  VERIFIED_DATASETS = [
      "moleculenet/bace",
      "moleculenet/bbbp",
      "moleculenet/esol",
      "moleculenet/freesolv",
      "moleculenet/lipo",
      "chembl/chembl_v30"
  ]
  ```  
  *Verification*: unit test `tests/unit/test_download.py` checks that `DataLoader().source` is one of the IDs and that a CSV file appears under `data/raw/`.

- [ ] **T013b** Extend the loader to **Proxy Mode**: after a dataset is selected, inspect its columns.  
  1. If an experimental permeability column (list above) exists → set `is_proxy_target: false`.  
  2. Else, if a calculated `logP` column exists → set `is_proxy_target: true` and log “Switching to Proxy Mode: using calculated logP”.  
  3. If **neither** is present, raise `RuntimeError("No experimental or proxy permeability target found. Pipeline halted.")`.  
  The flag is written to `results/metrics.json` (`{"is_proxy_target": <bool>}`) **without** aborting the pipeline when Proxy Mode is active.  
  *Verification*: after running the download script, `python -c "import json; d=json.load(open('results/metrics.json')); assert 'is_proxy_target' in d"` succeeds.

- [ ] **T014a** Implement `code/data/preprocess.py` → `MoleculeProcessor.process(df)` that, for each SMILES:  
  * Parses with `rdkit.Chem.MolFromSmiles`; invalid SMILES are logged and excluded.  
  * Computes **exactly** the following descriptors (using RDKit functions):  
    - Molecular Weight (`Descriptors.MolWt`)  
    - Crippen LogP (`Crippen.MolLogP`)  
    - Topological Polar Surface Area (`Descriptors.TPSA`)  
    - Num H‑Bond Acceptors (`Descriptors.NumHAcceptors`)  
    - Num H‑Bond Donors (`Descriptors.NumHDonors`)  
    - Num Rotatable Bonds (`Descriptors.NumRotatableBonds`)  
    - Num Aromatic Rings (`rdMolDescriptors.CalcNumAromaticRings`)  
    - Num Aliphatic Rings (`rdMolDescriptors.CalcNumAliphaticRings`)  
    - Num Saturated Rings (`rdMolDescriptors.CalcNumSaturatedRings`)  
    - Fraction C‑sp³ (`rdMolDescriptors.CalcFractionCSP3`)  
  * Missing descriptor values are median‑imputed; rows with missing target values are excluded with a logged warning.  
  *Verification*: `python -c "import pandas as pd; df=pd.read_csv('data/processed/processed_data.csv'); assert set(['mw','logp','tpsa','hba','hbd','rotatable_bonds','num_aromatic_rings']).issubset(df.columns)"`.

- [ ] **T014b** Continue `MoleculeProcessor` to **build graph objects** (node features: atomic number, degree, formal charge, hybridization, aromatic flag; edge features: bond type, conjugation) and store them **inline** in the unified CSV as JSON strings (`graph_nodes`, `graph_edges`). No separate `graph_features.csv` is created.  
  *Verification*: the processed CSV contains the columns `graph_nodes` and `graph_edges` and can be read without error.

- [ ] **T015** Add **data‑integrity enforcement** (FR‑011): after preprocessing, compute `valid_retention = n_valid / n_total`.  
  * If `valid_retention < 0.95` → log `"Data Integrity Warning: Retention < 95% (X%)"`; set `data_integrity_warning: true` in `results/metrics.json`; **terminate the pipeline with `SystemExit(1)`**.  
  * Otherwise, set `data_integrity_warning: false`.  
  *Verification*: a failing run produces a non‑zero exit code and the JSON flag is present.

- [ ] **T016** Implement **bias check** (FR‑013): calculate the **Pearson** correlation coefficient between each descriptor column and the target column (`np.corrcoef`).  
  * Load the threshold from `config.yaml` (`validation.bias_threshold`, default 0.85).  
  * If `max(|r|) > threshold` → set `bias_warning: true` and add a `"Bias Warning: |r|=X exceeds 0.85"` entry in `results/metrics.json`. The pipeline continues.  
  *Verification*: after preprocessing, `python -c "import json; d=json.load(open('results/metrics.json')); assert 'bias_warning' in d"`.

- [ ] **T017** Implement `code/data/split.py` → `create_splits(processed_path)`.  
  1. Detect the first available stratification column in the order `["polymer_type", "membrane_type", "material"]`.  
  2. If found, perform a **stratified** 80/20 split ensuring the absolute percentage‑point difference for each class ≤ 5 % (hard‑coded logic, **not configurable**).  
  3. If none is present, fall back to a random split and log `"Stratification column missing. Fallback to random split. Data leakage risk acknowledged for feasibility study."`.  
  4. Write `data/processed/train.csv` and `data/processed/test.csv`.  
  5. Immediately generate `results/stratification_report.md` containing sections **Split Strategy**, **Stratification Column**, **Distribution Diff**, **Retention Rate**.  
  *Verification*: greps for the four headings succeed.

- [ ] **T018** Write unit tests in `tests/unit/test_preprocess.py` covering: SMILES parsing, descriptor calculation, graph JSON serialization, invalid‑SMILES exclusion, retention‑warning logic, and bias‑warning flag.

- [ ] **T019** Write an integration test `tests/integration/test_pipeline.py` that runs the full pipeline up to the split step and asserts the existence and schema‑conformance of `data/processed/processed_data.csv`, `train.csv`, `test.csv`, and `results/metrics.json`.

---  

## Phase 3 – User Story 2: Comparative model training, evaluation, and statistical testing  

**Goal**: Train a CPU‑first MPNN, a standard Random Forest (descriptors only), and an RF‑ablation (graph‑derived features only); evaluate them; perform the required paired t‑test against the **standard RF** baseline.

- [ ] **T020** Implement `code/models/gnn.py` – a shallow MPNN (2 message‑passing layers, optional attention) that runs on CPU; expose `forward(self, batch)` returning a regression output. Include early‑stopping hooks (patience 5) based on a validation loss computed on a held‑out 10 % of the training set.

- [ ] **T021** Implement `code/models/rf.py` – train a `RandomForestRegressor` (default 100 trees, `max_features='sqrt'`) using **only the standard descriptor columns** from the processed CSV. Save the model to `data/interim/rf_descriptor.pkl`.

- [ ] **T022** Implement `code/models/rf_ablation.py` – train a `RandomForestRegressor` using **only the graph‑derived features** (`graph_nodes` and `graph_edges` flattened into numeric statistics such as mean node degree, graph connectivity, aromatic‑ring count). Save to `data/interim/rf_ablation.pkl`.

- [ ] **T023** Implement `code/analysis/train.py` – orchestrates training of the three models:  
    1. Load `train.csv`.  
    2. Train GNN (saving checkpoint `data/interim/gnn_checkpoint.pt`).  
    3. Train standard RF (T021) and RF‑ablation (T022).  
    4. Record `total_training_time_hours` and `peak_memory_gb` (using `psutil`) and write them into `results/training_log.json`.  
    *Verification*: the JSON contains both keys and the three checkpoint files exist.

- [ ] **T024** Implement `code/analysis/evaluate.py` – for each model, predict on `test.csv`, compute **RMSE**, **MAE**, **R²** (using `sklearn.metrics`).  
    * Write a consolidated `results/metrics.json` adhering to `specs/…/results.schema.yaml` (includes `gnn_metrics`, `rf_metrics`, `rf_ablation_metrics`).  
    * Also write `results/prediction_errors.json` containing three arrays: `errors_gnn`, `errors_rf`, `errors_rf_ablation`.  
    *Verification*: JSON validates against the schema (run `python -m jsonschema -i results/metrics.json specs/…/results.schema.yaml`).

- [ ] **T025** Perform the **primary paired t‑test** (FR‑007) between **GNN** and the **standard Random Forest** (descriptor‑only) using the error arrays from `results/prediction_errors.json`.  
    1. Compute paired‑t statistic and two‑tailed p‑value (`scipy.stats.ttest_rel`).  
    2. Compute **Cohen’s d** with pooled standard deviation.  
    3. Compute 95 % confidence interval for the mean difference (using `t.ppf`).  
    4. Store `p_value`, `significant` (p < 0.05), `method: "paired_t_test"`, `cohen_d`, `ci_lower`, `ci_upper` under `statistical_test` in `results/metrics.json`.  
    *Verification*: the JSON fields exist and `significant` is a boolean.

- [ ] **T025c** (Secondary) Perform a paired t‑test between **GNN** and **RF‑Ablation** (graph‑only) and store the result under `gnn_vs_rf_ablation` in `results/metrics.json`. (Keeps the extra analysis from the original plan without violating the primary hypothesis.)

---  

## Phase 4 – User Story 3: Feature attribution and comparative reporting  

- [ ] **T029** Implement `code/analysis/explain.py` – SHAP analysis for the standard RF model:  
    * Use `shap.TreeExplainer`.  
    * Produce a ranked list of descriptors by absolute mean SHAP value.  
    * Save to `results/feature_importance_rf.json`.  

- [ ] **T030** Implement GNNExplainer for the trained GNN:  
    * For each test molecule, run `gnnexplainer.explain` (CPU‑compatible implementation).  
    * Aggregate substructure importance scores across the test set.  
    * Save the aggregated ranking to `results/feature_importance_gnn.json`.  

- [ ] **T031** Create the **comparative feature report** (`results/comparative_report.md`):  
    1. Load both importance files.  
    2. List top‑5 SHAP descriptors and top‑5 GNN substructures.  
    3. Highlight substructures that rank high for GNN but are absent or low‑ranked in the SHAP list.  
    4. Include a short discussion linking these findings to the research question.  

- [ ] **T032** Generate visualisations (`results/figures/`):  
    * Bar chart of top‑5 SHAP descriptor importances.  
    * Bar chart of top‑5 GNN substructure importances.  
    * Save as high‑resolution PNGs (`shap_bar.png`, `gnn_substructures.png`).  

---  

## Phase 5 – Validation, success‑criteria alignment, and hand‑off  

- [ ] **T034a** Update `README.md` with a “## Data Pipeline” section describing the commands to run the download, preprocessing, and split steps.

- [ ] **T034b** Add a “## Model Training” section to `README.md` with commands to invoke `train.py` and `evaluate.py`.

- [ ] **T034c** Add a “## Interpretability” section to `README.md` with the command to run `explain.py`.

- [ ] **T034d** Add an “## Experimental Setup” header to `results/ablation_report.md` summarising dataset source, target mode (experimental vs. proxy), and split strategy.

- [ ] **T034e** Add a “## Results & Discussion” header to `results/comparative_report.md` that explicitly references **SC‑001 through SC‑005** (performance gap, statistical significance, effect size, computational feasibility, data‑integrity).  
  *Verification*: greps for the two headings succeed.

- [ ] **T037** Create `code/utils/verify_metrics.py` and `schema/metrics.schema.json` (the schema matches `results.schema.yaml` plus the two additional boolean flags `is_proxy_target` and `bias_warning`). The script validates `results/metrics.json` and exits with code 0 on success.  
  *Verification*: `python code/utils/verify_metrics.py` returns exit 0.

- [ ] **T038** Run `code/utils/verify_metrics.py` as part of the CI pipeline to ensure **all** success‑criteria (SC‑001 – SC‑005) are present and numerically plausible (e.g., RMSE > 0, 0 ≤ R² ≤ 1, training time ≤ 6 h, peak memory ≤ 7 GB).  
  *Verification*: the script prints “All success‑criteria satisfied” and exits 0.

---  

## Phase 6 – Additional robustness tasks (address reviewer concerns)

- [ ] **T039** Enhance `code/data/download.py` with **streaming support**:  
    1. Before download, query `datasets.get_dataset_info(name)` to obtain `dataset_size`.  
    2. If size > 7 GB, load the dataset with `datasets.load_dataset(name, streaming=True)` and process rows lazily (e.g., `for row in dataset:`).  
    3. Log “Streaming Mode: Active” in `results/metrics.json`.  

- [ ] **T040** Remove any synthetic‑fallback logic from the loader: ensure `DataLoader.fetch_dataset()` contains no `try/except` that creates mock data. On any fetch failure, raise a clear `RuntimeError`. Unit test `tests/unit/test_no_synthetic_fallback.py` asserts that no synthetic function is called.

- [ ] **T041** Support **Verified Real Data Source Injection**: if the environment variable `VERIFIED_DATA_SOURCE` is set (format `package::dataset_id::recipe`), the loader must **only** use that source, bypassing the hard‑coded list. The chosen source is recorded in `results/metrics.json` under `verified_source`. Unit test verifies the behaviour.

- [ ] **T042** Add a **CPU‑first feasibility check** before GNN training: run a forward pass on a 10‑sample batch, estimate peak memory with `torch.cuda.memory_allocated()` (will be zero on CPU) and `psutil`. If estimated usage > 7 GB, write `cpu_feasibility_check: "warning"` to `results/metrics.json`; otherwise write `"passed"`.

- [ ] **T043** Finalize the **bias‑warning validation**: after the bias check (T016), ensure `bias_warning` (boolean) is present in `results/metrics.json` and that `results/comparative_report.md` contains a “## Bias Warning” section when the flag is true.

---  

*All tasks above respect the real‑data‑only constitution, the fixed‑logic constraints (FR‑003 stratification ≤ 5 % difference, FR‑011 retention ≥ 95 %), and the original scientific requirements.  When all unchecked tasks are completed, the end‑to‑end pipeline will produce reproducible artifacts that satisfy every functional requirement, success criterion, and reviewer concern.*
