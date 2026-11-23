# Implementation Plan: Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets

**Branch**: `001-molecular-permeability-gnn` | **Date**: 2026-10-26 | **Spec**: `specs/001-molecular-permeability-gnn/spec.md`  
**Input**: Feature specification from `/specs/001-molecular-permeability-gnn/spec.md`

## Summary
The pipeline will (1) locate an open dataset that supplies either an experimental permeability coefficient **or** an **approved surrogate** target that passes an independence verification, (2) stream‑download and checksum‑verify the data, (3) parse SMILES to RDKit graphs, compute a standard set of molecular descriptors, and enforce a **≥ 95 % valid‑molecule retention guard** (abort if < 95 % valid), (4) create stratified CV splits (or a fallback random split) together with a hold‑out test set, (5) train a CPU‑only 3‑layer Message Passing Neural Network (MPNN) and a Random Forest baseline, (6) perform a **power analysis** (Cohen’s d = 0.3, power ≥ 0.8) and abort if insufficient, (7) evaluate both models with RMSE, MAE, R² on the hold‑out set, run a Shapiro‑Wilk test on paired error differences and then a paired t‑test or Wilcoxon signed‑rank test as appropriate, (8) conduct a **post‑split confounding assessment** that records the **maximum absolute Pearson correlation** between any descriptor and the target (no descriptor removal), (9) generate SHAP explanations for the Random Forest and GNNExplainer substructure importance for the GNN, and (10) compute a **data‑driven overlap metric** between the top‑5 GNN substructures and top‑5 descriptor rankings using empirical correlation‑based mapping; the boolean `overlap_meets_threshold` is set to **true when `overlap_top5 ≥ 3`** (per schema), satisfying SC‑003. All steps run on the GitHub Actions free‑tier CPU runner; no GPU is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `rdkit`, `torch==2.2.0`, `torch-geometric`, `scikit-learn`, `shap`, `pandas`, `datasets`, `statsmodels`, `numpy`, `matplotlib`, `jsonschema`  
- **Storage**: Local filesystem under `data/`, `results/`  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h)  
- **Constraints**: CPU‑only; streaming for any raw file > 7 GB; deterministic random seeds; strict reproducibility.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Fixed `requirements.txt`; seeds (`numpy`, `torch`, `random`) pinned to `42`; deterministic dataset URLs; all scripts are pure functions; `run_all.sh` orchestrates the exact sequence with `set -e`. |
| **II. Verified Accuracy** | Only the URLs listed in the “Verified Datasets” block are accessed; no new citations are introduced. |
| **III. Data Hygiene** | Raw files are streamed and SHA‑256 checksummed; every transformation writes a new file; no in‑place mutation; `results/training_log.json` records timestamps and durations. |
| **IV. Single Source of Truth** | Quantitative results live exclusively in `results/metrics.json` and `results/training_log.json`; figures reference these files directly. |
| **V. Versioning Discipline** | Artifact hashes are automatically recorded by the platform after each stage. |
| **VI. Graph‑Representation Fidelity** | Graphs are built **only** with `rdkit.Chem.MolFromSmiles`; no manual edge edits. |
| **VII. Validation Independence** | Modeling proceeds **only if** a true experimental permeability column exists **or** an approved surrogate column passes the independence verification (max |r| < 0.5). No circular validation is permitted. |

## Project Structure
```text
projects/PROJ-422-predicting-molecular-permeability-coeffi/
├─ code/
│  ├─ __init__.py
│  ├─ data/
│  │   ├─ download.py          # streaming download + checksum + target discovery & surrogate independence check
│  │   ├─ preprocess.py        # SMILES → graph + descriptors + ≥95 % retention guard
│  │   └─ split.py             # stratified CV + hold‑out split (handles surrogate target)
│  ├─ models/
│  │   ├─ __init__.py
│  │   ├─ gnn.py               # 3‑layer MPNN, checkpoint → gnn.pt
│  │   └─ rf.py                # RandomForestRegressor, pickle → rf.pkl
│  ├─ analysis/
│  │   ├─ train.py             # training loops, early stopping, power analysis, training log
│  │   ├─ evaluate.py          # metrics, normality test, paired test, bias assessment
│  │   └─ explain.py           # SHAP (RF) & GNNExplainer (GNN) + empirical overlap metric
│  └─ utils/
│      └─ logging.py           # structured JSON logging
├─ data/
│  ├─ raw/                     # streamed raw files (checksum‑verified)
│  ├─ processed/               # processed_data.parquet & .csv, split files
│  └─ interim/                 # optional serialized graph objects
├─ results/
│  ├─ metrics.json
│  ├─ training_log.json
│  └─ interpretability/        # PNG/HTML visualizations
├─ tests/
│  ├─ unit/
│  │   ├─ test_download.py
│  │   ├─ test_preprocess.py
│  │   ├─ test_split.py          # verifies non‑empty splits when target exists
│  │   ├─ test_models.py         # checks GNN checkpoint, RF pickle, training_log.json, and power‑sufficient flag
│  │   └─ test_evaluate.py
│  └─ integration/
│      └─ test_pipeline.py
├─ contracts/
│  ├─ dataset.schema.yaml
│  ├─ results.schema.yaml
│  └─ training_log.schema.yaml
├─ requirements.txt
├─ run_all.sh                # orchestrates the full pipeline; aborts on any non‑zero exit
└─ README.md
```

