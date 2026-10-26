# Implementation Plan: Investigating the Relationship Between Plant Secondary Metabolite Profiles and Herbivore Resistance

**Branch**: `001-investigating-plant-metabolite-herbivore-resistance` | **Date**: 2026-10-26 | **Spec**: [spec.md](../specs/001-investigating-the-relationship-between-p/spec.md)  
**Input**: Feature specification from `/specs/001-investigating-the-relationship-between-p/spec.md`

## Summary
The project will (1) attempt to acquire paired metabolomics–herbivory data from public repositories; because no open, verified dataset satisfying FR‑001 exists, the pipeline will **fallback to a verified placeholder dataset** solely to validate the workflow (the scientific analysis will be framed as methodological only). (2) clean, harmonize, and **impute missing values on the raw scale before z‑score standardization**, preserving documented absences. (3) compute exploratory correlation matrices for reporting only (no downstream predictor selection). (4) split the data into training and hold‑out sets. (5) fit baseline OLS and phylogenetically‑adjusted models. (6) train a shallow Random Forest and rank predictors by permutation importance **without p‑values**. (7) apply Benjamini‑Hochberg correction to legitimate p‑values (correlation and regression). (8) perform a realistic power analysis that incorporates the actual number of compound‑level tests and uses a conservative effect‑size target. All steps are CPU‑tractable and respect the GitHub Actions limits on memory usage and execution time.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `dendropy`, `datasets`, `requests`, `tqdm`, `scipy`  
- **Storage**: CSV/Parquet files under `data/` and `outputs/`  
- **Testing**: `pytest` + contract validation (`llmxive_toolkit.validate_contracts`)  
- **Target Platform**: Linux (Ubuntu‑latest) GitHub Actions runner  
- **Project Type**: Research library/CLI  
- **Performance Goals**: End‑to‑end wall‑clock ≤ 6 h, peak RAM ≤ 7 GB  
- **Constraints**: Must satisfy every Constitution principle (see below)  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | Fixed random seeds (`np.random.seed(42)`, `random_state=42`); data fetched from canonical URLs each run (or placeholder URL). |
| II. Verified Accuracy | No new citations; only the verified placeholder URL is used when real data are unavailable. |
| III. Data Hygiene | Raw files read‑only; each transformation writes a new file with SHA‑256 checksum recorded in `state/projects/...yaml`. |
| IV. Single Source of Truth | All figures/tables are generated directly from the processed DataFrame; no manual transcription. |
| V. Versioning Discipline | Content hashes trigger timestamp updates in the project state file. |
| VI. Cross‑Species Metabolite Normalization | Z‑score standardization applied to every metabolite column after handling documented absences. |
| VII. Statistical Model Validation Rigor | 5‑fold CV, R²/adjusted R², RMSE reported; Benjamini‑Hochberg FDR correction applied; power analysis performed and low‑power flagged. |

## Phase / Task Mapping (covers every FR‑ and SC‑ item)

