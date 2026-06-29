# Implementation Plan: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

**Branch**: `PROJ-511-predicting-molecular-packing-efficiency` | **Date**: 2026-06-29 | **Spec**: [spec.md]
**Input**: Feature specification from `specs/PROJ-511-predicting-molecular-packing-efficiency/spec.md`

## Summary
Create a reproducible CPU‑only pipeline that (1) downloads organic CIF entries from the Crystallography Open Database (COD) using a **verified URL** (`), (2) extracts or generates canonical SMILES, (3) computes raw packing coefficient and composition‑adjusted packing efficiency (CAPE) together with **molecule‑level** 3‑D geometry descriptors (radius of gyration, asphericity, principal moments of inertia) derived from RDKit‑generated conformers, (4) encodes SMILES with a frozen pre‑trained SMILES‑Transformer (`seyonec/PubChem10M_SMILES_BPE_60k` on HuggingFace) **and** augments this representation with the three 3‑D descriptors **and** the three confounder variables (lattice system, temperature, solvent flag). **Atom‑type count features are *not* used as primary predictors**; they are retained solely for partial‑correlation control (see FR‑014). (5) trains a lightweight 2‑layer MLP regression model (< 100 k trainable parameters) on the combined fingerprint + 3‑D + confounder vector, (6) evaluates the model with MAE, Pearson r, Spearman ρ, Shapiro‑Wilk, and a 10 000‑shuffle permutation test, (7) performs VIF diagnostics **only on the PCA‑reduced fingerprint components (10 PCs) plus the low‑dimensional descriptors and confounders** (FR‑009), (8) conducts a partial‑correlation analysis controlling for atom‑type composition (FR‑014), (9) runs a sensitivity analysis that sweeps the high‑packing threshold over {0.5, 0.6, 0.7) with Bonferroni correction (FR‑007, FR‑008), (10) runs an **ablation study** (training without the 3‑D descriptors) to assess possible circularity, and (11) generates a fully reproducible HTML report validated against `contracts/validation_report.schema.yaml`.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `rdkit`, `torch==2.3.0+cpu`, `torchvision`, `scikit-learn`, `pandas`, `numpy`, `requests`, `tqdm`, `jinja2`, `statsmodels`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `jsonschema`
- **Storage**: CSV files under `data/` and model checkpoint under `models/`
- **Testing**: `pytest`, `jsonschema` validation of artifacts
- **Target Platform**: Linux (GitHub Actions runner)
- **Constraints**: CPU‑only, ≤ 2 CPU cores, ≤ 7 GB RAM, ≤ 6 h total runtime, no GPU libraries, model size < 200 MB in memory.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are fixed; data download URLs are hard‑coded; the pipeline is fully scriptable. |
| II. Verified Accuracy | COD URL (`) and Bondi radii citation are recorded (FR‑017, FR‑018). SMILES‑Transformer source (`) is cited. |
| III. Data Hygiene | Checksums recorded for raw CIF archive and derived CSV; no in‑place mutation. |
| IV. Single Source of Truth | Every figure/table in `report.html` references a single row in `data/dataset.csv`. |
| V. Versioning Discipline | All artifacts (`dataset.csv`, `model.pt`, `report.html`) are hashed and logged. |
| VI. Open Crystallographic Data Integrity | Each record stores the COD entry identifier; provenance retained. |
| VII. Model Transparency and Statistical Validation | Frozen transformer checkpoint and MLP architecture are committed; permutation test executed and logged. |

## Project Structure
```
specs/PROJ-511-predicting-molecular-packing-efficiency/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
 ├── dataset.schema.yaml
 ├── model.schema.yaml
 └── validation_report.schema.yaml

code/
├── download_cif.py
├── parse_cif.py
├── compute_features.py
├── validate_dataset.py # NEW: schema validation step
├── train_mlp.py
├── evaluate.py
├── sensitivity.py
├── ablation.py # NEW: train without 3‑D descriptors
├── generate_report.py
└── utils.py

data/
├── raw_cif/ # downloaded CIF archive (unchanged)
├── dataset_raw.csv
├── dataset.csv
├── checksums.txt
└──...

models/
└── mlp_regressor.pt

results/
├── validation_report.json
└── report.html
```

## Phase Mapping (FR → Plan Phase / Script)
| FR | Plan Phase / Script |
|----|----------------------|
| FR‑001 | `download_cif.py` (download & filter ≤ 50 non‑H atoms) |
| FR‑002 | `parse_cif.py` (extract/generate SMILES, flag source) |
| FR‑003 | `compute_features.py` (raw packing coefficient) |
| FR‑004 | `compute_features.py` (SMILES‑Transformer encoding **plus** 3‑D descriptors) |
| FR‑005 | `train_mlp.py` (2‑layer MLP, ≤ 100 k params, 80/20 split) |
| FR‑006 | `evaluate.py` (MAE, Pearson r, Spearman ρ, Shapiro‑Wilk, permutation test) |
| FR‑007 | `sensitivity.py` (threshold sweep) |
| FR‑008 | `sensitivity.py` (Bonferroni correction) |
| FR‑009 | `evaluate.py` (VIF on PCA‑reduced fingerprint + low‑dim descriptors + confounders) |
| FR‑010 | `generate_report.py` (HTML report, schema validation) |
| FR‑011 | `compute_features.py` (CAPE calculation) |
| FR‑012 | `compute_features.py` (radius of gyration, asphericity, principal moments) |
| FR‑013 | `parse_cif.py` (record lattice system, temperature, solvent flag) *and* these confounders are **included** in the MLP feature vector (see Feature Construction) |
| FR‑014 | `evaluate.py` (partial‑correlation controlling for atom‑type counts) |
| FR‑015 | `evaluate.py` (Spearman ρ & Shapiro‑Wilk) |
| FR‑016 | `evaluate.py` (10 000 shuffles) |
| FR‑017 | `download_cif.py` (record COD URL and version) |
| FR‑018 | `compute_features.py` (Bondi radii table embedded) |
| FR‑019 | `contracts/` schemas referenced in `generate_report.py` |
| **New** | `validate_dataset.py` (validate `dataset.csv` against `contracts/dataset.schema.yaml`) |

## Success‑Criteria Mapping (SC → Verification)
| SC | Verification Method |
|----|----------------------|
| SC‑001 | `len(dataset.csv) ≥ 500` and no missing SMILES/PC values (checked after `validate_dataset.py`). |
| SC‑002 | Pearson r ≥ 0.4 and Bonferroni‑corrected permutation p ≤ 0.05 reported in `validation_report.json`. |
| SC‑003 | If r < 0.2, permutation p ≥ 0.05 (reported). |
| SC‑004 | Pearson r variation across thresholds ≤ ±0.05 (reported). |
| SC‑005 | Total runtime logged by CI; must be ≤ 6 h (checked in CI logs). |

## Complexity Tracking
No constitution violations identified; the plan respects all constraints and addresses all reviewer concerns.

## Execution Order
1. **Data Acquisition** – `download_cif.py` → raw CIF archive.
2. **Parsing & SMILES** – `parse_cif.py` → `dataset_raw.csv`.
3. **Feature Computation** – `compute_features.py` → `dataset.csv` (adds PC, CAPE, 3‑D descriptors, confounders, atom‑type counts).
4. **Dataset Validation** – `validate_dataset.py` → ensures compliance with `contracts/dataset.schema.yaml`.
5. **Model Training** – `train_mlp.py` → `models/mlp_regressor.pt`.
6. **Model Evaluation** – `evaluate.py` → `results/validation_report.json`.
7. **Ablation Study** – `ablation.py` (train without 3‑D descriptors; results appended to report).
8. **Sensitivity & Bonferroni** – `sensitivity.py` → extended section in `validation_report.json`.
9. **Report Generation** – `generate_report.py` → `results/report.html` (validated against `contracts/validation_report.schema.yaml`).

---

