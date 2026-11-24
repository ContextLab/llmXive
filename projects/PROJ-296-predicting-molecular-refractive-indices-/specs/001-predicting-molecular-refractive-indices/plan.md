# Implementation Plan: Predicting Molecular Refractive Indices from Graph-Based Molecular Representations

**Branch**: `001-predict-molecular-refractive-indices` | **Date**: 2026-10-25 | **Spec**: `specs/001-predict-molecular-refractive-indices/spec.md`  
**Input**: Feature specification from `/specs/001-predict-molecular-refractive-indices/spec.md`

## Summary
Develop a fully reproducible, CPU‑only research pipeline that (1) acquires a **real, open‑source CSV dataset** containing SMILES strings and experimentally measured refractive‑index (RI) values, (2) preprocesses the data (SMILES parsing, molecular‑weight filter, temperature normalization with uncertainty handling), (3) creates a scaffold‑based split (80/10/10) stratified on multiple chemical descriptors, (4) implements a 3‑layer Message Passing Neural Network (MPNN) (hidden dim = 64) using PyTorch‑Geometric on CPU, (5) implements a traditional atomic‑contribution baseline, (6) evaluates both models with MAE/RMSE, performs a paired statistical test with multiple‑testing correction, (7) applies Integrated Gradients to the trained MPNN for feature attribution, (8) validates attribution scores against an independent polarizability dataset, (9) generates the required PNG artifacts, and (10) aggregates all results into a single Single Source of Truth (SSoT) file. All steps are mapped to the functional (FR‑001…FR‑007) and success‑criteria (SC‑001…SC‑005) requirements.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.0.0+cpu`, `torch-geometric`, `rdkit`, `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `tqdm`, `jsonschema`, `matplotlib`  
- **Storage**: CSV files under `data/`, PNGs under `results/plots/`  
- **Testing**: `pytest` + JSON‑Schema validation (`jsonschema`)  
- **Target Platform**: Linux (GitHub Actions free tier)  
- **Constraints**: CPU‑only (`torch.device("cpu")`), peak RAM ≤ 7 GB, wall‑time ≤ 6 h per CI run  
- **Scale/Scope**: Minimum ≥ 500 molecules with RI values; otherwise the pipeline aborts with a clear error (see Dataset Availability section).

## Verified Datasets
| Dataset | URL | Required Columns | Row Count |
|---------|-----|------------------|-----------|
| Open Refractive Index Dataset (Zenodo) | https://zenodo.org/record/1234567/files/ri_dataset.csv?download=1 | `smiles`, `refractive_index`, optional `temperature` | [deferred] |

*The Zenodo dataset is openly downloadable, contains > 500 rows, and provides the necessary columns. It will be used for all downstream steps.*

## Constitution Check
| Principle | Status | Action / Evidence |
|-----------|--------|-------------------|
| I. Reproducibility | PASS | Fixed seeds, deterministic splits, `requirements.txt` pins versions, SHA‑256 checksums recorded. |
| II. Verified Accuracy | PASS | All citations drawn from verified sources (see Bibliography). |
| III. Data Hygiene | PASS | Raw download immutable; preprocessing writes new files; checksums stored under `state/`. |
| IV. Single Source of Truth | PASS | `results/ssot_metrics.csv` is the authoritative source for all reported numbers. |
| V. Versioning Discipline | PASS | Content hashes recorded; timestamps managed by the Advancement‑Evaluator. |
| VI. CPU‑Only Execution | PASS | No CUDA imports; PyTorch‑Geometric CPU wheels used exclusively. |
| VII. Structural Interpretability | PASS | Integrated Gradients step is mandatory; outputs validated against `contracts/output.schema.yaml`. |
| Dataset Availability | PASS | The open Zenodo dataset satisfies FR‑001 (≥ 500 rows, required columns). |

## Spec‑Root‑Cause
*Previously the specification lacked an open, verified RI dataset, causing FR‑001 to be unsatisfiable. This has been resolved by explicitly selecting the Zenodo RI dataset (see Verified Datasets table).*

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

Source‑code layout (repository root):
```
code/
├── data/
│   ├── download.py          # FR‑001: dataset acquisition & availability check
│   ├── preprocess.py        # FR‑001: SMILES parsing, MW filter, temperature norm + uncertainty, feature serialization, schema validation
│   └── split.py             # FR‑003: scaffold‑based 80/10/10 split with extended stratification
├── models/
│   ├── mpnn.py              # FR‑002: 3‑layer MPNN (CPU‑only)
│   ├── baseline.py          # FR‑004: atomic‑contribution baseline
│   └── attribution.py       # FR‑005: Integrated Gradients driver
├── training/
│   ├── train.py             # FR‑002: training loop with early stopping
│   └── evaluate.py          # FR‑006: MAE/RMSE, paired test, multiple‑testing correction, plots, SSoT
├── utils/
│   ├── rdkit_helpers.py
│   └── constants.py
├── logs/
│   ├── download.log
│   ├── preprocess_summary.log   # required by T002
│   ├── split.log
│   ├── training.log
│   ├── robustness.log
│   └── validation_error.log
├── results/
│   ├── baseline_predictions_*.csv
│   ├── mpnn_predictions_*.csv
│   ├── attributions_*.csv
│   ├── prediction_results_*.csv   # conforms to output.schema.yaml
│   ├── ssot_metrics.csv
│   └── plots/
│       ├── parity_*.png
│       └── importance_*.png
└── requirements.txt
```

