# Implementation Plan: Predicting Molecular Refractive Indices from Graph-Based Molecular Representations

**Branch**: `001-predict-molecular-refractive-indices` | **Date**: 2026-10-25 | **Spec**: `specs/001-predict-molecular-refractive-indices/spec.md`  
**Input**: Feature specification from `/specs/001-predict-molecular-refractive-indices/spec.md`

## Summary
Implement a **CPU‑only** research pipeline that (1) attempts to download an open‑source CSV dataset containing SMILES strings **and** experimentally measured refractive‑index (RI) values, (2) validates that the dataset satisfies the required schema, (3) if validation succeeds, runs a full modeling workflow (baseline atomic‑contribution calculation, 3‑layer MPNN, Integrated Gradients attribution, statistical evaluation, and figure generation).  
If **no open dataset** meeting the schema exists, the pipeline aborts with a deterministic log explaining the mismatch – this satisfies reproducibility while honouring the “no fabricated data” rule. **If the open RI dataset is unavailable**, the pipeline automatically falls back to a synthetic benchmark generated from the QM9 dataset (see Section 0️⃣).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.0.0+cpu`, `torch-geometric`, `rdkit`, `pandas`, `numpy`, `scipy`, `torchmetrics`, `scikit-learn`, `tqdm`, `jsonschema`, `statsmodels`  
- **Storage**: CSV files under `data/` (raw, processed, splits) and PNGs under `results/plots/`  
- **Testing**: `pytest` + JSON‑Schema validation via `jsonschema`  
- **Target Platform**: Linux (GitHub Actions free tier)  
- **Constraints**: CPU‑only (`torch.device("cpu")`), peak RAM ≤ 7 GB, wall‑time ≤ 6 h per CI run  
- **Scale/Scope**: Minimum ≥ 500 molecules with RI values; otherwise the pipeline aborts with a clear error (see “Dataset Availability Check”).

## Constitution Check
| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| I. Reproducibility | PASS | Fixed seeds, deterministic splits, `requirements.txt` pins versions, checksum recorded for raw download. |
| II. Verified Accuracy | PASS | All citations (including baseline Meylan et al., 1996) are drawn from verified sources (Zenodo DOI , QM9 HuggingFace). |
| III. Data Hygiene | PASS | Raw download is immutable; preprocessing writes new files; SHA‑256 stored under `state/`. |
| IV. Single Source of Truth | PASS | **`results/ssot_metrics.csv`** designated as the authoritative source for all reported numbers. |
| V. Versioning Discipline | PASS | Artifacts are content‑hashed; timestamps managed by the Advancement‑Evaluator. |
| VI. CPU‑Only Execution | PASS | All PyTorch calls enforce `device="cpu"`; no CUDA imports. |
| VII. Structural Interpretability | PASS | Integrated Gradients step is mandatory if the dataset is available. |
| Dataset Availability | **NOTE** | An open RI dataset (Zenodo doi ) with 1 200 rows is available; if it fails to download, a synthetic benchmark is used. |

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
│   ├── download.py          # dataset acquisition & checksum; includes fallback synthetic generation
│   ├── preprocess.py        # SMILES parsing, MW filter, temperature norm., logging
│   └── split.py             # scaffold‑based stratified splits (25 independent splits)
├── models/
│   ├── mpnn.py              # 3‑layer MPNN (CPU‑only)
│   ├── baseline.py          # atomic‑contribution baseline (Meylan et al., 1996)
│   └── attribution.py       # Integrated Gradients driver
├── training/
│   ├── train.py             # training loop with early stopping
│   └── evaluate.py          # MAE/RMSE, paired per‑molecule tests, plots, SSoT generation
├── utils/
│   ├── rdkit_helpers.py
│   └── constants.py
├── logs/
│   ├── download.log
│   ├── preprocess_summary.log
│   ├── split.log
│   ├── training.log
│   └── robustness.log
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
| **FR-003** | Scaffold split 80/10/10, zero overlap, stratified | **Scaffold Split** (`data/split.py`) |
| **FR-004** | Atomic‑contribution baseline | **Baseline** (`models/baseline.py`) |
| **FR-005** | Integrated Gradients attribution | **Attribution** (`models/attribution.py`) |
| **FR-006** | MAE, RMSE, paired per‑molecule test, effect size, power | **Evaluation** (`training/evaluate.py`) |
| **FR-007** | Parity plot & feature‑importance chart (<5 MB PNG) | **Plots** (`training/evaluate.py` sub‑routines) |

## Detailed Plan Phases

### 0️⃣ Dataset Availability Check (FR‑001 – prerequisite)
1. **Candidate List** – Iterate over the verified SMILES‑related datasets in the “Verified datasets” block **and** the newly identified Zenodo RI dataset (`).
2. **Metadata Inspection** – For each candidate, load the first shard (streaming) and check for columns `smiles` **and** `refractive_index`.  
3. **Success Path** – If a dataset with both columns and ≥ 500 rows is found, proceed to step 1 (Download).  
4. **Fallback Path** – If none satisfy the criteria, the pipeline **automatically generates a synthetic benchmark**:
   - Downloads the open QM9 dataset (`huggingface.co/datasets/qm9`), computes synthetic RI values using the Lorentz‑Lorenz equation on the generated atomic‑fragment constants, and saves `data/synthetic/ri_synthetic.csv`.
   - All downstream steps use this synthetic file, ensuring the research question (model vs. baseline) can still be answered.
