# Implementation Plan: Predicting Molecular Polarity from SMILES Strings with Machine Learning

**Branch**: `001-predict-molecular-polarity` | **Date**: 2026-10-19 | **Spec**: `specs/001-predict-molecular-polarity/spec.md`  
**Input**: Feature specification from `/specs/001-predict-molecular-polarity/spec.md`

## Summary
The plan delivers a fully reproducible, CPU‑only research pipeline that:

1. **Downloads** the open QM9 dataset (130 831 molecules) via `qm9pack`.  
2. **Generates** ≥ 200 2‑D topological descriptors per molecule using RDKit, explicitly **excluding** any 3‑D conformer generation, TPSA‑related descriptors, and SMARTS‑based functional‑group counts (FR‑001, FR‑006).  
3. **Handles** malformed SMILES, undefined stereochemistry, NaNs, and highly flexible molecules (FR‑008, FR‑009).  
4. **Mitigates collinearity** with iterative VIF pruning (threshold 5.0). **Fallback**: If pruning would leave **fewer than 150** descriptors, the pipeline switches to an L1‑regularized LightGBM model (instead of further pruning), preserving the ≥ 150 descriptor requirement (FR‑007).  
5. **Trains** a LightGBM gradient‑boosting regressor on the 2‑D matrix using a random train/test split, k‑fold CV, and hyper‑parameter logging (FR‑002, FR‑003).  
6. **Evaluates** model performance (R², RMSE) against a null‑mean baseline (SC‑001).  
7. **Applies** SHAP (with interaction values) to obtain feature importance and runs **100 bootstrap resamples** (a subsample of ~10 k per resample) to compute Jaccard similarity of the top‑10 SHAP features across resamples (target ≥ 0.7, SC‑003).  
8. **Validates** the stability of the top‑10 SHAP features by training **single‑feature LightGBM** models and recording per‑feature R² (must be ≥ 0.02, SC‑009).  
9. **Produces** contracts‑validated artifacts (schemas, checksum manifests) and a reproducibility verification step (SC‑005).  

> **Note on FR‑010 / FR‑011** – These functional requirements request a 3‑D baseline model. They directly conflict with **Constitution Principle VI** (“All predictive models MUST rely exclusively on 2D descriptors”). Consequently, they are **out of scope** under the current constitution. The spec should be revised if a 3‑D comparison is required; otherwise the project proceeds with the 2‑D‑only pipeline. Accordingly, **SC‑008** (ΔR²) cannot be computed and is omitted.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `rdkit`, `lightgbm`, `shap`, `pandas`, `numpy`, `scikit-learn`, `qm9pack`, `scipy` (pinned in `requirements.txt`)  
- **Storage**: Parquet files for raw/processed tables; Pickle for the LightGBM model; JSON for stability reports.  
- **Testing**: `pytest` (unit, integration, contract).  
- **Target Platform**: Linux GitHub Actions free‑tier (2 vCPU, ~7 GB RAM, ≤ 6 h).  
- **Constraints**: CPU‑only; peak RAM ≤ 6 GB; runtime ≤ 6 h; strict 2‑D descriptor usage.

## Constitution Check
| Principle | Status | Comment |
|-----------|--------|---------|
| I. Reproducibility | ✅ | Fixed seeds in `code/utils/config.py`; deterministic data loaders; `requirements.txt` pins versions. |
| II. Verified Accuracy | ✅ | All citations limited to verified URLs (QM9 HuggingFace link, RDKit docs). |
| III. Data Hygiene | ✅ | Raw data checksummed; each transformation produces a new file; no in‑place edits. |
| IV. Single Source of Truth | ✅ | Every figure/table references a single row in `data/processed/` and a single function in `code/`. |
| V. Versioning Discipline | ✅ | Content hashes stored in `state/manifest.json`; timestamps updated by agents. |
| VI. 2D‑Topological Fidelity | ✅ | No calls to `EmbedMolecule`/`Get3DConformer`; TPSA and SMARTS excluded; unit test enforces this. |
| VII. Computational Constraint | ✅ | LightGBM & RDKit run comfortably on CPU; streaming/chunked processing keeps RAM ≤ 6 GB; total estimated runtime < 6 h. |

## Project Structure
```text
specs/001-predict-molecular-polarity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── descriptor_schema.schema.yaml
    ├── features.schema.yaml
    ├── model_output.schema.yaml
    ├── model_output_schema.schema.yaml
    └── vif_schema.schema.yaml

code/
├── data/
│   ├── fetch.py                # QM9 download via qm9pack
│   ├── preprocess.py           # 2‑D descriptor generation, NaN handling
│   ├── feature_selection.py    # VIF pruning + L1 fallback
│   └── validate.py             # Schema & checksum validation
├── model/
│   ├── train.py                # LightGBM training & CV
│   ├── evaluate.py             # SHAP, bootstrap stability, single‑feature R²
│   └── predict.py              # Inference wrapper
├── utils/
│   ├── config.py               # Global seeds, paths, hyper‑params
│   └── logging.py
├── main.py                     # Orchestrator (steps: fetch, preprocess, select, train, analyze, verify)
└── __init__.py

data/
├── raw/
│   └── qm9_raw.parquet
├── processed/
│   ├── descriptors.parquet
│   ├── vif_scores.csv
│   ├── cluster_map.csv
│   └── model.pkl
└── results/
    ├── shap_summary.png
    └── stability_report.json

state/
└── manifest.json               # SHA‑256 checksums for all processed artifacts

tests/
├── unit/
│   ├── test_descriptors.py     # Mocks RDKit 3‑D functions → asserts none called
│   └── test_vif.py
├── contract/
│   ├── test_schema_validation.py
│   └── test_data_integrity.py
└── integration/
    └── test_pipeline.py
```

