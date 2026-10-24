# Implementation Plan: Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets

**Branch**: `001-molecular-permeability-gnn` | **Date**: 2026-10-24 | **Spec**: `specs/001-molecular-permeability-gnn/spec.md`  
**Input**: Feature specification from `/specs/001-molecular-permeability-gnn/spec.md`

## Summary
We will (1) **search for an open‑source dataset that contains both SMILES strings and experimental permeability coefficients**; if none exists the pipeline **halts** and reports a clear limitation (no surrogate target is permitted). (2) Stream the verified dataset(s), checksum‑verify, and preprocess SMILES into RDKit molecular graphs and a standard set of RDKit descriptors, writing both Parquet and CSV outputs. (3) Enforce a deferred [deferred] valid‑molecule retention guard **after** the output files are written (so the unit test can see the file). (4) Train a CPU‑optimized Message Passing Neural Network (MPNN) and a Random Forest baseline **only when a true permeability target column is present**. (5) Evaluate with RMSE, MAE, and R²; perform a Shapiro‑Wilk normality test, then a paired t‑test (or Wilcoxon if non‑normal), and conduct a **data‑driven power analysis** using either a pilot effect‑size estimate or a literature‑derived estimate. (6) Apply SHAP to the RF baseline and GNNExplainer to the GNN, compute an overlap‑count metric between the top‑5 substructures and top‑5 descriptors, satisfying SC‑003. (7) Assemble a reproducible JSON report and validate all artifacts against contracts. All steps run on the GitHub Actions free‑tier CPU runner; no GPU is required.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit`, `torch==2.2.0`, `torch-geometric`, `scikit-learn`, `shap`, `pandas`, `datasets`, `statsmodels`, `numpy`, `matplotlib`  
**Storage**: Local filesystem under `data/` (raw, processed, interim) and `results/` for metrics/figures  
**Testing**: `pytest` (unit & integration)  
**Target Platform**: Linux runner on GitHub Actions (2 CPU cores, ≤7 GB RAM, ≤6 h)  
**Constraints**: CPU‑only execution; streaming mode for any file > 7 GB  
**Scale/Scope**: ≤ 1 GB total raw data, ≤ 200 k molecules (verified open datasets)

## Constitution Check

| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Fixed `requirements.txt`; seeds (`numpy`, `torch`, `random`) pinned to `42`; deterministic dataset URLs; pure‑function scripts. |
| **II. Verified Accuracy** | Only URLs listed in the **Verified Datasets** block below are used; no new citations are introduced. |
| **III. Data Hygiene** | Raw files checksum‑verified; every transformation writes a new file under `data/processed/` or `data/interim/`; no in‑place mutation. |
| **IV. Single Source of Truth** | All quantitative results stored in `results/metrics.json` and `results/interpretability/`; final summary JSON references these files directly. |
| **V. Versioning Discipline** | Artifact hashes recorded automatically by the platform after each stage. |
| **VI. Graph‑Representation Fidelity** | Graphs generated **only** with `rdkit.Chem.MolFromSmiles`; no manual edge modifications. |
| **VII. Validation Independence** | Modeling proceeds **only** when a true experimental permeability column is present; surrogate targets are prohibited unless a spec amendment introduces a non‑descriptor target. |

## Verified Datasets
| Dataset | URL | Format | Variables |
|---------|-----|--------|-----------|
| **ChEMBL‑derived RDKit descriptors** | ` | Parquet | `smiles`, `mw`, `logp`, `tpsa`, `hba`, `hbd`, `rotatable_bonds` |
| **Half‑ChEMBL RDKit descriptors** | ` | Parquet | Same as above |
| **SMILES‑Transformers** | ` | Parquet | `smiles` only |
| **SELFormer SMILES** | ` | CSV | `smiles` only |
| **TPSA / GRAPO** | ` | Parquet | `smiles`, `tpsa`, `hba`, `hbd` |
| **RDKit (generic)** | ` | Parquet | `smiles` + a set of RDKit descriptors |

*None of the verified open datasets contain an experimental permeability column.* Consequently, **Phase 0** will stop the pipeline if no such column is found (see below).

## Project Structure
```text
projects/PROJ-422-predicting-molecular-permeability-coeffi/
├─ code/
│  ├─ __init__.py
│  ├─ data/
│  │   ├─ download.py          # Streams datasets, computes SHA‑256 checksums
│  │   ├─ preprocess.py        # SMILES → graph + descriptors; writes Parquet & CSV
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