## Phase Plan & FR/SC Mapping
| Phase | Tasks | FR(s) | SC(s) |
|-------|-------|-------|-------|
| **Phase 0 – Target Availability & Acquisition** | 0.1 Search verified open repositories for a column named `permeability` (experimental).<br>0.2 If absent, search for an **approved surrogate** column (e.g., `simulated_permeability`, `logS`).<br>0.3 **Independence verification**: compute Pearson correlation between the surrogate column and every standard descriptor; accept surrogate only if **max |r| < 0.5** (ensuring independence from the descriptor set).<br>0.4 Record `target_type` (`"experimental"` or `"surrogate"`).<br>0.5 If neither exists, **halt**, log error, and **auto‑create a GitHub issue** “Request open permeability dataset for PROJ‑422”.<br>0.6 Surrogates are only accepted when the provenance is verified (see Verified Datasets block). | FR‑001, FR‑014, FR‑016 | SC‑005 (data‑integrity guard) |
| **Phase 1 – Download** | 1.1 Stream each verified dataset via `datasets.load_dataset(..., streaming=True)`.<br>1.2 Compute SHA‑256 checksums; abort on mismatch. | FR‑001, FR‑002 | — |
| **Phase 2 – Preprocess** | 2.1 Parse SMILES with `rdkit.Chem.MolFromSmiles`; log & drop invalid entries (FR‑011).<br>2.2 **Retention Guard**: ensure **≥ 95 %** valid molecules; abort if < 95 % (FR‑012).<br>2.3 Compute MW, logP, TPSA, HBA, HBD, rotatable bonds, and one‑hot `polymer_type` (if present) (FR‑003).<br>2.4 Write `data/processed/processed_data.parquet` **and** `processed_data.csv` conforming to `contracts/dataset.schema.yaml`. | FR‑002, FR‑003, FR‑011, FR‑012 | SC‑005 |
| **Phase 3 – Split** | 3.1 Perform **5‑fold stratified CV** on the processed dataset (stratify by `polymer_type` when present; otherwise by target quantiles). Ensure ≤ 5 % class‑distribution deviation.<br>3.2 Create a **hold‑out test set** (seed = 42) for final unbiased evaluation.<br>3.3 Write each split as Parquet and CSV (`train_fold_{i}.parquet`, `holdout_test.parquet`, etc.).<br>3.4 If dataset < 50 rows, log a warning but still produce a minimal random split. | FR‑004 | — |
| **Phase 4 – Model Construction** | 4.1 `models/gnn.py`: 3‑layer MPNN, hidden = 64, global mean pooling, regression head, **CPU‑only** (`device="cpu"`). Node features = atomic number, degree, charge, hybridization, aromatic flag; edge features = bond type, conjugation flag. Save checkpoint `gnn.pt`.<br>4.2 `models/rf.py`: `RandomForestRegressor` (`n_estimators=200`, `max_features='sqrt'`) using **standard descriptors + polymer‑type one‑hot**. Serialize to `rf.pkl`. | FR‑005, FR‑006 | — |
| **Phase 5 – Training & Evaluation** | 5.1 `analysis/train.py`: train GNN (max 50 epochs, early stopping patience = 5) and RF on each CV fold; serialize models per fold.<br>5.2 **Power analysis**: use `statsmodels.stats.power.TTestPower` with effect size = 0.3, α = 0.05, power = 0.8; record `planned_sample_size`, `achieved_power`, `sufficient` in `results/training_log.json`. **If `sufficient` is false, abort training** and log the insufficiency (FR‑015).<br>5.3 Record wall‑clock time (`total_hours`) in `results/training_log.json` (required by unit tests and SC‑004).<br>5.4 `analysis/evaluate.py`: compute RMSE, MAE, R² on the **hold‑out test set**; aggregate mean ± SD across folds; store under `results/metrics.json` (validated against `contracts/results.schema.yaml`).<br>5.5 **Statistical test** on the hold‑out set: <br> a. Compute per‑sample prediction errors for GNN and RF.<br> b. Shapiro‑Wilk test on paired error differences.<br> c. If normal (p ≥ 0.05) → paired t‑test; else → Wilcoxon signed‑rank test.<br> d. Record method, p‑value, `significant` flag (SC‑001, SC‑002).<br>5.6 **Post‑split confounding assessment**: <br> a. Compute Pearson correlation between each descriptor and the target **using only the training folds**.<br> b. Record the **maximum absolute correlation** as `correlation_coefficient`.<br> c. Set `is_confounded: true` and `bias_warning: true` if max |r| > 0.6. **No descriptors are removed**, avoiding leakage. | FR‑007, FR‑008, FR‑012, FR‑015 | SC‑001, SC‑002, SC‑004, SC‑006 |
| **Phase 6 – Interpretability** | 6.1 `analysis/explain.py`: KernelSHAP on RF → ranked CSV + bar‑chart PNG.<br>6.2 GNNExplainer on 100 random test molecules; aggregate masks to a global subgraph importance ranking expressed as SMARTS strings; visualized as heatmaps.<br>6.3 **Empirical overlap metric**: <br> a. For each standard descriptor, compute Pearson correlation with the frequency of each SMARTS substructure across the **training set**.<br> b. Define a **data‑driven mapping** by selecting, for each descriptor, the SMARTS with the highest correlation.<br> c. For the top‑5 GNN SMARTS, check correspondence to the top‑5 descriptor‑mapped SMARTS.<br> d. Count overlaps (`overlap_top5`).<br> e. Set `overlap_meets_threshold` **true when `overlap_top5 ≥ 3`** (per SC‑003).<br> f. Store `overlap_top5` and `overlap_meets_threshold` in `results/metrics.json`. | FR‑009, FR‑010 | SC‑003 |
| **Phase 7 – Reporting & Validation** | 7.1 Assemble `results/summary.json` that references exact files in `data/processed/` and `results/` (single source of truth).<br>7.2 Run full CI (`./run_all.sh`); validate all contracts (`jsonschema`); ensure deterministic outputs across runs.<br>7.3 Update artifact hashes in the project state file. | FR‑001 – FR‑012 (all) | SC‑001 – SC‑007 |
| **Phase 8 – Cleanup** | 8.1 Delete optional `interim/` graph serializations, retain provenance logs.<br>8.2 Archive logs under `logs/`. | FR‑003 (data hygiene) | — |

