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
| No merged dataset reachable | The pipeline aborts with a clear logged error (Task T008); this prevents fabricating nutrient data. |
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

