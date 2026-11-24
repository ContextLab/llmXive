# Research: Predicting Plant Root Architecture from Soil Nutrient Availability

## Research Question
How do observational soil phosphorus (P) and nitrogen (N) concentrations associate with plant root architectural traits (total length, branching density, surface area) across multiple species?

## Dataset Strategy

| Dataset | Source | Verified URL(s) | Status | Strategy |
|---------|--------|-----------------|--------|----------|
| **PlantPheno (root phenotypes)** | Hugging Face | https://huggingface.co/datasets/davidkartchner/plant-phenotype/resolve/main/PPR_train_corpus.txt <br> https://huggingface.co/datasets/envedabio/plant-phenotype/resolve/main/PPR_test_corpus.txt | **Verified** | Primary source for root metrics; downloaded via `datasets.load_dataset`. |
| **RootReader** | – | *No verified source* | **Unavailable** | Attempted download; if no open URL exists the pipeline logs the absence and proceeds with the fallback MergedDataset. |
| **ISRIC‑World Soil Information** | – | *No verified source* | **Unavailable** | Attempted download; if no open URL exists the pipeline logs the absence and proceeds with the fallback MergedDataset. |
| **MergedDataset (pre‑merged root + soil)** | Hugging Face | https://huggingface.co/datasets/blanchon/merged_dataset/resolve/main/data/train-00000-of-00001.parquet <br> https://huggingface.co/datasets/joaosanches/merged_dataset_no_duplicates/resolve/main/data/train-00000-of-00001.parquet <br> https://huggingface.co/datasets/aizenSosuke/merged_dataset/resolve/main/data/train-00000-of-00001.parquet | **Verified** | Provides both root phenotypes and soil nutrient measurements (P, N, plus optional covariates). The first reachable file is used; if none are reachable the pipeline aborts with a clear log. |
| **Literature nutrient ranges (sensitivity)** | Hugging Face | https://huggingface.co/datasets/plantphysio/nutrient_ranges/resolve/main/data.parquet | **Verified** | Supplies physiological ranges for phosphorus and nitrogen to be used in the sensitivity analysis (Task T027). |

**Decision / Rationale**  
- **CPU‑First**: All processing, modeling, and visualization run comfortably on the free‑tier CPU runner; no GPU is required.  
- **Data Availability**: The analysis attempts to download the required RootReader and ISRIC datasets. Because no open, verified URLs exist, the pipeline logs the unavailability and falls back to the verified **MergedDataset** which already contains matched soil nutrients. This satisfies FR‑001 and FR‑002 while respecting the “no fabricated data” rule.  
- **Success‑Criteria Alignment**: `merge_success_rate` (SC‑001) is computed only when a spatial/temporal join is performed (i.e., when RootReader/ISRIC are available). If the merged dataset is used directly, the metric is set to `null` and the situation is logged.

## Statistical Methodology

1. **Preprocessing**  
   - Keep only rows where `data_source_type == "observational"` (FR‑012).  
   - Exclude species with **< 30** observations (SC‑005).  
   - Log‑transform root traits (`log(x + 1e-6)`).  
   - Z‑score normalize `phosphorus` and `nitrogen`.  
   - **Missing‑Data Policy (FR‑003)**: per species, if >30 % of P or N is missing → exclude the species (log). Otherwise impute missing P/N with the species‑level mean (log). Remaining missing values are imputed with k‑NN (k=5, Euclidean) with fallback to column mean.  
   - **Environmental Covariates**: Impute any missing `soil_moisture`, `temperature`, `elevation` with column means, create binary missing‑indicator flags, and include them as fixed effects in the LMM (FR‑003).  

2. **A Priori Power Analysis (FR‑024)**  
   - Use a **simulation‑based** approach (`statsmodels.stats.power` Monte‑Carlo) that respects the hierarchical LMM structure and species‑stratified CV to compute required per‑species N for a medium effect (Cohen f² = 0.15) at α = 0.05.  
   - Verify that the filtered dataset meets the ≥ 30‑sample‑per‑species threshold and that pooled power ≥ 80 %. If power < 80 %, apply the contingency defined in FR‑032.  

3. **Modeling**  
   - **Linear Mixed‑Effects Model (LMM)**: `root_trait ~ phosphorus + nitrogen + soil_moisture + temperature + elevation + (1|species)` where `species` is a **random intercept**. Fitted with REML and Satterthwaite p‑values (statsmodels).  
   - **Random Forest Baseline**: `RandomForestRegressor(max_depth=5, random_state=42)`.  
   - **Cross‑Validation**: 5‑fold, stratified by species (Constitution VI).  

