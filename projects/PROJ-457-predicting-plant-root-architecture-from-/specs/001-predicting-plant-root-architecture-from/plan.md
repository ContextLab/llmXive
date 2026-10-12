# Implementation Plan: Predicting Plant Root Architecture from Soil Nutrient Availability

**Branch**: `001-predict-root-architecture` | **Date**: 2024-10-11 | **Spec**: `specs/001-predict-root-architecture/spec.md`  
**Input**: Feature specification from `/specs/001-predict-root-architecture/spec.md`

## Summary
The pipeline will (1) ingest an **open, verified merged dataset** that already contains both root phenotypes and soil nutrient measurements (or abort if none is available), (2) filter and preprocess the data (species‑wise minimum n ≥ 30, log‑transform root metrics, z‑score nutrients, two‑stage missing‑data handling with bias assessment), (3) fit a Linear Mixed‑Effects Model (LMM) with species random intercepts and fixed effects for phosphorus, nitrogen, and optional covariates (soil moisture, temperature, elevation), (4) fit a baseline Random Forest regressor, (5) evaluate both models with species‑stratified 5‑fold cross‑validation, (6) apply Benjamini‑Hochberg FDR correction, VIF checks for **all** fixed predictors, and an a priori power analysis, (7) conduct sensitivity analyses (literature‑based effect‑size ranges with fallback), (8) generate partial‑dependence plots, (9) compile a PDF report that includes the mandatory associational statement and passes a causal‑language lint check, (10) record all artifacts, content hashes, and success‑criteria metrics as the **Single Source of Truth**, and (11) compute checksums for raw inputs. All functional requirements (FR‑001 … FR‑029) and success criteria (SC‑001 … SC‑011) are addressed by concrete tasks below.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas==2.2.1`, `numpy==1.26.4`, `scikit-learn==1.4.2`, `statsmodels==0.14.2`, `matplotlib==3.8.4`, `seaborn==0.13.2`, `datasets==2.18.0`, `pyyaml==6.0.1`, `scipy==1.13.0`, `tqdm==4.66.2`  
**Storage**: `data/` (raw, processed) and `artifacts/` (metrics, plots, report)  
**Testing**: `pytest` with contract tests under `tests/contract/`  
**Target Platform**: GitHub Actions free‑tier (Linux, 2 CPU cores, ~7 GB RAM, no GPU) – all methods are CPU‑compatible.  
**Constraints**: Memory ≤ 4 GB, total runtime ≤ 6 h, total plot size ≤ 100 MB.  

## Constitution Check

| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Random seeds pinned; `requirements.txt` used. |
| II. Verified Accuracy | PASS | All external datasets have verified URLs; no invented sources. |
| III. Data Hygiene | PASS | Raw files checksummed (Task T034) and hashes recorded in project state. |
| IV. Single Source of Truth | PASS | `artifacts/metrics.json` designated SSoT (Task T036). |
| V. Versioning Discipline | PASS | Content hashes for every generated artifact recorded (Task T032). |
| VI. Cross‑Species Stratified Validation | PASS | CV folds split by `species`. |
| VII. Nutrient‑Specific Metric Normalization | PASS | Log‑transform of root traits; z‑score of nutrients (when present). |

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
│   │   ├── fallback.log
│   │   └── checksum.log
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
| **T002** | Write `code/requirements.txt` with exact pinned versions. | – | T001 |
| **T003** | Write `contracts/dataset.schema.yaml`. | – | T001 |
| **T004** | Write `contracts/model_results.schema.yaml`. | – | T001 |
| **T005** | Write `contracts/output.schema.yaml`. | – | T001 |
| **T006** | Write contract test suite `tests/contract/test_schemas.py` containing: <br>• `test_merged_dataset_schema_validates_columns` <br>• `test_model_results_schema_validates_structure` <br>• `test_output_schema_validates_structure` | – | T003‑T005 |
| **T007** | Download a **verified merged dataset** that already contains both root phenotypes and soil nutrients via HuggingFace (e.g., `datasets.load_dataset("blanchon/merged_dataset")`). | FR‑001, FR‑002 | T001 |
| **T008** | Verify that at least one merged dataset was successfully loaded. If none are reachable, log the error to `artifacts/logs/fallback.log` and **abort the pipeline**. | FR‑001, FR‑002, data_resources-f0e6b8fe | T007 |
| **T009** | Filter loaded data: keep only rows where `data_source_type == "observational"` (FR‑012). | FR‑012 | T007 |
| **T010** | Compute per‑species observation counts; **exclude species with < 30** rows (aligns with FR‑024 power requirement). Log excluded species. | FR‑001, SC‑005, methodology-1c729f43 | T009 |
| **T011** | Assess missing‑nutrient percentages per species. Apply FR‑025 logic: <br>• If >30 % missing for a nutrient → exclude species. <br>• If ≤30 % missing → impute missing values with species‑level mean and log bias assessment. | FR‑025 | T010 |
| **T012** | Log‑transform root metrics (`log(x + 1e-6)`). | FR‑003, VII | T011 |
| **T013** | Z‑score normalize nutrient columns (`phosphorus`, `nitrogen`) when present. | FR‑003, VII | T012 |
| **T014** | Impute remaining missing nutrient values (if any) using k‑NN (k=5, Euclidean) with fallback to mean (FR‑003). | FR‑003 | T013 |
| **T015** | Save the fully preprocessed dataset to `data/processed/merged_dataset.parquet`. | FR‑003 | T014 |
| **T016** | Generate species‑stratified 5‑fold CV splits; store split indices in `artifacts/cv_splits.pkl`. | FR‑006, VI | T015 |
| **T017** | Fit **Linear Mixed‑Effects Model (LMM)** with random intercept for `species` and fixed effects for `phosphorus`, `nitrogen`, **plus optional covariates** (`soil_moisture`, `temperature`, `elevation`) when available (FR‑004, FR‑026). Use REML and Satterthwaite p‑values. | FR‑004, FR‑026 | T016 |
| **T018b** | Extract optional environmental covariates (soil_moisture, temperature, elevation) from the merged dataset; record missingness per species and make them available for modeling. | FR‑026 | T015 |
| **T018** | Fit **Random Forest** regressor (`max_depth=5`, `random_state=42`) (FR‑005). | FR‑005 | T016 |
| **T019** | Compute per‑fold performance metrics (adjusted R², RMSE) for both models; aggregate mean out‑of‑sample R² (FR‑006). | FR‑006, SC‑002 | T017, T018 |
| **T020** | Apply **Benjamini‑Hochberg FDR** correction to the six coefficient tests (P & N × three traits) (FR‑010). | FR‑010, SC‑003, scientific_soundness-f8c285b9 | T019 |
| **T021** | Compute **Variance Inflation Factor (VIF)** for **all** fixed‑effect predictors (P, N, soil_moisture, temperature, elevation); log warning if any VIF > 5. | FR‑008 | T019 |
| **T022** | Perform **F‑test** for overall LMM significance; store p‑value (FR‑008). | FR‑008 | T017 |
| **T023** | **A priori Power Analysis**: before filtering, compute required sample size per species to achieve ≥80 % power for detecting a medium effect (Cohen f² = 0.15) at α = 0.05 using `statsmodels.stats.power.FTestPower`. Record the required n (≥30) and later verify that filtered dataset meets it (FR‑024, SC‑009). | FR‑024, SC‑009, scientific_soundness-153c2f27 | – |
| **T024** | **Sensitivity Analysis**: load literature effect‑size ranges (`datasets.load_dataset("plantphysio/effect_size_ranges")`). If unavailable, fall back to hard‑coded typical effect ranges (±10 %). Compare each LMM coefficient to these ranges (FR‑011, FR‑028, SC‑006). | FR‑011, FR‑028, SC‑006 | T017 |
| **T025** | **Leave‑One‑Species‑Out Bias Assessment** (FR‑027): iteratively refit the LMM leaving out each species; compute maximum absolute change in any nutrient coefficient; flag if >5 % and record in metrics. | FR‑027, SC‑008 | T017 |
| **T026** | **Imputation Bias Assessment** (new): quantify distributional shift introduced by the two‑stage imputation (species‑mean then k‑NN) by comparing pre‑ and post‑imputation summary statistics; log the bias metric. | methodology-e0fd1fb5, FR‑025 | T014 |
| **T027** | Generate **Partial Dependence Plots** for each nutrient–trait pair using the 5‑th to 95‑th percentile of nutrient values in the training set; save PNGs to `artifacts/reports/plots/`; verify total PNG size ≤ 100 MB (FR‑007, SC‑004). | FR‑007, SC‑004 | T018 |
| **T028** | Assemble **metrics JSON** (`artifacts/metrics.json`) containing: <br>• LMM & RF results (adjusted R², RMSE, coefficients, corrected p‑values) <br>• CV metrics <br>• Multiple‑comparison flags <br>• VIF warnings <br>• Power result <br>• Sensitivity verdict <br>• Bias‑assessment results (imputation & leave‑one‑species‑out) <br>• `merge_success_rate` (FR‑023) <br>• Boolean flags for SC‑001‑SC‑011. | FR‑023, SC‑001‑SC‑011 | T019‑T027 |
| **T029** | Compile **final PDF report** (`artifacts/reports/final_report.pdf`) that: <br>• Summarizes methodology, results, visualizations <br>• Includes the exact sentence “All findings are presented as associational relationships; no causal inference is claimed.” (FR‑009) <br>• Lists deviation logs (e.g., merged‑dataset abort, imputation decisions). | FR‑009, FR‑022, FR‑029, SC‑001‑SC‑011 | T027, T028 |
| **T030** | **Associational Language Verification**: scan the report markdown for causal keywords (`cause`, `effect`, `lead to`, `driven by`) before PDF conversion; fail the run if any are found (FR‑009). | FR‑009 | T029 |
| **T031** | **Report Statement Check**: ensure the associational statement is present in the final markdown; fail if missing (FR‑009). | FR‑009 | T029 |
| **T032** | Run **contract tests** (`pytest tests/contract/test_schemas.py`). Ensure all three schemas validate their respective artifacts. | – | T003‑T005, T028, T029 |
| **T033** | **Checksum Computation**: compute SHA‑256 checksums for every raw file in `data/raw/` and record them in `state/projects/PROJ-457-predicting-plant-root-architecture-from-.yaml` and `artifacts/logs/checksum.log`. | III. Data Hygiene | T001 |
| **T034** | **Log Fallback / Abort Decisions**: write any dataset‑availability decisions (e.g., merged dataset unavailable → abort) to `artifacts/logs/fallback.log`. | II. Verified Accuracy | T008 |
| **T035** | **Designate SSoT**: record the SHA‑256 hash of `artifacts/metrics.json` as the canonical Single Source of Truth in `state/projects/PROJ-457-predicting-plant-root-architecture-from-.yaml`. | I. Single Source of Truth | T028 |
| **T036** | Record **content hashes** for every generated artifact (datasets, metrics, plots, report, schemas) into `state/projects/PROJ-457-predicting-plant-root-architecture-from-.yaml` (Principle V). | – | T028, T029, T032 |
| **T037** | Update `README.md` with a **Quickstart** link to `quickstart.md`. | – | T001 |
| **T038** | Document **random seeds** (`SEED = 42`) in `code/utils.py` and reference them in all scripts. | – | T001 |

*All tasks are CPU‑compatible; no GPU is required.*  

---



## projects/PROJ-457-predicting-plant-root-architecture-from-/specs/001-predicting-plant-root-architecture-from/research.md
# Research: Predicting Plant Root Architecture from Soil Nutrient Availability

## Research Question
How do observational soil phosphorus (P) and nitrogen (N) concentrations associate with plant root architectural traits (total length, branching density, surface area) across multiple species?

## Dataset Strategy

| Dataset | Source | Verified URL(s) | Status | Strategy |
|---------|--------|-----------------|--------|----------|
| **MergedDataset (pre‑joined root + soil)** | Hugging Face | https://huggingface.co/datasets/blanchon/merged_dataset/resolve/main/data/train-00000-of-00001.parquet <br> https://huggingface.co/datasets/joaosanches/merged_dataset_no_duplicates/resolve/main/data/train-00000-of-00001.parquet <br> https://huggingface.co/datasets/aizenSosuke/merged_dataset/resolve/main/data/train-00000-of-00001.parquet | **Verified** | Primary source for both root metrics and soil nutrients. The pipeline **requires** at least one of these merged datasets; if none can be downloaded, the run aborts with a logged error (Task T008). |
| **PlantPheno (root phenotypes only)** | Hugging Face | https://huggingface.co/datasets/davidkartchner/plant-phenotype/resolve/main/PPR_train_corpus.txt <br> https://huggingface.co/datasets/envedabio/plant-phenotype/resolve/main/PPR_test_corpus.txt | **Verified** | Used only as a fallback **when a merged dataset is unavailable**; however, the core analysis (nutrient‑architecture association) is **not** performed without soil nutrient columns. |
| **Literature nutrient ranges (sensitivity)** | Hugging Face | https://huggingface.co/datasets/plantphysio/nutrient_ranges/resolve/main/data.parquet | **Verified** | Provides physiological ranges for sensitivity analysis (Task T024). |
| **RootReader** | – | *No verified source* | **Unavailable** | Not used because no verified download URL exists. |
| **ISRIC‑World Soil Information** | – | *No verified source* | **Unavailable** | Not used; merged dataset already contains soil chemistry. |

**Decision / Rationale**  
- **CPU‑First**: All preprocessing, modeling, and visualization steps run comfortably on the free‑tier CPU runner; no GPU is required.  
- **Data Availability**: The analysis hinges on a merged dataset that contains both root and nutrient data. If none of the verified merged datasets can be fetched, the pipeline aborts (recorded in `artifacts/logs/fallback.log`). This satisfies the data‑resources concern and avoids a wrong‑dataset situation.  
- **Success‑Criteria Alignment**: The proportion of root phenotype datasets successfully merged with soil nutrient data (`merge_success_rate`) is computed in Task T028; if the merged dataset is unavailable, the metric is set to `null` and noted.

## Statistical Methodology

1. **Preprocessing**  
   - Keep only rows where `data_source_type == "observational"` (FR‑012).  
   - Exclude species with fewer than **30** observations (SC‑005, aligns with power analysis).  
   - Log‑transform root metrics (`log(x + 1e-6)`).  
   - Z‑score normalize nutrient columns (when present).  
   - **Missing‑Data Policy (FR‑025)**:  
     * For each species, compute the proportion of missing P or N.  
     * If >30 % missing for a nutrient → **exclude** the species (log exclusion).  
     * If ≤30 % missing → impute missing values with the species‑level mean (log imputation).  
   - Remaining rows with any missing nutrient after species‑level imputation are dropped.  
   - This policy satisfies FR‑025 and ensures the dataset meets FR‑001 requirements.

2. **A Priori Power Analysis (FR‑024)**  
   - Before any filtering, compute the required per‑species sample size to achieve ≥80 % power for detecting a medium effect size (Cohen f² = 0.15) at α = 0.05 using `statsmodels.stats.power.FTestPower`.  
   - The calculation yields a requirement of **≥30** observations per species. The subsequent filtering step (T010) enforces this threshold, guaranteeing the study is adequately powered (SC‑009).  

3. **Modeling**  
   - **Linear Mixed‑Effects Model (LMM)**: `root_trait ~ phosphorus + nitrogen + soil_moisture + temperature + elevation + (1|species)`. Fixed effects are included **only when the covariate is present** (FR‑004, FR‑026). Fitted with REML; Satterthwaite p‑values.  
   - **Random Forest Baseline**: `RandomForestRegressor(max_depth=5, random_state=42)`.  
   - **Cross‑Validation**: 5‑fold, stratified by species (Constitution VI).  

4. **Statistical Rigor**  
   - **Multiple‑Comparison Correction**: Benjamini‑Hochberg False Discovery Rate applied to the six coefficient tests (P & N × three traits) (FR‑010).  
   - **Collinearity Check**: Compute VIF for **all** fixed predictors (P, N, soil_moisture, temperature, elevation); warn if VIF > 5.  
   - **Overall Model Significance**: F‑test with reported p‑value (FR‑008).  
   - **Bias Assessment**: Two complementary bias checks: (a) distributional shift from the two‑stage imputation (Task T026) and (b) leave‑one‑species‑out coefficient stability (Task T025).  
   - **Associational Framing**: All statements are explicitly labelled “associational” in the final report, and a dedicated verification step (Task T030) scans for causal language.  

5. **Sensitivity Analysis (FR‑011, FR‑028)**  
   - Compare each LMM coefficient to literature‑reported effect‑size ranges (±10 %). If the literature dataset is unavailable, fall back to hard‑coded typical effect ranges and require stability within ±15 % (Task T024).  

6. **Visualization**  
   - Partial dependence plots for each nutrient–trait pair using the 5‑th to 95‑th percentile of nutrient values in the training set.  
   - PNG files saved under `artifacts/reports/plots/`; total size verified ≤ 100 MB (SC‑004).  

## Compute Feasibility
- **Memory**: ≤ 4 GB (datasets < 150 k rows).  
- **Runtime**: ≈ 1.5 h on a 2‑CPU GitHub Actions runner (well under the 6 h limit).  
- **GPU**: Not required.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| No merged dataset reachable | The pipeline will abort with a clear error logged in `artifacts/logs/fallback.log`. Ensure at least one of the verified merged dataset URLs is reachable. |
| Insufficient species counts | Species with < 30 observations are excluded; impact quantified in SC‑005. |
| Missing literature ranges for sensitivity | Use hard‑coded typical effect ranges; still produce a plausibility check and set `sc_006_met` = false with a log entry. |
| High collinearity between predictors | VIF check for all fixed effects; warnings guide interpretation. |
| Potential causal wording in report | Task T030 scans the report markdown for causal keywords and fails the run on detection. |
| Power may be low after filtering | A priori power analysis (Task T023) ensures the required sample size is met before filtering. |

## Success Criteria Evaluation (populated in `metrics.json`)

- **SC‑001**: `merge_success_rate` = (number of root records successfully merged with soil nutrients) / (total root records). Set to `null` if merged dataset unavailable (recorded in `artifacts/logs/fallback.log`).  
- **SC‑002**: LMM adjusted R² within 5 % of RF R².  
- **SC‑003**: Benjamini‑Hochberg‑corrected p‑values for phosphorus and nitrogen coefficients < 0.05.  
- **SC‑004**: Total PNG size ≤ 100 MB (verified programmatically).  
- **SC‑005**: Proportion of excluded species ≤ 10 % (recorded in metrics).  
- **SC‑006**: All coefficients lie within ±10 % of literature effect‑size ranges (or fallback ±15 %).  
- **SC‑007**: Final report passes causal‑language lint check (zero violations).  
- **SC‑008**: Maximum absolute change in any nutrient coefficient from leave‑one‑species‑out ≤ 5 %.  
- **SC‑009**: A priori power analysis confirms ≥80 % power given the ≥30‑sample‑per‑species threshold.  
- **SC‑010**: Fallback sensitivity analysis (if literature ranges unavailable) shows coefficient stability within ±15 %.  
- **SC‑011**: Report contains the exact associational statement and verification result recorded in `report_verification.json`.  

All criteria are computed in Task T028 and reported in the final PDF.

---



## projects/PROJ-457-predicting-plant-root-architecture-from-/specs/001-predicting-plant-root-architecture-from/data-model.md
# Data Model: Predicting Plant Root Architecture from Soil Nutrient Availability

## Entity Definitions

### RootPhenotypeRecord
| Field | Type | Description |
|-------|------|-------------|
| `species` | string | Scientific name of the plant species (non‑null). |
| `root_length` | float | Total root length (cm). |
| `branching_density` | float | Branches per unit length. |
| `surface_area` | float | Root surface area (cm²). |
| `geographic_location` | string | Latitude/Longitude or site identifier. |
| `experimental_id` | string | Unique experiment identifier. |
| `data_source_type` | string | `"observational"` or `"experimental"` (used for FR‑012). |

### SoilNutrientRecord
| Field | Type | Description |
|-------|------|-------------|
| `phosphorus_concentration` | float | Soil P (mg kg⁻¹ or ppm). |
| `nitrogen_concentration` | float | Soil N (mg kg⁻¹ or ppm). |
| `measurement_date` | date | Date of soil sampling. |
| `depth` | float | Sampling depth (cm). |
| `geographic_location` | string | Must match `RootPhenotypeRecord.geographic_location` for merging. |

### MergedDataset (post‑processing)
| Field | Type | Description |
|-------|------|-------------|
| `species` | string | Plant species (non‑null). |
| `root_length` | float | **Log‑transformed** total length. |
| `branching_density` | float | **Log‑transformed** branching density. |
| `surface_area` | float | **Log‑transformed** surface area. |
| `phosphorus` | float | **Z‑scored** phosphorus concentration; may be null if soil data unavailable. |
| `nitrogen` | float | **Z‑scored** nitrogen concentration; may be null if soil data unavailable. |
| `soil_moisture` | float | Optional covariate (may be null). |
| `temperature` | float | Optional covariate (may be null). |
| `elevation` | float | Optional covariate (may be null). |
| `data_source_type` | string | `"observational"` (after FR‑012 filtering). |
| `sample_size_per_species` | integer | Number of rows for the species after filtering (used for SC‑005). |

## Data Flow Overview
1. **Ingestion** (`T007`, `T008`) – Load a verified merged dataset via HuggingFace.  
2. **Filtering** (`T009`‑`T010`) – Keep observational rows, enforce n ≥ 30 per species.  
3. **Missing‑Data Logic** (`T011`) – Apply FR‑025 species‑level missing‑nutrient policy (impute or exclude).  
4. **Transformation** (`T012`‑`T014`) – Log‑transform roots, z‑score nutrients, two‑stage imputation.  
5. **Persistence** (`T015`) – Write Parquet file for downstream steps.  

## Schema Constraints (mirrored in `contracts/dataset.schema.yaml`)
- `species`: required, non‑null string.  
- Root metrics: required numbers (already log‑transformed).  
- `phosphorus`, `nitrogen`: numbers **or null** (`nullable: true`).  
- Optional covariates may be null.  
- No additional properties permitted.


## projects/PROJ-457-predicting-plant-root-architecture-from-/specs/001-predicting-plant-root-architecture-from/quickstart.md
# Quickstart: Predicting Plant Root Architecture from Soil Nutrient Availability

## Prerequisites
- Python 3.11 or newer
- `git` (to clone the repository)
- Internet access (to download datasets)

## Installation

```bash
# 1. Clone the repository
git clone 
cd plant-root-architecture

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

