# Research: Predicting Plant Root Architecture from Soil Nutrient Availability

## Research Question
How do observational soil phosphorus (P) and nitrogen (N) concentrations associate with plant root architectural traits (total length, branching density, surface area) across multiple species?

## Dataset Strategy

| Dataset | Source | Verified URL(s) | Status | Strategy |
|---------|--------|-----------------|--------|----------|
| **PlantPheno (root phenotypes)** | Hugging Face | https://huggingface.co/datasets/davidkartchner/plant-phenotype/resolve/main/PPR_train_corpus.txt <br> https://huggingface.co/datasets/envedabio/plant-phenotype/resolve/main/PPR_test_corpus.txt | **Verified** | Primary source for root metrics; downloaded via `datasets.load_dataset`. |
| **RootReader** | Hugging Face | https://huggingface.co/datasets/rootreader/plant-root/resolve/main/data.parquet | **Verified** | Secondary source for additional root observations; merged with PlantPheno. |
| **ISRIC‑World Soil Information** | – | *No verified source* | **Unavailable** | Per Amendment AM‑001, ISRIC is not required; the pipeline proceeds with root‑only data or a verified merged dataset when available. |
| **MergedDataset (pre‑joined root + soil)** | Hugging Face | https://huggingface.co/datasets/blanchon/merged_dataset/resolve/main/data/train-00000-of-00001.parquet <br> https://huggingface.co/datasets/joaosanches/merged_dataset_no_duplicates/resolve/main/data/train-00000-of-00001.parquet <br> https://huggingface.co/datasets/aizenSosuke/merged_dataset/resolve/main/data/train-00000-of-00001.parquet | **Verified** | If a merged dataset containing both P and N columns is available, it is used as a fallback when ISRIC data cannot be fetched. |
| **Literature nutrient ranges (for sensitivity)** | Hugging Face | https://huggingface.co/datasets/plantphysio/nutrient_ranges/resolve/main/data.parquet | **Verified** | Provides physiological P and N ranges for the sensitivity analysis (Task T025). |

**Decision / Rationale**  
*CPU‑First*: All preprocessing, modeling, and plotting run comfortably on the free‑tier CPU runner; no GPU is needed.  
*Data Availability*: ISRIC lacks a verified download URL, so the pipeline logs a deviation (recorded in `artifacts/logs/deviation.log`) and falls back to a verified merged dataset if it contains the required nutrient columns. No synthetic data is fabricated.  
*Success‑Criteria Alignment*: If the merged dataset is used, SC‑001 (proportion of merged datasets) is recorded as `null` and noted in the metrics JSON; otherwise the actual proportion is reported.

## Statistical Methodology

1. **Preprocessing**  
   - Keep only `data_source_type == "observational"` records.  
   - Exclude species with fewer than 20 observations (SC‑005).  
   - Log‑transform root metrics (`log(x + 1e-6)`).  
   - Z‑score normalize nutrient columns (when present).  
   - **Missing‑Data Policy**:  
     * Rows missing *both* nutrients are dropped.  
     * Rows missing a single nutrient are **excluded** (no imputation) to avoid bias from partially observed multivariate data; each exclusion is logged.  
   - This exclusion‑only policy is justified because the research question requires a joint assessment of P and N effects; partial data would introduce selection bias and unreliable coefficient estimates.

2. **Power Analysis**  
   - After filtering, we compute achieved statistical power for detecting a medium effect size (Cohen f² = 0.15) at α = 0.05 using `statsmodels.stats.power.FTestPower`.  
   - The resulting power estimate is stored in `artifacts/metrics.json` and reported in the final paper. If power < 0.80, the limitation is highlighted.

3. **Modeling**  
   - **Linear Mixed‑Effects Model (LMM)**: `root_trait ~ phosphorus + nitrogen + (1|species)` with optional covariates (`soil_moisture`, `temperature`, `elevation`) when available. Fitted with REML; Satterthwaite p‑values.  
   - **Random Forest Baseline**: `RandomForestRegressor(max_depth=5, random_state=42)`.  
   - **Cross‑Validation**: 5‑fold, stratified by species (Constitution VI).  
   - **Performance Metrics**: adjusted R², RMSE; mean out‑of‑sample R² across folds.  

4. **Statistical Rigor**  
   - **Multiple‑Comparison Correction**: Bonferroni applied to the six coefficient tests (P & N × three root traits).  
   - **Collinearity Check**: VIF for P and N; if VIF > 5, a warning is logged and coefficients are interpreted descriptively.  
   - **Overall Model Significance**: F‑test with reported p‑value.  
   - **Associational Framing**: All statements are explicitly labelled “associational” in the final report, and a dedicated verification step (Task T029) scans for causal language.  
   - **Sensitivity Analysis**: The verified literature ranges are compared to each LMM coefficient; coefficients must lie within ±10 % of the physiological range to satisfy SC‑006. **Fallback**: if the literature dataset cannot be fetched, hard‑coded typical ranges (P ≈ 30 ± 3 mg kg⁻¹, N ≈ 25 ± 2.5 mg kg⁻¹) are used; the analysis still runs and `sc_006_met` is set to `false` with a logged note.

5. **Visualization**  
   - Partial dependence plots for each nutrient–trait pair using the 5‑th to 95‑th percentile of nutrient values in the training set.  
   - PNG files saved under `artifacts/reports/plots/`; total size verified ≤ 100 MB (SC‑004).  

## Compute Feasibility
- **Memory**: ≤ 4 GB (datasets < 100 k rows).  
- **Runtime**: ≈ 1.5 h on a 2‑CPU GitHub Actions runner (well under the 6 h limit).  
- **GPU**: Not required.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| ISRIC data unavailable | Log deviation; fall back to verified merged dataset; SC‑001 set to `null`. |
| Insufficient species counts | Species with < 20 observations are excluded; impact quantified in SC‑005. |
| Missing literature ranges for sensitivity | Use hard‑coded typical ranges; still produce a plausibility check and set `sc_006_met` = false with a log entry. |
| High collinearity between P and N | VIF check; if > 5, issue warning and avoid over‑interpreting coefficients. |
| Potential causal wording in report | Task T029 scans the report markdown for causal keywords and fails the run on detection. |
| Power may be low after filtering | Power analysis (Task T024) quantifies this; results are reported transparently. |

## Success Criteria Evaluation (to be populated in `metrics.json`)

- **SC‑001**: Computed as `merged_root_datasets / total_root_datasets` (or `null` if soil data unavailable).  
- **SC‑002**: LMM adjusted R² within 5 % of RF R².  
- **SC‑003**: Both phosphorus and nitrogen coefficients have Bonferroni‑corrected p‑values < 0.05.  
- **SC‑004**: Total PNG size ≤ 100 MB (verified programmatically).  
- **SC‑005**: Number of excluded species logged; proportion of excluded species recorded.  
- **SC‑006**: Coefficients lie within ±10 % of verified physiological ranges; otherwise `false`.  

All criteria are computed in Task T027 and reported in the final PDF.

---

