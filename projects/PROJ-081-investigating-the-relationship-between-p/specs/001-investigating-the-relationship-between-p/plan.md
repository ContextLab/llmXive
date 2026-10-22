# Implementation Plan: Investigating the Relationship Between Plant Secondary Metabolite Profiles and Herbivore Resistance

**Branch**: `001-investigating-plant-metabolite-herbivore-resistance` | **Date**: 2026-10-22 | **Spec**: [spec.md](../specs/001-investigating-plant-metabolite-herbivore-resistance/spec.md)  
**Input**: Feature specification from `/specs/001-investigating-plant-metabolite-herbivore-resistance/spec.md`

## Summary
The project will (1) acquire paired metabolomics–herbivory data (or, if unavailable, run a methodological proof‑of‑concept on a verified placeholder dataset), (2) clean, harmonize, and z‑score‑standardize metabolite concentrations while preserving documented absences as a binary indicator, (3) compute **both class‑level and compound‑level** correlations with herbivory and identify 3‑5 metabolite classes showing significant negative associations, (4) fit baseline OLS (with optional additional covariates) and phylogenetically‑adjusted models (PGLS & mixed‑effects), (5) train a shallow Random Forest and rank metabolites by permutation importance, (6) apply Benjamini‑Hochberg FDR correction to all p‑values, (7) conduct a sensitivity analysis and a formal power analysis, and (8) generate reproducible artifacts validated against JSON schemas. All steps are CPU‑tractable and respect the 7 GB / 6 h GitHub Actions limits.

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
| I. Reproducibility | Fixed random seeds (`np.random.seed(42)`, `random_state=42`); data fetched from canonical URLs each run. |
| II. Verified Accuracy | No new citations; only the verified GHZ placeholder URL is used when real data are unavailable. |
| III. Data Hygiene | Raw files read‑only; each transformation writes a new file with SHA‑256 checksum recorded in `state/projects/...yaml`. |
| IV. Single Source of Truth | All figures/tables are generated directly from the processed DataFrame; no manual transcription. |
| V. Versioning Discipline | Content hashes trigger timestamp updates in the project state file. |
| VI. Cross‑Species Metabolite Normalization | Z‑score standardization applied to every metabolite column after handling documented absences. |
| VII. Statistical Model Validation Rigor | 5‑fold CV, R²/adjusted R², RMSE reported; Benjamini‑Hochberg FDR correction applied; power analysis performed and low‑power flagged. |

## Phase / Task Mapping (covers every FR‑ and SC‑ item)