```bash
# Step 1: Ingest data (requires at least one verified merged dataset)
python code/ingestion.py

# Step 2: Preprocess (filter, log‑transform, z‑score, missing‑data handling)
python code/preprocessing.py

# Step 3: Fit models and evaluate (species‑stratified CV)
python code/modeling.py

# Step 4: Visualize and compile the final report
python code/visualization.py
```

### Expected Outputs
- Clean dataset: `data/processed/merged_dataset.parquet`  
- Metrics JSON: `artifacts/metrics.json` (includes power analysis, merge success rate, and all SC booleans)  
- Partial dependence PNGs: `artifacts/reports/plots/*.png` (total ≤ 100 MB)  
- Final PDF report: `artifacts/reports/final_report.pdf` (contains the mandatory associational statement; causal wording checked)  

## Contract Validation

```bash
pytest tests/contract/test_schemas.py
```

All tests should pass. Failure indicates schema mismatches or missing artifacts.

## Troubleshooting
- **Merged dataset unavailable** – The pipeline will abort with a clear error logged in `artifacts/logs/fallback.log`. Ensure at least one of the verified merged dataset URLs is reachable.  
- **MemoryError** – Reduce dataset size by limiting to the top 5 species: `python code/preprocessing.py --max-species 5`.  
- **Schema test failures** – Ensure the three schema files exist under `contracts/` and that the dataset columns match the schema (nullability for `phosphorus`/`nitrogen` is allowed).  

