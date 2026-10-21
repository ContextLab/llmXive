# Research: Gut Microbiome and Cognitive Decline Analysis

## 1. Problem Statement
Determine whether gut microbial genus abundances are **associationally** linked to cognitive performance in older adults (age ≥ 60). The analysis is purely observational; no causal inference is claimed.

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
After loading, we compute the overlap:

```python
overlap = len(set(agp_df.participant_id) & set(hrs_df.participant_id))
```

If `overlap < 500`, the pipeline logs the count and **terminates** with a “Fatal Coverage Gap” error. No synthetic merging is performed, respecting Principle VI (Microbiome Data Provenance).

### 2.4 Data Volume & Streaming
Both parquet files are < 3 GB. They are streamed (`datasets.load_dataset(..., streaming=True)`) so that RAM stays ≤ 4 GB. After merge & age filter, the final dataframe is ≤ 500 MB.

## 3. Methodological Approach

### 3.1 Provenance Validation (Task T001)
1. Compute SHA‑256 checksums of the three raw files immediately after download.  
2. Compare each checksum to the values stored in `data/provenance/expected_checksums.json` (committed to the repo).  
3. Write observed checksums to `data/provenance/observed_checksums.json`.  
4. Exit with status 0 only if **all** match; otherwise abort with a descriptive error.  

Deterministic provenance guarantees reproducibility (Constitution I) and data hygiene (III).

### 3.2 Merge & Age Filtering (Task T002)
- Inner join on `participant_id`.  
- Abort if overlap < 500 (fatal coverage gap).  
- Filter to `age >= 60`.  
- Write `data/processed/merged_age60.parquet` and a companion `data/processed/dataset.json` that conforms to `contracts/dataset.schema.yaml`.  

### 3.3 Multicollinearity Assessment (VIF) – Pre‑CLR (Task T003)
- Compute Variance Inflation Factors (VIF) on the **raw** genus abundance matrix (after rarefaction, before CLR).  
- Any genus with VIF > 5 is excluded from downstream modelling; flagged pairs are recorded in the `vif_check` section of the model artifact.  
- This satisfies FR‑010 and provides a transparent collinearity report.

### 3.4 Rarefaction, CLR, BMI Imputation, Pearson Collinearity (Task T004)
1. **Rarefaction**: compute `min_depth` across retained samples; rarefy each sample to this depth.  
2. **CLR transformation**: apply `pycoda.clr` to the rarefied genus matrix.  
3. **BMI imputation**: run MICE (`miceforest`) on missing BMI values; add a boolean flag `is_missing_bmi`.  
4. **Pearson collinearity**: compute pairwise Pearson |r| among CLR‑transformed genera; any pair with |r| > 0.9 is recorded in `collinearity_report`.  
5. Write `clr_normalized.parquet` and `imputed.parquet`.  

All transformations are deterministic (random seed = 42).

### 3.5 Partial Spearman Correlation Analysis (Task T005)
- For each genus, compute a **partial Spearman** correlation with `cognitive_score` while controlling for `age`, `sex`, `bmi`, and `education_years` (using `pingouin.partial_corr`).  
- Generate raw two‑tailed p‑values.  
- Apply **Benjamini‑Hochberg FDR** (α = 0.05).  
- Store results in `data/results/correlations.json`, validated against `contracts/correlation.schema.yaml`.  
- Results are explicitly labeled “associational”.

