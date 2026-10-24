# Implementation Plan: Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets

**Branch**: `001-molecular-permeability-gnn` | **Date**: 2026-10-24 | **Spec**: `specs/001-molecular-permeability-gnn/spec.md`  
**Input**: Feature specification from `/specs/001-molecular-permeability-gnn/spec.md`

## Summary
We will (1) **search for a verified open‑source permeability dataset**; if none is found we will **raise a spec‑amendment request** to allow a chemically justified surrogate target (e.g., logP) and document this decision transparently.  
(2) Stream the data, compute checksums, and preprocess SMILES into RDKit molecular graphs plus a standard set of RDKit descriptors, writing both **Parquet and CSV** outputs.  
(3) Enforce a [deferred] valid‑molecule retention guard **after** the output files are written (so the unit test sees the file).  
(4) Train a CPU‑optimized Message Passing Neural Network (MPNN) and Random Forest baselines (full descriptors and graph‑derived only) **only if a target column is present** (or an approved surrogate target is in place).  
(5) Evaluate with RMSE, MAE, and R², perform normality checks, a paired statistical test (t‑test or Wilcoxon), and a power analysis.  
(6) Apply SHAP (RF) and GNNExplainer (GNN) and compute an **overlap‑count metric** between the top‑5 GNN substructure mappings and the top‑5 SHAP‑ranked descriptors (replacing the previously proposed Spearman correlation).  
(7) Assemble a reproducible JSON report. All steps run on the GitHub Actions free‑tier CPU runner; no GPU is required.

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
| **I. Reproducibility** | Fixed `requirements.txt`; seeds (`numpy`, `torch`, `random`) pinned to `42`; deterministic dataset URLs; all scripts are pure functions with no hidden state. |
| **II. Verified Accuracy** | Only URLs listed in the “Verified datasets” block are used; no new citations are introduced. |
| **III. Data Hygiene** | Raw files are checksum‑verified; every transformation writes a new file under `data/processed/` or `data/interim/`; no in‑place mutation. |
| **IV. Single Source of Truth** | All quantitative results are stored in `results/metrics.json` and `results/interpretability/`; the final summary JSON references these files directly. |
| **V. Versioning Discipline** | After each stage, artifact hashes are recorded in the project state file (handled by the platform). |
| **VI. Graph‑Representation Fidelity** | Graphs are generated **only** with `rdkit.Chem.MolFromSmiles`; no manual edge modifications. |
| **VII. Validation Independence** | If a permeability column is missing, the pipeline halts **before** any modeling, preserving statistical rigor. If a surrogate target is approved, the plan documents the justification and records it in the summary. |