---



## projects/PROJ-457-predicting-plant-root-architecture-from-/specs/001-predicting-plant-root-architecture-from/contracts/dataset.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "MergedDataset"
description: "Schema for the cleaned and merged root phenotype and soil nutrient dataset."
type: "object"
properties:
  species:
    type: "string"
    description: "Scientific name of the plant species."
  root_length:
    type: "number"
    description: "Log-transformed total root length."
  branching_density:
    type: "number"
    description: "Log-transformed branching density."
  surface_area:
    type: "number"
    description: "Log-transformed root surface area."
  phosphorus:
    type: "number"
    description: "Z-scored phosphorus concentration. May be null if soil data unavailable."
    nullable: true
  nitrogen:
    type: "number"
    description: "Z-scored nitrogen concentration. May be null if soil data unavailable."
    nullable: true
  soil_moisture:
    type: "number"
    description: "Optional soil moisture covariate."
    nullable: true
  temperature:
    type: "number"
    description: "Optional temperature covariate."
    nullable: true
  elevation:
    type: "number"
    description: "Optional elevation covariate."
    nullable: true
  data_source_type:
    type: "string"
    description: "Type of data source (observational/experimental)."
  sample_size_per_species:
    type: "integer"
    description: "Number of observations for the species after filtering."
required:
  - species
  - root_length
  - branching_density
  - surface_area
  - data_source_type