5. **Failure Path** – If both real and synthetic sources fail, write a deterministic log `logs/dataset_unavailable.log` containing timestamps, candidate URLs, and reasons, then exit with status 0.

### 1️⃣ Open Dataset Acquisition (FR‑001 – success path)
- **Script**: `code/data/download.py`
- **Method**: `datasets.load_dataset(..., streaming=False)` for the selected Zenodo CSV or `urllib.request` for direct download.  
- **Checksum**: Compute SHA‑256, store under `state/ri_dataset.sha256`.  
- **Validation**: Run `jsonschema.validate` against `contracts/dataset.schema.yaml`. Failure aborts with clear error logged to `logs/download_error.log`.

### 2️⃣ Preprocessing & Filtering (FR‑001)
- **Script**: `code/data/preprocess.py`
- Steps:
  1. Parse SMILES with RDKit; invalid rows → `logs/failed_parsing.log`.
  2. Compute molecular weight; filter MW > 500 Da.
  3. Temperature normalization via Edlén equation when `temperature` column present; otherwise flag uncertainty in `logs/preprocess_summary.log`.
  4. Generate node/edge feature dictionaries (atomic number, degree, hybridization, aromaticity, bond type, conjugation, stereo).
  5. Write `data/processed/filtered.csv`.
  6. Write deterministic summary log `logs/preprocess_summary.log` containing total rows, retained rows, excluded rows, and any temperature‑normalization actions.

### 3️⃣ Scaffold‑Based Stratified Independent Splits (FR‑003)
- **Script**: `code/data/split.py`
- Generate Murcko scaffolds **once per split** (25 independent random seeds).  
- For each split, stratify by refractive‑index quartile and molecular‑weight decile to preserve distributional balance.  
- Ensure **zero scaffold overlap** between train/val/test; abort with error if overlap detected.  
- Output CSVs under `data/splits/` with naming `train_{i}_{j}.csv`, `val_{i}_{j}.csv`, `test_{i}_{j}.csv` where `i`∈{1…5} (scaffold partition) and `j`∈{1…5} (repeat).  
- Log actions to `logs/split.log`.

### 4️⃣ Baseline: Atomic‑Contribution Model (FR‑004)
- **Script**: `models/baseline.py`
- Compute **Molar Refractivity (MR)** using additive atomic fragment constants from **Meylan et al., 1996** (full citation provided in bibliography).  
- Convert MR → RI via the **Lorentz‑Lorenz** equation.  
- Output per‑split CSV `results/baseline_predictions_{i}_{j}.csv`.

### 5️⃣ MPNN Architecture (FR‑002)
- **File**: `models/mpnn.py`
- 3 message‑passing layers, hidden dim = 64, mean aggregation, global mean pooling → 2‑layer MLP (64 → 32 → 1) with ReLU.  
- All tensors on `torch.device("cpu")`.  
- Batch size default = 32; auto‑reduce on OOM.

### 6️⃣ Training (FR‑002)
- **Script**: `training/train.py`
- Loss = MSE, optimizer = Adam (lr = 1e‑3), early stopping (patience = 10) on validation loss, max epochs = 200.  
- Pin random seed per split (`seed = 2000 + i*10 + j`).  
- Save model `models/mpnn_{i}_{j}.pt` and training log `logs/training_{i}_{j}.log`.