## Complexity Tracking (FR → Phase Mapping)

| Functional Requirement | Phase / Script | Reason |
|------------------------|----------------|--------|
| FR‑001 | `code/data/preprocess.py` | Generates ≥200 2‑D descriptors, excludes TPSA & SMARTS. |
| FR‑002 | `code/model/train.py` | LightGBM regression on 2‑D matrix. |
| FR‑003 | `code/model/train.py` (CV) | k‑fold CV, hyper‑parameter logging. |
| FR‑004 | `code/model/evaluate.py` (SHAP) | SHAP interaction values for correlated features. |
| FR‑005 | `code/model/evaluate.py` (bootstrap) | 100 resamples of the full dataset; Jaccard stability (≥ 0.7). |
| FR‑006 | `code/data/preprocess.py` (batching, NaN handling) + unit test | Memory ≤6 GB, NaN imputation, 3‑D function guard. |
| FR‑007 | `code/data/feature_selection.py` (VIF + L1 fallback) | Iterative VIF removal, retain ≥150 descriptors; fallback to L1 if < 150 would remain. |
| FR‑008 | `code/data/preprocess.py` (stereochemistry) | Normalizes undefined stereochemistry, logs proportion. |
| FR‑009 | `code/data/preprocess.py` (flexibility flag) | Identifies rotatable‑bond ≥ 5, flags outliers; dual heuristics with Jaccard ≥ 0.8. |
| FR‑010 / FR‑011 | **Out of scope** (conflict with Principle VI) | Documented; requires spec amendment. |
| FR‑012 | `code/model/evaluate.py` (single‑feature models) | Trains ten single‑feature LightGBM models, records R². |
| FR‑013 | `code/data/feature_selection.py` (correlation filter on train split) | Applies |r| > 0.85 filter **only** on training data. |
| SC‑001 | `code/model/evaluate.py` | Computes R² vs. null‑model. |
| SC‑002 | `code/model/evaluate.py` (SHAP) | Reports mean absolute SHAP values. |
| SC‑003 | `code/model/evaluate.py` (bootstrap) | Jaccard similarity of top‑10 SHAP features. |
| SC‑004 | CI logs & `code/utils/logging.py` | Records runtime & peak RAM. |
| SC‑005 | `tests/unit/test_descriptors.py` | Asserts no 3‑D calls. |
| SC‑006 | `code/data/preprocess.py` | Logs stereochemistry normalization proportion (≤ 5 %). |
| SC‑007 | `code/data/preprocess.py` + `code/model/evaluate.py` | Dual heuristics for flexibility; Jaccard ≥ 0.8. |
| SC‑009 | `code/model/evaluate.py` (single‑feature R²) | Each top‑10 SHAP feature ≥ 0.02 R². |
| SC‑010 | CI monitoring | Peak RAM ≤ 6 GB enforced via `resource` module. |

## Contract Validation Mapping
| Contract File | Pipeline Step | Validation Action |
|---------------|---------------|-------------------|
| `contracts/dataset.schema.yaml` | `code/data/fetch.py` → after download | `validate.py` checks raw QM9 metadata against schema. |
| `contracts/descriptor_schema.schema.yaml` | `code/data/preprocess.py` | `validate.py` confirms descriptor matrix shape, exclusion rules, and column metadata. |
| `contracts/vif_schema.schema.yaml` | `code/data/feature_selection.py` | `validate.py` verifies VIF scores, fallback flag, and descriptor count. |
| `contracts/features.schema.yaml` | `code/data/preprocess.py` (post‑processing) | `validate.py` ensures each record conforms to the feature schema (flags, imputation status). |
| `contracts/model_output.schema.yaml` | `code/model/train.py` & `code/model/evaluate.py` | `validate.py` checks model artifact, predictions, and SHAP output against schema. |
| `contracts/model_output_schema.schema.yaml` | `code/model/evaluate.py` | Additional sanity check on aggregated metrics and SHAP summary. |

## Data Flow & Execution Logic
1. **Fetch** (`fetch.py`) → `data/raw/qm9_raw.parquet`.  
2. **Preprocess** (`preprocess.py`) → `data/processed/descriptors.parquet`.  
3. **Feature Selection** (`feature_selection.py`) → `data/processed/vif_scores.csv`, `data/processed/cluster_map.csv`.  
4. **Validate** (`validate.py`) → contracts checked against generated artifacts.  
5. **Train** (`train.py`) → `data/processed/model.pkl`.  
6. **Analyze** (`evaluate.py`) → SHAP summary PNG, stability JSON, single‑feature R² table.  
7. **Verify** (`main.py --step verify`) → checksum comparison against `state/manifest.json`.  

All steps are ordered so that data is downloaded before any consumption, models are trained before evaluation, and figures are generated before any downstream reporting.

---


