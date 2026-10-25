# Implementation Plan: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

**Branch**: `001-predicting-molecular-fluorescence-quantum-yields` | **Date**: 2026-10-25 | **Spec**: [spec.md](../specs/001-predicting-molecular-fluorescence-quanti/spec.md)  
**Input**: Feature specification from `/specs/001-predicting-molecular-fluorescence-quanti/spec.md`

## Summary
The research question—*predicting experimental fluorescence quantum yields (FQY) from molecular structure*—requires a joint SMILES + FQY dataset. We now employ the **verified open dataset FluorDB v1.0** (`https://huggingface.co/datasets/fluordb/v1`), which provides canonical SMILES strings together with experimentally measured FQY values and associated metadata. All functional requirements (FR‑001 … FR‑018) can therefore be satisfied on the free‑tier CI runner. The pipeline proceeds through data acquisition, cleaning (including ε‑clipping of FQY), scaffold‑based splitting, feature extraction, model training, baseline comparison, attribution analysis, and final reporting. Modeling and interpretability steps are scheduled to run **after data download**; they are not omitted but will execute automatically once the dataset is present.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torch_geometric==2.5.3`, `rdkit==2024.03.2`, `pandas==2.2.2`, `scikit-learn==1.5.0`, `datasets==2.20.0`, `tqdm==4.66.5`  
- **Target Platform**: Linux (GitHub Actions free‑tier runner) – **CPU‑only**.  
- **Constraints**: ≤ 5 M trainable parameters, ≤ 7 GB RAM, ≤ 6 h wall‑clock, dataset size ≤ 7 GB after streaming if necessary.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Fixed random seeds (`src/utils/seed.py`); deterministic scripts; same dataset URL each run. |
| **II. Verified Accuracy** | Dataset URL is from the verified‑datasets list; checksum verification (`src/data/checksum.py`). |
| **III. Data Hygiene** | Raw files are checksum‑verified; each transformation writes a new file with provenance metadata. |
| **IV. Single Source of Truth** | All downstream artifacts derive from `processed_dataset.parquet`. |
| **V. Versioning Discipline** | Output files include content‑hash suffixes; any change updates the project state hash. |
| **VI. Scaffold‑Based Generalizability** | Scaffold split (80/10/10) with zero scaffold overlap; minimum test size = 50 (FR‑013). |
| **VII. Explicit Substructure Attribution** | Attribution phase (IG/SHAP) planned; top substructures will be reported and compared to the curated motif set. |

## Project Structure
```text
specs/001-predicting-molecular-fluorescence-quanti/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── processed_dataset.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
src/
├── data/
│   ├── download_fluordb.py   # fetches verified joint dataset
│   └── checksum.py           # SHA‑256 verification utility
├── preprocessing/
│   ├── clean.py              # invalid SMILES removal, ε‑clipping of FQY, metadata extraction (FR‑015)
│   └── scaffold_split.py     # Murcko scaffold extraction, 80/10/10 split, min‑test‑size=50 (FR‑013)
├── features/
│   └── rdkit_features.py     # node/edge extraction (atom type, hybridization, charge, bond type, conjugation) (FR‑001)
├── models/
│   ├── gnn.py                # <5 M‑parameter message‑passing GNN (CPU‑only) (FR‑003)
│   └── linear_regression.py  # ECFP4‑based baseline (FR‑005)
├── training/
│   └── train.py              # ≤ 50 epochs, early stopping (patience = 10) (FR‑004)
├── evaluation/
│   └── evaluate.py           # R², RMSE, MAE on test set (FR‑005)
├── interpretability/
│   ├── integrated_gradients.py
│   ├── shap_explain.py
│   └── aggregate_substructures.py   # aggregation into chemically meaningful fragments (FR‑006), comparison to reference motifs (FR‑016)
├── reporting/
│   └── generate_report.py    # assembles metrics, plots, attribution summary (FR‑007, SC‑007)
├── reference/
│   └── fluorophore_motifs.csv    # curated motif library (FR‑016)
├── utils/
│   ├── logger.py
│   └── seed.py
tests/
├── unit/
└── contract/
    └── test_processed_dataset.py   # validates schema compliance
