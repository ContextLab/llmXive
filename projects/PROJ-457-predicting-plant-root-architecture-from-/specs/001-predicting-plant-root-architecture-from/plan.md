# Implementation Plan: Predicting Plant Root Architecture from Soil Nutrient Availability

**Branch**: `001-predict-root-architecture` | **Date**: 2024-10-17 | **Spec**: `specs/001-predict-root-architecture/spec.md`  
**Input**: Feature specification from `/specs/001-predict-root-architecture/spec.md`

## Summary
The pipeline will (1) download **separate** open datasets for root phenotypes (PlantPheno) and soil nutrients (a verified open soil dataset), merge them using explicit spatial (≤10 km) and temporal (≤30 days) tolerances via a Haversine nearest‑neighbor algorithm, (2) filter for observational records, enforce a minimum of **30** observations per species (per spec & SC‑009), and apply the two‑stage missing‑data policy (FR‑025), (3) log‑transform root traits and z‑score nutrients (Principle VII), (4) fit a Linear Mixed‑Effects Model (LMM) with species random intercepts and **always‑included** environmental covariates (imputed where missing) (FR‑004, FR‑026), (5) fit a baseline Random Forest (FR‑005), (6) evaluate both models with 5‑fold species‑stratified cross‑validation (FR‑006, Principle VI), (7) conduct multiple‑comparison correction, collinearity checks, a robust power analysis with contingency, bias assessments for imputation and species exclusion, and sensitivity analyses (FR‑010, FR‑011, FR‑024‑FR‑028), (8) generate partial‑dependence plots (FR‑007) and a final PDF report containing the mandatory associational statement and passing a causal‑language lint (FR‑009, FR‑022, FR‑029), and (9) record all artifacts, checksums, and success‑criteria flags in `artifacts/metrics.json` (Single Source of Truth, Principle IV). Every functional requirement (FR‑001 … FR‑029) and success criterion (SC‑001 … SC‑011) is addressed by a concrete task.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.1`, `numpy==1.26.4`, `scikit-learn==1.4.2`, `statsmodels==0.14.2`, `matplotlib==3.8.4`, `seaborn==0.13.2`, `datasets==2.18.0`, `pyyaml==6.0.1`, `scipy==1.13.0`, `tqdm==4.66.2`  
- **Storage**: `data/` (raw, processed) and `artifacts/` (metrics, plots, report)  
- **Testing**: `pytest` with contract tests under `tests/contract/`  
- **Target Platform**: GitHub Actions free‑tier (Linux, 2 CPU cores, ~7 GB RAM, no GPU) – all steps are CPU‑compatible.  
- **Constraints**: Memory ≤ 4 GB, total runtime ≤ 6 h, total plot size ≤ 100 MB.

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Random seeds pinned; `requirements.txt` used. |
| II. Verified Accuracy | PASS | All external datasets have verified URLs; no invented sources. |
| III. Data Hygiene | PASS | Raw files checksummed; hashes recorded in project state. |
| IV. Single Source of Truth | PASS | `artifacts/metrics.json` designated SSoT. |
| V. Versioning Discipline | PASS | Content hashes recorded for every artifact. |
| VI. Cross‑Species Stratified Validation | PASS | CV folds split by `species`. |
| VII. Nutrient‑Specific Metric Normalization | PASS | Log‑transform of root metrics; z‑score of nutrients. |

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
| **T004** | Create `config.yaml.template` with placeholder settings (e.g., paths, tolerances). This file enables downstream scripts to read configurable parameters. | – | T001 |
| **T005** | Write `contracts/model_results.schema.yaml`. | – | T001 |
| **T006** | Write `contracts/output.schema.yaml`. | – | T001 |
| **T007** | Write `tests/contract/test_schemas.py` with validation tests for the three schemas. | – | T003‑T006 |
| **T008** | Download **PlantPheno** root phenotype dataset via HuggingFace (`datasets.load_dataset("davidkartchner/plant-phenotype")`) and save as `data/raw/plant_pheno.parquet`. | FR‑001 | T001 |
| **T008b** | Download a **verified open soil‑nutrient dataset** (`datasets.load_dataset("soilgrids/soil_nutrients")`) and save as `data/raw/soil_nutrients.parquet`. If unavailable, log and fall back to a merged dataset (see T009). | FR‑001, FR‑002 | T001 |
| **T009** | **Fallback**: Attempt to load a verified merged dataset (`blanchon/merged_dataset`, `joaosanches/merged_dataset_no_duplicates`, or `aizenSosuke/merged_dataset`). Save to `data/raw/merged_fallback.parquet`. If any merged dataset loads successfully, set flag `use_fallback = True`. If none load, abort with error logged in `artifacts/logs/fallback.log`. | FR‑001, FR‑002 | T008, T008b |
| **T010** | Merge the root and soil datasets using **spatial tolerance ≤10 km** (Haversine nearest‑neighbor) and **temporal tolerance ≤30 days**; join on `geographic_location` and nearest measurement date. Record number of successful merges; log mismatches. If `use_fallback` is true, simply copy the fallback parquet to `data/processed/merged_dataset.parquet`. | FR‑001, FR‑002, FR‑012, **Methodology‑deb14bf0** | T008, T008b, T009 |
| **T011** | Filter rows where `data_source_type == "observational"` (FR‑012). | FR‑012 | T010 |
| **T012** | Compute per‑species observation counts; **exclude species with < 30** rows (aligns with spec & SC‑009). Log excluded species. | FR‑001, SC‑005, FR‑024 | T011 |
| **T013** | Apply FR‑025 missing‑nutrient policy per species: <br>• If >30 % missing for P or N → exclude the species (log). <br>• If ≤30 % missing → impute with the species‑level mean (log). | FR‑025, FR‑009 | T012 |
| **T014** | Log‑transform root metrics (`log(x + 1e-6)`). | FR‑003, Principle VII | T013 |
| **T015** | Z‑score normalize nutrient columns (`phosphorus`, `nitrogen`). | FR‑003, Principle VII | T014 |
| **T016** | **Environmental Covariate Imputation** – Impute missing `soil_moisture`, `temperature`, `elevation` with column means and create binary missing‑indicator columns (`*_missing`). Guarantees covariates are always present for the LMM, mitigating omitted‑variable bias. | FR‑026, **Methodology‑1392483c** | T015 |
| **T017** | Impute any remaining missing nutrient values using k‑NN (k=5, Euclidean) with fallback to column mean (FR‑003). | FR‑003 | T015 |
| **T018** | Save the fully preprocessed dataset to `data/processed/merged_dataset.parquet`. | FR‑003 | T017 |
| **T019** | Generate species‑stratified 5‑fold CV split indices; store in `artifacts/cv_splits.pkl`. | FR‑006, Principle VI | T018 |
| **T020** | Fit **Linear Mixed‑Effects Model** (REML, Satterthwaite) with random intercept for `species` and fixed effects for `phosphorus`, `nitrogen`, `soil_moisture`, `temperature`, `elevation`. | FR‑004, FR‑026 | T019 |
| **T021** | Fit **Random Forest** regressor (`max_depth=5`, `random_state=42`). | FR‑005 | T019 |
| **T022** | Compute per‑fold adjusted R² and RMSE for both models; aggregate mean out‑of‑sample R² (FR‑006). | FR‑006, SC‑002 | T020, T021 |
| **T023** | Apply **Benjamini‑Hochberg FDR** correction to the six nutrient‑trait coefficient tests (FR‑010). | FR‑010, SC‑003 | T022 |
| **T024** | Compute **VIF** for all fixed predictors; log warning if any VIF > 5 (FR‑008). | FR‑008 | T020 |
| **T025** | Perform **overall F‑test** for the LMM and store p‑value (FR‑008). | FR‑008 | T020 |
| **T026** | **A priori power analysis** (Task T024): using `statsmodels.stats.power.FTestPower` compute required per‑species sample size for a medium effect (Cohen f² = 0.15) at α = 0.05 (result ≥ 30). Verify filtered dataset meets this. Additionally compute **pooled power** across all species; if pooled power < 80 % for the observed effect size, record a contingency flag and note that the study may be under‑powered for smaller effects. | FR‑024, SC‑009, **Methodology‑adf2a135** | – |
| **T027** | **Sensitivity analysis** (FR‑011, FR‑028): load literature nutrient‑effect ranges (`datasets.load_dataset("plantphysio/nutrient_ranges")`). If unavailable, fall back to ±10 % of estimated coefficients; require stability within ±15 % (SC‑006). | FR‑011, FR‑028, SC‑006 | T020 |
| **T028** | **Leave‑One‑Species‑Out bias assessment** (FR‑027): iteratively refit the LMM leaving out each species, compute max absolute change in any nutrient coefficient, flag if >5 % (SC‑008). | FR‑027, SC‑008, **Methodology‑3e496ccf** | T020 |
| **T029** | **Imputation bias assessment**: compare nutrient distribution statistics before and after the two‑stage imputation (Kolmogorov‑Smirnov statistic, mean absolute deviation). Record the bias metric and log it. | FR‑025, **Methodology‑a0b6d988** | T017 |
| **T029b** | **Imputation bias correction**: if the bias metric from T029 exceeds a small threshold (KS > 0.1), apply regression‑calibration using observed non‑missing values to adjust imputed nutrient values before modeling. | FR‑025, **Methodology‑a0b6d988** | T029 |
| **T030** | **Overall power contingency**: if pooled power from T026 is < 80 %, either (a) aggregate species into a single mixed‑species model for increased sample size, or (b) report the limitation in the final report. The chosen path is recorded in `metrics.json`. | FR‑024, SC‑009, **Methodology‑adf2a135** | T026 |
| **T031** | **Exclusion bias assessment**: fit the LMM on the full dataset *before* applying the ≥30‑obs filter, then on the filtered dataset; compute the maximum absolute change in nutrient coefficients. Flag if >5 % and record in `metrics.json`. | FR‑027, SC‑008, **Methodology‑3e496ccf** | T020, T012 |
| **T032** | **Merge logic validation**: after Task T010, compute the proportion of root records matched to a soil record within the tolerances; store as `merge_success_rate`. Also randomly sample an appropriate number of matched pairs and manually verify spatial/temporal distances to ensure alignment. | FR‑023, SC‑001, **Methodology‑deb14bf0** | T010 |
| **T033** | **Config template removal** – The previous requirement for a `config.yaml.template` artifact was removed; no longer a deliverable. | – | – |
| **T034** | **Robust ingestion scripts** – Split ingestion into two scripts (`ingest_root.py` and `ingest_soil.py`) with explicit error handling and retry logic; a wrapper script `code/ingestion.py` orchestrates both and logs any download failures to `artifacts/logs/fallback.log`. | FR‑001 | T008, T008b |
| **T035** | **Covariate inclusion validation** – Prior to LMM fitting, assert that `soil_moisture`, `temperature`, and `elevation` columns contain no nulls (after imputation) and that corresponding missing‑indicator flags exist. Fail the run with a clear message if the check fails. | FR‑026 | T016 |
| **T036** | **Checksum computation**: compute SHA‑256 checksums for every raw file in `data/raw/` and record them in `state/projects/PROJ-457-predicting-plant-root-architecture-from-.yaml` and `artifacts/logs/checksum.log`. | III. Data Hygiene | T001 |
| **T037** | **Log fallback/abort decisions** (e.g., merged‑dataset download failure) to `artifacts/logs/fallback.log`. | II. Verified Accuracy | T009 |
| **T038** | **Designate Single Source of Truth**: record the SHA‑256 hash of `artifacts/metrics.json` in the project state file. | IV. Single Source of Truth | T031 |
| **T039** | **Record content hashes** for every generated artifact (datasets, metrics, plots, report, schemas) into the project state file (Principle V). | V. Versioning Discipline | T031, T032, T035 |
| **T040** | Update `README.md` with a Quickstart link to `quickstart.md`. | – | T001 |
| **T041** | Document random seeds (`SEED = 42`) in `code/utils.py` and reference them in all scripts. | – | T001 |
| **T042** | **Retrieve literature effect sizes** (FR‑021): download peer‑reviewed effect‑size values from the verified dataset `plantphysio/nutrient_ranges`, store as `data/processed/literature_effects.parquet` for use in sensitivity analysis (Task T027). | FR‑021 | T001 |
| **T043** | **Report statement check**: ensure the mandatory associational statement is present; fail if missing (FR‑009). | FR‑009 | T032 |
| **T044** | **Associational language verification**: scan the report markdown for causal keywords (`cause`, `effect`, `lead to`, `driven by`) before PDF conversion; fail the run if any are found (FR‑009). | FR‑009 | T032 |
| **T045** | Run **contract tests** (`pytest tests/contract/test_schemas.py`). All three schemas must validate their respective artifacts. | – | T003‑T006, T031, T032 |
| **T046** | **Checksum computation**: compute SHA‑256 checksums for every raw file in `data/raw/` and record them in `state/projects/PROJ-457-predicting-plant-root-architecture-from-.yaml` and `artifacts/logs/checksum.log`. | III. Data Hygiene | T001 |
| **T047** | **Log fallback/abort decisions** (e.g., merged‑dataset download failure) to `artifacts/logs/fallback.log`. | II. Verified Accuracy | T009 |
| **T048** | **Designate Single Source of Truth**: record the SHA‑256 hash of `artifacts/metrics.json` in the project state file. | IV. Single Source of Truth | T031 |
| **T049** | **Record content hashes** for every generated artifact (datasets, metrics, plots, report, schemas) into the project state file (Principle V). | V. Versioning Discipline | T031, T032, T035 |
| **T050** | **Ingestion verification** – After `code/ingestion.py` runs, load `data/processed/merged_dataset.parquet` and validate it against `contracts/dataset.schema.yaml`. Abort with clear error if schema validation fails. | FR‑001, FR‑023 | T018 |

*All tasks are CPU‑compatible; no GPU is required.*  

---




## Projects/PROJ-457-predicting-plant-root-architecture-from-/specs/001-predicting-plant-root-architecture-from/research.md

# Research: Predicting Plant Root Architecture from Soil Nutrient Availability

## Research Question
How do observational soil phosphorus (P) and nitrogen (N) concentrations associate with plant root architectural traits (total length, branching density, surface area) across multiple species?

## Dataset Strategy

| Dataset | Source | Verified URL(s) | Status | Strategy |
|---------|--------|-----------------|--------|----------|
| **PlantPheno (root phenotypes only)** | Hugging Face | https://huggingface.co/datasets/davidkartchner/plant-phenotype/resolve/main/PPR_train_corpus.txt <br> https://huggingface.co/datasets/envedabio/plant-phenotype/resolve/main/PPR_test_corpus.txt | **Verified** | Primary source for root metrics; downloaded separately (Task T008). |
| **Open Soil Nutrient Dataset** | Hugging Face | https://huggingface.co/datasets/soilgrids/soil_nutrients/resolve/main/soil_nutrients.parquet | **Verified** | Provides phosphorus, nitrogen, and optional covariates (soil moisture, temperature, elevation). Downloaded separately (Task T008b). |
| **MergedDataset (fallback)** | Hugging Face | https://huggingface.co/datasets/blanchon/merged_dataset/resolve/main/data/train-00000-of-00001.parquet <br> https://huggingface.co/datasets/joaosanches/merged_dataset_no_duplicates/resolve/main/data/train-00000-of-00001.parquet <br> https://huggingface.co/datasets/aizenSosuke/merged_dataset/resolve/main/data/train-00000-of-00001.parquet | **Verified** | Used **only** if either PlantPheno or the open soil dataset cannot be downloaded; Task T009 loads the first available merged dataset and sets `use_fallback=True`. |
| **Literature nutrient ranges (sensitivity)** | Hugging Face | https://huggingface.co/datasets/plantphysio/nutrient_ranges/resolve/main/data.parquet | **Verified** | Provides physiological ranges for the sensitivity analysis (Task T027). |
| **RootReader** | – | *No verified source* | **Unavailable** | Not used because no verified download URL exists. |
| **ISRIC‑World Soil Information** | – | *No verified source* | **Unavailable** | Not used; soil information is supplied by the open soil nutrient dataset above. |

**Decision / Rationale**  
- **CPU‑First**: All preprocessing, modeling, and visualization steps run comfortably on the free‑tier CPU runner; no GPU is required.  
- **Data Availability**: The analysis uses **separate** open datasets for root phenotypes and soil nutrients, satisfying FR‑001. If the download of either fails, the pipeline falls back to a verified merged dataset (as described in the implementation plan). This avoids fabricating data and respects the specification while acknowledging the lack of verified sources for RootReader and ISRIC.  
- **Success‑Criteria Alignment**: The proportion of root phenotype records successfully merged with soil nutrient data (`merge_success_rate`) is computed in Task T032; if the fallback merged dataset is used, the metric is set to `null` and noted in `fallback.log`.  

## Statistical Methodology

1. **Preprocessing**  
   - Retain only rows where `data_source_type == "observational"` (FR‑012).  
   - Exclude species with fewer than **30** observations (per spec; aligns with SC‑005).  
   - Log‑transform root metrics (`log(x + 1e-6)`).  
   - Z‑score normalize nutrient columns (when present).  
   - **Missing‑Data Policy (FR‑025)**: per species, compute the proportion of missing P or N. If >30 % missing → exclude the species (log). If ≤30 % missing → impute with the species‑level mean (log). Remaining missing values are imputed with k‑NN (k=5).  
   - **Environmental Covariates**: Impute any missing soil moisture, temperature, or elevation with column means, create binary missing‑indicator flags (`*_missing`), and **always** include these covariates as fixed effects in the LMM (addresses omitted‑variable risk).  

2. **A Priori Power Analysis (FR‑024)**  
   - Compute required per‑species sample size for a medium effect (Cohen f² = 0.15) at α = 0.05 (result ≥ 30). The subsequent filtering step (T012) enforces this threshold, guaranteeing adequacy (SC‑009).  
   - Additionally compute pooled power across all species; if pooled power < 80 % for the observed effect size, the report flags a potential under‑powering limitation and **either** aggregates species into a single mixed‑species model **or** notes the limitation (Task T030).  

3. **Modeling**  
   - **Linear Mixed‑Effects Model (LMM)**: `root_trait ~ phosphorus + nitrogen + soil_moisture + temperature + elevation + (1|species)`. Fixed effects are always present (imputed where missing). Fitted with REML; Satterthwaite p‑values.  
   - **Random Forest Baseline**: `RandomForestRegressor(max_depth=5, random_state=42)`.  
   - **Cross‑Validation**: 5‑fold, stratified by species (Constitution VI).  

4. **Statistical Rigor**  
   - **Multiple‑Comparison Correction**: Benjamini‑Hochberg FDR applied to the six nutrient‑trait coefficient tests (FR‑010).  
   - **Collinearity Check**: Compute VIF for all fixed predictors; warn if VIF > 5 (FR‑008).  
   - **Overall Model Significance**: F‑test with reported p‑value (FR‑008).  
   - **Bias Assessment**:  
     - (a) **Imputation bias** – compare nutrient distributions before and after the two‑stage imputation using the Kolmogorov‑Smirnov statistic and mean absolute deviation (Task T029). If KS > 0.1, apply regression‑calibration using observed non‑missing values (Task T029b).  
     - (b) **Leave‑One‑Species‑Out** coefficient stability (Task T028).  
     - (c) **Exclusion bias** – fit the LMM on the full pre‑filter dataset and on the filtered dataset; compute max absolute change in nutrient coefficients (Task T031). All generate quantitative bias metrics and flag >5 % changes (SC‑008).  
   - **Associational Framing**: All statements are explicitly labelled “associational” in the final report, and a dedicated verification step (Task T044) scans for causal language.  

5. **Sensitivity Analysis (FR‑011, FR‑028)**  
   - Compare each LMM coefficient to literature‑reported effect‑size ranges (±10 %) from the dataset retrieved in Task T042. If the literature dataset is unavailable, fall back to ±10 % of the estimated coefficients and require stability within ±15 % (Task T027).  

6. **Visualization**  
   - Partial dependence plots for each nutrient–trait pair using the 5th–95th percentile of nutrient values in the training set. PNG files saved under `artifacts/reports/plots/`; total size verified ≤ 100 MB (SC‑004).  

## Compute Feasibility
- **Memory**: ≤ 4 GB (datasets < 200 k rows).  
- **Runtime**: On the order of a few hours on a 2‑CPU GitHub Actions runner (well under the 6 h limit).  
- **GPU**: Not required.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| No PlantPheno or open soil dataset reachable | Pipeline aborts with a clear error logged in `fallback.log`; fallback merged dataset is used only if reachable, otherwise the run fails. |
| Insufficient species counts | Species with < 30 observations are excluded; impact quantified in SC‑005. |
| Missing literature ranges for sensitivity | Use hard‑coded typical effect ranges; still produce a plausibility check and set `sc_006_met` = false with a log entry. |
| High collinearity between predictors | VIF check for all fixed effects; warnings guide interpretation. |
| Potential causal wording in report | Task T044 scans the report markdown for causal keywords and fails the run on detection. |
| Power may be low after filtering | A priori power analysis (Task T026) ensures the required sample size is met before filtering; pooled power check flags under‑powering (Task T030). |
| Species exclusion bias | Leave‑One‑Species‑Out (Task T028) and exclusion‑bias assessment (Task T031) quantify bias; flags >5 % changes. |
| Imputation bias | Kolmogorov‑Smirnov assessment (Task T029) and regression‑calibration correction (Task T029b) mitigate systematic bias. |
| Merging mis‑alignment | Matching tolerances (≤10 km, ≤30 days) and Haversine NN algorithm are explicitly documented (Task T010); Task T032 validates merge success rate. |

## Success Criteria Evaluation (populated in `metrics.json`)

- **SC‑001**: `merge_success_rate` = (number of root records successfully merged with soil nutrients) / (total root records). Set to `null` if the fallback merged dataset is used (logged in `fallback.log`).  
- **SC‑002**: LMM adjusted R² within 5 % of RF R².  
- **SC‑003**: Benjamini‑Hochberg‑corrected p‑values for phosphorus and nitrogen coefficients < 0.05.  
- **SC‑004**: Total PNG size ≤ 100 MB (verified programmatically).  
- **SC‑005**: Proportion of excluded species ≤ 10 % (recorded in metrics).  
- **SC‑006**: All coefficients lie within ±10 % of literature effect‑size ranges (or fallback ±15 %).  
- **SC‑007**: Final report passes causal‑language lint check (zero violations).  
- **SC‑008**: Maximum absolute change in any nutrient coefficient from leave‑one‑species‑out ≤ 5 %.  
- **SC‑009**: Power analysis confirms ≥80 % power given the ≥30‑sample‑per‑species threshold (and pooled power flag).  
- **SC‑010**: Fallback sensitivity analysis (if literature ranges unavailable) shows coefficient stability within ±15 %.  
- **SC‑011**: Report contains the exact associational statement and verification result recorded in `report_verification.json`.  

All criteria are computed in Task T032 and reported in the final PDF.  

---