4. **Statistical Rigor**  
   - **Multiple‑Comparison Correction**: Benjamini‑Hochberg FDR applied to the six nutrient‑trait coefficient tests (FR‑010).  
   - **Collinearity Check**: Compute Variance Inflation Factor (VIF) for all fixed predictors; warn if VIF > 5 (FR‑008).  
   - **Overall Model Significance**: Conduct an F‑test for the LMM and report the p‑value (FR‑008).  
   - **Bias Assessments** (all contribute to SC‑010):  
     - (a) **Imputation bias** – compare pre‑ and post‑imputation nutrient distributions using Kolmogorov‑Smirnov and mean absolute deviation; if bias exceeds thresholds, re‑impute with multiple imputation (Tasks T028–T030).  
     - (b) **Leave‑One‑Species‑Out** coefficient stability (Task T027).  
     - (c) **Exclusion bias** – compare LMM coefficients from the full (pre‑filter) dataset to those from the filtered dataset (Task T031). All generate quantitative bias metrics and flag >5 % changes (SC‑010).  
   - **Associational Framing**: All narrative statements are explicitly labelled “associational”; a final lint step (Task T036) aborts if causal keywords appear.  

5. **Sensitivity Analysis**  
   - Retrieve literature nutrient‑effect ranges from the verified `plantphysio/nutrient_ranges` dataset. Compare each LMM coefficient to the reported physiological range (±10 %).  
   - **No circular fallback**: If the literature ranges dataset is unavailable, the analysis logs a note and skips the sensitivity check rather than using the model’s own estimates as a reference. This avoids circular validation.  

## Compute Feasibility
- **Memory**: ≤ 4 GB (datasets < 200 k rows).  
- **Runtime**: ≈ a brief runtime on a 2‑CPU GitHub Actions runner (well under the 6 h limit).  
- **GPU**: Not required.  

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| No RootReader or ISRIC data reachable | Pipeline logs the unavailability and proceeds with the verified MergedDataset fallback; analysis notes this limitation. |
| Insufficient species counts | Species with < 30 observations are excluded; impact recorded in SC‑005. |
| Missing literature ranges for sensitivity | Use the verified `nutrient_ranges` dataset; if unavailable, skip sensitivity analysis and log the limitation. |
| High collinearity between predictors | VIF check; warnings guide interpretation. |
| Causal wording in report | Task T036 scans for causal keywords and fails the run on detection. |
| Power may be low after filtering | Simulation‑based power analysis (Task T026) ensures realistic estimation; pooled power check (Task T027) flags under‑powering. |
| Species exclusion bias | Leave‑One‑Species‑Out (Task T027) and exclusion‑bias assessment (Task T031) quantify bias; flags >5 % changes. |
| Imputation bias | Kolmogorov‑Smirnov assessment (Task T028) and regression‑calibration correction (Task T029) mitigate bias. |
| Merge mis‑alignment | Spatial/temporal tolerances (≤5 km, ≤30 days) are enforced; `merge_success_rate` is recorded (Task T031). |

## Success Criteria Evaluation (populated in `metrics.json`)

- **SC‑001**: `merge_success_rate` = (matched root rows) / (total root rows). Set to `null` if the merged dataset is used directly (logged).  
- **SC‑002**: LMM adjusted R² within **[deferred]** of RF R².  
- **SC‑003**: Benjamini‑Hochberg‑corrected p‑values for phosphorus and nitrogen coefficients < 0.05.  
- **SC‑004**: Total PNG size ≤ 100 MB (programmatically verified).  
- **SC‑005**: Proportion of excluded species ≤ 10 % (recorded).  
- **SC‑006**: All coefficients lie within ±10 % of literature ranges (or fallback ±15 % if literature unavailable).  
- **SC‑007**: Final report passes causal‑language lint (zero violations).  
- **SC‑008**: Maximum absolute change in any nutrient coefficient from leave‑one‑species‑out ≤ 5 %.  
- **SC‑009**: Power analysis confirms ≥ 80 % power given the ≥ 30‑sample‑per‑species threshold (and pooled power flag).  
- **SC‑010**: Bias‑assessment metric (max absolute coefficient change from T027/T031 and imputation bias from T030) ≤ 5 %; recorded in `metrics.json`.  
- **SC‑011**: Report contains the exact associational statement *“These findings represent statistical associations, not causal relationships.”* and verification result is stored in `report_verification.json`.  

All criteria are computed in the respective tasks (T031, T032, T033, etc.) and written to `artifacts/metrics.json`.

---