### Fixes for Previously Failed Tasks
- **T003 (split.py exit = 1)** – The split phase now checks for the presence of a non‑null `target` column before attempting stratification; if the target column is missing, it aborts with a clear error and creates the required GitHub issue (Phase 0). The script returns `0` on successful split creation.
- **T004 (run_all.sh exit = 1)** – `run_all.sh` now runs each stage with `set -e` and captures exit codes. It includes explicit checks after each command (download, preprocess, split, train, evaluate, explain) and will only exit with `0` when all stages succeed. Errors from missing target or insufficient power cause an early, graceful abort with informative logging.
- **T007 (train.py exit = 1)** – `train.py` now writes a complete `results/training_log.json` (including `total_hours`, `planned_sample_size`, `achieved_power`, `sufficient`) for each model, and the power‑analysis gate prevents aborts due to insufficient power. The script returns `0` on successful training.
- **T014 / T015 (model tests missing training_log.json)** – The training phase now records `total_hours` (wall‑clock time) and ensures it is `< 6 h` (CI constraint) and `< 1 h` for the unit‑test time‑limit check. The unit tests will read `results/training_log.json` to verify these fields.
- **T005 (RF test missing training_log.json)** – Same fix as above; the RF training routine writes a `training_log.json` entry with the required fields.

All functional requirements (FR‑001 – FR‑016) and success criteria (SC‑001 – SC‑007) are addressed, no extra constraints are introduced. The plan now fully respects the schema definitions and methodological concerns.

---



