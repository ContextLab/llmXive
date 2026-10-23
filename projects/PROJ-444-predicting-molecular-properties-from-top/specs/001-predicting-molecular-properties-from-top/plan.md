# Implementation Plan: Predicting Molecular Properties from Topological Data Analysis

**Branch**: `001-predict-molecular-properties-tda` | **Date**: 2026-10-14 | **Spec**: `specs/001-predict-molecular-properties-tda/spec.md`  
**Input**: Feature specification from `specs/001-predict-molecular-properties-tda/spec.md`

## Summary
Implement a reproducible CPU‑only pipeline that (1) downloads the **MoleculeNet Lipophilicity** dataset (contains experimental logP values) – note: a verified download URL is not currently available; the dataset must be obtained from the official MoleculeNet repository, (2) validates SMILES strings and logs exclusions idempotently, (3) builds molecular graphs, (4) computes persistent homology using a shortest‑path distance filtration, (5) vectorizes diagrams into 10×10 persistence images (baseline) with **required `target_property` and `target_value` fields per `feature_matrix.schema.yaml`**, and sweeps 20×20, 30×30 for sensitivity, (6) assembles traditional RDKit descriptors, (7) merges feature sets **after dropping the target column** to avoid circular prediction, (8) trains Linear Regression (L2, α=1.0) and Random Forest (100 trees, max_depth=10) on three feature sets (traditional only, topological only, combined) using 5‑fold scaffold‑based splits (seed = 42), (9) evaluates R² and RMSE per fold, (10) performs paired statistical tests, (11) runs VIF diagnostics **only for the Linear Regression model**, (12) computes mutual information between descriptor sets, (13) extracts and records feature importance for both traditional and topological descriptors (validated against `model_metrics.schema.yaml`), (14) generates a **`model_metrics.json`** file that conforms to `contracts/model_metrics.schema.yaml` with top‑level keys `traditional`, `topological`, `combined`, `feature_importance`, and `metadata` (metadata includes timestamps, git commit hash, random seed, and dataset version), and (15) records resource usage to satisfy SC‑004.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `rdkit`, `gudhi` (CPU wheel), `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `deepchem`, `pytest`
- **Storage**: CSV files under `data/` (raw, processed) and JSON reports under `reports/`
- **Testing**: `pytest` with contract tests (`tests/contract/`) and unit tests (`tests/unit/`)
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU, ~7 GB RAM, no GPU)
- **Constraints**: CPU‑only (FR‑008), reproducibility (Constitution I), data hygiene (III), single source of truth (IV)

## Constitution Check
| Principle | Compliance | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ Pass | Fixed seeds, pinned `requirements.txt`, deterministic data loader from the MoleculeNet Lipophilicity source (must be consistent across runs) |
| II. Verified Accuracy | ✅ Pass | Dataset source is the official MoleculeNet repository; citations will be validated |
| III. Data Hygiene | ✅ Pass | Checksums recorded, raw data immutable, derived files written to new paths, idempotent exclusion log |
| IV. Single Source of Truth | ✅ Pass | Every metric traced to a specific CSV row; no hand‑typed numbers |
| V. Versioning Discipline | ✅ Pass | Artifact hashes stored in `state/projects/PROJ-444...yaml` |
| VI. Molecular Graph Integrity | ✅ Pass | RDKit valence/aromaticity checks; invalid SMILES logged & excluded with idempotent log |
| VII. Topological Feature Validation | ✅ Pass | Shortest‑path filtration, documented grid size, baseline descriptors included, target fields in output |

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
│   ├── 00_checksum_verify.py            # validates checksums; supports SC‑004
│   ├── 01_data_ingestion.py             # downloads Lipophilicity dataset; validates against contracts/dataset.schema.yaml; idempotent exclusion log
│   ├── 02_tda_computation.py            # output validated against contracts/feature_matrix.schema.yaml (includes target_property & target_value)
│   ├── 03_feature_engineering.py        # computes traditional descriptors (FR‑003) & merges with type‑safe molecule_id (string); drops target column before training
│   ├── 04_model_training.py
│   ├── 05_sensitivity_analysis.py
│   ├── 06_diagnostics.py                # VIF only for Linear Regression (FR‑007); MI (FR‑009)
│   ├── 06_feature_importance.py         # extracts importance; output conforms to contracts/model_metrics.schema.yaml
│   ├── 07_resource_monitor.py
│   └── utils/
│       ├── graph_builder.py
│       └── persistence_utils.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── checksums.txt
├── reports/
│   ├── figures/
│   └── metrics/
├── tests/
│   ├── contract/
│   ├── unit/
│   └── integration/
└── state/
    └── projects/PROJ-444...yaml
```