## Project Structure
```text
projects/PROJ-422-predicting-molecular-permeability-coeffi/
├─ code/
│  ├─ __init__.py
│  ├─ data/
│  │   ├─ download.py          # Streams datasets, computes SHA‑256 checksums, writes raw files
│  │   ├─ preprocess.py        # SMILES → graph + descriptors; writes Parquet **and** CSV; guard after write
│  │   └─ split.py             # Stratified (polymer_type) or random split
│  ├─ models/
│  │   ├─ __init__.py
│  │   ├─ gnn.py               # 3‑layer CPU‑friendly MPNN
│  │   ├─ rf.py                # Random Forest on full descriptors
│  │   └─ rf_ablation.py       # Random Forest on graph‑derived stats only
│  ├─ analysis/
│  │   ├─ train.py             # Training loops, early stopping, power analysis
│  │   ├─ evaluate.py          # Metrics, normality test, paired test, results JSON
│  │   └─ explain.py           # SHAP (RF) & GNNExplainer (GNN) + overlap‑count metric
│  └─ utils/
│      └─ logging.py           # Structured JSON logging
├─ data/
│  ├─ raw/                     # Downloaded datasets (checksum‑verified)
│  ├─ processed/               # Processed feature table (Parquet & CSV)
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
All Functional Requirements (FR‑001 – FR‑014) and Success Criteria (SC‑001 – SC‑005) are explicitly mapped to concrete phases/steps below. No extra constraints are introduced.

## Phase Plan & FR/SC Mapping

| Phase | Tasks (high‑level) | FR(s) addressed | SC(s) addressed |
|-------|-------------------|-----------------|-----------------|
| **Phase 0 – Data Acquisition & Target Strategy** | 0.1 Search open repositories (Zenodo, OpenML, Figshare) for datasets containing `smiles` **and** experimental `permeability` columns. Use programmatic APIs; if found, add URL to the verified list and proceed.<br>0.2 **If no such dataset is found**, automatically raise a spec‑amendment request (recorded in `state/projects/...yaml`) to permit a surrogate target (e.g., `logp`). The request includes scientific justification and will be reviewed before any modeling.<br>0.3 If a surrogate is approved, treat the chosen column as `target`; otherwise abort with clear message. | FR‑001 (conditional on successful acquisition or approved amendment) | SC‑005 (data‑integrity guard still applies) |
| **Phase 1 – Download** | 1.1 `code/data/download.py` streams each verified dataset via `datasets.load_dataset(..., streaming=True)`, computes SHA‑256 checksums, writes raw files to `data/raw/`.<br>1.2 On checksum mismatch, abort with clear error. | FR‑001, FR‑002 | — |
| **Phase 2 – Preprocess** | 2.1 `code/data/preprocess.py` reads streamed raw files, parses SMILES with `rdkit.Chem.MolFromSmiles` (logs & drops invalid SMILES – FR‑011).<br>2.2 Computes RDKit descriptors (MW, logP, TPSA, H‑bond acceptors/donors, rotatable bonds).<br>2.3 Writes **`data/processed/processed_data.parquet` and `processed_data.csv`** **before** any retention check (satisfies unit test).<br>2.4 Calculates fraction of rows with `mol_valid=True`. If < 95 % → log warning, set exit code = 1 **after** files exist (FR‑012, FR‑010).<br>2.5 Performs bias check: Pearson |r| > 0.6 between any descriptor and `target`; if found, set `bias_warning=True` in results (FR‑014). | FR‑002, FR‑003, FR‑010, FR‑011, FR‑014 | SC‑005 |
| **Phase 3 – Split** | 3.1 `code/data/split.py` creates stratified train/test splits by `polymer_type` when present; otherwise random split with seed = 42. Only rows with non‑null `target` (or approved surrogate) are included. Writes `train.parquet` and `test.parquet`. | FR‑004 | — |
| **Phase 4 – Model Construction** *(executed only if `target` exists or surrogate approved)* | 4.1 `models/gnn.py` – 3‑layer MPNN, hidden = 64, global mean pooling, regression head; CPU‑only (`device="cpu"`).<br>4.2 `models/rf.py` – Random Forest on full descriptor vector (`n_estimators=200`).<br>4.3 `models/rf_ablation.py` – Random Forest on **graph‑derived statistics only** (no standard descriptors) to isolate topological value (FR‑013). | FR‑005, FR‑006, FR‑013 | — |
| **Phase 5 – Training & Evaluation** *(only when `target` is present or surrogate approved)* | 5.1 `analysis/train.py` – train GNN (max 50 epochs, early stopping patience = 5) and both RF variants; serialize models.<br>5.2 **Power analysis**: using `statsmodels` compute required N for medium effect (Cohen’s d = 0.5) at α = 0.05, 80 % power; record planned size; flag if actual N is smaller (SC‑004).<br>5.3 `analysis/evaluate.py` – compute RMSE, MAE, R² on test set for all three models; store in `results/metrics.json` (validated against `contracts/results.schema.yaml`).<br>5.4 Compute per‑sample absolute errors for GNN and RF baseline.<br>5.5 **Normality test** (Shapiro‑Wilk). If p ≥ 0.05 → paired t‑test; else → Wilcoxon signed‑rank test. Record method, p‑value, decision (SC‑001, SC‑002).<br>5.6 Record runtime and peak memory; abort with clear error if > 6 h or > 7 GB (SC‑004). | FR‑006, FR‑007, FR‑012 | SC‑001, SC‑002, SC‑004 |
| **Phase 6 – Interpretability** *(only when `target` is present or surrogate approved)* | 6.1 `analysis/explain.py` – SHAP (KernelSHAP) on the RF baseline and RF‑ablation; produce ranked CSV and bar‑chart PNG.<br>6.2 Run GNNExplainer on 100 random test molecules; aggregate masks to a global substructure importance ranking; visualized as heatmaps.<br>6.3 **Overlap‑count metric**: map each GNN‑identified substructure to the most chemically related standard descriptor (e.g., aromatic ring → logP, H‑bond donor groups → HBD). Count how many of the top‑5 substructures overlap with the top‑5 SHAP‑ranked descriptors. Store this integer and a boolean flag `overlap_meets_threshold` (≥3 overlap) in `results/metrics.json` (replaces previous Spearman correlation) (SC‑003). | FR‑008, FR‑009 | SC‑003 |
| **Phase 7 – Reporting & Validation** | 7.1 Assemble `results/summary.json` referencing exact files in `data/processed/` and `results/` (single source of truth).<br>7.2 Run full CI (`./run_all.sh`); validate all contracts; ensure deterministic outputs across runs.<br>7.3 Update artifact hashes in project state file. | FR‑001 – FR‑014 (all) | SC‑001 – SC‑005 |
| **Phase 8 – Cleanup** | 8.1 Delete temporary `interim/` graph serializations (keep provenance logs).<br>8.2 Archive logs under `logs/` for auditability. | — | — |

### Additional Guarantees
- **Deterministic Output**: `numpy.random.seed(42)`, `torch.manual_seed(42)`, `random.seed(42)`.
- **Retention Guard**: Output files are always written; the script exits with code = 1 **after** the files exist if the 95 % threshold is not met, satisfying the unit test.
- **Multiple‑Comparison**: Only a single hypothesis (GNN vs. RF) is tested; no family‑wise correction needed.
- **CPU‑First**: All model training uses CPU; no CUDA calls. If a GPU‑only method were ever required, the plan would explicitly switch to the Kaggle GPU escape hatch.

---



## projects/PROJ-422-predicting-molecular-permeability-coeffi/specs/001-predicting-molecular-permeability-coeffi/research.md
# Research: Predicting Molecular Permeability Coefficients Using Graph Neural Networks

## 1. Problem Definition
We evaluate whether a graph‑based Message Passing Neural Network (MPNN) can outperform a descriptor‑based Random Forest (RF) in predicting **experimental permeability coefficients** of polymeric membranes. The target must be an independent experimental measurement; no surrogate (e.g., logP) will be used **unless** the specification is formally amended to permit a justified surrogate (see Phase 0 of the implementation plan).

## 2. Dataset Strategy

### 2.1 Verified Open Datasets
Only the following open datasets (verified URLs) are available for download via the Hugging Face `datasets` library:

| Dataset | URL | Format | Variables |
|---------|-----|--------|-----------|
| **ChEMBL‑derived RDKit descriptors** | `https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet` | Parquet | `smiles`, `mw`, `logp`, `tpsa`, `hba`, `hbd`, `rotatable_bonds` |
| **Half‑ChEMBL RDKit descriptors** | `https://huggingface.co/datasets/fabikru/half-of-chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet` | Parquet | Same as above |
| **SMILES‑Transformers** | `https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet` | Parquet | `smiles` only |
| **SELFormer SMILES** | `https://huggingface.co/datasets/HUBioDataLab/SELFormer-smiles/resolve/main/data.csv` | CSV | `smiles` only |
| **TPSA / GRAPO** | `https://huggingface.co/datasets/Alan123/hba_hbd_tpsa_grpo/resolve/main/data/train-00000-of-00001.parquet` | Parquet | `smiles`, `tpsa`, `hba`, `hbd` |
| **RDKit (generic)** | `https://huggingface.co/datasets/nglebm19/rdkit_chemical/resolve/main/data/train-00000-of-00001.parquet` | Parquet | `smiles` + a set of RDKit descriptors |