```

## Mapping of Functional Requirements (FR) & Success Criteria (SC) to Phases
| Phase | Tasks (FR) | Success Checks (SC) |
|-------|------------|---------------------|
| **0️⃣ Data Acquisition** | `download_fluordb.py` – fetches **joint SMILES + FQY** from <https://huggingface.co/datasets/fluordb/v1> (FR‑018, verified) | Log checksum verification; confirm presence of `smiles` and `fqy` columns. |
| **1️⃣ Cleaning** | `clean.py` – removes invalid SMILES (FR‑009), **ε‑clips** FQY to (ε, 1‑ε) with ε = 1e‑6 (FR‑010), extracts solvent/temperature/method metadata (FR‑015) | Generates `processed_dataset.parquet` that validates against `processed_dataset.schema.yaml`; logs count of clipped boundary values (FR‑011). |
| **2️⃣ Scaffold Split** | `scaffold_split.py` – Murcko scaffold extraction, 80/10/10 split, zero scaffold overlap (FR‑002, FR‑014), **minimum test set size = 50** (FR‑013). Reseed up to 5 times; abort with warning if still < 50. | Writes `train.parquet`, `validation.parquet`, `test.parquet`; creates `split_stats.json` with overlap stats (SC‑004). |
| **3️⃣ Feature Extraction** | `rdkit_features.py` – builds node/edge feature tensors (FR‑001). Detects unseen atom/bond types; logs warnings and **skips** such molecules for inference (FR‑012). | Saves `train_graphs.pt`, `val_graphs.pt`, `test_graphs.pt`; passes sanity‑check unit tests. |
| **4️⃣ Model Definition** | `models/gnn.py` (FR‑003) and `models/linear_regression.py` (FR‑005) are **implemented**; ready for execution once data are present. | Static type‑checking and unit tests succeed. |
| **5️⃣ Training** | `training/train.py` – ≤ 50 epochs, early stopping (patience = 10) on validation loss (FR‑004). Saves best checkpoint (`model_best.pt`). | Training completes within CPU limits; logs best epoch. |
| **6️⃣ Evaluation** | `evaluation/evaluate.py` – computes R², RMSE, MAE on test set (FR‑005). | Outputs `metrics.json`; **SC‑001** records GNN vs baseline R². |
| **7️⃣ Attribution** | `interpretability/` – IG & SHAP (FR‑006), aggregation into substructures, top‑20 ranking. Validation against `fluorophore_motifs.csv` (FR‑016). | **SC‑005** reports overlap count and enrichment vs random baseline; **SC‑006** reports Pearson correlation between IG and SHAP on ≥ 30 molecules. |
| **8️⃣ Reporting** | `reporting/generate_report.py` – training curves, parity plot, feature‑importance charts (FR‑007), consolidates all metrics and logs into `final_report.zip`. | **SC‑007** ensures artifact is archived as CI run artifact. |
| **🧭 Resource Monitoring** | `utils/logger.py` records wall‑clock time and peak RAM; aborts if > 6 h or > 7 GB (FR‑008). | **SC‑002** & **SC‑003** validated post‑run. |

## Timeline (CPU‑only, estimated on free‑tier runner)

| Phase | Approx. Time |
|-------|--------------|
| Data download & checksum | < 5 min |
| Cleaning (incl. clipping & metadata) | 8 min |
| Scaffold split | 6 min |
| Feature extraction | 10 min |
| Model definition (static) | < 1 min |
| Training (max) | 2 h 30 min |
| Evaluation & attribution | 30 min |
| Reporting | 10 min |
| **Total** | **≈ 3 h 30 min** (well under 6 h) |

All steps respect the 7 GB RAM ceiling on the CI runner.

---



