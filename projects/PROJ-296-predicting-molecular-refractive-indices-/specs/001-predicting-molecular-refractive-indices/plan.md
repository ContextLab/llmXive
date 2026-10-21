# Implementation Plan: Predicting Molecular Refractive Indices from Graph-Based Molecular Representations

**Branch**: `001-predict-molecular-refractive-indices` | **Date**: 2026-10-21 | **Spec**: `specs/001-predict-molecular-refractive-indices/spec.md`  
**Input**: Feature specification from `/specs/001-predict-molecular-refractive-indices/spec.md`

## Summary
Implement a CPU‑only pipeline that (1) **acquires** a publicly available open‑source dataset of organic molecules with experimentally measured refractive indices containing **≥ 500** samples (if such a dataset becomes available; otherwise the plan flags the shortfall for specification revision), (2) preprocesses the data into graph objects, (3) performs **5 × 5 scaffold‑based cross‑validation** (5 random scaffold splits, each repeated 5 times) to prevent data leakage and mitigate variance on small datasets, (4) trains a lightweight 3‑layer Message Passing Neural Network (MPNN) (hidden dim = 64) on each training split, (5) computes a physics‑based atomic‑contribution baseline, (6) evaluates both models with MAE/RMSE **and a paired t‑test** (with Wilcoxon signed‑rank fallback if normality fails), (7) applies Integrated Gradients for node/edge attribution, and (8) generates the required PNG artifacts. All steps are deterministic, schema‑validated, and respect the 7 GB / 6 h CPU‑only constraints.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.0.0+cpu`, `torch-geometric`, `rdkit`, `pandas`, `numpy`, `scipy`, `torchmetrics`, `tqdm`, `scikit-learn`  
- **Storage**: CSV files under `data/` (raw, processed, splits)  
- **Testing**: `pytest` for unit/integration tests; contract validation via JSON‑Schema  
- **Target Platform**: Linux (GitHub Actions free tier)  
- **Constraints**: CPU‑only (`device="cpu"`), peak RAM ≤ 7 GB, wall‑time ≤ 6 h  

## Constitution Check
| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| **I. Reproducibility** | PASS | Fixed random seeds, deterministic data split, `requirements.txt` pins versions, checksum recorded for curated CSV (if available). |
| **II. Verified Accuracy** | PASS | All citations (e.g., NIST WebBook, OpenChem) are verified; no unverified sources introduced. |
| **III. Data Hygiene** | PASS | Raw data is immutable; preprocessing creates new files; checksums stored under `state/`. |
| **IV. Single Source of Truth** | PASS | Every metric, plot, and table is generated from the CSV outputs of the pipeline; no hand‑typed numbers. |
| **V. Versioning Discipline** | PASS | Artifacts (model weights, CSVs, PNGs) are content‑hashed; timestamps managed by the Advancement‑Evaluator. |
| **VI. CPU‑Only Execution** | PASS | All PyTorch calls enforce `torch.device("cpu")`; no CUDA libraries are imported. |
| **VII. Structural Interpretability** | PASS | Integrated Gradients applied to every trained model; attribution CSV and bar chart are mandated outputs. |
| **Dataset Limitation** | NOTE | No open‑source RI dataset with ≥ 500 samples is currently known. The plan records this limitation and flags the specification for revision. |

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

Source code layout (under repository root):
```
code/
├── data/
│   ├── download.py          # fetches open RI dataset, computes checksum
│   ├── preprocess.py
│   └── split.py
├── models/
│   ├── mpnn.py
│   ├── baseline.py
│   └── attribution.py
├── training/
│   ├── train.py
│   └── evaluate.py
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
| **FR-001** | Download & parse CSV with SMILES & RI, filter MW < 500 Da. | **Dataset Acquisition** (download.py) – now targets an open dataset ≥ 500 samples. |
| **FR-002** | 3‑layer MPNN, hidden 64, CPU‑only. | **MPNN Architecture** (models/mpnn.py) |
| **FR-003** | Scaffold split 80/10/10, zero overlap. | **Scaffold Split** (data/split.py) – 5 × 5 repeated splits. |
| **FR-004** | Atomic‑contribution baseline. | **Baseline** (models/baseline.py) |
| **FR-005** | Integrated Gradients attribution. | **Attribution** (models/attribution.py) |
| **FR-006** | MAE, RMSE, paired t‑test (or Wilcoxon). | **Evaluation** (training/evaluate.py) – paired t‑test reinstated. |
| **FR-007** | Parity plot & feature‑importance bar chart (<5 MB PNG). | **Plots** (training/evaluate.py) |

## Detailed Plan Phases

### 1. Open Dataset Acquisition (FR‑001)
1. **Search**: Attempt to download an open‑source RI dataset (e.g., from Zenodo, Figshare, or a curated subset of the *OPERA* database) that contains **≥ 500** organic molecules with experimental RI values.  
2. **Script**: `code/data/download.py` performs an HTTP GET using `datasets.load_dataset` (HuggingFace) or `urllib.request` for a direct URL.  
3. **Verification**: Compute SHA‑256 checksum, store under `state/ri_dataset.sha256`. Validate columns against `contracts/dataset.schema.yaml`. If no such dataset is found, the script aborts with a clear error and the plan records a *spec‑root cause* for kick‑back.

### 2. Preprocessing & Filtering (FR‑001)
- Parse SMILES with RDKit; invalid entries logged to `failed_parsing.log`.  
- Compute molecular weight; drop rows with MW > 500 Da.  
- Apply temperature normalization via the Edlén equation when temperature metadata exists; otherwise flag uncertainty.  
- Add **global feature**: normalized molecular weight (z‑score).  
- Output: `data/processed/filtered.csv`.

