# Implementation Plan: Predicting Plant Root Architecture from Soil Nutrient Availability

**Branch**: `001-predict-root-architecture` | **Date**: 2024-10-11 | **Spec**: `specs/001-predict-root-architecture/spec.md`  
**Input**: Feature specification from `/specs/001-predict-root-architecture/spec.md`

## Summary
The pipeline will (1) ingest root phenotype data from **PlantPheno** *and* **RootReader**, (2) **omit** ISRIC soil data per amendment AM‑001 and proceed with root‑only or a verified merged dataset, (3) preprocess (filter, log‑transform, z‑score, **exclude** rows with any missing nutrient values), (4) fit a Linear Mixed‑Effects Model (LMM) with optional covariates and a baseline Random Forest (RF) using species‑level stratified 5‑fold CV, (5) apply Bonferroni correction, VIF checks, and a literature‑based sensitivity analysis with fallback, (6) generate partial‑dependence plots, (7) compile a PDF report that explicitly contains the associational statement, (8) run dedicated verification steps to ensure no causal language appears and that the associational statement is present, (9) compute all success‑criteria metrics (including SC‑001, SC‑002, SC‑003, SC‑004, SC‑005, SC‑006), and (10) record content‑hashes for all artifacts per Constitution Principle V.

All functional requirements (FR‑001 … FR‑012) and success criteria (SC‑001 … SC‑006) are addressed by specific tasks below.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.1`, `numpy==1.26.4`, `scikit-learn==1.4.2`, `statsmodels==0.14.2`, `matplotlib==3.8.4`, `seaborn==0.13.2`, `datasets==2.18.0`, `pyyaml==6.0.1`, `scipy==1.13.0`, `tqdm==4.66.2`  
- **Storage**: `data/` (raw, processed) and `artifacts/` (metrics, plots, report)  
- **Testing**: `pytest` with contract tests under `tests/contract/`  
- **Target Platform**: GitHub Actions free‑tier (Linux, 2 CPU cores, ~7 GB RAM, no GPU) – all methods are CPU‑compatible.  
- **Constraints**: Memory ≤ 4 GB, total runtime ≤ 6 h, total plot size ≤ 100 MB.  

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Random seeds pinned; `requirements.txt` used. |
| II. Verified Accuracy | PASS | All external datasets are from the verified list; no invented URLs. |
| III. Data Hygiene | PASS | Raw files stored under `data/raw/`; checksums recorded in state file. |
| IV. Single Source of Truth | PASS | All figures/tables generated programmatically. |
| V. Versioning Discipline | PASS | Content hashes for **all** generated artifacts (datasets, metrics, plots, report, schemas) are recorded in `state/projects/PROJ-457-predicting-plant-root-architecture-from-.yaml` as required by Principle V. |
| VI. Cross‑Species Stratified Validation | PASS | CV folds split by `species`. |
| VII. Nutrient‑Specific Metric Normalization | PASS | Log‑transform of root traits; z‑score of nutrients (when present). |
| **Amendment AM‑001** | PASS | FR‑002 (ISRIC merge) and FR‑003 (KNN imputation) are excluded; deviations are logged (Task T010b). |

*No new constraints beyond those in the spec were introduced.*

## Project Structure
```text
specs/001-predict-root-architecture/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── model_results.schema.yaml
│   └── output.schema.yaml
└── tasks.md            # generated later by /speckit-tasks

projects/PROJ-457-predicting-plant-root-architecture-from-/
├── code/
│   ├── requirements.txt
│   ├── ingestion.py
│   ├── preprocessing.py
│   ├── modeling.py
│   ├── visualization.py
│   └── utils.py
├── data/
│   ├── raw/
│   └── processed/
├── artifacts/
│   ├── metrics.json
│   ├── logs/
│   └── reports/
│       ├── plots/
│       └── final_report.pdf
├── tests/
│   └── contract/
│       └── test_schemas.py
└── state/
    └── projects/PROJ-457-predicting-plant-root-architecture-from-.yaml