### 3.6 Predictive Modeling (Task T006) & Permutation Null (Task T007)
- **Model**: `RandomForestRegressor` (scikit‑learn, CPU‑only).  
- **Features**: CLR‑scaled genera **plus** demographic covariates (`age`, `sex`, `bmi`, `education_years`).  
- **Split**: 80/20 train‑test split, stratified by `age_group`.  
- **Nested CV**: outer 5‑fold CV for performance, inner 3‑fold grid search over `n_estimators ∈ {100,200}` and `max_depth ∈ {10,20,None}`; `random_state=42`.  
- **Metrics**: R² and RMSE on the hold‑out set.  
- **Permutation test**: shuffle `cognitive_score` 1 000 times, refit using the same nested CV pipeline, collect R² distribution.  
- **Significance**: model R² must exceed the 95th percentile of the null distribution; Holm‑Bonferroni corrects the permutation‑derived p‑value.  
- **Interpretability**: compute SHAP values (`shap.TreeExplainer`) and record the top‑20 genera; also compute permutation importance via `sklearn.inspection.permutation_importance`.  
- All outputs are stored in `data/results/model.json` and validated against `contracts/model.schema.yaml`.

### 3.7 Sensitivity Analysis (Task T009)
- Sweep rarefaction depth over `{5 000, min_depth}` (if `min_depth` > 5 000).  
- For each depth repeat Tasks T003–T006, recording the hold‑out R² and number of significant taxa.  
- Store the results in `data/results/sensitivity.json`.

### 3.8 Power Analysis (Task T010)
- **Correlation power**: using `statsmodels.stats.power.NormalIndPower`, estimate detectable effect size |r| ≥ 0.2 given the number of taxa and α = 0.05 (FDR‑adjusted).  
- **Regression power**: using `statsmodels.stats.power.FTestPower`, estimate detectable ΔR² ≥ 0.05 given sample size, number of predictors, and α = 0.05 (Holm‑Bonferroni).  
- Emit warnings in `summary.md` if (a) effective N < 100 or (b) required sample size exceeds the observed N, satisfying FR‑009 and SC‑004.

### 3.9 Resource Guardrails (Task T011)
- Each script imports `utils.stats.monitor_resources()` which uses `psutil` to check RAM usage every 30 s.  
- If RAM > 6 GB, the script automatically:  
  1. Truncates the genus matrix to the top‑200 most abundant genera, **and**  
  2. Reduces permutation count to 500.  
- The adjustment is logged; the pipeline continues, satisfying FR‑007.

### 3.10 Unified Results Assembly (Task T012)
- Combine `dataset.json`, `correlations.json`, `model.json`, and `sensitivity.json` into a single `data/results/unified_results.json` that conforms to `contracts/results.schema.yaml`.  
- **Add** `checksum_agp` and `checksum_hrs` (from provenance) to `dataset.metadata`.

### 3.11 Reporting (Task T013)
- Generate `data/results/summary.md` that:  
  - Reports overlap count, age filter stats, and any checksum warnings.  
  - Lists the number of significant genus‑cognition associations (SC‑002).  
  - Shows model R², null‑distribution percentile, and significance flag (SC‑003).  
  - Summarizes peak RAM usage vs the 7 GB limit (SC‑004).  
  - Includes key figures (saved as PNGs in `data/results/figures/`).  

## 4. Statistical Rigor
- **Multiple comparisons**: BH FDR for correlations; Holm‑Bonferroni for permutation‑derived p‑values.  
- **Power**: Formal power calculations (Task T010) warn if N < 100 or detectable effect sizes are unrealistic (SC‑004).  
- **Causality**: All statements are explicitly labeled “associational”.  
- **Measurement validity**: Cognitive scores are taken directly from HRS documentation; AGP 16S protocol is standard (assumption VI).  
- **Collinearity**: VIF > 5 flagged pre‑CLR (FR‑010); Pearson |r| > 0.9 flagged post‑CLR.  

## 5. Compute Feasibility (CPU‑first)
- **Data download & checksum**: < 15 min, < 200 MB RAM.  
- **Pre‑processing**: < 10 min, ≤ 4 GB RAM.  
- **Correlation**: < 20 min, ≤ 2 GB RAM.  
- **Random Forest + 1 000 permutations**: 3–4 h, ≤ 6 GB RAM.  
- **Sensitivity sweeps (2 depths)**: ~1 h.  
- **Total**: ≤ 6 h, ≤ 6 GB RAM.  

No GPU is required; all libraries run on CPU.

---
