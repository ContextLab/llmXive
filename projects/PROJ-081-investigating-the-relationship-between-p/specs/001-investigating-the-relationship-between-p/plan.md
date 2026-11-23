# Implementation Plan: Investigating the Relationship Between Plant Secondary Metabolite Profiles and Herbivore Resistance

**Branch**: `001-investigating-plant-metabolite-herbivore-resistance` | **Date**: 2026-10-26 | **Spec**: [spec.md](../specs/001-investigating-the-relationship-between-p/spec.md)  
**Input**: Feature specification from `/specs/001-investigating-the-relationship-between-p/spec.md`

## Summary
The pipeline will (1) attempt to download paired metabolomics‑herbivory data from MetaboLights, PMN, and HPID; if insufficient data (< 50 species) are obtained, it will **fallback to a verified placeholder dataset** (GHZ parquet) solely to demonstrate that the workflow is functional. (2) Clean, harmonize, and z‑score standardize metabolite concentrations while handling documented absences and outliers. (3) Perform exploratory correlation analyses, (4) split data into training/hold‑out sets, (5) fit baseline OLS and phylogenetically‑adjusted models (PGLS & mixed‑effects), (6) train a shallow Random Forest with permutation importance, (7) conduct a sensitivity analysis, (8) run a formal power analysis, and (9) generate a complete report plus contract‑validated artifacts. All steps are CPU‑tractable and respect the GitHub Actions free‑tier limits.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `dendropy`, `datasets`, `requests`, `tqdm`, `scipy`  
- **Storage**: CSV/Parquet under `data/` and `outputs/`  
- **Testing**: `pytest` + `llmxive_toolkit.validate_contracts`  
- **Target Platform**: Ubuntu‑latest GitHub Actions runner (2 vCPU, 7 GB RAM)  
- **Project Type**: Research library/CLI  
- **Performance Goals**: Wall‑clock ≤ 6 h, peak RAM ≤ 7 GB  
- **Constraints**: Must satisfy every Constitution principle; all statistical methods run on CPU (no GPU needed).  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Fixed random seeds (`np.random.seed(42)`, `random_state=42`); data fetched from canonical URLs each run (or placeholder). |
| II. Verified Accuracy | No new citations; only the verified GHZ placeholder URL is used when primary sources fail. |
| III. Data Hygiene | Raw files are read‑only; each transformation writes a new file with SHA‑256 checksum recorded in `state/projects/...yaml`. |
| IV. Single Source of Truth | All figures/tables are generated directly from the processed DataFrame; no manual transcription. |
| V. Versioning Discipline | Content hashes trigger timestamp updates in the project state file. |
| VI. Cross‑Species Metabolite Normalization | Z‑score standardization applied to every metabolite column after imputation. |
| VII. Statistical Model Validation Rigor | 5‑fold CV, R²/adjusted R²/RMSE reported; Benjamini‑Hochberg FDR correction applied; power analysis performed. |

## Phase / Task Mapping (covers every FR‑ and SC‑ item)