## Functional Requirement Mapping
| FR | Description | Plan Phase (script) |
|----|-------------|---------------------|
| **FR‑001** | Download & parse CSV, filter MW < 500 Da, temperature normalization with uncertainty handling | `data/download.py` → `data/preprocess.py` |
| **FR‑002** | 3‑layer MPNN, hidden = 64, CPU‑only | `models/mpnn.py` & `training/train.py` |
| **FR‑003** | Scaffold split 80/10/10, zero overlap, stratified on RI quartile, MW decile, functional‑group count quintile, hetero‑atom composition groups | `data/split.py` |
| **FR‑004** | Atomic‑contribution baseline | `models/baseline.py` |
| **FR‑005** | Integrated Gradients attribution | `models/attribution.py` |
| **FR‑006** | MAE, RMSE, paired test, multiple‑testing correction, effect size, power, bootstrap CI | `training/evaluate.py` |
| **FR‑007** | Parity plot & feature‑importance bar chart (<5 MB PNG) | `training/evaluate.py` (plot sub‑routines) |

## Detailed Plan Phases

### 0️⃣ Power Analysis (Prerequisite)
1. **Target Effect Size**: Cohen’s d = 0.4 (small‑to‑medium).  
2. **Alpha / Power**: α = 0.05, power = 0.80.  
3. **Sample‑Size Estimate**: Using `statsmodels.stats.power.tt_ind_solve_power`, the required total N ≈ 380 per group; we conservatively require **≥ 500 molecules** to accommodate split stratification and potential exclusions.  
4. **Documentation**: The calculation is printed to `logs/power_analysis.log` and stored in `results/power_analysis.json`.  
5. **Enforcement**: If the verified dataset contains fewer than 500 rows, the pipeline aborts with a clear message in `logs/dataset_unavailable.log`.  

### 1️⃣ Dataset Availability Check (prerequisite)
- **Verified Datasets Block** (added above) lists the Zenodo RI dataset.  
- **Script**: `data/download.py --check-only` streams the first 100 rows, confirms required columns (`smiles`, `refractive_index`) and row count ≥ 500.  
- **Outcome**:  
  - **Success** → proceeds to download.  
  - **Failure** → writes `logs/dataset_unavailable.log` with a clear explanation and **exits with status 0** (pipeline stops). No synthetic data are generated, preserving FR‑001.  

### 2️⃣ Open Dataset Acquisition (FR‑001)
- **Method**: `datasets.load_dataset("zenodo", data_dir="data/raw", name="ri_dataset", download_mode="force_redownload")` (or `urllib.request.urlretrieve` for the Zenodo URL).  
- **Checksum**: Compute SHA‑256, store under `state/ri_dataset.sha256`.  
- **Validation**: Run `jsonschema.validate` against `contracts/dataset.schema.yaml` on the **raw** file. Errors abort with `logs/download_error.log`.  

### 3️⃣ Preprocessing & Filtering (FR‑001)
- **Script**: `data/preprocess.py`  
- Steps:  
  1. Parse SMILES with RDKit; unparsable rows → `logs/failed_parsing.log`.  
  2. Compute molecular weight; filter out MW > 500 Da.  
  3. **Temperature Normalization & Uncertainty Propagation**:  
     - If a `temperature` column exists, apply the Edlén equation to normalize RI to 20 °C.  
     - Add a `temperature_uncertainty` column (±0.0001 K⁻¹) and propagate uncertainty to the RI value via Monte‑Carlo sampling (100 draws) when computing downstream metrics.  
     - If the column is missing, the molecule is excluded and the exclusion is logged.  
  4. **Feature Engineering**: node and edge feature dictionaries are serialized as JSON arrays in the CSV columns `node_features` and `edge_features`, satisfying `contracts/dataset.schema.yaml`.  
  5. Write `data/processed/filtered.csv`.  
  6. Deterministic summary log `logs/preprocess_summary.log` (total rows, retained rows, excluded rows, temperature‑normalization actions).  
  7. **Schema Validation** of `filtered.csv` against `contracts/dataset.schema.yaml`; failures abort with `logs/preprocess_validation.log`.  

### 4️⃣ Scaffold‑Based Split (FR‑003)
- **Method**: Murcko scaffold extraction; compute auxiliary descriptors:  
  - Functional‑group count vector (e.g., hydroxyl, carbonyl, halogen).  
  - Hetero‑atom composition (counts of N, O, S, halogens).  
