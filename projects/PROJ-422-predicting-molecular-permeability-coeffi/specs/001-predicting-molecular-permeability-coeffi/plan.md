# Implementation Plan: Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets

**Branch**: `001-molecular-permeability-gnn` | **Date**: 2026-10-20 | **Spec**: `specs/001-molecular-permeability-gnn/spec.md`

## Summary
The project will ingest open‑source chemical datasets containing SMILES strings, compute RDKit‑based molecular descriptors, and construct graph representations for each molecule. Because no verified open dataset provides experimental permeability coefficients, the study pivots to a **Feasibility Study** that predicts the calculated `logP` value (a standard descriptor) as a proxy target. A shallow Message Passing Neural Network (MPNN) will be trained on graph inputs, and a Random Forest (RF) baseline will be trained on standard descriptors. An **ablation RF** will be trained on graph‑derived statistics only. Model performance will be compared using RMSE, MAE, R², and a paired t‑test. Interpretability will be assessed with GNNExplainer (GNN) and SHAP (RF). All steps are designed to run on the GitHub Actions free‑tier CPU runner; no GPU is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `rdkit`, `torch==2.2.0`, `torch-geometric`, `scikit-learn`, `shap`, `pandas`, `datasets`, `statsmodels`, `numpy`, `matplotlib`  
- **Storage**: Local filesystem under `data/` (raw, processed, interim) and `results/` for metrics/figures.  
- **Testing**: `pytest` for unit and integration tests.  
- **Target Platform**: Linux runner on GitHub Actions (2 CPU cores, ≤7 GB RAM, ≤6 h).  
- **Project Type**: Computational research pipeline (CLI‑driven).  
- **Performance Goals**: Full pipeline ≤ 6 h, peak RAM ≤ 7 GB.  
- **Constraints**: CPU‑only execution; streaming mode if any raw file exceeds 7 GB.  
- **Scale/Scope**: Datasets range from ~200 K to <1 GB; the pipeline will stream when needed.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Fixed `requirements.txt`, deterministic random seeds (`numpy`, `torch`, `random`), and canonical Hugging Face URLs for all downloads. |
| **II. Verified Accuracy** | Only the URLs listed in the “Verified datasets” block are used; no external citations are introduced. |
| **III. Data Hygiene** | Raw files are checksum‑verified; all transformations write to new files under `data/processed/` and `data/interim/`. |
| **IV. Single Source of Truth** | All quantitative results are logged to `results/metrics.json` and `results/interpretability/` and referenced directly in the final report. |
| **V. Versioning Discipline** | Artifact hashes are recorded in the project state file after each stage. |
| **VI. Graph‑Representation Fidelity** | Graphs are generated exclusively via `rdkit.Chem.MolFromSmiles`; no manual edge modifications. |
| **VII. Validation Independence** | Target is the calculated `logP` (proxy). A bias check (FR‑013) will flag the expected high correlation but will not be treated as a validation error. |

## Project Structure
```text
projects/PROJ-422-predicting-molecular-permeability-coeffi/
├─ code/
│  ├─ __init__.py
│  ├─ data/
│  │   ├─ download.py          # Fetches raw files, verifies checksums
│  │   ├─ preprocess.py        # SMILES → graph + descriptors; retention & bias checks
│  │   └─ split.py             # Stratified (polymer_type) or random split
│  ├─ models/
│  │   ├─ __init__.py
│  │   ├─ gnn.py               # 3‑layer MPNN (CPU‑friendly)
│  │   └─ rf.py                # Random Forest baseline & ablation mode
│  ├─ analysis/
│  │   ├─ train.py             # Training loops, early stopping
│  │   ├─ evaluate.py          # Metrics, paired t‑test, effect size, power analysis
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
│  │   ├─ test_download.py
│  │   ├─ test_preprocess.py
│  │   └─ test_models.py
│  └─ integration/
│      └─ test_pipeline.py
├─ requirements.txt
└─ README.md
```

## Complexity Tracking
All Functional Requirements (FR‑001 – FR‑013) and Success Criteria (SC‑001 – SC‑005) are mapped to concrete phases/steps below. No extra constraints are introduced.

## Phase Plan & FR/SC Mapping

| Phase | Tasks (high‑level) | FR(s) addressed | SC(s) addressed |
|-------|-------------------|-----------------|-----------------|
| **Phase 0 – Research & Data Verification** | 0.1 Verify dataset URLs & variable presence.<br>0.2 Decide “Proxy Mode” if permeability missing. | FR‑001, FR‑002, FR‑013 (bias check) | SC‑005 (data integrity) |
| **Phase 1 – Data Pipeline** | 1.1 `download.py`: fetch & checksum.<br>1.2 `preprocess.py`: parse SMILES, compute descriptors, build graphs, retention check (≥95 %).<br>1.3 `split.py`: stratified 80/20 split (polymer_type) or fallback random.<br>1.4 Contract validation against `contracts/dataset.schema.yaml`. | FR‑001, FR‑002, FR‑003, FR‑010, FR‑011, FR‑013 | SC‑005 |
| **Phase 2 – Model Construction** | 2.1 `models/gnn.py`: 3‑layer MPNN, CPU‑only, early stopping (patience = 5).<br>2.2 `models/rf.py`: baseline RF on descriptors; `--ablation` flag trains RF on graph‑derived stats only. | FR‑004, FR‑005, FR‑012 | — |
| **Phase 3 – Training & Evaluation** | 3.1 `analysis/train.py`: fit GNN & both RF variants, log epoch metrics, enforce max‑epoch = 50.<br>3.2 `analysis/evaluate.py`: compute RMSE, MAE, R²; paired t‑test (FR‑007); effect size (Cohen’s d) and 95 % CI; post‑hoc power analysis.<br>3.3 Enforce runtime ≤ 6 h, RAM ≤ 7 GB; if exceeded, abort with clear error. | FR‑006, FR‑007, FR‑012 | SC‑001, SC‑002, SC‑004 |
| **Phase 4 – Interpretability** | 4.1 `analysis/explain.py`: SHAP on RF (baseline & ablation).<br>4.2 GNNExplainer on GNN; aggregate subgraph importance.<br>4.3 Produce ranked feature list & visualizations (bar chart, heatmap). | FR‑008, FR‑009 | SC‑003 |
| **Phase 5 – Reporting & Validation** | 5.1 Assemble `results/metrics.json` and `results/interpretability/` figures.<br>5.2 Verify contracts (`results.schema.yaml`).<br>5.3 Run full CI end‑to‑end test; ensure reproducibility (seeded runs). | FR‑004‑FR‑009 (all) | SC‑001‑SC‑005 |
| **Phase 6 – Cleanup** | 6.1 Delete temporary `interim/` objects, keep only provenance files.<br>6.2 Update artifact hashes in project state. | — | — |

### Additional Guarantees
- **Retention Guard**: `preprocess.py` aborts with a clear error if valid molecules < 95 % (FR‑011).  
- **Bias Guard**: If |corr| > 0.85, `bias_warning: true` is written to `results/metrics.json` (FR‑013).  
- **Early‑Stopping Guard**: GNN training stops automatically; if validation loss never improves, a warning is logged and the best epoch is restored (FR‑004).  
- **Statistical Rigor**: Paired t‑test is performed **only** after both models have predictions on the same test set; multiple‑comparison correction is unnecessary because a single hypothesis is tested (SC‑002).  

---