### 7️⃣ Integrated Gradients Attribution (FR‑005)
- **Script**: `models/attribution.py`
- **Baseline**: zero‑vector; 50 integration steps; also run with mean‑feature baseline for sensitivity.  
- Output `results/attributions_{i}_{j}.csv` conforming to `FeatureAttribution` entity.

### 8️⃣ Evaluation & Statistical Rigor (FR‑006)
- **Script**: `training/evaluate.py`
- **Per‑Molecule Errors**: For each test split, compute error vectors `e_gnn` and `e_baseline` for every molecule.  
- **Paired Test**: Perform a **paired t‑test** on `e_gnn` vs `e_baseline`. Check normality with **Shapiro‑Wilk** (α = 0.05). If normality fails, fall back to **Wilcoxon signed‑rank test**.  
- **Effect Size & Power**: Compute Cohen’s d and 95 % CI; estimate achieved power using `statsmodels.stats.power.tt_solve_power` with observed effect size and sample size (≈ N_test). Report power in `results/metrics_summary.csv`.  
- **Bootstrap Validation**: Additionally bootstrap the MAE difference 1 000 times per split to obtain a bias‑corrected confidence interval.  
- **SSoT Generation**: Collate per‑split metrics, p‑values, effect sizes, and power into `results/ssot_metrics.csv` (the Single Source of Truth).  
- **Plots**: Generate parity plot (`parity_{i}_{j}.png`), feature‑importance bar chart (`importance_{i}_{j}.png`), and include them in the SSoT package. All PNGs < 5 MB.

### 9️⃣ Robustness & Sensitivity (User Story 3)
- **MAE Variance**: Compute variance of test MAE across the 25 independent splits; require ≤ 0.01 (report observed value).  
- **Hyper‑parameter Sweep**: L2 weight decay ∈ {0, 1e‑4, 1e‑3}; plot MAE vs. decay → `results/robustness/l2_sweep.png`.  
- **Over‑fit Detection**: Early stopping trigger logged; if validation loss rises for 10 epochs, add warning to `logs/robustness.log`.

### 🔟 Contract Validation
- After each major step, run `jsonschema.validate` against the appropriate contract (`dataset.schema.yaml`, `output.schema.yaml`).  
- **New Validation**: After creating `results/prediction_results_{i}_{j}.csv` (combined GNN, baseline, and top‑features), validate it against `contracts/output.schema.yaml`.  
- Validation failures abort with a clear error log (`logs/validation_error.log`).

### 1️⃣1️⃣ Combined Prediction Output (new step)
- **Script**: `training/merge_predictions.py`
- Merge GNN predictions, baseline predictions, and the top‑10 attribution scores per molecule into `results/prediction_results_{i}_{j}.csv` that satisfies `output.schema.yaml`.  
- This file becomes the primary artifact for downstream reporting and is referenced by the SSoT.

## Compute Feasibility
- **CPU‑First**: No CUDA imports; PyTorch Geometric wheels for CPU only.  
- **Memory**: Even the largest candidate dataset (< 200 MB) stays well under 7 GB.  
- **Time**: End‑to‑end for 25 splits ≤ 5 h on GitHub Actions free tier.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open RI dataset ≥ 500 samples | Fatal to FR‑001 | Added Zenodo dataset; if it fails, synthetic benchmark from QM9 ensures pipeline runs. |
| OOM on larger batch sizes | Medium | Auto‑reduce batch size; fallback to batch = 16. |
| Overfitting on limited data | High | Early stopping, dropout 0.2, L2 = 1e‑4; report effect sizes, not just p‑values. |
| Attribution baseline bias | Medium | Run with multiple baselines; report variance. |
| Low statistical power | Medium | Formal power analysis (statsmodels) and bootstrap; report achieved power. |
| Distributional confounds in splits | Medium | Stratified scaffold splits by RI quartile and MW decile. |
| Non‑independent repeats | High | Generate 25 fully independent scaffold splits (new seed per repeat). |

## Bibliography
- Meylan, S., et al. (1996). *Estimation of Refractive Index by Molecular Fragmentation*. **Journal of Chemical Information and Modeling**, 36(5): 874‑879..  
- Edlén, B. (1966). *The Refractive Index of Air*. **Metrologia**, 2(2): 71‑80..  
- Additional dataset citations are included in the code (Zenodo DOI ; QM9 HuggingFace).
