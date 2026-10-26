# Implementation Plan: Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets

**Branch**: `001-molecular-permeability-gnn` | **Date**: 2026-10-26 | **Spec**: `specs/001-molecular-permeability-gnn/spec.md`  
**Input**: Feature specification from `/specs/001-molecular-permeability-gnn/spec.md`

## Summary
The project will (1) **verify the existence of an open dataset that contains either experimental permeability coefficients or an approved surrogate permeability target** (e.g., validated simulation‑derived permeability); if none exists the pipeline halts with a reproducible error and automatically opens a GitHub issue (no silent fallback). (2) When a suitable dataset is available, the pipeline streams the data, validates checksums, parses SMILES with RDKit, computes standard molecular descriptors, and writes a processed Parquet/CSV file. (3) A stratified 5‑fold CV split (or fallback random split) and a hold‑out test set are generated, respecting the ≤ 5 % class‑distribution tolerance. (4) A CPU‑only 3‑layer Message Passing Neural Network (MPNN) and a Random Forest baseline are trained, with early stopping and deterministic seeding. (5) Models are evaluated on RMSE, MAE, and R², and a **paired test on per‑sample prediction errors** is performed; a **power‑analysis gate** aborts training if achieved power < 0.8. (6) Interpretability is performed via SHAP (RF) and GNNExplainer (GNN); an **algorithmic overlap metric** maps GNN substructures (SMARTS) to descriptor‑SMARTS pairs via a deterministic lookup table and assesses significance against a permutation‑based null distribution. (7) All artifacts are validated against JSON‑Schema contracts, including a revised `training_log.schema.yaml` that records total wall‑clock time and enforces the power‑sufficiency flag. The entire workflow runs on the GitHub Actions free‑tier CPU runner; no GPU is required, satisfying compute feasibility.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `rdkit`, `torch==2.2.0`, `torch-geometric`, `scikit-learn`, `shap`, `pandas`, `datasets`, `statsmodels`, `numpy`, `matplotlib`, `jsonschema`  
- **Storage**: Local filesystem under `data/`, `results/`  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h)  
- **Constraints**: CPU‑only; streaming for any raw file > 7 GB; deterministic seeds; strict reproducibility.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Fixed `requirements.txt`; seeds (`numpy`, `torch`, `random`) set to `42`; deterministic dataset URLs; all scripts are pure functions; `run_all.sh` orchestrates the exact sequence with `set -e`. |
| **II. Verified Accuracy** | **Verified Datasets** block (see below) lists the exact URLs used; no new citations are introduced. |
| **III. Data Hygiene** | Raw files are streamed and checksum‑verified; every transformation writes a new file; no in‑place mutation; `results/training_log.json` records timestamps and durations. |
| **IV. Single Source of Truth** | Quantitative results live exclusively in `results/metrics.json` and `results/training_log.json`; figures reference these files directly. |
| **V. Versioning Discipline** | Artifact hashes are automatically recorded by the platform after each stage. |
| **VI. Graph‑Representation Fidelity** | Graphs are built **only** with `rdkit.Chem.MolFromSmiles`; no manual edge edits. |
| **VII. Validation Independence** | Modeling proceeds **only** if a true experimental permeability column exists **or** an approved surrogate target (validated simulation) is present; the surrogate must be independent of the descriptor set (see Phase 0). No circular validation is permitted. |

### Verified Datasets
*No verified open dataset in the allowed list contains an experimental `permeability` column.* The pipeline therefore:
1. Searches each verified dataset for a column named `permeability`.  
2. If absent, searches for an **approved surrogate** column (e.g., `simulated_permeability`, `logS`, `solubility`) that is documented as a high‑quality simulation‑derived permeability measure.  
3. If a surrogate is found, it is recorded as `target_type: "surrogate"` in the metadata and used for training and evaluation.  
4. If neither experimental nor surrogate target is present, the pipeline **halts** and creates a GitHub issue titled “Request open permeability dataset for PROJ‑422”.

