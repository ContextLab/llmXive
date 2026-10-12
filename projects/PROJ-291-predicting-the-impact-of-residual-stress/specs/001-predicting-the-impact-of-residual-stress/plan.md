# Implementation Plan: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

**Branch**: `001-predict-residual-stress-fatigue` | **Date**: 2026-10-11 | **Spec**: [spec.md](../specs/001-predict-residual-stress-fatigue/spec.md)  
**Input**: Feature specification from `/specs/001-predict-residual-stress-fatigue/spec.md`

## Summary
The project will (1) ingest publicly available fatigue‑related datasets (or fall back to a synthetic validation set when no open source contains the required fields), (2) harmonize them into a unified schema, (3) construct three feature sets (process‑only, process + measured stress, process + material properties), (4) train and evaluate Random Forest, Gradient Boosting, and a shallow neural network using 5‑fold CV and a held‑out test set, (5) compare predictive gains with paired t‑tests (including Bonferroni correction), (6) assess cross‑material transfer performance, and (7) run bootstrap mediation analysis **only when a sufficient number of rows contain measured residual stress**. All steps are CPU‑friendly and designed to run within GitHub Actions free‑tier limits.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `torch==2.3.*` (CPU‑only), `statsmodels==0.14.*`, `datasets==2.20.*`, `pyyaml==6.0.*`, `pytest==8.2.*`  
- **Storage**: File‑based CSV/Parquet under `data/` (raw) and `data/processed/` (derived)  
- **Testing**: `pytest` with contract validation (`contracts/dataset_schema.yaml`)  
- **Target Platform**: Linux (Ubuntu‑latest) GitHub Actions runner  
- **Compute Feasibility**: All steps run on CPU; total wall‑clock ≤ 2.5 h, peak RAM ≤ 6 GB, disk ≤ 12 GB. No GPU required.

## Constitution Check
| Principle | Mapping to FR / SC |
|-----------|--------------------|
| I. Reproducibility | Fixed seeds (FR‑010); deterministic scripts; data fetched from canonical URLs (FR‑001) |
| II. Verified Accuracy | Only the verified URLs listed in the “Verified datasets” block are cited (Research.md) |
| III. Data Hygiene | Raw files immutable; checksum recorded; derived files carry provenance checksum (FR‑001, FR‑010) |
| IV. Single Source of Truth | All figures/tables trace back to rows in `data/processed/unified_fatigue.csv` and scripts in `src/` |
| V. Versioning Discipline | Content hashes drive state updates (FR‑010) |
| VI. Residual‑Stress Proxy Integrity | Proxy calculation, flagging (`is_proxy`), and separate handling for mediation (FR‑003, FR‑012) |
| VII. Cross‑Material Mediation Validation | Stratified mediation, paired t‑tests, and cross‑material transfer evaluation (FR‑009, FR‑011) |

## Detailed Phases & FR/SC Coverage

| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|-----------------|-----------------|
| **0. Environment Verification** | Run `scripts/env_check.sh` to ensure required Python version and dependencies; abort if fails. | — | — |
| **1. Data Ingestion & Preprocessing** | • Download each verified open dataset (UCI, NIST, DatasetRecord) via `datasets.load_dataset`.<br>• Compute SHA‑256 checksum for every raw file and store in `data/raw/`.<br>• Append a `checksum` column to the unified CSV.<br>• Convert all stress units to MPa.<br>• Median‑impute missing numerics.<br>• Compute proxy residual stress when measured is missing (using material‑specific `k`). Clamp negatives to 0.01 MPa; set `is_proxy=True` and store `residual_stress_proxy`.<br>• Write processed file `data/processed/unified_fatigue.csv` and validate against `contracts/dataset_schema.yaml`. | FR‑001, FR‑002, FR‑003, FR‑010, FR‑012 | SC‑005 (runtime limits) |
| **2. Feature‑Set Construction** | Create three CSVs (or views) for Feature Sets A, B, C as described in the spec. Feature Set B includes only rows where `is_proxy=False`. | FR‑001 (schema continuity) | — |
| **3. Model Training & Hyper‑parameter Search** | For each algorithm (RF, GB, shallow NN):<br>• Define a 10‑combination grid.<br>• Perform 5‑fold CV stratified by `material_class`.<br>• Record MAPE and R² per fold.<br>• Select hyper‑parameters with lowest mean CV‑MAPE.<br>• Retrain on the full training split (train + validation) and save the best model per feature set. | FR‑004, FR‑005, FR‑010 | SC‑002 (predictive gain), SC‑005 |
| **4. Held‑out Test Evaluation** | Split data (stratified by material) using seed 42; compute MAPE & R² for each saved model on the test set. | FR‑005, FR‑010 | SC‑002, SC‑005 |
| **5. Paired t‑tests & Multiple‑Comparison** | • Compute absolute errors for Model A vs. Model B on the full test set (including proxy rows).<br>• Run paired t‑test; apply Bonferroni correction for the three algorithm families (α = 0.05/3).<br>• Repeat the test on the measured‑stress subset (if ≥ 50 rows) and report both p‑values. | FR‑008, FR‑010 | SC‑002, SC‑003 (significance), SC‑005 |
| **6. Cross‑Material Transfer Evaluation** | Train each model on steel‑only data, test on aluminum‑only data, and vice‑versa; report ΔMAPE relative to within‑material baseline. | FR‑011, FR‑010 | SC‑004 (generalization), SC‑005 |
| **7. Mediation Analysis (Conditional)** | • If `is_proxy=False` rows ≥ 50, run bootstrap mediation (10 000 resamples) using `statsmodels`.<br>• Include all process parameters and material properties as covariates.<br>• Compute VIF; flag any > 5.<br>• Apply Holm‑Bonferroni correction across material classes.<br>• Save `mediation_summary.csv` and generate effect‑size plots.<br>• If < 50 rows, log warning and skip mediation (edge‑case handling). | FR‑006, FR‑007, FR‑010, FR‑012 | SC‑001 (proportion mediated), SC‑003 (CI), SC‑005 |
| **8. Reporting & Artifact Generation** | • Consolidate all metrics into `results/reports/model_performance.csv`.<br>• Export paired‑t‑test results, cross‑material ΔMAPE, and mediation summary (if run).<br>• Generate PNG figures for performance, t‑test distributions, and mediation effects.<br>• Create `runtime_summary.csv` with wall‑clock & memory usage per phase. | FR‑001–FR‑012 (traceability) | SC‑001–SC‑005 |
| **9. Edge‑Case Logic** | • If no measured stress in any dataset, set `proxy_dependent=True` in final report and omit mediation.<br>• If any proxy calculation yields negative values, clamp to 0.01 MPa and log adjustment.<br>• If total sample size < 50, raise a warning and skip mediation. | FR‑003, FR‑006, FR‑012 | — |

## Deliverables
- `plan.md` (this document)  
- `research.md` (detailed methodology, dataset strategy, statistical rigor)  
- `data-model.md` (unified schema)  
- `quickstart.md` (one‑command end‑to‑end run)  
- `contracts/dataset_schema.yaml` (JSON‑Schema for the processed CSV)

---
