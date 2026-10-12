# Research: Predicting Plant Root Architecture from Soil Nutrient Availability

## Research Question
How do observational soil phosphorus (P) and nitrogen (N) concentrations associate with plant root architectural traits (total length, branching density, surface area) across multiple species?

## Dataset Strategy

| Dataset | Source | Verified URL(s) | Status | Strategy |
|---------|--------|-----------------|--------|----------|
| **PlantPheno (root phenotypes)** | Hugging Face | https://huggingface.co/datasets/davidkartchner/plant-phenotype/resolve/main/PPR_train_corpus.txt <br> https://huggingface.co/datasets/envedabio/plant-phenotype/resolve/main/PPR_test_corpus.txt | **Verified** | Primary source for root metrics; downloaded via `datasets.load_dataset`. |
| **RootReader** | – | *No verified source* | **Unavailable** | Excluded; deviation noted in AM‑001. |
| **ISRIC‑World Soil Information** | – | *No verified source* | **Unavailable** | Attempted download; on failure, log deviation (AM‑001) and fall back to merged datasets. |
| **MergedDataset (pre‑joined root + soil)** | Hugging Face | https://huggingface.co/datasets/blanchon/merged_dataset/resolve/main/data/train-00000-of-00001.parquet <br> https://huggingface.co/datasets/joaosanches/merged_dataset_no_duplicates/resolve/main/data/train-00000-of-00001.parquet <br> https://huggingface.co/datasets/aizenSosuke/merged_dataset/resolve/main/data/train-00000-of-00001.parquet | **Verified** | If ISRIC is unavailable, we search these verified merged datasets for the required columns. If none contain both P and N, we proceed with root‑only data. |
| **Literature nutrient ranges (for sensitivity)** | Hugging Face (intended) | *No verified source* | **Unavailable** | Sensitivity analysis will be performed only if a verified source is found; otherwise the step is logged as skipped. |

**Decision/Rationale**  
- **CPU‑First**: All analyses (KNN, LMM, RF, PDP) run comfortably on the free‑tier CPU runner. No GPU is needed.  
- **Data Availability**: ISRIC lacks a verified download URL; we therefore implement a robust deviation path (AM‑001). The verified merged datasets provide a fallback that already contain soil nutrients; we will use the first that satisfies the schema.  
- **No Fabrication**: No synthetic soil data is created. If no dataset supplies P/N, the nutrient hypothesis is omitted and the report clearly states the limitation.

## Statistical Methodology

1. **Preprocessing**  
   - Filter to observational records (`data_source_type == "observational"`).  
   - Exclude species with < 20 observations (SC‑005).  
   - Log‑transform root metrics (`log(x + 1e-6)`).  
   - Z‑score normalize nutrient columns (when present).  
   - Missing‑value handling: rows missing *both* nutrients → excluded; rows missing a single nutrient → excluded from multivariate analysis; remaining missing values imputed via KNN (k=5, Euclidean) with mean fallback.  
2. **Modeling**  
   - **Linear Mixed‑Effects Model (LMM)**: `root_trait ~ P + N + (1|species)`, fitted with REML; Satterthwaite approximation for p‑values.  
   - **Random Forest baseline**: `RandomForestRegressor(max_depth=5, random_state=SEED)`.  
   - **Cross‑validation**: 5‑fold, species‑stratified (Constitution VI).  
   - **Performance metrics**: adjusted R², RMSE; mean out‑of‑sample R² across folds.  
   - **Multiple‑comparison correction**: Bonferroni applied to the six coefficient tests (P & N across three traits).  
   - **Collinearity check**: VIF for P and N; if VIF > 5, report descriptive relationship only.  
3. **Validation & Rigor**  
   - **Associational framing**: All statements explicitly labelled “associational”.  
   - **Sensitivity analysis**: Compare coefficient estimates to literature‑reported physiological ranges (±10 % variation). Executed only when a verified literature source exists; otherwise logged as “skipped”.  
   - **F‑test** for overall model significance (reported p‑value).  
   - **Effect size reporting**: adjusted R², coefficient magnitude, confidence intervals.  

## Compute Feasibility
- **Memory**: ≤ 4 GB (datasets < 100 k rows).  
- **Runtime**: ≈ 1.5 h for full pipeline on 2‑CPU runner (well under 6 h limit).  
- **GPU**: Not required; all libraries run on CPU.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| No verified soil data (ISRIC) | AM‑001 logs deviation; use verified merged dataset or proceed with root‑only analysis; report limitation. |
| Insufficient species counts (n < 20) | Species excluded automatically; SC‑005 quantifies impact. |
| Missing literature ranges for sensitivity | Skip step, log “unverified source”; SC‑006 marked as N/A. |
| High collinearity between P and N | VIF check; if high, report descriptive trends only. |

---