## Complexity Tracking
No violations; the multi‑stage pipeline is necessary to satisfy all FRs/SCs.

## FR/SC Coverage Map
| ID | Plan Phase / Script | Description |
|----|---------------------|-------------|
| **FR-001** | `02_tda_computation.py` | Compute persistent homology via shortest‑path distance filtration (GUDHI). |
| **FR-002** | `02_tda_computation.py` (baseline run) | Vectorize diagrams to 10×10 persistence images **and include `target_property` and `target_value` fields per `feature_matrix.schema.yaml`**; output validated against contract. |
| **FR-003** | `04_model_training.py` & `03_feature_engineering.py` | Train Linear Regression (α=1.0) and Random Forest (100 trees, max_depth=10) on three feature sets; traditional descriptors computed in 03. |
| **FR-004** | `01_data_ingestion.py` | Scaffold‑based 5‑fold split (Bemis‑Murcko), seed = 42; compute R² & RMSE per fold. |
| **FR-005** | `06_diagnostics.py` | Apply Bonferroni (Holm–Bonferroni, α = 0.05) correction to p‑values from model‑comparison tests. |
| **FR-006** | `05_sensitivity_analysis.py` | Sweep grid resolutions `{10, 20, 30}`; report R² variance. |
| **FR-007** | `06_diagnostics.py` | Compute VIF **only for Linear Regression**; flag predictors with VIF > 5. |
| **FR-008** | `04_model_training.py` (runtime guard) | Assert `torch.cuda.is_available()` is False; abort if GPU detected. |
| **FR-009** | `06_diagnostics.py` | Compute mutual information between traditional and topological feature sets. |
| **SC-001** | `04_model_training.py` | Compare combined vs. traditional R²; significance assessed after FR‑009 confirms non‑trivial redundancy. |
| **SC-002** | `05_sensitivity_analysis.py` | Verify stability of R² across resolutions. |
| **SC-003** | `06_diagnostics.py` | Verify family‑wise error rate ≤ 0.05 after Bonferroni (Holm–Bonferroni method, α = 0.05). |
| **SC-004** | `07_resource_monitor.py` & `00_checksum_verify.py` | Log peak RAM & CPU time; must stay < 90 % of CI limits. |
| **SC-005** | `06_diagnostics.py` | Report VIF diagnostics against threshold 5. |
| **SC-006** | `06_feature_importance.py` & `04_model_training.py` | Generate `model_metrics.json` containing `traditional`, `topological`, `combined`, `feature_importance`, and `metadata` sections (metadata includes timestamps, git commit hash, seed, dataset version). |

## Compute Feasibility Strategy
- **Dataset**: MoleculeNet **Lipophilicity** (≈4 000 molecules) – fits comfortably in RAM; downloaded from the official MoleculeNet repository (no verified URL, see plan note).  
- **CPU‑only**: GUDHI and scikit‑learn run on CPU; no CUDA libraries.  
- **Parallelism**: Cross‑validation folds processed sequentially to keep memory < 6 GB.  
- **Time Budget**: Estimated total < 5 h on GitHub Actions free tier; each phase has early‑exit checks (checksum, scaffold count, power analysis) to fail fast if resources insufficient.

## Data Hygiene & Type Safety
- **Lipophilicity Download**: Script `01_data_ingestion.py` downloads from the official MoleculeNet source, validates the CSV against `contracts/dataset.schema.yaml` (ensuring `smiles` and `logP` columns exist), and aborts with **Data Gap** error if missing.  
- **Exclusion Log**: Idempotent append logic (check checksum before appending) prevents duplicate entries of invalid SMILES.  
- **Type Consistency**: All `molecule_id` columns across CSVs are cast to **string** before any merge operation to prevent int64/object type errors.  
- **Target Handling**: After merging traditional and topological descriptors, the `target` column (`logP`) is **dropped** from the predictor matrix before model training to avoid circular prediction.  
- **Checksums**: Every raw and processed file is checksummed and recorded in `data/checksums.txt` before downstream tasks begin.

## Risk Mitigation
- Invalid SMILES → logged & excluded with idempotent append (VI).  
- Empty persistence diagrams → zero‑vector fallback.  
- Dataset mismatch → ingestion script validates required columns (`smiles`, `logP`) and aborts with **Data Gap** if absent.  
- GPU detection → explicit abort (FR‑008).  
- Type merge errors → enforce `molecule_id` as string consistently across all CSVs before merge.  
- Duplicate log entries → idempotent append logic guarded by checksum file.  
- Contract violations → `02_tda_computation.py` output validated against `feature_matrix.schema.yaml` (includes `target_property` & `target_value`); `06_feature_importance.py` output validated against `model_metrics.schema.yaml`.  

---

