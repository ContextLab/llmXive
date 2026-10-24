# Implementation Plan: Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets

**Branch**: `001-molecular-permeability-gnn` | **Date**: 2026-10-24 | **Spec**: `specs/001-molecular-permeability-gnn/spec.md`  
**Input**: Feature specification from `/specs/001-molecular-permeability-gnn/spec.md`

## Summary
We will (1) **audit verified open repositories** for a column named `permeability` (experimental). If none exists, the pipeline halts with a clear, reproducible message and automatically opens a GitHub issue requesting a suitable open dataset (fulfilling FR‑001). **CRITICAL: If the pipeline halts here, NO downstream artifacts (splits, models, or metrics) shall be produced; dummy artifacts are strictly prohibited.** (2) Stream the verified dataset, checksum‑verify, and preprocess SMILES into RDKit molecular graphs and a standard set of RDKit descriptors, writing both Parquet and CSV files. (3) Enforce a ≥ 95 % valid‑molecule retention guard **with remediation** (canonicalization, fallback to the largest valid subset, and a warning flag). (4) Perform a **5‑fold stratified cross‑validation** (fallback to random CV when stratification is impossible) and a final [deferred] hold‑out test, ensuring each split respects the ≤ 5 % class‑distribution tolerance and yields both Parquet and CSV files. (5) Train a CPU‑only 3‑layer MPNN (checkpoint saved as `code/models/gnn.pt`) and a Random Forest baseline (saved as `code/models/rf.pkl`), both receiving **polymer‑type one‑hot features** as covariates. (6) Evaluate models using RMSE, MAE, and R² on each CV fold and on the hold‑out set; compute a **paired statistical test** (Shapiro‑Wilk → paired t‑test or Wilcoxon) and a **bias‑check** (Pearson correlation of each descriptor with the target). (7) Apply GNNExplainer and SHAP, compute the required **overlap‑count metric**, and store all artifacts under `results/`. (8) Validate every artifact against JSON‑Schema contracts.

All steps run on the GitHub Actions free‑tier CPU runner; no GPU is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `rdkit`, `torch==2.2.0`, `torch-geometric`, `scikit-learn`, `shap`, `pandas`, `datasets`, `statsmodels`, `numpy`, `matplotlib`  
- **Storage**: Local filesystem (`data/`, `results/`)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: Linux runner (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h)  
- **Constraints**: CPU‑only; streaming for any raw file > 7 GB; strict reproducibility (pinned seeds, deterministic URLs).  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Fixed `requirements.txt`; seeds (`numpy`, `torch`, `random`) set to `42`; deterministic dataset URLs; all scripts are pure functions. |
| **II. Verified Accuracy** | Only URLs listed in the “Verified Datasets” block are used; no new citations are introduced. |
| **III. Data Hygiene** | Raw files checksum‑verified; every transformation writes a new file; no in‑place mutation. |
| **IV. Single Source of Truth** | All quantitative results are stored in `results/metrics.json` and referenced directly by the report; no hand‑typed numbers. |
| **V. Versioning Discipline** | Artifact hashes are recorded automatically by the platform after each stage. |
| **VI. Graph‑Representation Fidelity** | Graphs built **only** with `rdkit.Chem.MolFromSmiles`; no manual edge tweaks. |
| **VII. Validation Independence** | Modeling proceeds **only** if a true experimental permeability column exists; otherwise the pipeline halts before any model training. If a surrogate target is approved, the surrogate column is **excluded** from the descriptor set used by the Random Forest baseline, preventing circular validation. |