**No verified source contains experimental permeability measurements.** Consequently, FR‑001 (acquire a permeability dataset) cannot be satisfied with the current open data. The pipeline therefore **halts after preprocessing** if no `permeability` column is detected, emitting a clear limitation warning (Constitution VII).  

**Spec‑amendment path:** If the project stakeholders approve using a chemically justified surrogate target (e.g., `logP`, which is known to correlate with membrane permeability), the plan will treat that column as the regression target and proceed with modeling. This amendment must be recorded in the project state file.

### 2.2 Target Selection (Current Limitation)
- **If** a dataset with a true `permeability` column is later added, it will be used as the regression target.
- **If** a surrogate target is approved, the chosen column (e.g., `logP`) will be used and the analysis will note the surrogate nature throughout.
- **Otherwise**, the pipeline stops after preprocessing; no model training or evaluation occurs, preserving statistical rigor.

### 2.3 Data Volume & Streaming
All listed datasets are ≤ 1 GB each. We will load them with `datasets.load_dataset(..., streaming=True)` to keep RAM usage low while processing the full dataset.

## 3. Methodology

### 3.1 Feature Engineering
1. **SMILES → Graph** using `rdkit.Chem.MolFromSmiles`. Invalid SMILES are logged and excluded (FR‑011).  
2. **Node Features**: atomic number, degree, formal charge, hybridization, aromatic flag.  
3. **Edge Features**: bond type, conjugation flag.  
4. **Standard Descriptors** (RDKit): MW, TPSA, H‑bond acceptors/donors, rotatable bonds, logP.  
5. **Graph‑Derived Statistics** (for RF‑ablation): mean node degree, graph density, aromatic‑ring count, functional‑group counts (carbonyl, amine, etc.).  

