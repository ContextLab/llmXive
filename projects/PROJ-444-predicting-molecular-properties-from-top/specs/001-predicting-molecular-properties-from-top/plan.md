# Implementation Plan: Predicting Molecular Properties from Topological Data Analysis

**Branch**: `001-predict-molecular-properties-tda` | **Date**: 2026-10-24 | **Spec**: `specs/001-predict-molecular-properties-tda/spec.md`  
**Input**: Feature specification from `specs/001-predict-molecular-properties-tda/spec.md`

## Summary
Implement a fully reproducible, CPU‑only pipeline that (1) streams the open **PubChem 10 M canonicalized** dataset from Hugging Face, (2) extracts valid SMILES and the XLogP3 property (renamed to `logP`), (3) validates each SMILES with RDKit, (4) builds molecular graphs and computes persistent homology using a shortest‑path distance filtration, (5) vectorizes diagrams into 10 × 10 persistence images (baseline) and sweeps 20 × 20 and 30 × 30 for sensitivity, (6) computes traditional RDKit descriptors, (7) merges feature sets (ensuring `molecule_id` is a string and dropping the target column before training), (8) trains Linear Regression (L2, α = 1.0) and Random Forest (100 trees, max_depth = 10) on three feature sets using **5 repeats of 10‑fold** scaffold‑based splits (seed = 42), (9) evaluates R² and RMSE per fold, (10) performs paired statistical tests on **RMSE** differences with Wilcoxon signed‑rank test and applies **Holm–Bonferroni** correction (α = 0.05), (11) runs VIF diagnostics (flag VIF > 5) for the Linear Regression model, (12) calculates mutual information between traditional and topological descriptor matrices, (13) extracts feature importance, (14) records all metrics in `model_metrics.json` conforming to the contract schema, (15) validates all generated CSVs against their respective JSON schemas, and (16) logs resource usage to satisfy SC‑004.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `rdkit`, `gudhi`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `datasets` (🤗 datasets), `tqdm`, `joblib`  
- **Storage**: CSV/Parquet files under `data/` (raw, processed) and JSON reports under `reports/`  
- **Testing**: `pytest` with contract tests (`tests/contract/`) and unit tests (`tests/unit/`)  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU, ~7 GB RAM, no GPU)  
- **Constraints**: CPU‑only (FR‑008), reproducibility, data‑hygiene, single source of truth (Constitution)  

## Constitution Check
| Principle | Compliance | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ | Fixed seeds, deterministic streaming loader, pinned `requirements.txt`. |
| II. Verified Accuracy | ✅ | Dataset sourced from Hugging Face URL (verified). |
| III. Data Hygiene | ✅ | Checksums recorded, immutable raw files, derived files written to new paths, idempotent exclusion log. |
| IV. Single Source of Truth | ✅ | Every metric traced to a specific row in `data/processed/*.csv`. |
| V. Versioning Discipline | ✅ | Artifact hashes stored in `state/projects/PROJ-444...yaml`. |
| VI. Molecular Graph Integrity | ✅ | RDKit valence/aromaticity checks; invalid SMILES logged & excluded. |
| VII. Topological Feature Validation | ✅ | Shortest‑path filtration, documented grid sizes, baseline 10 × 10 persistence images, inclusion of `target_property`/`target_value`. |

## Project Structure
```text
specs/001-predict-molecular-properties-tda/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── feature_matrix.schema.yaml
│   └── model_metrics.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
projects/PROJ-444-predicting-molecular-properties-from-top/
├── code/
│   ├── requirements.txt
│   ├── 00_checksum_verify.py            # verifies SHA‑256 checksums of raw/processed files
│   ├── 01_download_pubchem.py            # streams Hugging Face PubChem dataset, shuffles with seed=42, then **randomly samples** N=5000 valid molecules
│   ├── 02_tda_computation.py            # shortest‑path filtration → persistence images (grid sizes 10/20/30)
│   ├── 03_feature_engineering.py        # RDKit traditional descriptors, merges with topological vectors
│   ├── 04_model_training.py
│   ├── 05_sensitivity_analysis.py
│   ├── 06_diagnostics.py                # VIF (Linear Regression), MI, Holm–Bonferroni correction
│   ├── 07_feature_importance.py
│   ├── 08_resource_monitor.py
│   └── utils/
│       ├── graph_builder.py
│       └── persistence_utils.py
├── data/
│   ├── raw/
│   │   └── pubchem.parquet               # streamed, not fully materialized
│   ├── processed/
│   │   ├── molecules.csv                 # validated SMILES + logP
│   │   ├── topological_features_10.csv
│   │   ├── topological_features_20.csv
│   │   ├── topological_features_30.csv
│   │   ├── traditional_descriptors.csv
│   │   └── combined_features.csv
│   └── checksums.txt
├── reports/
│   ├── figures/
│   └── metrics/
│       ├── model_metrics.json
│       ├── feature_importance.json
│       ├── vif_report.json
│       ├── mi_report.json
│       ├── sensitivity_report.json
│       └── resource_usage.json
├── tests/
│   ├── contract/
│   ├── unit/
│   └── integration/
└── state/
    └── projects/PROJ-444...yaml
```