| Phase | High‑level Tasks | FR(s) addressed | SC(s) addressed |
|-------|------------------|-----------------|-----------------|
| **Phase 0 – Data Acquisition & Target Strategy** | 0.1 Search open repositories for a dataset **with** experimental permeability coefficients.<br>0.2 If none is found, **halt** the pipeline with a clear message and **do not** fall back to any surrogate target (preserves construct validity).<br>0.3 If a spec‑amendment later introduces a validated non‑descriptor target, the pipeline may resume from this point. | FR‑001 (conditional) | SC‑005 (data‑integrity guard still applies) |
| **Phase 1 – Download** | 1.1 `code/data/download.py` streams each verified dataset via `datasets.load_dataset(..., streaming=True)`, computes SHA‑256 checksums, writes raw files to `data/raw/`.<br>1.2 Abort on checksum mismatch. | FR‑001, FR‑002 | — |
| **Phase 2 – Preprocess** | 2.1 `code/data/preprocess.py` reads raw files, parses SMILES with `rdkit.Chem.MolFromSmiles` (logs & drops invalid SMILES – FR‑011).<br>2.2 Computes RDKit descriptors (MW, logP, TPSA, HBA, HBD, rotatable bonds).<br>2.3 Writes **both** `data/processed/processed_data.parquet` and `processed_data.csv` **before** any retention check (satisfies unit test).<br>2.4 Calculates fraction of rows with `mol_valid=True`; if < 95 % → log warning and **exit with non‑zero code after files exist** (FR‑012).<br>2.5 Bias check: compute Pearson |r| between each descriptor and the target. If |r| > 0.6, **exclude** that descriptor from the Random Forest baseline and record `bias_warning=True` in results (FR‑014). | FR‑002, FR‑003, FR‑010, FR‑011, FR‑014 | SC‑005 |
| **Phase 3 – Split** | 3.1 `code/data/split.py` creates stratified train/test splits by `polymer_type` when present; otherwise random split with seed = 42. Writes `train.parquet` and `test.parquet`. | FR‑004 | — |
| **Phase 4 – Model Construction** | 4.1 `models/gnn.py` – 3‑layer MPNN, hidden = 64, global mean pooling, regression head; CPU‑only (`device="cpu"`).<br>4.2 `models/rf.py` – Random Forest on **full descriptor vector** (`n_estimators=200`).<br>4.3 `models/rf_ablation.py` – Random Forest on **graph‑derived statistics only** (isolates topological value). | FR‑005, FR‑006, FR‑013 | — |
| **Phase 5 – Training & Evaluation** | 5.1 `analysis/train.py` – train GNN (max 50 epochs, early stopping patience = 5) and both RF models; serialize models.<br>5.2 **Power analysis**: if a pilot run or literature provides an effect‑size estimate, use it; otherwise assume a conservative small effect (Cohen’s d = 0.3) and document the choice. Record planned N, achieved power, and flag insufficient power (SC‑004).<br>5.3 `analysis/evaluate.py` – compute RMSE, MAE, R² on test set for all three models; store in `results/metrics.json` (validated against `contracts/results.schema.yaml`).<br>5.4 Compute per‑sample absolute errors for GNN and RF baseline.<br>5.5 **Normality test** (Shapiro‑Wilk). If p ≥ 0.05 → paired t‑test; else → Wilcoxon signed‑rank test. Record method, p‑value, decision (SC‑001, SC‑002).<br>5.6 Record runtime and peak memory; abort if > 6 h or > 7 GB (SC‑004). | FR‑006, FR‑007, FR‑012 | SC‑001, SC‑002, SC‑004 |
| **Phase 6 – Interpretability** | 6.1 `analysis/explain.py` – SHAP (KernelSHAP) on the RF baseline and RF‑ablation; output ranked CSV and bar‑chart PNG.<br>6.2 Run GNNExplainer on 100 random test molecules; aggregate masks to a global substructure importance ranking; visualized as heatmaps.<br>6.3 **Overlap‑count metric**: map each top‑5 GNN substructure to the most chemically related descriptor (e.g., aromatic ring → logP). Count overlaps with top‑5 SHAP descriptors; store integer `overlap_top5` and boolean `overlap_meets_threshold` (≥3) in `results/metrics.json` (satisfies SC‑003). | FR‑008, FR‑009 | SC‑003 |
| **Phase 7 – Reporting & Validation** | 7.1 Assemble `results/summary.json` referencing exact files in `data/processed/` and `results/` (single source of truth).<br>7.2 Run full CI (`./run_all.sh`); validate all contracts; ensure deterministic outputs across runs.<br>7.3 Update artifact hashes in the project state file. | FR‑001 – FR‑014 (all) | SC‑001 – SC‑005 |
| **Phase 8 – Cleanup** | 8.1 Delete temporary `interim/` graph serializations (keep provenance logs).<br>8.2 Archive logs under `logs/` for auditability. *(fulfills FR‑014 – Data Hygiene)* | FR‑014 | — |