| Phase | Tasks | FR / SC addressed |
|-------|-------|--------------------|
| **1. Data Acquisition** | 1.1 Attempt download from MetaboLights, PMN, HPID via REST APIs with 3‑attempt exponential back‑off (30 s).<br>1.2 Verify presence of required columns (`species_id`, `family`, metabolite class columns, `herbivory_score`).<br>1.3 **If any source fails or total paired species < 50**, abort with “insufficient paired data” **or** fall back to the **verified GHZ placeholder dataset** (`https://huggingface.co/datasets/khaoula-ghz/guanaco-llama2-5k/resolve/main/data/train-00000-of-00001.parquet`). The placeholder is used **only to validate the pipeline**; a disclaimer will be added to the final report.<br>1.4 Compute SHA‑256 checksums; store in `state/projects/...yaml`.<br>1.5 Log final species count; if < 50, set `under_power_flag` for later phases. | FR‑001, FR‑007, SC‑001 |
| **2. Pre‑processing** | 2.1 Concatenate all source tables; harmonize column names.<br>2.2 Detect documented absence of a metabolite class (metadata flag). Record in `absence_indicator` and **exclude those rows from imputation/standardization for that class**.<br>2.3 Impute true missing values on the **raw scale** (median of observed values per metabolite).<br>2.4 **Z‑score standardize** all metabolite columns (Constitution VI).<br>2.5 Detect herbivory outliers via IQR (1.5 × IQR) and cap values.<br>2.6 Drop any rows still missing required predictors/outcome after imputation.<br>2.7 Write `data/processed/clean.parquet` and record checksum. | FR‑002, FR‑006, SC‑002 |
| **3. Exploratory Correlation** | 3.1 Compute **class‑level** Pearson r between each metabolite class (average of compounds) and herbivory.<br>3.2 Compute **compound‑level** Pearson r for every individual metabolite vs. herbivory.<br>3.3 Apply **Benjamini‑Hochberg** FDR correction to **all** p‑values.<br>3.4 Generate heatmap PNG (`outputs/heatmap.png`) with significance annotations (color intensity / asterisk).<br>3.5 Save `outputs/correlation_summary.json` listing **3‑5 metabolite classes** showing a **significant negative correlation** (q < 0.05).<br>3.6 **Do not use correlation results for predictor selection**; all metabolites remain for modeling. | FR‑003, FR‑006, SC‑001, SC‑003 |
| **4. Train‑Test Split** | 4.1 Stratify by `family`; reserve **20 %** of species as a **hold‑out validation set** (never used in training or CV).<br>4.2 Remaining 80 % becomes the **training set** for all modeling phases. | FR‑001 (ensures enough data for training), SC‑001 |
| **5. Baseline OLS Regression** | 5.1 Fit OLS (`statsmodels.api.OLS`) on the **training set** with all metabolite predictors, `family` as a covariate, and any additional covariates present.<br>5.2 Compute **VIF** for each predictor; flag any VIF ≥ 5 (SC‑004).<br>5.3 Apply Benjamini‑Hochberg to regression coefficients’ p‑values.<br>5.4 Evaluate on the **hold‑out set**: R², adjusted R², RMSE.<br>5.5 Write `outputs/ols_results.json`. | FR‑004, FR‑006, SC‑002, SC‑004 |
| **6. Phylogenetic Adjustment** | 6.1 Retrieve a **phylogenetic tree** for the species from **Open Tree of Life** via `dendropy`.<br>6.2 Match species IDs (fuzzy matching); unmatched species are documented and excluded from PGLS.<br>6.3 Build the phylogenetic covariance matrix.<br>6.4 Fit **PGLS** (`statsmodels.api.GLS`) using the covariance matrix.<br>6.5 Conduct a **likelihood‑ratio test** vs. the baseline OLS; record statistic & p‑value.<br>6.6 Fit a **mixed‑effects model** (`statsmodels.MixedLM`) with `family` fixed and a species‑level random intercept.<br>6.7 Save `outputs/pgls_results.json` and `outputs/mixed_effects_results.json`. | FR‑008, SC‑001 |
| **7. Random Forest Modeling** | 7.1 Use the **training set** (same split as OLS).<br>7.2 Fit `RandomForestRegressor(max_depth=5, n_estimators=200, random_state=42)` with **5‑fold CV**.<br>7.3 Compute **permutation importance** (`sklearn.inspection.permutation_importance`, n_repeats=100) – **no p‑values** are produced.<br>7.4 Evaluate on the **hold‑out set**: R², adjusted R², RMSE.<br>7.5 Log a warning if test R² < 0.1 (FR‑003 scenario).<br>7.6 Write `outputs/rf_results.json`. | FR‑005, SC‑002 |
| **8. Feature‑Count Limitation (FR‑011)** | 8.1 If the raw feature set exceeds **20 predictors** (more than 5 metabolites per class), compute **variance across species** for each metabolite and retain the **top 5 per class** (total ≤ 20).<br>8.2 Document the selected features in `outputs/selected_features.json`. | FR‑011 |
| **9. External Literature Validation (FR‑009)** | 9.1 **Attempt** to download the PlantCyc defense‑metabolite list. **No verified URL is available**, so the step will **record that the external list could not be fetched** and **skip the overlap calculation**.<br>9.2 The final report will note this limitation explicitly. | FR‑009 (acknowledged as unmet) |
| **10. Sensitivity Analysis** | 10.1 Sweep Benjamini‑Hochberg **q‑threshold** from 0.01 to 0.10 (step 0.01); record number of significant classes.<br>10.2 Vary herbivory outlier caps by ± 10 % and recompute OLS & RF metrics.<br>10.3 Re‑run OLS & RF on **raw (non‑standardized)** concentrations and compare biomarker rankings to the standardized results.<br>10.4 Store all outcomes in `outputs/sensitivity.json`. | SC‑003, Constitution VI |
| **11. Power Analysis** | 11.1 Compute **effective N** after phylogenetic adjustment (λ from the tree).<br>11.2 Determine total number of **compound‑level tests** from Phase 3; set **effective α = 0.05 / total_tests** (Bonferroni‑like) and adopt a **conservative target effect size (r≈0.2)**.<br>11.3 Estimate power for OLS, PGLS, and RF using `statsmodels.stats.power` utilities.<br>11.4 If effective N < 50, set `under_power_flag: true` and label the study exploratory.<br>11.5 Write `outputs/power_analysis.json`. | SC‑001, SC‑005 |
| **12. Reporting & Contract Validation** | 12.1 Assemble `outputs/report.md` summarizing all results, including a **clear disclaimer** when the placeholder dataset is used and when FR‑009 cannot be satisfied.<br>12.2 Run `llmxive_toolkit.validate_contracts` against `contracts/processed_data.schema.yaml` and `contracts/model_output.schema.yaml` for every output file; abort on any validation error.<br>12.3 Archive all artifacts under `outputs/` with SHA‑256 checksums recorded in the project state file. | All FR/SC, Constitution IV |

## Edge‑Case Handling (maps to spec)
- **Missing metabolite‑class columns** → recorded in `absence_indicator`; excluded from imputation/standardization.  
- **Extreme herbivory outliers** → IQR‑based capping (Phase 2).  
- **Repository downtime** → 3‑attempt back‑off; graceful fallback to placeholder.  
- **Species not in phylogeny** → fuzzy matching; unmatched species omitted from PGLS with documentation.  
- **Under‑power (N < 50)** → formal flag; results framed as hypothesis‑generating.  

## Compute Feasibility
All steps run on CPU; the largest in‑memory object is the concatenated metabolomics table, streamed if > 7 GB. Random Forest (200 trees, depth 5) and permutation importance are well within RAM/time limits. Expected total runtime on the free GitHub Actions runner: **3–5 h**.

---
