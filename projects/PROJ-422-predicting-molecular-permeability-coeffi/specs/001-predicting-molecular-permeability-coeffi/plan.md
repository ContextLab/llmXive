# Implementation Plan: Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets

**Branch**: `001-molecular-permeability-gnn` | **Date**: 2026-10-20 | **Spec**: `specs/001-molecular-permeability-gnn/spec.md`  
**Input**: Feature specification from `/specs/001-molecular-permeability-gnn/spec.md`

## Summary
The project will download verified open‑source chemical datasets, parse SMILES strings into RDKit molecular graphs, compute a standard set of RDKit descriptors, and (if a true experimental permeability column is present) train a CPU‑optimized 3‑layer Message Passing Neural Network (MPNN) and a Random Forest baseline. The pipeline is designed to run on the GitHub Actions free‑tier CPU runner, with deterministic outputs validated against JSON‑Schema contracts.

> **Important** – No publicly verified dataset currently provides experimental permeability coefficients. Consequently, the pipeline **stops after preprocessing** if a `permeability` column is absent, emitting a clear warning and **does not** fall back to any surrogate target such as `logP`. This limitation is flagged for a specification revision; no model training or comparative evaluation will be performed without a genuine permeability target.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `rdkit`, `torch==2.2.0`, `torch-geometric`, `scikit-learn`, `shap`, `pandas`, `datasets`, `statsmodels`, `numpy`, `matplotlib`  
- **Storage**: Local filesystem under `data/` (raw, processed, interim) and `results/` for metrics/figures.  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: Linux runner on GitHub Actions (2 CPU cores, ≤7 GB RAM, ≤6 h)  
- **Constraints**: CPU‑only execution; streaming mode for any file > 7 GB.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Fixed `requirements.txt`; random seeds (`numpy`, `torch`, `random`) pinned to `42`; dataset loading uses deterministic URLs via `datasets.load_dataset`. |
| **II. Verified Accuracy** | Only URLs listed in the “Verified datasets” block are used; no new citations introduced. |
| **III. Data Hygiene** | Raw files are checksum‑verified; every transformation writes a new file under `data/processed/` or `data/interim/`. |
| **IV. Single Source of Truth** | All quantitative results are stored in `results/metrics.json` and `results/interpretability/`; the final report references these files directly. |
| **V. Versioning Discipline** | After each stage, artifact hashes are recorded in the project state file. |
| **VI. Graph‑Representation Fidelity** | Graphs are generated **only** with `rdkit.Chem.MolFromSmiles`; no manual edge modifications. |
| **VII. Validation Independence** | When a true permeability target is available it is used; otherwise the pipeline halts before any modeling, avoiding circular validation with a proxy target. |

## Project Structure
```text
projects/PROJ-422-predicting-molecular-permeability-coeffi/
├─ code/
│  ├─ __init__.py
│  ├─ data/
│  │   ├─ download.py          # Streams datasets, computes SHA‑256 checksums
│  │   ├─ preprocess.py        # SMILES → graph + descriptors; writes output before any guard
│  │   └─ split.py             # Stratified (polymer_type) or random split
│  ├─ models/
│  │   ├─ __init__.py
│  │   ├─ gnn.py               # 3‑layer MPNN (CPU‑friendly)
│  │   ├─ rf.py                # Random Forest on full descriptors
│  │   └─ rf_ablation.py       # Random Forest on graph‑derived statistics only
│  ├─ analysis/
│  │   ├─ train.py             # Training loops, early stopping
│  │   ├─ evaluate.py          # Metrics, paired test, power analysis
│  │   └─ explain.py           # SHAP (RF) & GNNExplainer (GNN)
│  └─ utils/
│      └─ logging.py           # Structured JSON logging
├─ data/
│  ├─ raw/                     # Downloaded datasets (checksum‑verified)
│  ├─ processed/               # Processed feature tables (Parquet/CSV)
│  └─ interim/                 # Serialized graph objects (optional)
├─ results/
│  ├─ metrics.json
│  └─ interpretability/        # PNG/HTML visualizations
├─ tests/
│  ├─ unit/
│  │   ├─ test_preprocess.py
│  │   └─ test_models.py
│  └─ integration/
│      └─ test_pipeline.py
├─ requirements.txt
└─ README.md
```

## Complexity Tracking
All Functional Requirements (FR‑001 – FR‑013) and Success Criteria (SC‑001 – SC‑005) are explicitly mapped to concrete phases/steps below. No extra constraints are introduced.

## Phase Plan & FR/SC Mapping