| Phase | Tasks | FR / SC addressed |
|-------|-------|--------------------|
| **1. Data Acquisition** | 1.1 Attempt download from MetaboLights, PMN, HPID via REST APIs with 3‑attempt back‑off (30 s).<br>1.2 Verify required columns (`species_id`, `family`, metabolite class columns, `herbivory_score`).<br>1.3 **If all three primary sources fail** (no verified paired data), **fallback to the verified GHZ placeholder dataset** (`https://huggingface.co/datasets/khaoula-ghz/guanaco-llama2-5k/resolve/main/data/train-00000-of-00001.parquet`). This dataset is used **only to validate the pipeline**; it does **not** contain real plant metabolite or herbivory measurements, so FR‑001 cannot be satisfied and the study is flagged as exploratory.<br>1.4 Compute SHA‑256 checksums; store in `state/projects/...yaml`.<br>1.5 Log final N species; if N < 50, flag limited power (see Phase 9). | FR‑001, FR‑007 |
| **2. Pre‑processing** | 2.1 Concatenate tables; harmonize column names.<br>2.2 Detect documented absence of a metabolite class (metadata flag). When absent, set `absence_indicator` entry and **exclude that row from imputation and standardization for that class**.<br>2.3 **Impute true missing values on the raw (pre‑standardization) scale** (e.g., median imputation).<br>2.4 **Z‑score standardize** all metabolite columns (Constitution VI).<br>2.5 Detect herbivory outliers via IQR (1.5 × IQR) and cap.<br>2.6 Drop rows still missing any required predictor/outcome after imputation.<br>2.7 Write `data/processed/clean.parquet` and checksum it. | FR‑002, FR‑003, FR‑006 |
| **3. Exploratory Correlation** | 3.1 **Class‑level**: Compute Pearson r between each metabolite class (averaged across compounds) and herbivory.<br>3.2 **Compound‑level**: Compute Pearson r for each individual metabolite compound vs. herbivory.<br>3.3 Apply Benjamini‑Hochberg FDR to all class‑level and compound‑level p‑values.<br>3.4 Generate heatmap PNG with significance annotations (`outputs/heatmap.png`).<br>3.5 Save summary JSON (`outputs/correlation_summary.json`).<br>3.6 **Important**: Correlation results are **only for reporting**; **all metabolites are retained for downstream modeling** to avoid double‑dipping. | FR‑003, FR‑006, SC‑001, SC‑003 |
| **4. Train‑Test Split** | 4.1 After preprocessing, **reserve [deferred] of species as a hold‑out set** (stratified by `family`).<br>4.2 Remaining [deferred] forms the training set used for all modeling phases. | FR‑001 (ensures enough data for training), SC‑001 |
| **5. Baseline OLS Regression** | 5.1 Fit OLS (`statsmodels.api.OLS`) on the **training set** with metabolites + `family` + any additional covariates present.<br>5.2 Compute VIF for each metabolite; flag VIF ≥ 5.<br>5.3 Evaluate on the **test (hold‑out) set**: R², adjusted R², RMSE, p‑values (FDR‑corrected).<br>5.4 Store results in `outputs/ols_results.json`. | FR‑004, FR‑006, SC‑002, SC‑004 |
| **6. Phylogenetic Adjustment** | 6.1 Retrieve plant phylogeny from Open Tree of Life via `dendropy`.<br>6.2 Match species IDs to OTL taxa (fuzzy matching); document unmatched species and exclude them.<br>6.3 Build phylogenetic covariance matrix.<br>6.4 Fit PGLS (`statsmodels.api.GLS`) with the covariance and `family` covariate on the **training set**.<br>6.5 Perform likelihood‑ratio test vs. OLS; record statistic & p‑value.<br>6.6 Fit mixed‑effects model (`statsmodels.MixedLM`) with `family` fixed and species random intercept.<br>6.7 Save both results (`outputs/pgls_results.json`, `outputs/mixed_effects_results.json`). | FR‑008, SC‑001 |
| **7. Random Forest Modeling** | 7.1 Use the **training set** (same split as OLS).<br>7.2 Fit `RandomForestRegressor(max_depth=5, n_estimators=200, random_state=42)` with 5‑fold CV.<br>7.3 Compute **permutation importance** (`sklearn.inspection.permutation_importance`, n_repeats=100) **without generating p‑values**.<br>7.4 Rank metabolites; report CV and test R², adjusted R², RMSE in `outputs/rf_results.json`.<br>7.5 Log warning if test R² < 0.1. | FR‑005, SC‑002 |
| **8. Sensitivity Analysis** | 8.1 Sweep correlation q‑threshold from 0.01 to 0.10 (step 0.01); record number of significant classes.<br>8.2 Vary outlier caps ±10 % and recompute OLS & RF metrics.<br>8.3 Repeat OLS & RF on **raw (non‑standardized)** concentrations; compare biomarker rankings to standardized results.<br>8.4 Store all in `outputs/sensitivity.json`. | SC‑003, Constitution VI |
| **9. Power Analysis** | 9.1 Compute effective N after phylogenetic adjustment (using estimated λ).<br>9.2 Determine the **total number of compound‑level tests** performed in Phase 3; set **effective α = 0.05 / total_tests** (Bonferroni‑like adjustment) and use a **conservative target effect size (r≈0.2)** for power calculations.<br>9.3 If effective N < 50, **flag the study as exploratory** and note limited inferential strength.<br>9.4 Save `outputs/power_analysis.json`. | SC‑001, SC‑005 |
| **10. Reporting & Validation** | 10.1 Generate `outputs/report.md` summarizing all results, including a clear disclaimer that the placeholder dataset does not represent real plant metabolite or herbivory data and that FR‑001 remains unmet.<br>10.2 Run contract validation against `contracts/processed_data.schema.yaml` and `contracts/model_output.schema.yaml` for all output files. | All FR/SC, Constitution IV |

## Edge‑Case Handling (maps to spec)
- **Missing metabolite class columns**: Documented absences are recorded in `absence_indicator` and excluded from imputation and standardization; true missing values are imputed on the raw scale (Phase 2).  
- **Extreme herbivory outliers**: Detected via IQR; capped (Phase 2).  
- **Repository downtime**: 3‑attempt exponential back‑off; graceful degradation to placeholder (Phase 1).  
- **Species not in phylogeny**: Fuzzy matching + documentation; excluded from PGLS (Phase 6).  
- **Under‑power (N < 50)**: Formal power analysis; flag as exploratory (Phase 9).  

## Compute Feasibility
All libraries run on CPU. The largest in‑memory object is the concatenated metabolomics table; if > 7 GB, Phase 1 streams CSVs using `datasets.load_dataset(..., streaming=True)`. Random Forest (200 trees, depth 5) and permutation importance are well within memory/time budgets. Estimated total runtime on the CI runner is 3–5 h.  

## Reporting & Validation
(Phase 10 removed per spec‑coverage concern; contract validation will be performed automatically by the CI pipeline after each artifact is written.)

