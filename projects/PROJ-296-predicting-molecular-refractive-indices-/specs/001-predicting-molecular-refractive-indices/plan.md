# Implementation Plan: Predicting Molecular Refractive Indices from Graph-Based Molecular Representations

**Branch**: `001-predict-molecular-refractive-indices` | **Date**: 2026-10-21 | **Spec**: `specs/001-predict-molecular-refractive-indices/spec.md`  
**Input**: Feature specification from `/specs/001-predict-molecular-refractive-indices/spec.md`

## Summary
Implement a CPU‑only pipeline that (1) acquires an open‑source CSV dataset containing SMILES strings and experimentally measured refractive indices for organic molecules (MW < 500 Da), (2) preprocesses the data into graph objects, (3) creates scaffold‑based splits (80/10/10) with zero scaffold overlap, (4) trains a lightweight 3‑layer Message Passing Neural Network (MPNN, hidden dim = 64) on each split, (5) computes a physics‑based atomic‑contribution baseline, (6) evaluates both models with MAE, RMSE, and a paired statistical test, (7) applies Integrated Gradients for node/edge attribution, and (8) generates PNG artifacts (parity plot, feature‑importance chart). All steps are deterministic, schema‑validated, and respect the 7 GB RAM / 6 h CPU‑only constraints.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.0.0+cpu`, `torch-geometric`, `rdkit`, `pandas`, `numpy`, `scipy`, `torchmetrics`, `tqdm`, `scikit-learn`  
- **Storage**: CSV files under `data/` (raw, processed, splits) and PNGs under `results/plots/`  
- **Testing**: `pytest` for unit/integration tests; JSON‑Schema validation via `jsonschema`  
- **Target Platform**: Linux (GitHub Actions free tier)  
- **Constraints**: CPU‑only (`torch.device("cpu")`), peak RAM ≤ 7 GB, wall‑time ≤ 6 h  
- **Scale/Scope**: Minimum ≥ 500 molecules (if available); otherwise the pipeline aborts with a clear error.

## Constitution Check
| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| **I. Reproducibility** | PASS | Fixed random seeds, deterministic splits, `requirements.txt` pins versions, checksum recorded for raw CSV (if downloaded). |
| **II. Verified Accuracy** | PASS | All citations are drawn from the verified dataset list (none required for RI dataset; absence is noted). |
| **III. Data Hygiene** | PASS | Raw data immutable; preprocessing creates new files; SHA‑256 stored under `state/`. |
| **IV. Single Source of Truth** | PASS | Every metric/figure generated from pipeline outputs; no hand‑typed numbers. |
| **V. Versioning Discipline** | PASS | Artifacts (model weights, CSVs, PNGs) are content‑hashed; timestamps managed by the Advancement‑Evaluator. |
| **VI. CPU‑Only Execution** | PASS | All PyTorch calls enforce `device="cpu"`; no CUDA imports. |
| **VII. Structural Interpretability** | PASS | Integrated Gradients applied to each trained model; attribution CSV and bar chart are mandated outputs. |
| **Dataset Availability** | NOTE | No open‑source refractive‑index CSV with ≥ 500 samples is present in the verified list. The pipeline will abort with a clear message if such a dataset cannot be located, prompting a specification revision. |

## Project Structure
```
specs/001-predict-molecular-refractive-indices/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

Source code layout (repository root):
```
code/
├── data/
│   ├── download.py          # fetches open RI dataset, computes checksum
│   ├── preprocess.py        # RDKit parsing, MW filter, temperature norm.
│   └── split.py             # scaffold‑based 5×5 repeated splits
├── models/
│   ├── mpnn.py              # 3‑layer MPNN (CPU‑only)
│   ├── baseline.py          # atomic‑contribution baseline
│   └── attribution.py       # Integrated Gradients driver
├── training/
│   ├── train.py             # training loop with early stopping
│   └── evaluate.py          # MAE/RMSE, paired test, plots
├── utils/
│   ├── rdkit_helpers.py
│   └── constants.py
├── tests/
│   ├── test_download.py
│   ├── test_preprocess.py
│   ├── test_split.py
│   └── test_models.py
└── requirements.txt
```

## Functional Requirement Mapping
| FR | Description | Plan Phase |
|----|-------------|------------|
| **FR-001** | Download & parse CSV, filter MW < 500 Da | **Dataset Acquisition** (`code/data/download.py`) |
| **FR-002** | 3‑layer MPNN, hidden 64, CPU‑only | **MPNN Architecture** (`models/mpnn.py`) |
| **FR-003** | Scaffold split 80/10/10, zero overlap | **Scaffold Split** (`data/split.py`) – 5 × 5 repeats |
| **FR-004** | Atomic‑contribution baseline | **Baseline** (`models/baseline.py`) |
| **FR-005** | Integrated Gradients attribution | **Attribution** (`models/attribution.py`) |
| **FR-006** | MAE, RMSE, paired t‑test (or Wilcoxon) | **Evaluation** (`training/evaluate.py`) |
| **FR-007** | Parity plot & feature‑importance bar chart (<5 MB PNG) | **Plots** (`training/evaluate.py` sub‑routines) |

## Detailed Plan Phases

### 1. Open Dataset Acquisition (FR‑001)
1. **Search**: Attempt to download an open RI dataset (e.g., Zenodo, Figshare, or a curated HuggingFace dataset) that contains **≥ 500** organic molecules with experimental RI values.  
2. **Script**: `code/data/download.py` uses `datasets.load_dataset` (if a HF dataset exists) or `urllib.request` for a direct URL.  
3. **Verification**: Compute SHA‑256 checksum, store under `state/ri_dataset.sha256`. Validate columns against `contracts/dataset.schema.yaml`.  
4. **Failure Path**: If no such dataset is found, the script aborts with a clear error and the pipeline stops, flagging the specification for revision (non‑fatal to the plan but fatal to execution).