All transformations output a Parquet file `data/processed/processed_data.parquet` **and** a CSV `processed_data.csv` that conform to `contracts/dataset.schema.yaml`.

### 3.2 Model Architectures
- **MPNN (GNN)**: 3 message‑passing layers, hidden = 64, global mean pooling, linear regression head. Trained with Adam (`lr=0.001`), batch size = 32, early stopping (patience = 5) on validation loss. CPU‑only (`device="cpu"`).  
- **Random Forest Baseline**: `sklearn.ensemble.RandomForestRegressor`, `n_estimators=200`, `max_features='sqrt'`. Trained on the full descriptor vector.  
- **Random Forest Ablation**: Same hyper‑parameters, trained **only** on graph‑derived statistics (no standard descriptors) to isolate topological value (FR‑013).

### 3.3 Training & Evaluation (only when `target` is present or surrogate approved)
- **Split**: Train / test split (ratio deferred) stratified by `polymer_type` when available; otherwise random with fixed seed `42`.  
- **A‑priori Power Analysis**: Using `statsmodels.stats.power.tt_ind_solve_power` to compute required N for a medium effect (Cohen’s d = 0.5) at α = 0.05, 80 % power. Record planned size; if actual N is smaller, log a “limited power” flag (SC‑004).  
- **Metrics**: RMSE, MAE, R² on the held‑out test set.  
- **Statistical Test**:  
  1. Shapiro‑Wilk test on paired error differences.  
  2. If normal (p ≥ 0.05) → paired two‑sample t‑test; else → Wilcoxon signed‑rank test.  
  3. Record method, p‑value, and significance decision (SC‑001, SC‑002).  
- **Effect Size**: Compute Cohen’s d for the paired differences; store in results.  

