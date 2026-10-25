# Research: Gut Microbiome and Cognitive Decline Analysis

## 1. Problem Statement
Determine whether gut microbial genus abundances are **associationally** linked to cognitive performance in older adults (age ≥ 60). The analysis is purely observational; no causal claims are made.

## 2. Dataset Strategy

### 2.1 Verified Sources
| Dataset | Description | Verified URL |
|---|---|---|
| **AGP (American Gut Project)** | 16S rRNA genus‑level count table (parquet) | `https://huggingface.co/datasets/eternalaudrey/jump-cp-0016-labelfree-AGP/resolve/main/data/train-00000-of-00053.parquet` |
| **HRS (Health and Retirement Study)** | Cognitive scores, demographics, BMI (parquet) | `https://huggingface.co/datasets/irenepap/en-it-hrs-data/resolve/main/data/train-00000-of-00001-5379c2a0af0a1773.parquet` |
| **BMI supplement** (optional) | Additional BMI records for participants missing HRS BMI (CSV) | `https://huggingface.co/datasets/karan451/BMI-labeled-faced/resolve/main/archive/Final_Dataset.csv` |

All files are directly downloadable via the HuggingFace `datasets` library; no authentication is required.

### 2.2 Variable Verification
- **AGP** provides `sample_id`, `participant_id`, and one column per genus (`genus_<name>`).  
- **HRS** provides `participant_id`, `age`, `sex`, `bmi`, and `cognitive_score`.  
- **BMI supplement** provides `participant_id` and `bmi` (used when HRS BMI is missing).  

If any required column is absent, the pipeline aborts with a clear error (fulfills FR‑001).

### 2.3 Linkage Feasibility (Fatal Coverage Gap)
After loading, we compute the participant‑ID overlap:

```python
overlap = len(set(agp_df.participant_id) & set(hrs_df.participant_id))
```

**Public releases contain no shared participant identifiers**, so `overlap` will be 0. The pipeline therefore **logs the count and aborts** with a “Fatal Coverage Gap” error (see Task T002‑OV). This limitation is documented in the Constitution (Principle VI) and in the plan. **A future specification revision must provide a truly linked microbiome‑cognition dataset**; otherwise the core cross‑sectional analysis cannot be performed.

### 2.4 Data Volume & Streaming
Both parquet files are < 3 GB. They are streamed (`datasets.load_dataset(..., streaming=True)`) so that RAM stays ≤ 4 GB. After merge & age filter (if possible), the final dataframe is ≤ 500 MB.

## 2.2 Methodological Approach

### 2.2.1 Provenance Validation (Task T001)
1. Compute SHA‑256 checksums of the three raw files immediately after download.  
2. Compare each checksum to the values stored in `data/provenance/expected_checksums.json` (committed).  
3. Write observed checksums to `data/provenance/observed_checksums.json`.  
4. Abort if any checksum mismatches (ensures reproducibility & data hygiene).

### 2.2.2 Merge, Age Filter, Overlap Check (Task T002 & T002‑OV)
- **If** `overlap >= 500` **then** perform an inner join on `participant_id`, filter to `age >= 60`, and write `data/processed/merged_age60.parquet` and `data/processed/dataset.json`.  
- **If** `overlap < 500` **then** abort with a clear diagnostic (“Fatal Coverage Gap”) and stop all downstream analyses that require the merged dataset.  

### 2.2.3 Pre‑CLR VIF & Rarefaction (Task T003)
- Compute **Variance Inflation Factors** on the **raw** genus abundance matrix (post‑rarefaction, pre‑CLR).  
- Exclude any genus with VIF > 5; flagged taxa are recorded in the model artifact.  
- Rarefy each sample to the **minimum** read depth observed among retained samples.

### 2.2.4 CLR Transformation, BMI Imputation, Pearson Collinearity (Task T004)
1. Apply **CLR** (`pycoda.clr`) to the rarefied genus matrix.  
2. Impute missing BMI values via **MICE** (`miceforest`), adding a boolean flag `is_missing_bmi`.  
3. Compute pairwise Pearson |r| among CLR‑transformed genera; flag any pair with |r| > 0.9 (recorded in `collinearity_report`).  
4. Output `clr_normalized.parquet` and `imputed.parquet`.

### 2.2.5 Covariate‑Adjusted Partial Spearman Correlations (Task T005)
- For each genus, compute a **partial Spearman** correlation with `cognitive_score` while adjusting for `age`, `sex`, `bmi`, and `education_years` (using `pingouin.partial_corr`).  
- Generate raw two‑tailed p‑values.  
- Apply **Benjamini‑Hochberg FDR** (α = 0.05).  
- Store results in `data/results/correlations.json`, validated against `contracts/correlation.schema.yaml`.  
- All results are explicitly labeled “associational”.