## Project Structure
```text
projects/PROJ-422-predicting-molecular-permeability-coeffi/
├─ code/
│  ├─ __init__.py
│  ├─ data/
│  │   ├─ download.py          # streaming download + checksum
│  │   ├─ preprocess.py        # SMILES → graph + descriptors + retention guard
│  │   └─ split.py             # stratified 5‑fold CV + hold‑out split, CSV & Parquet output
│  ├─ models/
│  │   ├─ __init__.py
│  │   ├─ gnn.py               # 3‑layer MPNN, checkpoint → gnn.pt
│  │   └─ rf.py                # RandomForestRegressor, pickle → rf.pkl
│  ├─ analysis/
│  │   ├─ train.py             # training loops, early stopping, power analysis
│  │   ├─ evaluate.py          # metrics, normality & paired tests, bias check, results JSON
│  │   └─ explain.py           # SHAP (RF) & GNNExplainer (GNN) + overlap metric
│  └─ utils/
│      └─ logging.py           # structured JSON logging
├─ data/
│  ├─ raw/                     # streamed raw files (checksum‑verified)
│  ├─ processed/               # processed_data.parquet & .csv, split files
│  └─ interim/                 # optional serialized graph objects
├─ results/
│  ├─ metrics.json
│  └─ interpretability/        # PNG/HTML visualizations
├─ tests/
│  ├─ unit/
│  │   ├─ test_download.py
│  │   ├─ test_preprocess.py
│  │   ├─ test_models.py      # includes test_gnn_training and test_rf_pickle
│  │   └─ test_split.py       # verifies non‑empty train/test CSVs with ~0.8/0.2 ratio
│  └─ integration/
│      └─ test_pipeline.py
├─ contracts/
│  ├─ dataset.schema.yaml
│  └─ results.schema.yaml
├─ requirements.txt
└─ README.md
```

## Complexity Tracking
All functional requirements (FR‑001 – FR‑012) and success criteria (SC‑001 – SC‑005) are mapped to concrete phases below; no extra constraints are introduced.

## Phase Plan & FR/SC Mapping

