# Implementation Plan: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

**Branch**: `001-predict-residual-stress-fatigue` | **Date**: 2026-10-24 | **Spec**: [spec.md](../specs/001-predict-residual-stress-fatigue/spec.md)  
**Input**: Feature specification from `/specs/001-predict-residual-stress-fatigue/spec.md`

## Summary
The project will (1) verify the CI environment (without requiring non‑standard packages such as `ucimlrepo`), (2) generate a deterministic synthetic fatigue dataset **only for pipeline validation**, (3) attempt to ingest any **verified open‑source fatigue dataset** that satisfies the required schema; **if no such dataset exists, the pipeline proceeds solely on the synthetic data for methodological illustration (no empirical claims are made)**, (4) standardize units, median‑impute missing values, and compute a **linear residual‑stress proxy** `σ_res = k·heat_input·cooling_rate` **only when measured stress is missing**, (5) build three feature sets (A = process only, B = process + measured or estimated stress, C = process + material properties + proxy), (6) train Random Forest, Gradient Boosting, and a shallow neural network with 5‑fold CV **on the synthetic data** (or on a real dataset if one becomes available), (7) **perform comparative statistics only as an illustrative demonstration** (paired t‑test and Wilcoxon signed‑rank test with Bonferroni correction) and **report improvement thresholds solely for illustration**, (8) **omit mediation analysis as a primary scientific claim** because no open dataset provides ≥ 50 rows with measured residual stress; mediation will be run only if such a dataset becomes available, otherwise it is skipped, and (9) produce reproducible CSV/PNG artifacts and a runtime summary. All steps run on the GitHub Actions free‑tier CPU runner; no GPU is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `torch==2.3.*` (CPU‑only), `statsmodels==0.14.*`, `pyyaml==6.0.*`, `pytest==8.2.*`  
- **Storage**: CSV files under `data/` (raw) and `data/processed/` (derived)  
- **Testing**: `pytest` with contract validation (`contracts/dataset_schema.yaml`) and custom unit tests (`code/tests/`)  
- **Target Platform**: Linux (Ubuntu‑latest) GitHub Actions runner  
- **Compute Feasibility**: Entire pipeline ≤ 2.5 h, RAM ≤ 6 GB, disk ≤ 12 GB, CPU‑only  

## Constitution Check
| Principle | Mapping to FR / SC |
|-----------|--------------------|
| **I. Reproducibility** | Fixed seeds (`SEED=42`) for data generation, splits, model init, and bootstrap; deterministic `env_check.sh` ensures identical runtime environment (FR‑010, SC‑005). |
| **II. Verified Accuracy** | No unverified dataset URLs introduced; absence of a suitable open dataset is explicitly reported (data‑resources‑9a00440e). |
| **III. Data Hygiene** | Raw files immutable; checksums recorded in `data/raw/checksums.json`; derived files version‑hashed; missing‑value flags stored (FR‑001, FR‑002). |
| **IV. Single Source of Truth** | `data/processed/unified_fatigue.csv` is the sole source for all downstream tables/figures (FR‑001‑FR‑014). |
| **V. Versioning Discipline** | Content hashes drive `state/projects/...yaml` updates; any change updates the hash (FR‑010). |
| **VI. Residual‑Stress Proxy Integrity** | Proxy computed **linearly** for all rows; flagged with `is_proxy` and used only when measured stress is missing (FR‑003, FR‑012). |
| **VII. Cross‑Material Mediation Validation** | Stratified analyses, Bonferroni/Holm‑Bonferroni corrections, paired t‑test with ≥10 % MAPE improvement rule (illustrative only), and explicit associational framing for mediation (when/if performed). |

## Detailed Phases & FR/SC Coverage

| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|-----------------|-----------------|
| **0. Environment Verification** | `scripts/env_check.sh` checks Python 3.11, required packages (standard library + listed dependencies), ≥ 6 GB RAM, ≥ 12 GB free disk, and exits 0 only if all checks pass. No import of non‑standard packages such as `ucimlrepo`. | — | SC‑005 |
| **1. Synthetic Data Generation (Pipeline Validation Only)** | Deterministic generator (`src/data/gen_synthetic.py`, using a fixed seed) creates `data/raw/synthetic_fatigue.csv` (a substantial number of rows). and updates `data/raw/checksums.json`. Synthetic data is **never used for scientific inference** and **never eligible for mediation** as primary evidence. | FR‑001 (schema creation), FR‑010 | — |
| **2. Ingestion & Preprocessing** | 1. Compute SHA‑256 checksums for each raw file.<br>2. Load any **verified open fatigue dataset** that matches the schema (if available).<br>3. Concatenate sources, add `source` column.<br>4. Convert stress units to MPa using the explicit `stress_unit` column (psi → MPa conversion factor as defined in the methodology).<br>5. Median‑impute missing numeric columns (FR‑002).<br>6. Compute **linear residual‑stress proxy** `σ_res = k·heat_input·cooling_rate` (`k=0.8` for steel, `k=0.6` for aluminum). Proxy is computed for **all rows** (enables FR‑014) but **used only when `residual_stress_measured` is missing** (`is_proxy=True`).<br>7. Clamp negative proxy values to `0.01 MPa`; log count.<br>8. Record per‑row checksum in `checksum` column.<br>9. Validate against `contracts/dataset_schema.yaml`; abort on failure.<br>10. Write `data/processed/unified_fatigue.csv` and `data/processed/missing_flags.json`. | FR‑001, FR‑002, FR‑003, FR‑010, FR‑012, FR‑014 | SC‑005 |
| **3. Test Suite Generation** | • `code/tests/test_ingest.py` checks file existence, checksum match, schema compliance, correct unit conversion, median imputation, proxy flag correctness, and clamp‑log entry.<br>• `code/tests/test_features.py` asserts that Feature Sets A and B share identical `sample_id` order and length.<br>• `code/tests/test_mediation.py` verifies that mediation runs **only** when a real dataset provides ≥ 50 measured‑stress rows; otherwise it is skipped. All tests run via `pytest -q`. | FR‑010 | SC‑005 |
| **4. Balanced Subset & Feature‑Set Construction** | 1. Filter `unified_fatigue.csv` to rows where `is_proxy=False` (measured stress present).<br>2. Down‑sample with fixed seed to obtain a **balanced steel/aluminum subset** → `data/processed/balanced_measured.csv`.<br>3. **Feature Set A**: process parameters only (from balanced subset).<br>4. **Feature Set B**: process parameters + `residual_stress_measured` (same rows as Set A).<br>5. **Feature Set C**: full dataset (including proxy rows) with process parameters, material properties, and `residual_stress_proxy` as the stress feature for `is_proxy=True` rows. | FR‑003, FR‑012 | — |
| **5. Model Training & Hyper‑parameter Search** | For each algorithm (RF, GB, shallow NN):<br>• Define a 10‑combo grid.<br>• Perform 5‑fold CV (stratified by `material_class`).<br>• Select combo with lowest mean CV‑MAPE.<br>• Retrain on full training split.<br>• Persist model under `models/<feature_set>/<algorithm>.pt`. | FR‑004, FR‑005, FR‑010 | SC‑002, SC‑005 |
| **6. Held‑out Test Evaluation** | Stratified train/test split from the balanced subset (seed 42). Compute MAPE & R² for each saved model; store in `results/reports/model_performance.csv`. | FR‑005, FR‑010 | SC‑002, SC‑005 |
| **7. Comparative Statistics (Illustrative)** | • Compute absolute errors for Models A vs B on identical test rows.<br>• **Paired t‑test** on absolute errors per algorithm family **and** **Wilcoxon signed‑rank test** as a non‑parametric backup.<br>• Apply **Bonferroni correction** (α = 0.05/3).<br>• **Improvement thresholds** (≥10 % lower MAPE for Model B vs A) are reported **solely as illustrative criteria**; no empirical claim is made unless a real dataset is later available (Constitution Principle VII).<br>• Cross‑material transfer: train on steel‑only, test on aluminum‑only (and vice‑versa); compute ΔMAPE; significance via 10 000‑permutation test with Holm‑Bonferroni. | FR‑008, FR‑009, FR‑011, FR‑010 | SC‑003, SC‑004, SC‑005 |
| **8. Mediation Analysis (Conditional – **NOT** a Primary Claim)** | **Eligibility**: If a **real open dataset** (source ≠ `synthetic` ∧ source ≠ `verification`) provides ≥ 50 rows with measured residual stress, perform mediation on that real data (fulfills FR‑013). **Otherwise**, mediation is **skipped** and a log entry notes the data limitation. No synthetic mediation is performed to avoid violating FR‑013’s power requirement. | FR‑006, FR‑007, FR‑010, FR‑012, FR‑013, FR‑014 (only when real data available) | SC‑001, SC‑003, SC‑005 |
| **9. Reporting & Artifact Generation** | Consolidate all CSV/PNG artifacts under `results/reports/` with provenance columns linking back to `unified_fatigue.csv`. Generate `runtime_summary.csv` (wall‑clock time & peak memory per phase). | FR‑001‑FR‑014 (traceability) | SC‑001‑SC‑005 |
| **10. End‑to‑End Orchestration** | `code/src/run_e2e.py` orchestrates phases 0‑9 in order, exits 0 only if every step succeeds and all `pytest` tests pass. | — | SC‑005 |

## Deliverables
- `plan.md` (this document)  
- `research.md` (methodology, dataset strategy, statistical rigor)  
- `data-model.md` (unified schema)  
- `quickstart.md` (one‑command run)  
- `contracts/dataset_schema.yaml` (JSON‑Schema for `unified_fatigue.csv`)  