## Project Structure
```text
projects/PROJ-422-predicting-molecular-permeability-coeffi/
├─ code/
│  ├─ __init__.py
│  ├─ data/
│  │   ├─ download.py          # streaming download + checksum
│  │   ├─ preprocess.py        # SMILES → graph + descriptors + retention guard
│  │   └─ split.py             # stratified CV + hold‑out split (handles surrogate target)
│  ├─ models/
│  │   ├─ __init__.py
│  │   ├─ gnn.py               # 3‑layer MPNN, checkpoint → gnn.pt
│  │   └─ rf.py                # RandomForestRegressor, pickle → rf.pkl
│  ├─ analysis/
│  │   ├─ train.py             # training loops, early stopping, power analysis, training log
│  │   ├─ evaluate.py          # metrics, normality test, paired test on per‑sample errors, bias check
│  │   └─ explain.py           # SHAP (RF) & GNNExplainer (GNN) + deterministic overlap metric
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
└─ README.md
```

## Complexity Tracking
All functional requirements (FR‑001 – FR‑012) and success criteria (SC‑001 – SC‑005) are mapped to concrete phases below; no extra constraints are introduced.

## Phase Plan & FR/SC Mapping

| Phase | Tasks | FR(s) | SC(s) |
|-------|-------|-------|-------|
| **Phase 0 – Target Availability & Acquisition** | 0.1 Search verified open repositories for a column named `permeability` (experimental).<br>0.2 If absent, search for an **approved surrogate** column (e.g., `simulated_permeability`, `logS`). Surrogates must be documented as independent simulation‑derived permeability values.<br>0.3 If a surrogate is found, record `target_type: "surrogate"` in metadata and proceed.<br>0.4 If neither experimental nor surrogate target exists, **halt** with a clear error, create a GitHub issue titled “Request open permeability dataset for PROJ‑422”, and **exit** with status 1.<br>0.5 **Surrogate targets are not permitted** without the documented independence guarantee. | FR‑001 (conditional) | SC‑005 (data‑integrity guard) |
| **Phase 1 – Download** | 1.1 Stream each verified dataset via `datasets.load_dataset(..., streaming=True)`.<br>1.2 Compute SHA‑256 checksums; abort on mismatch. | FR‑001, FR‑002 | — |
| **Phase 2 – Preprocess** | 2.1 Parse SMILES with `rdkit.Chem.MolFromSmiles`; log & drop invalid entries (FR‑011).<br>2.2 **Retention Guard**: if valid‑molecule rate < 95 % → attempt canonicalization; if still < 95 % → write the largest valid subset, set `retention_warning: true` in `results/metrics.json`, and continue.<br>2.3 Compute MW, logP, TPSA, HBA, HBD, rotatable bonds, and one‑hot `polymer_type` (if present).<br>2.4 Write `data/processed/processed_data.parquet` **and** `processed_data.csv` (both conform to `contracts/dataset.schema.yaml`). | FR‑002, FR‑003, FR‑011, FR‑012 | SC‑005 |
| **Phase 3 – Split** *(executed only if a non‑null `target` column is present)* | 3.1 Perform **5‑fold stratified CV** on the processed dataset (stratify by `polymer_type` when present; otherwise stratify by quantile bins of the target). Each fold respects ≤ 5 % class‑distribution tolerance.<br>3.2 Additionally create a **hold‑out test set** (random seed = 42) for final unbiased evaluation.<br>3.3 Write each split as both Parquet and CSV: `train_fold_{i}.parquet`, `train_fold_{i}.csv`, `test_fold_{i}.parquet`, `test_fold_{i}.csv`, plus `holdout_test.parquet` / `.csv`.<br>3.4 Verify that each split contains at least one row; if the dataset < 50 rows, log a warning but still produce a minimal split (fulfills edge‑case handling). | FR‑004 | — |
| **Phase 4 – Model Construction** | 4.1 `models/gnn.py`: 3‑layer MPNN, hidden = 64, global mean pooling, regression head, **CPU‑only** (`device="cpu"`). Node features = atomic number, degree, charge, hybridization, aromatic flag; edge features = bond type, conjugation flag. Save checkpoint `gnn.pt`.<br>4.2 `models/rf.py`: `RandomForestRegressor` (`n_estimators=200`, `max_features='sqrt'`) receiving **standard descriptors + polymer‑type one‑hot**. Model serialized to `rf.pkl`. | FR‑005, FR‑006 | — |
| **Phase 5 – Training & Evaluation** | 5.1 `analysis/train.py`: train GNN (max 50 epochs, early stopping patience = 5) and RF on each CV fold; serialize models per fold.<br>5.2 **Power analysis**: using `statsmodels.stats.power.TTestPower` with effect size = 0.3, α = 0.05, power = 0.8; record `planned_sample_size`, `achieved_power`, and `sufficient` flag in `results/training_log.json`. **If `sufficient` is false, abort training** and log the insufficiency.<br>5.3 Record wall‑clock time (`total_hours`) in `results/training_log.json` (required by unit tests).<br>5.4 `analysis/evaluate.py`: compute RMSE, MAE, R² on each CV fold **and** on the **hold‑out test set**; aggregate mean ± SD across folds; store under `results/metrics.json` (validated against `contracts/results.schema.yaml`).<br>5.5 **Statistical test** (performed on the hold‑out set only): <br> a. Compute per‑sample prediction errors for GNN and RF on the **hold‑out test set**.<br> b. Perform Shapiro‑Wilk on the paired error differences.<br> c. If normal (p ≥ 0.05) → paired t‑test; else → Wilcoxon signed‑rank test.<br> d. Record method, p‑value, `significant` flag (SC‑001, SC‑002).<br>5.6 **Bias check**: <br> a. Compute Pearson correlation between the target and each descriptor.<br> b. If any |r| > 0.6, **drop those descriptors**, retrain both models, and set `is_confounded: true`, `bias_warning: true`, and record the dropped descriptor list in `results/metrics.json`. | FR‑007, FR‑008, FR‑012 | SC‑001, SC‑002, SC‑004 |
| **Phase 6 – Interpretability** | 6.1 `analysis/explain.py`: KernelSHAP on RF (using the final descriptor set) → ranked CSV + bar‑chart PNG.<br>6.2 GNNExplainer on 100 random test molecules; aggregate masks to a global subgraph importance ranking expressed as SMARTS strings; visualized as heatmaps.<br>6.3 **Deterministic overlap metric**: <br> a. Use a **pre‑defined deterministic lookup table** mapping each standard descriptor to a representative SMARTS pattern (e.g., `logP` ↔ aromatic ring SMARTS, `TPSA` ↔ polar‑oxygen SMARTS, etc.).<br> b. For the top‑5 GNN SMARTS, check whether they correspond to any of the top‑5 descriptor SMARTS via this lookup.<br> c. Compute the observed overlap count.<br> d. Generate a **null distribution** by randomly permuting descriptor rankings 10 000 times; compute a permutation‑test p‑value.<br> e. Store `overlap_top5`, `overlap_p_value`, and `overlap_significant` (true if p < 0.05) in `results/metrics.json`, satisfying SC‑003. | FR‑009, FR‑010 | SC‑003 |
| **Phase 7 – Reporting & Validation** | 7.1 Assemble `results/summary.json` that references exact files in `data/processed/` and `results/` (single source of truth).<br>7.2 Run full CI (`./run_all.sh`); validate all contracts (`jsonschema`); ensure deterministic outputs across runs.<br>7.3 Update artifact hashes in the project state file. | FR‑001 – FR‑012 (all) | SC‑001 – SC‑005 |
| **Phase 8 – Cleanup** | 8.1 Delete optional `interim/` graph serializations, retain provenance logs.<br>8.2 Archive logs under `logs/`. | FR‑003 (data hygiene) | — |

### Guarantees
- **Determinism**: `numpy.random.seed(42)`, `torch.manual_seed(42)`, `random.seed(42)`.
- **Multiple‑Comparison**: Only a single hypothesis (GNN vs. RF) is tested; no family‑wise correction needed.
- **CPU‑First**: All training runs on CPU; no CUDA calls. If future GPU‑only methods are added, the plan will explicitly use the Kaggle GPU escape hatch.

---



