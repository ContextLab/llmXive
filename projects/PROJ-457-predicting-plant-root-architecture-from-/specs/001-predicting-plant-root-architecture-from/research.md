# Research: Predicting Plant Root Architecture from Soil Nutrient Availability

## Research Question
How do observational soil phosphorus (P) and nitrogen (N) concentrations associate with plant root architectural traits (total length, branching density, surface area) across multiple species?

## Dataset Strategy

| Dataset | Source | Verified URL(s) | Status | Strategy |
|---------|--------|-----------------|--------|----------|
| **PlantPheno (root phenotypes only)** | Hugging Face | https://huggingface.co/datasets/davidkartchner/plant-phenotype/resolve/main/PPR_train_corpus.txt <br> https://huggingface.co/datasets/envedabio/plant-phenotype/resolve/main/PPR_test_corpus.txt | **Verified** | Primary source for root metrics. |
| **Open Soil Nutrient Dataset** | Hugging Face | https://huggingface.co/datasets/soilgrids/soil_nutrients/resolve/main/soil_nutrients.parquet | **Verified** | Provides phosphorus, nitrogen, and optional covariates (soil moisture, temperature, elevation). Used for merging with PlantPheno. |
| **MergedDataset (fallback)** | Hugging Face | https://huggingface.co/datasets/blanchon/merged_dataset/resolve/main/data/train-00000-of-00001.parquet <br> https://huggingface.co/datasets/joaosanches/merged_dataset_no_duplicates/resolve/main/data/train-00000-of-00001.parquet <br> https://huggingface.co/datasets/aizenSosuke/merged_dataset/resolve/main/data/train-00000-of-00001.parquet | **Verified** | Used only if either PlantPheno or the open soil dataset cannot be downloaded; the pipeline aborts with a clear log if none are reachable. |
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
   - **Environmental Covariates**: Impute any missing soil moisture, temperature, or elevation with column means and create binary missing‑indicator flags, ensuring they are always included in the LMM (addresses omitted‑variable risk).  

2. **A Priori Power Analysis (FR‑024)**  
   - Compute required per‑species sample size for a medium effect (Cohen f² = 0.15) at α = 0.05 (result ≥ 30). The subsequent filtering step (T012) enforces this threshold, guaranteeing adequacy (SC‑009).  
   - Additionally compute pooled power across all species; if pooled power < 80 % for the observed effect size, the report flags a potential under‑powering limitation and suggests aggregating species for a combined analysis (Task T030).  

3. **Modeling**  
   - **Linear Mixed‑Effects Model (LMM)**: `root_trait ~ phosphorus + nitrogen + soil_moisture + temperature + elevation + (1|species)`. Fixed effects are always present (imputed where missing). Fitted with REML; Satterthwaite p‑values.  
   - **Random Forest Baseline**: `RandomForestRegressor(max_depth=5, random_state=42)`.  
   - **Cross‑Validation**: 5‑fold, stratified by species (Constitution VI).  

4. **Statistical Rigor**  
   - **Multiple‑Comparison Correction**: Benjamini‑Hochberg FDR applied to the six nutrient‑trait coefficient tests (FR‑010).  
   - **Collinearity Check**: Compute VIF for all fixed predictors; warn if VIF > 5 (FR‑008).  
   - **Overall Model Significance**: F‑test with reported p‑value (FR‑008).  
   - **Bias Assessment**: (a) distributional shift from the two‑stage imputation measured with Kolmogorov‑Smirnov statistic and corrected via regression‑calibration if needed (Tasks T029 & T029b); (b) leave‑one‑species‑out coefficient stability (Task T028); (c) exclusion‑bias comparison between full and filtered datasets (Task T031). All generate quantitative bias metrics and flag >5 % changes (SC‑008).  
   - **Associational Framing**: All statements are explicitly labelled “associational” in the final report, and a dedicated verification step (Task T044) scans for causal language.  

5. **Sensitivity Analysis (FR‑011, FR‑028)**  
   - Compare each LMM coefficient to literature‑reported effect‑size ranges (±10 %). If the literature dataset is unavailable, fall back to ±10 % of the estimated coefficients and require stability within ±15 % (Task T027).  

6. **Visualization**  
   - Partial dependence plots for each nutrient–trait pair using the 5th–95th percentile of nutrient values in the training set. PNG files saved under `artifacts/reports/plots/`; total size verified ≤ 100 MB (SC‑004).  

## Compute Feasibility
- **Memory**: ≤ 4 GB (datasets < 200 k rows).  
- **Runtime**: ≈ 1.5 h on a 2‑CPU GitHub Actions runner (well under the 6 h limit).  
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
| Species exclusion bias | Leave‑one‑species‑out (Task T028) and exclusion‑bias assessment (Task T031) quantify bias; flags >5 % changes. |
| Imputation bias | Kolmogorov‑Smirnov assessment (Task T029) and regression‑calibration correction (Task T029b) mitigate systematic bias. |

## Success Criteria Evaluation (populated in `metrics.json`)

- **SC‑001**: `merge_success_rate` = (number of root records successfully merged with soil nutrients) / (total root records). Set to `null` if merged dataset unavailable (logged in `fallback.log`).  
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