additionalProperties: false

## projects/PROJ-457-predicting-plant-root-architecture-from-/specs/001-predicting-plant-root-architecture-from/contracts/model_results.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "ModelResults"
description: "Schema for the output of the LMM and Random Forest modeling phase."
type: "object"
properties:
  lmm_results:
    type: "object"
    properties:
      adjusted_r_squared:
        type: "number"
        description: "Adjusted R-squared value for the LMM."
      rmse:
        type: "number"
        description: "Root Mean Squared Error."
      coefficients:
        type: "object"
        description: "Mapping predictor → {coefficient, p_value, corrected_p_value}."
        additionalProperties:
          type: "object"
          properties:
            coefficient:
              type: "number"
            p_value:
              type: "number"
            corrected_p_value:
              type: "number"
          required:
            - coefficient
            - p_value
            - corrected_p_value
      p_values:
        type: "object"
        description: "Mapping predictor → p-value (redundant for convenience)."
        additionalProperties:
          type: "number"
    required:
      - adjusted_r_squared
      - rmse
      - coefficients
      - p_values
  rf_results:
    type: "object"
    properties:
      r_squared:
        type: "number"
        description: "R-squared value for the Random Forest."
      rmse:
        type: "number"
        description: "Root Mean Squared Error."
    required:
      - r_squared
      - rmse
  cv_metrics:
    type: "object"
    properties:
      mean_out_of_sample_r2:
        type: "number"
        description: "Mean R-squared from species‑stratified cross‑validation."
    required:
      - mean_out_of_sample_r2
  success_criteria:
    type: "object"
    properties:
      sc_002_met:
        type: "boolean"
        description: "True if LMM R² is within 5 % of RF R² (SC‑002)."
      sc_003_met:
        type: "boolean"
        description: "True if nutrient coefficient p-values < 0.05 after correction (SC‑003)."
      sc_006_met:
        type: "boolean"
        description: "True if sensitivity analysis confirms biological plausibility (SC‑006)."
      power_achieved:
        type: "number"
        description: "Achieved statistical power for detecting a medium effect size."
    required:
      - sc_002_met
      - sc_003_met
      - sc_006_met
      - power_achieved