### Additional Guarantees
- **Deterministic Output**: `numpy.random.seed(42)`, `torch.manual_seed(42)`, `random.seed(42)`.
- **Retention Guard**: Output files are always written; the script exits **after** the files exist if the 95 % threshold is not met, satisfying the unit test.
- **Multiple‑Comparison**: Only a single hypothesis (GNN vs. RF) is tested; no family‑wise correction needed.
- **CPU‑First**: All training uses CPU; no CUDA calls. If a GPU‑only method were ever needed, the plan would explicitly switch to the Kaggle GPU escape hatch (not required here).

---


## projects/PROJ-422-predicting-molecular-permeability-coeffi/specs/001-predicting-molecular-permeability-coeffi/research.md

# Research: Predicting Molecular Permeability Coefficients Using Graph Neural Networks

## 1. Problem Definition
We evaluate whether a graph‑based Message Passing Neural Network (MPNN) can outperform a descriptor‑based Random Forest (RF) in predicting **experimental permeability coefficients** of polymeric membranes. The target must be an independent experimental measurement; **no surrogate target (e.g., logP) is permitted** unless a future spec‑amendment introduces a validated non‑descriptor target. This preserves construct validity and complies with Constitution VII.

## 2. Dataset Strategy

### 2.1 Verified Open Datasets
Only the following open datasets (verified URLs) are available for download via the Hugging Face `datasets` library:

| Dataset | URL | Format | Variables |
|---------|-----|--------|-----------|
| **ChEMBL‑derived RDKit descriptors** | ` | Parquet | `smiles`, `mw`, `logp`, `tpsa`, `hba`, `hbd`, `rotatable_bonds` |
| **Half‑ChEMBL RDKit descriptors** | ` | Parquet | Same as above |
| **SMILES‑Transformers** | ` | Parquet | `smiles` only |
| **SELFormer SMILES** | ` | CSV | `smiles` only |
| **TPSA / GRAPO** | ` | Parquet | `smiles`, `tpsa`, `hba`, `hbd` |
| **RDKit (generic)** | ` | Parquet | `smiles` + a set of RDKit descriptors |

**No verified source contains experimental permeability coefficients.** Consequently, the research pipeline **stops after preprocessing** if no `permeability` column is present, emitting a clear message that FR‑001 cannot be satisfied with current open data. A future spec‑amendment may introduce a suitable target; until then, no modeling or downstream analysis is performed, preserving statistical rigor (Constitution VII).

### 2.2 Target Selection (Current Limitation)
- **If** a dataset with a true `permeability` column is later added, it will be used as the regression target.
- **If** a spec‑amendment introduces a **non‑descriptor** surrogate (e.g., a simulated permeability estimate derived from independent molecular‑simulation studies), that column may be used, but the amendment must be recorded and the target must not be a descriptor already used as a predictor.
- **Otherwise**, the pipeline halts after preprocessing; no model training occurs.

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
- **Random Forest Baseline**: `sklearn.ensemble.RandomForestRegressor`, `n_estimators=200`, `max_features='sqrt'`. Trained on the **full descriptor vector**.  
- **Random Forest Ablation**: Same hyper‑parameters, trained **only** on graph‑derived statistics (no standard descriptors) to isolate topological value (FR‑013).

