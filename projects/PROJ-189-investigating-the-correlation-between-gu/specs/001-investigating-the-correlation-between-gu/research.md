# Research: Gut Microbiome and Cognitive Decline Analysis

## 1. Problem Statement
Determine whether gut microbial genus abundances are **associationally** linked to cognitive performance in older adults (age ≥ 60). Because both AGP and HRS are observational, all conclusions are limited to association.

## 2. Dataset Strategy

### 2.1 Verified Sources
| Dataset | Description | Verified URL |
|---|---|---|
| **AGP (American Gut Project)** | 16S rRNA genus‑level counts | `https://huggingface.co/datasets/eternalaudrey/jump-cp-0016-labelfree-AGP/resolve/main/data/train-00000-of-00053.parquet` |
| **HRS (Health and Retirement Study)** | Cognitive scores, demographics, BMI | `https://huggingface.co/datasets/irenepap/en-it-hrs-data/resolve/main/data/train-00000-of-00001-5379c2a0af0a1773.parquet` |
| **BMI supplement** (optional) | Additional BMI records for imputation | `https://huggingface.co/datasets/karan451/BMI-labeled-faced/resolve/main/archive/Final_Dataset.csv` |

All files are directly downloadable via the HuggingFace `datasets` library; no manual login required.

### 2.2 Variable Verification
- **AGP** provides `sample_id`, `participant_id`, and genus‑level count columns.  
- **HRS** provides `participant_id`, `age`, `sex`, `bmi`, and `cognitive_score`.  
- **BMI supplement** provides `participant_id` and `bmi` (used only when HRS BMI is missing).  

If any required column is absent, the pipeline aborts with a clear error (fulfills FR‑001).

### 2.3 Linkage Feasibility (Fatal Coverage Gap)
After loading, we compute the overlap:

```python
overlap = len(set(agp_df.participant_id) & set(hrs_df.participant_id))
```

If `overlap < 500`, the pipeline logs the count and **terminates** with a “Fatal Coverage Gap” message. No synthetic merging is performed, respecting Principle VI (Microbiome Data Provenance).

### 2.4 Data Volume & Streaming
Both parquet files are < 3 GB. They are streamed (`datasets.load_dataset(..., streaming=True)`) so that RAM stays ≤ 4 GB. After merge & filter, the final dataframe is ≤ 500 MB.

## 3. Methodological Approach

### 3.1 Pre‑processing (FR‑001, FR‑002, FR‑006)
1. **Provenance validation** – compute SHA‑256 checksums of downloaded files and compare to the reference values stored in the project state yaml (Task T001).  
2. **Merge** on `participant_id` (inner join). Abort if overlap < 500.  
3. **Age filter**: retain rows with `age >= 60`.  
4. **Rarefaction**: compute `min_depth` across retained samples; rarefy all samples to this depth.  
5. **CLR transformation**: apply centered log‑ratio (`pycoda.clr`) to the rarefied genus matrix.  
6. **Missing BMI**: impute using MICE (`miceforest`); flag imputed rows (`is_missing_bmi`).  
7. **VIF check**: compute variance inflation factors on the CLR matrix; any pair with VIF > 5 is recorded in the model artifact (FR‑006).  

All steps produce deterministic Parquet files under `data/processed/`.

### 3.2 Correlation Analysis (FR‑003)
- Compute **Spearman** rank correlation between each genus (CLR‑scaled) and `cognitive_score`.  
- Generate raw two‑tailed p‑values.  
- Apply **Benjamini‑Hochberg FDR** (α = 0.05).  
- Save a JSON table (`correlations.json`) that conforms to the `results.schema.yaml` definition for the `correlation` block.  
- Results are explicitly labeled “associational”.

### 3.3 Predictive Modeling (FR‑004, FR‑005, FR‑006, FR‑007)
- **Model**: `RandomForestRegressor` (scikit‑learn).  
- **Split**: 80 % train / 20 % hold‑out, stratified by `age_group`.  
- **Nested CV**: outer 5‑fold CV for performance, inner 3‑fold grid search over `n_estimators` ∈ {100,200} and `max_depth` ∈ {10,20,None}. Fixed `random_state=42`.  
- **Metrics**: R², RMSE on hold‑out.  
- **Permutation null**: 1000 shuffles of `cognitive_score`, refit using the same nested CV pipeline, collect R² distribution.  
- **Significance**: model R² must exceed the 95th percentile of the null distribution; Holm‑Bonferroni corrects the permutation‑derived p‑values.  
- **Interpretability**: compute SHAP values (`shap.TreeExplainer`) and store the top‑20 genus rankings.  

All artifacts (`model_metrics.json`) adhere to the `results.schema.yaml` definition for the `model` block.

### 3.4 Sensitivity Analysis (FR‑005)
- Sweep rarefaction depth across `{5_000, min_depth}` (if `min_depth` > 5 000).  
- For each depth repeat steps 3.1‑3.3 and record R² variance in `sensitivity.json`.  

### 3.5 Statistical Rigor
- **Multiple comparisons**: BH FDR for correlations; Holm‑Bonferroni for permutation p‑values.  
- **Power**: If merged N < 100, a warning is emitted (SC‑004).  
- **Causality**: All statements limited to “association”.  
- **Collinearity**: VIF flags reported; Random Forest tolerates correlated predictors but flags are recorded.  
- **Measurement validity**: Cognitive scores taken directly from HRS documentation; AGP 16S protocol is standard (assumption VI).  

## 4. Compute Feasibility
- **CPU‑only**: All libraries run on CPU; `shap` uses kernel explainer (CPU‑friendly).  
- **Runtime estimate**:  
  - Data download & checksum: < 15 min  
  - Pre‑processing (CLR + VIF): < 10 min  
  - Correlations: < 20 min  
  - Random Forest + 1000 permutations: 3‑4 h  
  - Sensitivity sweeps (2 depths): ~1 h  
  - Total ≤ 6 h, RAM ≤ 6 GB.  

If any step exceeds limits, Task T010 automatically reduces taxa or permutation count and logs the change.

---
