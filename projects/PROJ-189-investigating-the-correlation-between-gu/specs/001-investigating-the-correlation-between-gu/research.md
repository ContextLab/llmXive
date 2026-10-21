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

### 3.3 Rarefaction, CLR, Imputation, VIF (Task T003)
1. **Rarefaction**: compute `min_depth` across retained samples; rarefy each sample to this depth.  
2. **CLR transformation**: apply `pycoda.clr` to the rarefied genus matrix.  
3. **BMI imputation**: run MICE (`miceforest`) on missing BMI values; add a boolean flag `is_missing_bmi`.  
4. **VIF**: compute variance inflation factors on the CLR matrix; any pair with VIF > 5 is recorded in `vif_check` (included later in the model artifact).  
5. Write `clr_normalized.parquet` and `imputed.parquet`.  

All transformations are deterministic (fixed random seed `42`).

### 3.4 Correlation Analysis (Task T004)
- Compute **Spearman** rank correlation between each genus (CLR‑scaled) and `cognitive_score`.  
- Generate raw two‑tailed p‑values.  
- Apply **Benjamini‑Hochberg FDR** (α = 0.05).  
- Store results in `data/results/correlations.json`, validated against `contracts/correlation.schema.yaml`.  
- Results are explicitly labeled “associational”.

### 3.5 Predictive Modeling (Task T005) & Permutation Null (Task T006)
- **Model**: `RandomForestRegressor` (scikit‑learn, CPU‑only).  
- **Split**: [deferred] train / [deferred] hold‑out, stratified by `age_group`.
- **Nested CV**: outer 5‑fold CV for performance, inner 3‑fold grid search over `n_estimators ∈ {100,200}` and `max_depth ∈ {10,20,None}`; `random_state=42`.  
- **Metrics**: R² and RMSE on the hold‑out set.  
- **Permutation test**: shuffle `cognitive_score` 1000 times, refit using the same nested CV pipeline, collect R² distribution.  
- **Significance**: model R² must exceed the 95th percentile of the null distribution; Holm‑Bonferroni corrects the permutation‑derived p‑value.  
- **Interpretability**: compute SHAP values (`shap.TreeExplainer`) and record the top‑20 genera.  
- All outputs are stored in `data/results/model.json` and validated against `contracts/model.schema.yaml`.

### 3.6 Sensitivity Analysis (Task T008)
- Sweep rarefaction depth over `{5 000, min_depth}` (if `min_depth` > 5 000).  
- For each depth repeat Tasks T003–T005, recording the hold‑out R².  
- Store the variance of R² across depths in `data/results/sensitivity.json`.  

### 3.7 Unified Results Assembly (Task T009)
- Combine `dataset.json`, `correlations.json`, `model.json`, and `sensitivity.json` into a single `data/results/unified_results.json` that conforms to `contracts/results.schema.yaml`.  

### 3.8 Resource Guardrails (Task T010)
- Each script imports `utils.stats.monitor_resources()` which uses `psutil` to check RAM usage every 30 seconds.  
- If RAM > 6 GB, the script automatically:  
  1. Truncates the genus matrix to the top‑200 most abundant genera, **and**  
  2. Reduces permutation count to 500 (for modeling).  
- The adjustment is logged; the pipeline continues, satisfying FR‑007.

### 3.9 Reporting (Task T011)
- Generate `data/results/summary.md` that:  
  - Reports overlap count, age filter stats, and any checksum warnings.  
  - Lists the number of significant genus‑cognition associations (SC‑002).  
  - Shows model R², null‑distribution percentile, and significance flag (SC‑003).  
  - Summarizes peak RAM usage vs the 7 GB limit (SC‑004).  
  - Includes key figures (saved as PNGs in `data/results/figures/`).  

## 4. Statistical Rigor
- **Multiple comparisons**: BH FDR for correlations; Holm‑Bonferroni for permutation p‑values.  
- **Power**: If the merged dataset contains < 100 participants, a warning is emitted (SC‑004). No formal power calculation is mandated.  
- **Causality**: All statements are explicitly labeled “associational”.  
- **Measurement validity**: Cognitive scores are taken directly from HRS documentation; AGP 16S protocol is standard (assumption VI).  
- **Collinearity**: VIF computed; any VIF > 5 flagged and reported (FR‑006).  

## 5. Compute Feasibility (CPU‑first)
- **Data download & checksum**: < 15 min, < 200 MB RAM.  
- **Pre‑processing**: < 10 min, < 4 GB RAM.  
- **Correlation**: < 20 min, < 2 GB RAM.  
- **Random Forest + 1000 permutations**: 3–4 h, ≤ 6 GB RAM.  
- **Sensitivity sweeps (2 depths)**: ~1 h.  
- **Total**: ≤ 6 h, ≤ 6 GB RAM.  

No GPU is required; all libraries run on CPU.

---