### 3.4 Interpretability
- **SHAP (RF)**: KernelSHAP on the descriptor baseline (and on the ablation model); mean absolute SHAP values are ranked and plotted.  
- **GNNExplainer**: Run on a representative set of random test molecules; aggregate subgraph masks to a global importance ranking of functional groups/substructures; visualized as heatmaps.  
- **Cross‑Model Comparison**: We compute an **overlap‑count metric**: each top‑5 GNN‑identified substructure is mapped to the most chemically related standard descriptor (e.g., aromatic ring → logP, H‑bond donor groups → HBD). We then count how many of the top‑5 mapped descriptors overlap with the top‑5 SHAP‑ranked descriptors. The metric reports the integer overlap (0–5) and a boolean flag `overlap_meets_threshold` (true if overlap ≥ 3), satisfying SC‑003.  

All outputs are saved under `results/interpretability/`.

### 3.5 Risk & Mitigation Summary
| Risk | Mitigation |
|------|------------|
| No true permeability data | Flag spec limitation; halt before training to avoid circular validation. |
| Small dataset → overfitting | Early stopping, modest hidden size, dropout = 0.1, RF ablation baseline. |
| Invalid SMILES | RDKit parsing guard; log & drop; retention check ensures ≥ 95 % valid molecules (FR‑011). |
| High correlation between descriptors & target (proxy risk) | Bias check (FR‑014) flags |r| > 0.6; reported transparently. |
| CPU memory overflow | Streaming load, batch size = 32, fallback to random subset if needed. |

---



## projects/PROJ-422-predicting-molecular-permeability-coeffi/specs/001-predicting-molecular-permeability-coeffi/data-model.md
# Data Model: Molecular Permeability Prediction

## 1. Overview
Defines JSON‑Schema contracts for raw ingestion, processed intermediate representations, and model output. All files are validated against the schemas located in `contracts/`.

## 2. Entities

### 2.1 Raw Molecule Record
| Field | Type | Description |
|-------|------|-------------|
| `smiles` | string | SMILES notation of the molecule |
| `polymer_type` | string / null | Optional stratification label |
| `permeability` | number / null | Experimental permeability coefficient (may be missing in open datasets) |
| `logp` | number / null | Calculated LogP (present in some descriptor datasets) |

### 2.2 Processed Molecule Record *(conforms to `contracts/dataset.schema.yaml`)*  
| Field | Type | Description |
|-------|------|-------------|
| `smiles` | string | Original SMILES |
| `mol_valid` | boolean | `True` if RDKit parsed successfully |
| `mw` | number | Molecular Weight |
| `logp` | number | Calculated LogP |
| `tpsa` | number | Topological Polar Surface Area |
| `hba` | integer | Number of Hydrogen Bond Acceptors |
| `hbd` | integer | Number of Hydrogen Bond Donors |
| `rotatable_bonds` | integer | Number of Rotatable Bonds |
| `target` | number / null | Experimental permeability coefficient if available; null otherwise |
| `polymer_type` | string / null | Polymer type for stratification (optional) |

### 2.3 Model Prediction Record *(conforms to `contracts/results.schema.yaml`)*  
| Field | Type | Description |
|-------|------|-------------|
| `molecule_id` | string | Unique identifier (e.g., row index) |
| `true_value` | number | Ground‑truth target (permeability) |
| `predicted_gnn` | number | GNN regression output |
| `predicted_rf` | number | RF baseline output |
| `predicted_rf_ablation` | number | RF trained on graph stats only |
| `error_gnn` | number | `predicted_gnn – true_value` |
| `error_rf` | number | `predicted_rf – true_value` |

## 3. Transformation Workflow
1. **Download** raw files → `data/raw/` (checksum verified).  
2. **Preprocess** (`code/data/preprocess.py`):  
   - Parse SMILES → graph; compute descriptors.  
   - Set `mol_valid`; drop rows where `mol_valid=False`.  
 - Write `data/processed/processed_data.parquet` **before** applying the [deferred] retention guard.
   - If the guard fails, the script exits with a non‑zero code **after** the file exists, satisfying the unit test.  
   - Rows with `target` = null are excluded from modeling later.  