| Phase | Tasks | FR(s) | SC(s) |
|-------|-------|-------|-------|
| **Phase 0 – Target Availability & Acquisition** | 0.1 Search verified open repositories for a column named `permeability` (experimental).<br>0.2 If absent, log a clear halt message, create a GitHub issue requesting a suitable open dataset, and **exit**. **DO NOT proceed to Phase 1-8 or generate any dummy files.**<br>0.3 If a spec‑amendment later approves a surrogate target that is **not** a standard descriptor, record the approved column name, flag it as `target_surrogate`, and proceed. | FR‑001 (conditional) | SC‑005 (data‑integrity guard) |
| **Phase 1 – Download** | 1.1 Stream each verified dataset via `datasets.load_dataset(..., streaming=True)`.<br>1.2 Compute SHA‑256 checksums; abort on mismatch. | FR‑001, FR‑002 | — |
| **Phase 2 – Preprocess** | 2.1 Parse SMILES with `rdkit.Chem.MolFromSmiles`; log & drop invalid entries (FR‑011).<br>2.2 **Retention Guard**: if valid‑molecule rate < 95 % → attempt canonicalization; if still < 95 % → write the largest valid subset, set `retention_warning: true` in results, and continue.<br>2.3 Compute MW, logP, TPSA, HBA, HBD, rotatable bonds, and **one‑hot polymer_type** (if present).<br>2.4 If a surrogate target is approved, **remove that column from the descriptor set** supplied to the Random Forest baseline to avoid circularity.<br>2.5 Write `data/processed/processed_data.parquet` **and** `processed_data.csv` (both conform to `contracts/dataset.schema.yaml`). | FR‑002, FR‑003, FR‑011, FR‑012 | SC‑005 |
| **Phase 3 – Split** | 3.1 Perform **5‑fold stratified CV** on the processed dataset (stratify by `polymer_type` when present; otherwise stratify by quantile bins of the target). Each fold respects ≤ 5 % class‑distribution tolerance.<br>3.2 Additionally create a **[deferred] hold‑out test set** (random seed = 42) for final unbiased evaluation.<br>3.3 Write each split as both Parquet and CSV: `train_fold_{i}.parquet`, `train_fold_{i}.csv`, `test_fold_{i}.parquet`, `test_fold_{i}.csv`, plus `holdout_test.parquet` / `.csv`.<br>3.4 Verify that each split contains at least one row; if the dataset < 50 rows, log a warning but still produce a minimal split. | FR‑004 | — |
| **Phase 4 – Model Construction** | 4.1 `models/gnn.py`: 3‑layer MPNN, hidden = 64, global mean pooling, regression head, **CPU‑only** (`device="cpu"`). Node features are concatenated with polymer‑type one‑hot vectors. Save checkpoint `gnn.pt`.<br>4.2 `models/rf.py`: `RandomForestRegressor` (`n_estimators=200`, `max_features='sqrt'`) receiving **standard descriptors + polymer‑type one‑hot**. Save pickle `rf.pkl`. | FR‑005, FR‑006 | — |
| **Phase 5 – Training & Evaluation** | 5.1 `analysis/train.py`: train GNN (max 50 epochs, early stopping patience = 5) and RF on each CV fold; serialize models per fold.<br>5.2 **Power analysis**: compute required sample size for Cohen’s d = 0.3, α = 0.05, 80 % power; compare with actual N and record `planned_sample_size`, `achieved_power`, `sufficient` flag. If insufficient, continue but flag under‑powered (SC‑004).<br>5.3 `analysis/evaluate.py`: compute RMSE, MAE, R² on each CV fold and on hold‑out set; aggregate mean ± SD across folds; store under `results/metrics.json` (validated against `contracts/results.schema.yaml`).<br>5.4 Compute per‑sample absolute errors for GNN and RF.<br>5.5 **Statistical test**: Shapiro‑Wilk on paired error differences; if p ≥ 0.05 → paired t‑test, else Wilcoxon signed‑rank. Record method, p‑value, `significant` flag (SC‑001, SC‑002).<br>5.6 **Bias check**: Pearson correlation between target and each descriptor; store `correlation_coefficient` (max |r|), `is_confounded` (true if any |r| > 0.6), `bias_warning` (mirrors `is_confounded`). | FR‑007, FR‑008, FR‑012 | SC‑001, SC‑002, SC‑004 |
| **Phase 6 – Interpretability** | 6.1 `analysis/explain.py`: KernelSHAP on RF (using the descriptor set **excluding** any surrogate target) → ranked CSV + bar‑chart PNG.<br>6.2 GNNExplainer on 100 random test molecules; aggregate masks to a global substructure importance ranking of functional groups/substructures; visualized as heatmaps.<br>6.3 **Overlap‑count metric**: map top‑5 GNN substructures to the most chemically related descriptors, count overlaps with top‑5 SHAP descriptors; store `overlap_top5` and `overlap_meets_threshold` (≥ 3) in `results/metrics.json`, satisfying SC‑003. | FR‑009, FR‑010 | SC‑003 |
| **Phase 7 – Reporting & Validation** | 7.1 Assemble `results/summary.json` that references exact files in `data/processed/` and `results/` (single source of truth).<br>7.2 Run full CI (`./run_all.sh`); validate all contracts; ensure deterministic outputs across runs.<br>7.3 Update artifact hashes in the project state file. | FR‑001 – FR‑012 (all) | SC‑001 – SC‑005 |
| **Phase 8 – Cleanup** | 8.1 Delete optional `interim/` graph serializations, retain provenance logs.<br>8.2 Archive logs under `logs/`. | FR‑003 (data hygiene) | — |

### Additional Guarantees
- **Determinism**: `numpy.random.seed(42)`, `torch.manual_seed(42)`, `random.seed(42)`.
- **Multiple‑Comparison**: Only a single hypothesis (GNN vs. RF) is tested; no family‑wise correction needed.
- **CPU‑First**: All training runs on CPU; no CUDA calls. If future GPU‑only methods are added, the plan will explicitly use the Kaggle GPU escape hatch.