## Complexity Tracking
No violations; the multi‑stage pipeline is required to satisfy every FR and SC.

## FR/SC Coverage Map
| ID | Plan Phase / Script | Description |
|----|---------------------|-------------|
| **FR-001** | `02_tda_computation.py` | Compute persistent homology via shortest‑path distance filtration (GUDHI). |
| **FR-002** | `02_tda_computation.py` (baseline) | Vectorize diagrams to 10 × 10 persistence images; also produce 20 × 20 and 30 × 30 for sensitivity. |
| **FR-003** | `04_model_training.py` & `03_feature_engineering.py` | Train Linear Regression (α = 1.0) and Random Forest (100 trees, max_depth = 10) on three feature sets; traditional descriptors computed in `03`. |
| **FR-004** | `01_download_pubchem.py` + `04_model_training.py` | **5 repeats of 10‑fold** scaffold‑based splits (Bemis‑Murcko, seed = 42); compute R² & RMSE per fold. |
| **FR-005** | `06_diagnostics.py` | Apply **Holm–Bonferroni** correction (α = 0.05) to p‑values from model‑comparison tests. |
| **FR-006** | `05_sensitivity_analysis.py` | Sweep grid resolutions `{10,20,30}`; report R² variance and **assert that σ < 0.02** to satisfy SC‑002. |
| **FR-007** | `06_diagnostics.py` | Compute VIF for Linear Regression; flag predictors with VIF > 5. |
| **FR-008** | `04_model_training.py` (runtime guard) | Assert `torch.cuda.is_available()` is False; abort if GPU detected. |
| **FR-009** | `06_diagnostics.py` | Compute mutual information between traditional and topological descriptor matrices. |
| **SC-001** | `04_model_training.py` | Compare combined vs. traditional RMSE; significance assessed after FR‑009 confirms non‑trivial redundancy. |
| **SC-002** | `05_sensitivity_analysis.py` | Verify stability of R² across resolutions (σ < 0.02). |
| **SC-003** | `06_diagnostics.py` | Verify family‑wise error rate ≤ 0.05 after Holm–Bonferroni correction. |
| **SC-004** | `08_resource_monitor.py` & `00_checksum_verify.py` | Log peak RAM & CPU time; must stay < 90 % of CI limits. |
| **SC-005** | `06_diagnostics.py` | Report VIF diagnostics against threshold 5. |
| **SC-006** | `07_feature_importance.py` | Generate `model_metrics.json` with `traditional`, `topological`, `combined`, `feature_importance`, and `metadata`. |

## Compute Feasibility Strategy
- **Dataset**: Hugging Face `sagawa/pubchem-10m-canonicalized` (≈10 M rows). We **stream** the dataset (`datasets.load_dataset(..., streaming=True)`) and **shuffle** the stream using a fixed seed (`42`). After shuffling we **randomly sample** the first **5 000** valid molecules. This unbiased sampling avoids systematic bias from taking the first N records.
- **CPU‑only**: GUDHI and scikit‑learn run on CPU; no CUDA libraries.  
- **Parallelism**: Cross‑validation folds processed sequentially; topological computation parallelized over molecules using `joblib` with `n_jobs=2` (max 2 cores).  
- **Time Budget**: Estimated total < 5 h on GitHub Actions free tier; each phase includes early‑exit checks (checksum, column presence, power analysis) to fail fast if resources insufficient.
- **Contract Validation**:  
  1. After `01_download_pubchem.py`, run `pytest tests/contract/test_dataset_schema.py` to validate `molecules.csv` against `contracts/dataset.schema.yaml`.  
  2. After each `02_tda_computation.py` run (grid 10, 20, 30), run `pytest tests/contract/test_feature_matrix_schema.py --grid <size>` to validate the corresponding CSV against `contracts/feature_matrix.schema.yaml`.  
  3. After feature merging, run a contract test for the combined matrix (same schema).  
- **Sensitivity Check**: `05_sensitivity_analysis.py` records the standard deviation of R² across the three grid resolutions and **asserts σ < 0.02**; failure aborts the pipeline.

## Data Hygiene & Type Safety
- **Checksum**: `00_checksum_verify.py` computes SHA‑256 of every raw and processed file; mismatches abort the run (ensuring SC‑004).  
- **Exclusion Log**: Idempotent CSV (`data/processed/exclusions.csv`) records `molecule_id` and `exclusion_reason` for every invalid SMILES; duplicates prevented via checksum guard.  
- **String IDs**: All `molecule_id` fields are cast to string before any merge to avoid type‑mix errors.  
- **Target Handling**: After merging, the `logP` column is removed from the predictor matrix before model fitting (preventing circular prediction).  
- **Zero‑Vector Fallback**: If a persistence diagram is empty, the script inserts a zero‑filled 10 × 10 vector.

## Risk Mitigation
- Invalid SMILES → logged & excluded (VI).  
- Empty persistence diagrams → zero‑vector fallback.  
- Missing required columns (`canonical_smiles`, `XLogP3`) → `Data Gap` error abort.  
- GPU detection → explicit abort (FR‑008).  
- Duplicate exclusion entries → idempotent logging guarded by checksum file.  
- Contract violations → each output file validated against its JSON schema after creation.  

---