3. **Split** (`code/data/split.py`): produce `train.parquet` and `test.parquet` under `data/processed/` (only rows with non‑null `target`).  
4. **Model Training** → serialize models under `code/models/`.  
5. **Evaluation** → write `results/metrics.json` (validated against `contracts/results.schema.yaml`).  
6. **Interpretability** → write PNG/HTML under `results/interpretability/`.

## 4. Constraints
- No NaNs in any numeric column of the processed dataset.  
- Graph construction must be a faithful RDKit conversion (Constitution VI).  
- **Target column must be experimental permeability**; if absent, the pipeline stops before modeling (Constitution VII).

---



## projects/PROJ-422-predicting-molecular-permeability-coeffi/specs/001-predicting-molecular-permeability-coeffi/quickstart.md
# Quickstart: Molecular Permeability GNN Pipeline

## Prerequisites
- Python 3.11 or newer
- Git
- Internet access (to download Hugging Face datasets)

## Installation
```bash
# Clone the repository (replace <repo-url> with the actual URL)
git clone <repo-url>
cd projects/PROJ-422-predicting-molecular-permeability-coeffi

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install exact dependencies
pip install -r requirements.txt
```

## Step‑by‑Step Execution

1. **Load & Verify Data (streaming)**
   ```bash
   python code/data/preprocess.py
   ```
   - Streams the verified datasets from Hugging Face, computes SHA‑256 checksums on the fly, parses SMILES, and writes **both** `data/processed/processed_data.parquet` **and** `data/processed/processed_data.csv`.  
   - If the valid‑molecule retention rate falls below 95 %, the script logs a warning and **exits with a non‑zero code after the files are written** (so they are available for inspection).  
   - **If no `permeability` column is found**, the script stops after this step with an informative message and prompts the user to approve a surrogate target via the spec‑amendment workflow (see Phase 0 of the plan).  

2. **Train & Evaluate** *(only runs when a true permeability target is present or an approved surrogate is used)*
   ```bash
   # Train all models, perform power analysis, and evaluate
   python code/analysis/train.py --config config.yaml
   ```
   - Handles train/validation split, early stopping, power analysis, and writes `results/metrics.json`.  
   - If the required target column is missing and no surrogate is approved, the script terminates gracefully after reporting the limitation.

3. **Interpretability**
   ```bash
   python code/analysis/explain.py
   ```
   - Generates SHAP plots for the Random Forest (and ablation) and GNNExplainer visualizations for the GNN.  
   - Outputs are stored in `results/interpretability/`.

4. **Full End‑to‑End Run (optional)**
   ```bash
   ./run_all.sh
   ```
   *`run_all.sh`* simply chains the three commands above and exits with a non‑zero code if any step fails.

## Expected Outputs
- `data/processed/processed_data.parquet` and `processed_data.csv` – cleaned feature tables (or a warning if retention < 95 %).  
- `results/metrics.json` – RMSE, MAE, R² for GNN, RF, RF‑ablation; paired test result; normality test outcome; power‑analysis summary; bias‑check flag; **interpretability overlap** metric.  
- `results/interpretability/` – PNG/HTML files for SHAP bar charts and GNNExplainer substructure heatmaps.  

## Reproducibility Tips
- Random seeds are fixed (`seed=42`) inside the code base.  
- All dataset URLs are hard‑coded; rerunning the pipeline will fetch identical data.  
- The CI runner uses the same `requirements.txt`; no hidden dependencies.

## What Happens When No Permeability Data Is Available?
The pipeline will stop after the preprocessing step and emit a clear message indicating that **FR‑001 cannot be satisfied with the current open datasets**. At that point, a spec‑amendment request can be submitted (see Phase 0) to permit a surrogate target. Until such an amendment is approved, no modeling or downstream analysis will be performed, preserving scientific rigor.  