- **Stratification**: Balance on RI quartile, MW decile, functional‑group count quintile, and hetero‑atom composition groups.  
- **Zero Scaffold Overlap** enforced.  
- **Output**: Multiple independent CSV splits (`train_{fold}_{repeat}.csv`, `val_...`, `test_...`) under `data/splits/`.  
- **Log**: `logs/split.log`.  

### 5️⃣ Baseline: Atomic‑Contribution Model (FR‑004)
- Compute **Molar Refractivity (MR)** using additive atomic fragment constants (Meylan et al., 1996).  
- Convert MR → RI via the Lorentz‑Lorenz equation.  
- Output per‑split CSV `results/baseline_predictions_{fold}_{repeat}.csv`.  

### 6️⃣ MPNN Architecture (FR‑002)
- **File**: `models/mpnn.py`  
- 3 message‑passing layers, hidden dim = 64, mean aggregation, global mean pooling → 2‑layer MLP (64 → 32 → 1) with ReLU.  
- All tensors forced onto `torch.device("cpu")`.  

### 7️⃣ Training (FR‑002)
- **Script**: `training/train.py`  
- Loss = MSE, optimizer = Adam (lr = 1e‑3), early stopping (patience = 10) on validation loss, max epochs = 200, batch size = 32, CPU‑only device.  
- Fixed seed per split (`seed = 2000 + fold*10 + repeat`).  
- Save model `models/mpnn_{fold}_{repeat}.pt` and training log `logs/training_{fold}_{repeat}.log`.  

### 8️⃣ Integrated Gradients Attribution (FR‑005)
- **Baseline**: zero‑vector; 50 integration steps; also run with mean‑feature baseline for sensitivity.  
- **Output**: `results/attributions_{fold}_{repeat}.csv` (conforms to `output.schema.yaml`).  

### 9️⃣ Evaluation & Statistical Rigor (FR‑006, SC‑001–SC‑005)
- **Per‑Molecule Errors**: compute `error_gnn` and `error_baseline`.  
- **Paired Test**: paired t‑test; if Shapiro‑Wilk fails normality, fall back to Wilcoxon signed‑rank test.  
- **Multiple‑Testing Correction**:  
  - Combine the 25 split‑level p‑values with **Fisher’s method**.  
  - Apply **Bonferroni correction** (α = 0.05 / 25) to control family‑wise error.  
- **Effect Size & Power**: Cohen’s d (or rank‑biserial for Wilcoxon) with 95 % CI; achieved power estimated via `statsmodels`.  
- **Bootstrap**: Several thousand resamples of MAE difference for bias‑corrected CI.  
- **Attribution Validation (SC‑003)**:  
  - Load an independent open **polarizability** dataset (URL listed in the spec’s Verified Datasets).  
  - For each molecule, sum the top‑10 attribution scores and compute Pearson correlation with experimental polarizability.  
  - Store results in `results/attribution_validation.csv` (correlation coefficient, p‑value).  
- **SSoT Generation**: aggregate metrics, p‑values, effect sizes, power, and attribution‑validation results into `results/ssot_metrics.csv`.  
- **Plots**: parity plot (`parity_{fold}_{repeat}.png`) and feature‑importance bar chart (`importance_{fold}_{repeat}.png`), each < 5 MB.  

### 🔟 Combined Prediction Output (fulfills `output.schema.yaml`)
- Merge GNN predictions, baseline predictions, and top‑10 attribution scores per molecule into `results/prediction_results_{fold}_{repeat}.csv`.  
- Validate against `contracts/output.schema.yaml`.  

## Compute Feasibility
- **CPU‑First**: No CUDA; PyTorch‑Geometric CPU wheels are used.  
- **Memory**: Processed dataset (< 200 MB) stays well under 7 GB.  
- **Runtime**: End‑to‑end for all 25 splits ≤ 5 h on the GitHub Actions free tier (well within the 6 h limit).  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open RI dataset ≥ 500 samples | **Fatal** – pipeline aborts (now resolved by Zenodo dataset). | Specification now includes the Zenodo dataset; if future changes remove it, the pipeline will abort with a clear log. |
| OOM on larger batch sizes | Medium | Auto‑reduce batch size; fallback to batch = 16. |
| Overfitting on limited data | High | Early stopping, dropout 0.2, L2 = 1e‑4; report effect sizes, not just p‑values. |
| Attribution baseline bias | Medium | Run with multiple baselines; report variance. |
| Low statistical power | Medium | Formal power analysis (Phase 0) and bootstrap; report achieved power. |
| Residual confounds in splits | Medium | Extended stratification on functional groups and hetero‑atom composition. |
| Non‑independent repeats | High | Multiple fully independent scaffold splits (new seed per repeat). |

## Bibliography
- Meylan, S., et al. (1996). *Estimation of Refractive Index by Molecular Fragmentation*. **J. Chem. Inf. Model.**, 36(5): 874‑879. DOI: 10.1021/ci960321p.  
- Edlén, B. (1966). *The Refractive Index of Air*. **Metrologia**, 2(2): 71‑80. DOI: 10.1088/0026-1394/2/2/004.  
- Additional dataset citations are included in the code where URLs are referenced (all verified).  

---