```

## Task List (Phase‑wise)

| ID | Description | FR / SC Covered | Dependencies |
|----|-------------|----------------|--------------|
| **T001** | Create project directory skeleton (`code/`, `data/raw/`, `data/processed/`, `artifacts/`, `tests/contract/`). | – | – |
| **T002** | Write `code/requirements.txt` with exact pinned versions for all dependencies. | – | T001 |
| **T003** | Create `contracts/dataset.schema.yaml`. | – | T001 |
| **T004** | Create `contracts/model_results.schema.yaml`. | – | T001 |
| **T005** | Create `contracts/output.schema.yaml`. | – | T001 |
| **T006** | Write contract test suite `tests/contract/test_schemas.py` with three validation functions. | – | T003‑T005 |
| **T007** | Download **PlantPheno** root phenotype data via HuggingFace: `datasets.load_dataset("davidkartchner/plant-phenotype")`. | FR‑001 | T001 |
| **T007b** | Download **RootReader** root phenotype data via HuggingFace: `datasets.load_dataset("rootreader/plant-root")`. | FR‑001 | T001 |
| **T008** | **(Removed)** – ISRIC download omitted per AM‑001. |
| **T009** | **(Removed)** – ISRIC merge step omitted per AM‑001. |
| **T010a** | **(Removed)** – logging of ISRIC unavailability replaced by T010b. |
| **T010b** | Log amendment‑driven omission of ISRIC merge (“AM‑001: ISRIC merge excluded per amendment”). | FR‑002 (deviation) | T001 |
| **T011** | Filter loaded data: keep only rows where `data_source_type == "observational"`; drop experimental rows. | FR‑001, FR‑012 | T007, T007b |
| **T012** | Compute per‑species observation counts; exclude species with **< 20** rows. Log excluded species. | FR‑001, SC‑005 | T011 |
| **T013** | Log‑transform root metrics (`log(x + 1e-6)`). | FR‑003, VII | T012 |
| **T014** | Z‑score normalize nutrient columns (`phosphorus`, `nitrogen`) **if present**. | FR‑003, VII | T013 |
| **T015** | **Exclude** rows where either phosphorus or nitrogen is missing; log each exclusion. (No imputation per AM‑001.) | FR‑003 (exclusion path) | T014 |
| **T016** | Save the fully preprocessed dataset to `data/processed/merged_dataset.parquet`. | FR‑003 | T015 |
| **T017** | Generate species‑stratified 5‑fold CV splits (store split indices in `artifacts/cv_splits.pkl`). | FR‑006, VI | T016 |
| **T018** | Fit **Linear Mixed‑Effects Model (LMM)** with random intercept for `species` and optional covariates (`soil_moisture`, `temperature`, `elevation`) when present. Use REML; Satterthwaite p‑values. | FR‑004 | T017 |
| **T019** | Fit **Random Forest** regressor (`max_depth=5`, `random_state=42`). | FR‑005 | T017 |
| **T020** | Compute per‑fold performance metrics (adjusted R², RMSE) for both models; aggregate mean out‑of‑sample R². | FR‑006, SC‑002 | T018, T019 |
| **T021** | Apply **Bonferroni correction** to the six coefficient tests (P & N × three root traits). Store corrected p‑values. | FR‑010 | T020 |
| **T022** | Compute **Variance Inflation Factor (VIF)** for `phosphorus` and `nitrogen`; warn if VIF > 5. | FR‑008 (implicit) | T020 |
| **T023** | Perform **F‑test** for overall LMM significance; store p‑value. | FR‑008 | T018 |
| **T024** | **Power Analysis**: after filtering, compute achieved power for detecting a medium effect (Cohen f² = 0.15) at α = 0.05 using `statsmodels.stats.power.FTestPower`. Store result in metrics. | – | T012 |
| **T025** | **Sensitivity Analysis**: attempt to load literature nutrient‑range dataset (`datasets.load_dataset("plantphysio/nutrient_ranges")`). If unavailable, fall back to hard‑coded typical P/N ranges (e.g., P = 30 ± 3 mg kg⁻¹, N = 25 ± 2.5 mg kg⁻¹). Compare each LMM coefficient to ±10 % of the appropriate range; set `sc_006_met` accordingly and log fallback use. | FR‑011, SC‑006 | T018 |
| **T026** | Generate **Partial Dependence Plots** for each nutrient–trait pair using the 5‑th to 95‑th percentile of nutrient values in the training set. Save PNGs to `artifacts/reports/plots/`. Verify total PNG size ≤ 100 MB. | FR‑007, SC‑004 | T019 |
| **T027** | Assemble **metrics JSON** (`artifacts/metrics.json`) containing: LMM & RF results, CV metrics, multiple‑comparison flags, VIF warnings, sensitivity verdict, power result, SC‑001‑SC‑006 booleans (including computed SC‑001). | SC‑001‑SC‑006 | T020‑T026 |
| **T028** | **Compile final PDF report** (`artifacts/reports/final_report.pdf`) that: summarizes methodology, results, visualizations; includes the exact sentence “All findings are presented as associational relationships; no causal inference is claimed.”; lists all deviation logs. | FR‑009, SC‑001‑SC‑006 | T026, T027 |
| **T029** | **Associational Language Verification**: scan the report markdown for causal keywords (`cause`, `effect`, `lead to`, `driven by`) before PDF conversion; fail the run if any are found. | FR‑009 | T028 |
| **T030** | **Report Statement Check**: ensure the associational statement is present in the final markdown; fail if missing. | FR‑009 | T028 |
| **T031** | Run **contract tests** (`pytest tests/contract/test_schemas.py`). Ensure all three schemas validate their respective artifacts. | – | T003‑T005, T027, T028 |
| **T032** | Compute **SC‑001**: proportion of root phenotype datasets successfully merged with soil nutrient data (using counts from T012 and the fallback merged dataset). Store result in metrics JSON and flag as `null` if soil data unavailable. | SC‑001 | T012, T010b |
| **T033** | Record **content hashes** for every generated artifact (datasets, metrics, plots, report, schemas) into `state/projects/PROJ-457-predicting-plant-root-architecture-from-.yaml` as part of Principle V compliance. | – | T027, T028, T031 |
| **T034** | Update `README.md` with a **Quickstart** link to `quickstart.md`. | – | T001 |
| **T035** | Document **random seeds** (`SEED = 42`) in `code/utils.py` and reference them in all scripts. | – | T001 |
| **T009a** | Write `contracts/dataset.schema.yaml` (already exists) – schema definition prerequisite for contract test T009. | – | T003 |
| **T020a** | Write `contracts/model_results.schema.yaml` – schema definition prerequisite for contract test T020. | – | T004 |
| **T030a** | Write `contracts/output.schema.yaml` – schema definition prerequisite for contract test T030. | – | T005 |

*All tasks are CPU‑compatible; no GPU is required.*