### 2.2.6 Predictive Modeling & Permutation Null (Task T006 & T007)
- **Model**: `RandomForestRegressor` (CPU‑only, scikit‑learn).  
- **Features**: CLR‑scaled genera **plus** demographics (`age`, `sex`, `bmi`, `education_years`).  
- **Split**: 80/20 train‑test, stratified by `age_group`.  
- **Nested CV**: outer 5‑fold CV for performance, inner 3‑fold grid search over `n_estimators ∈ {100,200}` and `max_depth ∈ {10,20,None}`; `random_state=42`.  
- **Metrics**: R² and RMSE on hold‑out set.  
- **Permutation test**: shuffle `cognitive_score` 1 000 times, refit using the same nested CV pipeline, collect R² distribution.  
- **Significance**: model R² must exceed the 95th percentile of the null distribution; Holm‑Bonferroni corrects the permutation‑derived p‑value.  
- **Interpretability**: compute **SHAP** values (`shap.TreeExplainer`) and **permutation importance** (`sklearn.inspection.permutation_importance`).  
- Save all artefacts in `data/results/model.json` (validated against `contracts/model.schema.yaml`).

### 2.2.7 Linear Regression (Cross‑sectional) (Task T014)
- **Data**: When a merged microbiome‑cognition dataset is available (i.e., overlap ≥ 500), run a **standard linear regression** of `cognitive_score` on CLR‑transformed genera plus covariates (`age`, `sex`, `bmi`, `education_years`).  
- **When** no linked dataset is present, this step is skipped (the pipeline has already aborted).  
- **Output**: Fixed‑effect coefficients, standard errors, and p‑values stored in `data/results/linear_regression.json`.  

### 2.2.8 Sensitivity Analysis (Task T009)
- Sweep rarefaction depth over `{5 000, min_depth}` in steps of 500 reads.  
- For each depth repeat Tasks T003–T006, recording hold‑out R² and the number of FDR‑significant taxa.  
- Store the sweep results in `data/results/sensitivity.json`.

### 2.2.9 Power Analysis (Task T010)
- **Correlation power**: using `statsmodels.stats.power.NormalIndPower`, estimate detectable effect size |r| ≥ 0.2 given the effective sample size and α = 0.05 (FDR‑adjusted).  
- **Regression power**: using `statsmodels.stats.power.FTestPower`, estimate detectable ΔR² ≥ 0.05 given the number of predictors, α = 0.05, and the observed N.  
- Emit warnings in `summary.md` if (a) effective N < 100 or (b) required sample size exceeds observed N, satisfying FR‑009 and SC‑004.

### 2.2.10 Resource Guardrails (Task T011)
- Each script invokes `utils.stats.monitor_resources()` (via `psutil`) to check RAM every 30 s.  
- If RAM > 6 GB, the script automatically:
  1. Truncates the genus matrix to the top‑200 most abundant genera, **and**  
  2. Reduces permutation count to 500.  
- Adjustments are logged; the pipeline continues, satisfying internal safeguard requirements.

### 2.2.11 Unified Results Assembly (Task T012)
- Combine `dataset.json`, `correlations.json`, `model.json`, and `linear_regression.json` into a single `data/results/unified_results.json` that conforms to `contracts/results.schema.yaml`.  
- **Add** `checksum_agp` and `checksum_hrs` (from provenance) to `dataset.metadata`.

### 2.2.12 Reporting (Task T013)
- Generate `data/results/summary.md` that:
  - Reports overlap count and any fatal‑gap abort reason.  
  - Summarizes number of significant genus‑cognition associations (SC‑002).  
  - Shows model R², null‑distribution percentile, and significance flag (SC‑003).  
  - Summarizes linear regression fixed‑effect table (when available).  
  - Summarizes peak RAM usage vs the 6 GB limit (SC‑004).  
  - Includes key figures (`correlation_heatmap.png`, `model_shap_summary.png`).

## 3. Statistical Rigor
- **Multiple comparisons**: BH‑FDR for correlation matrix; Holm‑Bonferroni for permutation‑derived model p‑value.  
- **Power**: Formal calculations (Task T010) with explicit warnings.  
- **Causality**: All statements are labeled “associational”.  
- **Measurement validity**: Cognitive scores are taken directly from HRS documentation; AGP 16S protocol is standard (assumption VI).  
- **Collinearity**: Pre‑CLR VIF > 5 flagged; post‑CLR Pearson |r| > 0.9 flagged; both reported.

## 4. Compute Feasibility (CPU‑first)
- **Download & checksum**: < 15 min, < 200 MB RAM.  
- **Pre‑processing**: < 10 min, ≤ 4 GB RAM.  
- **Correlation**: < 20 min, ≤ 2 GB RAM.  
- **Random Forest + 1 000 permutations**: 3–4 h, ≤ 6 GB RAM.  
- **Linear regression**: < 5 min, ≤ 2 GB RAM.  
- **Sensitivity sweeps**: ~1 h.  
- **Total**: ≤ 6 h, ≤ 6 GB RAM.  
No GPU is required; all libraries run on CPU.

---