### 3.3 Training & Evaluation (only when a true `target` is present)
- **Split**: Train / test split (ratio deferred) stratified by `polymer_type` when available; otherwise random with fixed seed `42`.  
- **A‑priori Power Analysis**: If a pilot run or literature provides an effect‑size estimate, we use that; otherwise we adopt a conservative small effect (Cohen’s d = 0.3) and document the choice. The analysis records planned sample size, achieved power, and flags insufficient power (SC‑004).  
- **Metrics**: RMSE, MAE, R² on the held‑out test set.  
- **Statistical Test**:  
  1. Shapiro‑Wilk test on paired error differences.  
  2. If normal (p ≥ 0.05) → paired two‑sample t‑test; else → Wilcoxon signed‑rank test.  
  3. Record method, p‑value, and significance decision (SC‑001, SC‑002).  
- **Effect Size**: Compute Cohen’s d for the paired differences; store in results.  

### 3.4 Interpretability
- **SHAP (RF)**: KernelSHAP on the descriptor baseline (and on the ablation model); mean absolute SHAP values are ranked and plotted.  
- **GNNExplainer**: Run on a representative set of random test molecules; aggregate subgraph masks to a global importance ranking of functional groups/substructures; visualized as heatmaps.  
- **Cross‑Model Comparison**: Compute an **overlap‑count metric**: each top‑5 GNN‑identified substructure is mapped to the most chemically related descriptor (e.g., aromatic ring → logP). The integer count of overlaps with the top‑5 SHAP‑ranked descriptors (`overlap_top5`) and a boolean flag `overlap_meets_threshold` (true if ≥ 3) are stored in `results/metrics.json`, satisfying SC‑003.  

All outputs are saved under `results/interpretability/`.

## 4. Risk & Mitigation Summary
| Risk | Mitigation |
|------|------------|
| No true permeability data | Explicitly halt after preprocessing; no modeling proceeds without a validated target. |
| Small dataset → overfitting | Early stopping, modest hidden size, dropout = 0.1, RF ablation baseline. |
| Invalid SMILES | RDKit parsing guard; log & drop; retention check ensures ≥ 95 % valid molecules (FR‑011). |
| High correlation between descriptors & surrogate target (if ever introduced) | Bias check flags |r| > 0.6 and **excludes** the offending descriptor from the RF baseline; results record the exclusion. |
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
| `permeability` | number / null | **Experimental permeability coefficient** (must be present for modeling) |
| `logp` | number / null | Calculated LogP (descriptor only) |

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
| `target` | number / null | **Experimental permeability coefficient**; rows with `null` are excluded from modeling |
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
 - Write `data/processed/processed_data.parquet` **before** applying the deferred [deferred] retention guard (the guard exits **after** the file exists, satisfying the unit test).
   - Rows with `target` = null are excluded from any later modeling step.  
3. **Split** (`code/data/split.py`): produce `train.parquet` and `test.parquet` under `data/processed/` (only rows with non‑null `target`).  
4. **Model Training** → serialize models under `code/models/`.  
5. **Evaluation** → write `results/metrics.json` (validated against `contracts/results.schema.yaml`).  
6. **Interpretability** → write PNG/HTML under `results/interpretability/`.

## 4. Constraints
- No NaNs in any numeric column of the processed dataset.  
- Graph construction must be a faithful RDKit conversion (Constitution VI).  
- **Target column must be experimental permeability**; surrogate targets are **not allowed** (Constitution VII).  

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
   - Streams the verified datasets from Hugging Face, computes SHA‑256 checksums, parses SMILES, and writes **both** `data/processed/processed_data.parquet` **and** `data/processed/processed_data.csv`.  
   - If the valid‑molecule retention rate falls below 95 %, the script logs a warning and **exits with a non‑zero code after the files are written** (so they are available for inspection).  
   - **If no `permeability` column is found**, the script terminates with an informative message and **does not proceed to training**; a spec‑amendment is required to add a valid target.

