# Implementation Plan: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

**Branch**: `001-predict-residual-stress-fatigue` | **Date**: 2026-10-18 | **Spec**: [spec.md](../specs/001-predict-residual-stress-fatigue/spec.md)  
**Input**: Feature specification from `/specs/001-predict-residual-stress-fatigue/spec.md`

## Summary
The project will (1) run a **Preliminary Environment Check**, (2) ingest publicly available engineering datasets and a synthetic validation dataset, (3) harmonize them into a unified schema, (4) construct three feature sets (process‑only, process + measured residual stress, process + material properties + proxy stress), (5) train Random Forest, Gradient Boosting, and a shallow neural network with 5‑fold CV and a held‑out test set, (6) compare predictive gains using paired t‑tests **restricted to the measured‑stress subset**, (7) evaluate cross‑material transfer performance with permutation testing, (8) conditionally run bootstrap mediation analysis on the measured‑stress subset (with an a‑priori power justification), and (9) generate reproducible reports. All steps are CPU‑only, reproducible, and designed to stay within GitHub Actions free‑tier limits.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `torch==2.3.*` (CPU‑only), `statsmodels==0.14.*`, `datasets==2.20.*`, `pyyaml==6.0.*`, `pytest==8.2.*`  
- **Storage**: File‑based CSV/Parquet under `data/` (raw) and `data/processed/` (derived)  
- **Testing**: `pytest` with contract validation (`contracts/dataset_schema.yaml`)  
- **Target Platform**: Linux (Ubuntu‑latest) GitHub Actions runner  
- **Compute Feasibility**: Entire pipeline runs on CPU; estimated wall‑clock ≤ 2.5 h, peak RAM ≤ 6 GB, disk ≤ 12 GB. No GPU required.

## Constitution Check
| Principle | Mapping to FR / SC |
|-----------|--------------------|
| **I. Reproducibility** | Fixed seeds (FR‑010); deterministic scripts; data fetched from canonical URLs (FR‑001) |
| **II. Verified Accuracy** | All external dataset URLs are programmatically verified and cited (citation‑verification task) |
| **III. Data Hygiene** | Raw files immutable; checksums recorded; derived files documented (FR‑001, FR‑010) |
| **IV. Single Source of Truth** | `data/processed/unified_fatigue.csv` is the SSoT for all downstream figures and tables |
| **V. Versioning Discipline** | Content hashes drive state updates (FR‑010) |
| **VI. Residual‑Stress Proxy Integrity** | Proxy calculation flagged (`is_proxy=True`); mediation excludes proxy rows (FR‑003, FR‑012) |
| **VII. Cross‑Material Mediation Validation** | Stratified mediation, paired t‑tests, cross‑material transfer evaluation (FR‑009, FR‑011) |

## Detailed Phases & FR/SC Coverage

| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|-----------------|-----------------|
| **0. Preliminary Environment Check** | Run `scripts/env_check.sh` to verify Python version, required packages, and available disk/RAM. Fails fast if the CI runner cannot meet the resource budget. | — | SC‑005 |
| **1. Data Ingestion & Preprocessing** | • Download each verified dataset via `datasets.load_dataset` (streaming mode for large files).<br>• Compute SHA‑256 checksum for every raw file; store under `data/raw/` and embed as a `checksum` column.<br>• Convert stress units to MPa.<br>• Median‑impute missing numeric values.<br>• Compute proxy residual stress when measured is missing using `σ_res = k·heat_input·cooling_rate` (`k=0.8` for steel, `k=0.6` for aluminum); clamp negatives to 0.01 MPa; set `is_proxy=True`.<br>• Flag proxy rows in the schema (see data‑model).<br>• Validate the unified CSV against `contracts/dataset_schema.yaml`; abort on failure.<br>• Fixed random seed `SEED=42`. | FR‑001, FR‑002, FR‑003, FR‑010, FR‑012 | SC‑005 |
| **2. Feature‑Set Construction** | Generate three derived CSVs:<br>• **Feature Set A – Process‑only** (process parameters only).<br>• **Feature Set B – Process + Measured Stress** (A + `residual_stress_measured`; includes only rows where `is_proxy=False`).<br>• **Feature Set C – Process + Material Props + Proxy Stress** (A + material properties + `residual_stress_proxy`; includes only rows where `is_proxy=True`). | FR‑001 (schema continuity) | — |
| **3. Model Training & Hyper‑parameter Search** | For each algorithm (Random Forest, Gradient Boosting, shallow NN):<br>• Define a grid of 10 hyper‑parameter combos.<br>• Perform 5‑fold CV stratified by `material_class`.<br>• Record MAPE and R² per fold.<br>• Select combo with lowest mean CV‑MAPE.<br>• Retrain on the full training split (train + validation) and persist the best model per feature set. | FR‑004, FR‑005, FR‑010 | SC‑002, SC‑005 |
| **4. Held‑out Test Evaluation** | Split data ([deferred] test, stratified by material) using seed 42; compute MAPE & R² for each saved model on the test set. | FR‑005, FR‑010 | SC‑002, SC‑005 |
| **5. Paired t‑tests & Multiple‑Comparison Correction** | • Compute absolute errors for Model A vs. Model B **only on the measured‑stress subset** (`is_proxy=False`).<br>• Run paired t‑test per algorithm family.<br>• Apply Bonferroni correction across the three families (α = 0.05/3).<br>• **Exploratory**: optionally run the same test on the full test set (including proxy rows) and flag results as “proxy‑mixed”. | FR‑008, FR‑010 | SC‑003, SC‑005 |
| **6. Cross‑Material Transfer Evaluation** | Train each model on steel‑only data, test on aluminum‑only data, and vice‑versa; compute ΔMAPE relative to within‑material baseline.<br>• Assess significance using a **permutation test** (10 000 permutations, α = 0.05, Holm‑Bonferroni across material pairs). | FR‑011, FR‑010 | SC‑004, SC‑005 |
| **7. Mediation Analysis (Conditional)** | • **Eligibility**: proceed only if rows with `is_proxy=False` ≥ 50. Power analysis (detectable indirect effect ≈ 0.5, α = 0.05, power = 0.8) suggests ≈ 64 samples; 50 is a pragmatic lower bound, and a warning is logged if below.<br>• **Model Specification**: Linear models for the **a‑path** (process → residual stress) and **b‑path** (residual stress → fatigue life) controlling for `heat_input`, `cooling_rate`, `elastic_modulus`, `yield_strength`, `material_class`, and any additional numeric process parameters.<br>• Compute VIF for each predictor; flag any > 5.<br>• Run bootstrap mediation with 10 000 resamples (`statsmodels`).<br>• Apply Holm‑Bonferroni correction across material classes.<br>• **Causal Framing**: Results are reported as *associational* mediation; no causal claims are made. For causal inference, a structural equation model with explicit assumptions is suggested for future work.<br>• Save `mediation_summary.csv` and generate effect‑size plots. | FR‑006, FR‑007, FR‑010, FR‑012 | SC‑001, SC‑003, SC‑005 |
| **8. Reporting & Artifact Generation** | • Consolidate metrics into `results/reports/model_performance.csv`.<br>• Export paired‑t‑test results, cross‑material ΔMAPE (with permutation p‑values), and mediation summary (if run).<br>• Generate PNG figures for performance curves, t‑test distributions, and mediation effects.<br>• Produce `runtime_summary.csv` with wall‑clock & memory usage per phase. | FR‑001–FR‑012 (traceability) | SC‑001–SC‑005 |
| **9. Edge‑Case Logic** | • If no measured residual stress exists, set `proxy_dependent=True` in final report and omit mediation.<br>• If any proxy calculation yields negative values, clamp to 0.01 MPa and log adjustment.<br>• If total sample size < 50, raise a warning and skip mediation. | FR‑003, FR‑006, FR‑012 | — |

## Deliverables
- `plan.md` (this document)  
- `research.md` (detailed methodology, dataset strategy, statistical rigor)  
- `data-model.md` (unified schema)  
- `quickstart.md` (one‑command end‑to‑end run)  
- `contracts/dataset_schema.yaml` (JSON‑Schema for the processed CSV)  