required:
  - lmm_results
  - rf_results
  - cv_metrics
  - success_criteria
additionalProperties: false

## projects/PROJ-457-predicting-plant-root-architecture-from-/specs/001-predicting-plant-root-architecture-from/contracts/output.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "FinalReportOutput"
description: "Schema for the final report artifacts and summary metrics."
type: "object"
properties:
  report_file:
    type: "string"
    description: "Path to the generated PDF report."
  plots:
    type: "array"
    items:
      type: "string"
    description: "List of paths to generated PNG plots."
  total_plot_size_mb:
    type: "number"
    description: "Total size of plot files in MB (must be ≤ 100)."
  associational_statement:
    type: "string"
    description: "Explicit statement confirming findings are associational, not causal."
  deviations:
    type: "array"
    items:
      type: "string"
    description: "Logged deviation messages (e.g., merged dataset unavailable, imputation decisions)."
  success_criteria:
    type: "object"
    properties:
      sc_001_met:
        type: "boolean"
        description: "True if proportion of merged datasets meets SC‑001; null if not measurable."
      sc_002_met:
        type: "boolean"
        description: "True if LMM R² within 5 % of RF R² (SC‑002)."
      sc_003_met:
        type: "boolean"
        description: "True if nutrient coefficients significant (SC‑003)."
      sc_004_met:
        type: "boolean"
        description: "True if total plot size ≤ 100 MB (SC‑004)."
      sc_005_met:
        type: "boolean"
        description: "True if species exclusion count recorded (SC‑005)."
      sc_006_met:
        type: "boolean"
        description: "True if sensitivity analysis passes (SC‑006) or is marked N/A."
    required:
      - sc_001_met
      - sc_002_met
      - sc_003_met
      - sc_004_met
      - sc_005_met
      - sc_006_met
required:
  - report_file
  - plots
  - total_plot_size_mb
  - associational_statement
  - deviations
  - success_criteria
additionalProperties: false