| Phase | Tasks (high‑level) | FR(s) addressed | SC(s) addressed |
|-------|-------------------|-----------------|-----------------|
| **Phase 0 – Research & Data Verification** | 0.1 Verify each verified dataset URL is reachable and contains required columns (`smiles`, **optional** `permeability`).<br>0.2 **If no dataset contains a true permeability column, the pipeline stops here**, logs a spec‑limitation warning (see Constitution VII). | FR‑001, FR‑002, FR‑013 | SC‑005 |
| **Phase 1 – Data Pipeline** | 1.1 `code/data/download.py` – stream each verified dataset via `datasets.load_dataset(..., streaming=True)`; compute SHA‑256 checksums and write raw files to `data/raw/`.<br>1.2 `code/data/preprocess.py` – parse SMILES with RDKit, compute descriptors, set `mol_valid` flag.<br>1.3 Log and exclude invalid SMILES (FR‑010).<br>1.4 Write `data/processed/processed_data.parquet` **before** applying any retention guard (ensuring the file exists for the unit test).<br>1.5 **Retention guard**: after the file is written, compute the fraction of rows with `mol_valid=True`. If < 95 % the script logs a warning and exits with a non‑zero status **after** the file is present (satisfies FR‑011).<br>1.6 Perform bias‑check (Pearson correlation between each descriptor and `permeability` when present); flag if |r| > 0.85 (FR‑013). | FR‑001, FR‑002, FR‑010, FR‑011, FR‑013 | SC‑005 |
| **Phase 2 – Model Construction** *(executed only if a `permeability` column exists)* | 2.1 `models/gnn.py` – define 3‑layer MPNN (hidden = 64), global mean pooling, linear regression head; CPU‑only (`device="cpu"`).<br>2.2 `models/rf.py` – Random Forest on the full descriptor vector (`n_estimators=200`).<br>2.3 `models/rf_ablation.py` – Random Forest on **graph‑derived statistics only** (no standard descriptors). | FR‑004, FR‑005, FR‑012 | — |
| **Phase 3 – Training & Evaluation** *(executed only if a `permeability` column exists)* | 3.1 `analysis/train.py` – train GNN (max 50 epochs, early stopping patience = 5) and both RF variants; serialize models under `code/models/`.<br>3.2 **A‑priori power analysis**: compute required sample size for a medium effect (Cohen’s d = 0.5) at α = 0.05, 80 % power using `statsmodels`. Record planned size; if actual N is smaller, log a limitation flag (FR‑007, methodology‑68ef9d7e).<br>3.3 `analysis/evaluate.py` – compute RMSE, MAE, R² on the held‑out test set.<br>3.4 Compute per‑sample absolute errors for GNN and RF baseline.<br>3.5 **Normality check** on paired error differences (Shapiro‑Wilk). If p ≥ 0.05 → paired t‑test; else → Wilcoxon signed‑rank test. Record method, p‑value, decision in `results/metrics.json` (methodology‑743d42e3).<br>3.6 Store all metrics, statistical‑test outcome, normality result, and power‑analysis summary in `results/metrics.json` (validated against `contracts/results.schema.yaml`).<br>3.7 Enforce runtime ≤ 6 h and peak RAM ≤ 7 GB; abort with clear error if exceeded (SC‑004). | FR‑006, FR‑007, FR‑012 | SC‑001, SC‑002, SC‑004 |
| **Phase 4 – Interpretability** *(executed only if a `permeability` column exists)* | 4.1 `analysis/explain.py` – SHAP (KernelSHAP) on RF baseline and RF‑ablation; produce ranked descriptor importance CSV and bar‑chart PNG.<br>4.2 GNNExplainer on 100 random test molecules; aggregate subgraph masks to a global importance ranking; save heatmap PNG.<br>4.3 Store visualizations under `results/interpretability/`. | FR‑008, FR‑009 | SC‑003 |
| **Phase 5 – Reporting & Validation** | 5.1 Assemble a concise JSON report (`results/summary.json`) that references the exact files in `results/` and `data/processed/` (single source of truth).<br>5.2 Run the full CI end‑to‑end test (`./run_all.sh`); verify that all contracts pass and that random seeds produce identical outputs.<br>5.3 Update artifact hashes in the project state file. | FR‑001‑FR‑009 (all) | SC‑001‑SC‑005 |
| **Phase 6 – Cleanup** | 6.1 Delete temporary `interim/` graph serializations (keep provenance files).<br>6.2 Archive logs under `logs/` for auditability. | — | — |

### Additional Guarantees
- **Deterministic Output**: All scripts set `numpy.random.seed(42)`, `torch.manual_seed(42)`, and `random.seed(42)`.
- **Retention Guard Implementation**: `preprocess.py` writes the processed parquet **before** checking the 95 % validity threshold; if the guard fails, the script exits with a non‑zero code *after* the file exists, satisfying the unit test that expects the file.
- **RF Ablation Script**: Mirrors the CLI of `rf.py` but trains exclusively on the graph‑derived statistics computed in preprocessing, ensuring a verifiable baseline.
- **Multiple‑Comparison**: Only a single hypothesis (GNN vs. RF) is tested; no family‑wise correction is required (SC‑002).
- **Power Analysis**: Reported but not used as a gating condition; transparency about potential under‑power is maintained.

---