2. **Train & Evaluate** *(only runs when a true permeability target is present)*
   ```bash
   # Train all models, perform power analysis, and evaluate
   python code/analysis/train.py --config config.yaml
   ```
   - Handles train/validation split, early stopping, power analysis, and writes `results/metrics.json`.  
   - If the required target column is missing or the power analysis flags insufficient power, the script halts gracefully after reporting the issue.

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

## What Happens When No Permeability Data Is Available?
The preprocessing step will detect the absence of a `permeability` column, emit a clear message, and **stop** the pipeline. No modeling or interpretability analysis is performed, preserving scientific rigor and constitutional compliance. A spec‑amendment can later introduce a validated non‑descriptor target, after which the pipeline can be re‑run.  

---


## projects/PROJ-422-predicting-molecular-permeability-coeffi/specs/001-predicting-molecular-permeability-coeffi/contracts/dataset.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Processed Molecule Dataset"
type: object
properties:
  smiles:
    type: string
    description: "SMILES string of the molecule"
  mol_valid:
    type: boolean
    description: "Whether the SMILES was successfully parsed"
  mw:
    type: number
    description: "Molecular Weight"
  logp:
    type: number
    description: "Calculated LogP"
  tpsa:
    type: number
    description: "Topological Polar Surface Area"
  hba:
    type: integer
    description: "Number of Hydrogen Bond Acceptors"
  hbd:
    type: integer
    description: "Number of Hydrogen Bond Donors"
  rotatable_bonds:
    type: integer
    description: "Number of Rotatable Bonds"
  target:
    type:
      - number
      - "null"
    description: "Experimental permeability coefficient if available; null otherwise"
  polymer_type:
    type:
      - string
      - "null"
    description: "Polymer type for stratification (optional)"
required:
  - smiles
  - mol_valid
  - mw
  - logp
  - tpsa
  - hba
  - hbd
  - rotatable_bonds
  - target
additionalProperties: false


## projects/PROJ-422-predicting-molecular-permeability-coeffi/specs/001-predicting-molecular-permeability-coeffi/contracts/results.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Model Evaluation Results"
type: object
properties:
  gnn_metrics:
    type: object
    properties:
      rmse:
        type: number
      mae:
        type: number
      r2:
        type: number
    required:
      - rmse
      - mae
      - r2
  rf_metrics:
    type: object
    properties:
      rmse:
        type: number
      mae:
        type: number
      r2:
        type: number
    required:
      - rmse
      - mae
      - r2
  rf_ablation_metrics:
    type: object
    properties:
      rmse:
        type: number
      mae:
        type: number
      r2:
        type: number
    required:
      - rmse
      - mae
      - r2
  statistical_test:
    type: object
    properties:
      p_value:
        type: number
      significant:
        type: boolean
      method:
        type: string
        enum: ["paired_t_test", "wilcoxon_signed_rank"]
    required:
      - p_value
      - significant
      - method
  normality_test:
    type: object
    properties:
      method:
        type: string
        enum: ["shapiro_wilk"]
      p_value:
        type: number
      normal:
        type: boolean
    required:
      - method
      - p_value
      - normal
  power_analysis:
    type: object
    properties:
      planned_sample_size:
        type: integer
      achieved_power:
        type: number
      sufficient:
        type: boolean
    required:
      - planned_sample_size
      - achieved_power
      - sufficient
  bias_check:
    type: object
    properties:
      correlation_coefficient:
        type: number
      is_confounded:
        type: boolean
      bias_warning:
        type: boolean
        description: "True if |r| > 0.6, indicating high correlation (expected for proxy target)."
    required:
      - correlation_coefficient
      - is_confounded
      - bias_warning
  interpretability_overlap:
    type: object
    properties:
      overlap_top5:
        type: integer
        description: "Number of overlapping features between GNN substructure mapping and SHAP descriptor ranking (0–5)."
      overlap_meets_threshold:
        type: boolean
        description: "True if overlap_top5 >= 3, satisfying SC‑003."
    required:
      - overlap_top5
      - overlap_meets_threshold
required:
  - gnn_metrics
  - rf_metrics
  - rf_ablation_metrics
  - statistical_test
  - normality_test
  - power_analysis
  - bias_check
  - interpretability_overlap
additionalProperties: false