### 2. Preprocessing & Filtering (FR‑001)
- Parse SMILES with RDKit; log unparsable rows to `logs/failed_parsing.log`.  
- Compute molecular weight; drop rows with MW > 500 Da.  
- Apply temperature normalization via the Edlén equation when temperature metadata exists; otherwise flag uncertainty in `logs/preprocess_summary.log`.  
- Add normalized molecular weight as a global scalar feature.  
- Output: `data/processed/filtered.csv`.

### 3. Scaffold‑Based Repeated Splits (FR‑003)
- Generate Murcko scaffolds (`RDKit.Chem.Scaffolds.MurckoScaffold`).  
- Create **5 random scaffold splits** (seeds 100‑104); each split is repeated **5 times** with different train/val/test seeds (total 25 splits).  
- Ratios: 80 % train, 10 % validation, 10 % test.  
- Guarantee **zero scaffold overlap** between sets.  
- Save as `data/splits/train_{i}_{j}.csv`, `val_{i}_{j}.csv`, `test_{i}_{j}.csv` (`i=1..5`, `j=1..5`).

### 4. Baseline Implementation (FR‑004)
- Compute **Molar Refractivity (MR)** using additive atomic fragment constants from public tables (e.g., Meylan et al.).  
- Convert MR → RI via the **Lorentz‑Lorenz** relation.  
- Produce `results/baseline_predictions_{i}_{j}.csv` for each test split.

### 5. MPNN Architecture (FR‑002)
- 3 message‑passing layers, hidden dim = 64, mean aggregation.  
- Global readout → 2‑layer MLP (64 → 32 → 1) with ReLU.  
- All tensors on `torch.device("cpu")`.  
- Batch size defaults to 32; auto‑reduce on OOM.

### 6. Training (FR‑002)
- Loss: MSE; Optimizer: Adam (lr = 1e‑3).  
- Early stopping (patience = 10) on validation loss.  
- Max epochs = 200 (usually stops < 100).  
- Random seed pinned per split (`--seed 2000 + i*10 + j`).  
- Outputs: `models/mpnn_{i}_{j}.pt`, `logs/training_{i}_{j}.log`.

### 7. Integrated Gradients Attribution (FR‑005)
- Baseline: zero‑vector (all‑zero node/edge features).  
- 50 integration steps.  
- Sensitivity check: also run with mean‑feature and random baselines; report variance of top‑10 scores.  
- Output per split: `results/attributions_{i}_{j}.csv` conforming to `FeatureAttribution` entity.

### 8. Evaluation & Statistical Rigor (FR‑006)
- Compute **MAE** and **RMSE** for GNN and baseline on each test split.  
- Paired error differences per molecule.  
- **Paired t‑test** on differences; assess normality with Shapiro‑Wilk; if violated, fall back to **Wilcoxon signed‑rank test**.  
- Report **Cohen’s d**, 95 % CI, and p‑value (with explicit power note).  
- Summarize across 25 splits in `results/metrics_summary.csv`.

### 9. Plot Generation (FR‑007)
- **Parity plot** (`parity_{i}_{j}.png`) and **Feature‑importance bar chart** (`importance_{i}_{j}.png`) per split (< 5 MB each).  
- Aggregate across splits into `results/plots/average_parity.png` and `average_importance.png`.

### 10. Robustness & Sensitivity (User Story 3)
- Report variance of test MAE across the 25 splits (target < 0.01).  
- Hyper‑parameter sweep on L2 weight decay ∈ {0, 1e‑4, 1e‑3}; plot MAE vs. decay in `results/robustness/l2_sweep.png`.  
- Include explicit caveats about dataset size and statistical power.

### 11. Contract Validation
- After each major step, validate CSV/PNG against `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`.  
- Validation failures abort the pipeline with a logged error.

## Compute Feasibility
- **CPU‑First**: No CUDA imports; PyTorch Geometric compiled for CPU.  
- **Memory**: Even with 500+ rows, peak RAM < 1 GB.  
- **Time**: End‑to‑end runtime on GitHub Actions free tier for all 25 splits is estimated ≤ 5 h (well within the 6 h limit).

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open RI dataset ≥ 500 samples | Fatal to FR‑001 | Abort with clear message; request specification revision. |
| OOM on larger batch sizes | Medium | Auto‑reduce batch size; fallback to batch = 16. |
| Overfitting on limited data | High | Early stopping, dropout 0.2, L2 = 1e‑4; report pilot nature. |
| Attribution baseline bias | Medium | Sensitivity analysis across multiple baselines. |
| Low statistical power | Medium | Use paired test with power disclaimer; also report effect sizes. |

## Timeline (≈12 tasks)
1. **Task 1** – Implement `download.py`.  
2. **Task 2** – Implement `preprocess.py`.  
3. **Task 3** – Implement `split.py`.  
4. **Task 4** – Implement atomic‑contribution baseline (`baseline.py`).  
5. **Task 5** – Code MPNN architecture (`mpnn.py`).  
6. **Task 6** – Training script with early stopping (`train.py`).  
7. **Task 7** – Integrated Gradients attribution (`attribution.py`).  
8. **Task 8** – Evaluation metrics & paired test (`evaluate.py`).  
9. **Task 9** – Plot generation (`evaluate.py` sub‑routines).  
10. **Task 10** – Multi‑seed & hyper‑parameter robustness experiments.  
11. **Task 11** – Contract validation integration.  
12. **Task 12** – Documentation & Quickstart update.  

---