| Phase | Tasks | FR / SC addressed |
|-------|-------|--------------------|
| **0. Project Setup** | - Create virtualenv from `requirements.txt`<br>- Pin random seeds | – |
| **1. Data Acquisition** | 1.1 Attempt download from MetaboLights, PMN, HPID via REST APIs with 3‑attempt back‑off (30 s).<br>1.2 Verify required columns (`species_id`, `family`, metabolite class columns, `herbivory_score`).<br>1.3 If **all three primary sources fail** (no verified paired data), **fallback to the verified GHZ placeholder dataset** (`).<br>1.4 Compute SHA‑256 checksums; store in `state/projects/...yaml`.<br>1.5 Log final N species; if N < 50, flag limited power (see Phase 8). | FR‑001, FR‑007 |
| **2. Pre‑processing** | 2.1 Concatenate tables; harmonize column names.<br>2.2 Detect documented absence of a metabolite class (metadata flag). When absent, set `absence_indicator` entry and **exclude that row from z‑score calculation for that class**.<br>2.3 After standardization, impute true missing values **with the column mean on the standardized scale** (not literal zero).<br>2.4 Drop rows still missing any required predictor/outcome after imputation.<br>2.5 Detect herbivory outliers via IQR (1.5 × IQR) and cap.<br>2.6 Z‑score standardize all metabolite columns (Constitution VI).<br>2.7 Write `data/processed/clean.parquet` and checksum it. | FR‑002, FR‑003, FR‑006 |
| **3. Exploratory Correlation** | 3.1 **Class‑level**: Compute Pearson r between each metabolite class (averaged across compounds) and herbivory.<br>3.2 **Compound‑level**: Compute Pearson r for each individual metabolite compound vs. herbivory.<br>3.3 Apply Benjamini‑Hochberg FDR to all class‑level and compound‑level p‑values.<br>3.4 Select 3‑5 classes with significant **negative** correlation (q < 0.05).<br>3.5 Generate heatmap PNG with significance annotations (`outputs/heatmap.png`).<br>3.6 Save summary JSON (`outputs/correlation_summary.json`). | FR‑003, FR‑006, SC‑001, SC‑003 |
| **4. Baseline OLS Regression** | 4.1 80/20 split stratified by `family` (train = 0.8, test = 0.2).<br>4.2 Fit OLS (`statsmodels.api.OLS`) with metabolites + `family` + **any additional covariates present** (e.g., plant size, geographic region).<br>4.3 Compute VIF for each metabolite; flag VIF ≥ 5.<br>4.4 Evaluate on test set: R², adjusted R², RMSE, p‑values (FDR‑corrected).<br>4.5 Store results in `outputs/ols_results.json`. | FR‑004, FR‑006, SC‑002, SC‑004 |
| **5. Phylogenetic Adjustment** | 5.1 Retrieve plant phylogeny from Open Tree of Life via `dendropy`.<br>5.2 Match species IDs to OTL taxa (fuzzy matching); document unmatched species and exclude them.<br>5.3 Build phylogenetic covariance matrix.<br>5.4 Fit PGLS (`statsmodels.api.GLS`) with the covariance and `family` covariate.<br>5.5 Perform likelihood‑ratio test vs. OLS; record statistic & p‑value.<br>5.6 Fit mixed‑effects model (`statsmodels.MixedLM`) with `family` fixed and species random intercept.<br>5.7 Save both results (`outputs/pgls_results.json`, `outputs/mixed_effects_results.json`). | FR‑008, SC‑001 |
| **6. Random Forest Modeling** | 6.1 Use same train/test split as OLS.<br>6.2 Fit `RandomForestRegressor(max_depth=5, n_estimators=200, random_state=42)` with 5‑fold CV.<br>6.3 Compute permutation importance (`sklearn.inspection.permutation_importance`, n_repeats=100) and obtain p‑values.<br>6.4 Apply Benjamini‑Hochberg to permutation p‑values.<br>6.5 Rank metabolites; report CV and test R², adjusted R², RMSE in `outputs/rf_results.json`.<br>6.6 Log warning if test R² < 0.1. | FR‑005, SC‑002 |
| **7. Sensitivity Analysis** | 7.1 Sweep correlation q‑threshold from 0.01 to 0.10 (step 0.01); record number of significant classes.<br>7.2 Vary outlier caps ±10 % and recompute OLS & RF metrics.<br>7.3 Repeat OLS & RF on **raw (non‑standardized)** concentrations; compare biomarker rankings to standardized results.<br>7.4 Store all in `outputs/sensitivity.json`. | SC‑003, Constitution VI |
| **8. Power Analysis** | 8.1 Compute effective N after phylogenetic adjustment (using estimated λ).<br>8.2 Estimate power to detect r ≈ 0.3 at α ≈ 0.0125 (BH‑adjusted).<br>8.3 If effective N < 50, **flag the study as exploratory** and note limited inferential strength.<br>8.4 Save `outputs/power_analysis.json`. | SC‑001, SC‑005 |
| **9. Reporting & Validation** | 9.1 Validate `clean.parquet` against `contracts/processed_data.schema.yaml`.<br>9.2 Validate all JSON result files against `contracts/model_output.schema.yaml`.<br>9.3 Assemble `outputs/report.md` linking to all artifacts, including a **clear disclaimer** when the GHZ placeholder dataset is used.<br>9.4 Record total wall‑clock time; enforce ≤ 6 h. | SC‑005 |
| **10. Contract Generation** | 10.1 Create `contracts/model_output.schema.yaml` (covers all AnalysisResult types).<br>10.2 Create `contracts/processed_data.schema.yaml` (covers cleaned DataFrame). | – |

## Edge‑Case Handling (maps to spec)
- **Missing metabolite class columns**: Documented absences are recorded in `absence_indicator` and excluded from standardization; true missing values are imputed after standardization (Phase 2).  
- **Extreme herbivory outliers**: Detected via IQR; capped (Phase 2).  
- **Repository downtime**: 3‑attempt exponential back‑off; graceful degradation to GHZ placeholder (Phase 1).  
- **Species not in phylogeny**: Fuzzy matching + documentation; excluded from PGLS (Phase 5).  

## Compute Feasibility
All libraries run on CPU. The largest in‑memory object is the concatenated metabolomics table; if > 7 GB, Phase 1 streams CSVs using `datasets.load_dataset(..., streaming=True)`. Random Forest (200 trees, depth 5) and permutation importance are well within memory/time budgets. Estimated total runtime on the CI runner is 3–5 h.

--- 