### 3. Scaffold‑Based Repeated Splits (FR‑003)
- Generate Murcko scaffold fingerprints via `RDKit.Chem.Scaffolds.MurckoScaffold`.  
- Create **5 random scaffold splits** (seeded 100‑104); each split is further repeated **5 times** with different random seeds for train/val/test (total 25 splits).  
- Ratios: [deferred] train, [deferred] validation, [deferred] test; guarantee **zero scaffold overlap** within each split.
- Save each split as `train_{i}_{j}.csv`, `val_{i}_{j}.csv`, `test_{i}_{j}.csv` (`i = 1..5`, `j = 1..5`).

### 4. Baseline Implementation (FR‑004)
- Compute **Molar Refractivity (MR)** using additive atomic fragment constants (public tables, e.g., Meylan et al.).  
- Convert MR → RI via the **Lorentz‑Lorenz** relation.  
- Store baseline predictions for each test split in `results/baseline_predictions_{i}_{j}.csv`.

### 5. MPNN Architecture (FR‑002)
- 3 message‑passing layers, hidden dim = 64, mean aggregation.  
- Global readout + 2‑layer MLP (64 → 32 → 1) with ReLU.  
- All tensors on `torch.device("cpu")`; MKL‑DNN enabled for speed.  
- Batch size defaults to 32; automatically reduced on OOM.

### 6. Training (FR‑002)
- Loss: MSE; Optimizer: Adam (lr = 1e‑3); Early stopping (patience = 10) on validation loss.  
- Max epochs = 200 (typically stops < 100).  
- Random seed pinned per split (`--seed 2000 + i*10 + j`).  
- Output per split: `models/mpnn_{i}_{j}.pt`, `logs/training_{i}_{j}.log`.

### 7. Integrated Gradients Attribution (FR‑005)
- Baseline: zero‑vector (all‑zero node/edge features).  
- 50 integration steps.  
- Sensitivity check: also run with mean‑feature and random baselines; report variance of top‑10 scores.  
- Output per split: `results/attributions_{i}_{j}.csv` conforming to the `FeatureAttribution` entity (now uses `top_features`).

### 8. Evaluation & Statistical Rigor (FR‑006)
- Compute **MAE** and **RMSE** for GNN and baseline on each test split.  
- For each split, compute per‑molecule error differences.  
- Perform a **paired t‑test** on the error differences.  
  - Assess normality with Shapiro‑Wilk; if violated, fall back to **Wilcoxon signed‑rank test**.  
- Report **Cohen’s d**, 95 % confidence interval, and the p‑value (noting low power).  
- Summarize results across the 25 splits in `results/metrics_summary.csv`.

### 9. Plot Generation (FR‑007)
- **Parity plot** (`parity_{i}_{j}.png`) and **Feature‑importance bar chart** (`importance_{i}_{j}.png`) per split.  
- PNG files compressed < 5 MB.  
- Aggregate plots across splits into `results/plots/average_parity.png` and `average_importance.png`.

### 10. Robustness & Sensitivity (User Story 3)
- **Variance reporting**: compute variance of test MAE across the 25 splits; report observed value (target < 0.01 noted as aspirational).  
- **Hyper‑parameter sweep** on L2 weight decay ∈ {0, 1e‑4, 1e‑3} within each training split; MAE vs. decay plotted in `results/robustness/l2_sweep.png`.  
- Results are interpreted with explicit caveats about dataset size.

### 11. Contract Validation
- After each major step, validate produced CSV/PNG against `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`.  
- Validation failures abort the pipeline with a logged error.

## Compute Feasibility
- **CPU‑First**: No CUDA imports; PyTorch Geometric compiled for CPU.  
- **Memory**: Even with 500+ rows, peak RAM < 1 GB.  
- **Time**: End‑to‑end runtime on GitHub Actions free tier [deferred] per split [deferred]; total duration is well within the 6 h limit for all 25 splits..

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open RI dataset ≥ 500 samples | Fatal to FR‑001 | Flag for specification revision; pipeline aborts with clear message. |
| OOM on larger batch sizes | Medium | Auto‑reduce batch size; fallback to batch = 16. |
| Overfitting on limited data | High | Early stopping, dropout 0.2, L2 = 1e‑4; report pilot nature, no significance claim. |
| Attribution baseline bias | Medium | Sensitivity analysis across multiple baselines. |
| Low statistical power | Medium | Use paired t‑test with clear power disclaimer; also report effect sizes and confidence intervals. |

## Timeline (≈12 tasks)
1. **Task 1** – Implement `download.py` (open RI dataset acquisition).  
2. **Task 2** – Implement `preprocess.py` (RDKit parsing, MW filter, temperature normalization).  
3. **Task 3** – Implement `split.py` (5 × 5 scaffold repetitions).  
4. **Task 4** – Implement atomic‑contribution baseline (`baseline.py`).  
5. **Task 5** – Code MPNN architecture (`mpnn.py`).  
6. **Task 6** – Training script with early stopping (`train.py`).  
7. **Task 7** – Integrated Gradients attribution (`attribution.py`).  
8. **Task 8** – Evaluation metrics & paired t‑test (`evaluate.py`).  
9. **Task 9** – Plot generation (`evaluate.py` sub‑routines).  
10. **Task 10** – Multi‑seed & hyper‑parameter robustness experiments.  
11. **Task 11** – Contract validation integration.  
12. **Task 12** – Documentation & Quickstart update.  

---


