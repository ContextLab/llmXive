# Research: Gut Microbiome and Cognitive Decline Analysis

## 1. Problem Statement
We aim to determine whether the relative abundances of gut microbial genera are **associationally** linked to cognitive performance in older adults (age ≥ 60). The analysis must respect the compositional nature of 16S rRNA data and control for key covariates (sex, BMI, education). Because both datasets are observational, all conclusions are limited to association.

## 2. Dataset Strategy

### 2.1 Verified Sources
| Dataset | Description | Verified URL(s) |
|---|---|---|
| **AGP (American Gut Project)** | 16S rRNA taxonomic counts (genus‑level) | `https://huggingface.co/datasets/eternalaudrey/jump-cp-0016-labelfree-AGP/resolve/main/data/train-00000-of-00053.parquet` |
| **HRS (Health and Retirement Study)** | Cognitive test scores, demographics, BMI | `https://huggingface.co/datasets/irenepap/en-it-hrs-data/resolve/main/data/train-00000-of-00001-5379c2a0af0a1773.parquet` |
| **BMI supplement (optional)** | Additional BMI records for imputation | `https://huggingface.co/datasets/karan451/BMI-labeled-faced/resolve/main/archive/Final_Dataset.csv` |

All files are directly downloadable via the HuggingFace `datasets` library, requiring no manual login.

### 2.2 Variable Verification
- **AGP** provides `sample_id`, `participant_id`, and genus‑level count columns.
- **HRS** provides `participant_id`, `age`, `sex`, `bmi`, and `cognitive_score`.
- **BMI supplement** contains `participant_id` and `bmi`; used only when HRS BMI is missing.

If any required column is absent, the pipeline aborts with a clear error (fulfills FR‑001).

### 2.3 Linkage Feasibility (Fatal Coverage Gap)
The spec assumes a shared `participant_id`. We will **programmatically verify** the overlap after loading both tables:
- Compute `len(set(AGP.participant_id) ∩ set(HRS.participant_id))`.
- If the overlap < 500, the pipeline logs the count and **terminates** with a “Fatal Coverage Gap” message. No synthetic merging is performed, respecting the constitution’s data‑provenance principle.

### 2.4 Data Volume & Streaming
Both parquet files are < 3 GB each. We load them with `datasets.load_dataset(..., streaming=True)` to keep RAM ≤ 4 GB. After merging and filtering, the final dataframe is expected to be ≤ 500 MB.

## 3. Methodological Approach

### 3.1 Pre‑processing (FR‑001, FR‑002, FR‑006)
1. **Merge** on `participant_id` (inner join).  
2. **Age filter**: retain rows with `age >= 60`.  
3. **Rarefaction**: calculate the minimum read depth (`min_depth`) across retained samples; rarefy all samples to `min_depth`.  
4. **CLR transformation**: apply centered log‑ratio to the rarefied genus matrix (`pycoda.clr`).  
5. **Missing BMI**: apply MICE (`miceforest`) to impute missing BMI; flag imputed rows (`is_missing_bmi`).  
6. **VIF**: compute variance inflation factors on the CLR‑transformed matrix; flag any pair with VIF > 5 (FR‑006).  

All steps produce deterministic output files under `data/processed/`.

### 3.2 Correlation Analysis (FR‑003)
- Compute **Spearman rank** correlation between each genus (CLR‑scaled) and the continuous `cognitive_score`.  
- Generate raw two‑tailed p‑values.  
- Apply **Benjamini‑Hochberg FDR** (α = 0.05).  
- Save a JSON table adhering to `contracts/correlation.schema.yaml`.  
- Results are explicitly labeled “associational”.

### 3.3 Predictive Modeling (FR‑004, FR‑005, FR‑006, FR‑007)
- **Model**: `RandomForestRegressor` (scikit‑learn).  
- **Splitting**: 80 % train / 20 % hold‑out, stratified by `age_group`.  
- **Nested CV**: outer 5‑fold CV for performance, inner 3‑fold grid search over `n_estimators` ∈ {100,200} and `max_depth` ∈ {10,20,None}. Fixed `random_state=42`.  
- **Performance metrics**: R², RMSE on the hold‑out set.  
- **Permutation null**: shuffle `cognitive_score` 1000 times, refit model each time (using the same CV pipeline), collect R² distribution.  
- **Significance**: model R² must exceed the 95th percentile of the null distribution; p‑values from permutations are corrected with **Holm‑Bonferroni** (family‑wise error control).  
- **Interpretability**: compute SHAP values (`shap.TreeExplainer`) and store top‑20 genus rankings.  

All model artifacts (pickle, metrics, SHAP rankings) are saved under `data/results/` and validated against `contracts/model.schema.yaml`.

### 3.4 Sensitivity Analysis (FR‑005)
- Sweep rarefaction depth across `{5_000, min_depth}` (if `min_depth` > 5 000, both points are distinct).  
- For each depth, repeat steps 3.1‑3.3 and record R² variance in `data/results/sensitivity.json`.  

### 3.5 Statistical Rigor (Section 4 of the spec)
- **Multiple comparisons**: BH FDR for correlations; Holm‑Bonferroni for permutation p‑values.  
- **Power**: If merged N < 100, a warning is emitted (SC‑004).  
- **Causality**: All statements limited to “association”.  
- **Collinearity**: VIF flags reported; no predictor removal (RF robust).  
- **Measurement validity**: Cognitive scores are taken directly from HRS documentation; microbiome counts follow AGP 16S protocol (assumption VI of the constitution).  

## 4. Compute Feasibility
- **CPU‑only**: All libraries run on CPU; `shap` uses the `KernelExplainer` which is CPU‑friendly.  
- **Runtime estimate**:  
  - Data download & merge: < 15 min.  
  - CLR + VIF: < 10 min.  
  - Correlations: < 20 min.  
  - Random Forest (nested CV) + 1000 permutations: 3‑4 h on 2 cores.  
  - Sensitivity sweeps (2 depths): additional ~1 h.  
  - Total ≤ 6 h, RAM ≤ 6 GB.  

If any step exceeds limits, T010 automatically scales down (e.g., reduces permutations to 500, limits taxa to top‑200 abundant genera) and logs the adjustment.

---
