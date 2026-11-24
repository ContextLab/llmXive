# Research: Gut Microbiome and Cognitive Decline Analysis

## 1. Problem Statement
Determine whether gut microbial genus abundances are **associationally** linked to cognitive performance in older adults (age ≥ 60). All statements are observational; no causal inference is claimed.

## 2. Dataset Strategy

### 2.1 Required Input
The pipeline expects a **single paired microbiome‑cognition dataset** that already contains, for each participant, (a) CLR‑transformed or raw genus‑level abundances, and (b) a validated cognitive score from the Health and Retirement Study (or an equivalent standardized cognitive assessment). The dataset must be placed in `data/raw/paired_dataset.parquet` before execution.

### 2.2 Provenance & Source
- **Microbiome component**: Must originate from the American Gut Project and be downloaded directly from the Qiita/EBI repository (` Name or service not known)"))]).  
- **Cognitive component**: Must be a publicly available cognitive assessment dataset that can be legally paired with the AGP microbiome data (e.g., a dataset released on Zenodo that includes both stool sequencing and HRS‑compatible cognitive scores). **No public AGP/HRS identifier overlap exists**, so a pre‑paired dataset is required.

### 2.3 Variable Verification
- `sample_id` (string) – unique AGP identifier.  
- `participant_id` (string) – identifier shared between microbiome and cognition within the paired file.  
- `age`, `sex`, `bmi`, `education_years` – demographic covariates.  
- `cognitive_score` – continuous cognitive metric.  
- One column per genus (`genus_<name>`) containing raw read counts or relative abundances.

If any required column is missing, the pipeline aborts with a clear error (fulfills FR‑001).

### 2.4 Feasibility & Fatal Coverage Gap
Public AGP and HRS releases have **zero overlapping participant identifiers**; therefore a probabilistic linkage cannot produce the ≥ 200 participants required by SC‑001. The pipeline **does not attempt such linkage**. Instead, it checks whether the user‑provided paired dataset contains **≥ 200 rows** after filtering to age ≥ 60. If not, execution stops with a “Fatal Coverage Gap” diagnostic, and the specification must be revised to supply a suitable dataset.

### 2.5 Data Volume & Streaming
The paired parquet file is expected to be < 3 GB. It is streamed (`datasets.load_dataset(..., streaming=True)`) to keep RAM ≤ 4 GB. After successful loading the filtered dataframe is ≤ 500 MB.

## 3. Methodological Approach

### 3.1 Provenance Validation (Task T001)
1. Compute SHA‑256 checksums of the raw AGP file and the paired dataset immediately after download/placement.  
2. Compare each checksum to the values stored in `data/provenance/expected_checksums.json`.  
3. Write observed checksums to `data/provenance/observed_checksums.json`.  
4. Abort on any mismatch (ensures reproducibility & data hygiene).

### 3.2 Load Paired Dataset & Age Filter (Task T002)
- Load `paired_dataset.parquet`.  
- Filter to `age >= 60`.  
- Verify that the resulting dataframe contains **≥ 200 participants**.  
- If the count is < 200, log the count and **exit with a clear “Fatal Coverage Gap” error**. No downstream analysis proceeds.

### 3.3 Pre‑CLR VIF Screening & Rarefaction (Task T003)
- Compute **Variance Inflation Factors** on the raw genus count matrix (post‑rarefaction).  
- Exclude any genus with VIF > 5; flagged taxa are recorded in the model artifact.  
- Rarefy each sample to the **minimum** read depth observed among retained samples.

### 3.4 CLR Transformation, BMI Imputation & Post‑CLR Collinearity (Task T004)
1. Apply **Centered Log‑Ratio (CLR)** transformation (`pycoda.clr`).  
2. Impute missing BMI via **MICE** (`miceforest`), adding a boolean flag `is_missing_bmi`.  
3. Compute Pearson |r| among CLR‑transformed genera; flag any pair with |r| > 0.9 (recorded in `collinearity_report`).  

### 3.5 Covariate‑Adjusted Partial Spearman Correlations (Task T005)
- For each genus, regress the CLR abundance on **age, sex, BMI, and education**; retain residuals.  
- Likewise regress `cognitive_score` on the same covariates; retain residuals.  
- Compute **Spearman** correlation between the two sets of residuals (using `pingouin.partial_corr`).  
- Apply **Benjamini‑Hochberg FDR** (α = 0.05).  
- Store results in `data/results/correlations.json` (validated against `contracts/correlation.schema.yaml`).  

### 3.6 Predictive Modeling & Permutation Null (Task T006 & T007)
- **Model**: `RandomForestRegressor` (CPU‑only).  
- **Features**: CLR‑scaled genera + demographics (`age`, `sex`, `bmi`, `education_years`).  
- **Split**: 80/20 train‑test, stratified by `age_group`.  
- **Nested CV**: outer 5‑fold CV for performance, inner 3‑fold grid search over `n_estimators ∈ {100,200}` and `max_depth ∈ {10,20,None}`; `random_state=42`.  
- **Metrics**: R² and RMSE on hold‑out set.  
- **Permutation test**: shuffle `cognitive_score` 1 000 times, refit the same nested CV pipeline, collect R² distribution.  
- **Significance**: model R² must exceed the 95th percentile of the null distribution; Holm‑Bonferroni corrects the permutation p‑value.  
- **Interpretability**: compute **SHAP** values (`shap.TreeExplainer`) and **permutation importance** (`sklearn.inspection.permutation_importance`).  
- Output `data/results/model.json` (validated against `contracts/model.schema.yaml`).  

### 3.7 Standard Linear Regression (Task T014)
- Fit an OLS regression of `cognitive_score` on CLR‑transformed genera plus covariates using `statsmodels`.  
- Record fixed‑effect coefficients, standard errors, and p‑values in `data/results/linear_regression.json`.  

### 3.8 Sensitivity Analysis (Task T009)
- Sweep rarefaction depth over `{5 000, min_depth}` in increments of 500 reads.  
- For each depth repeat VIF screening, CLR, correlation, and modeling steps, logging hold‑out R² and the count of FDR‑significant taxa.  
- Store the sweep in `data/results/sensitivity.json`.  

### 3.9 Power Analyses (Task T010)
- **Correlation power**: using `statsmodels.stats.power.NormalIndPower`, compute detectable effect size |r| ≥ 0.2 given the effective N and α = 0.05 (FDR‑adjusted).  
- **Regression power**: using `statsmodels.stats.power.FTestPower`, compute detectable ΔR² ≥ 0.05 given N, number of predictors, and α = 0.05.  
- Emit warnings in `summary.md` if (a) effective N < 100 or (b) required sample size exceeds observed N (satisfies FR‑009 and SC‑004).  

### 3.10 Resource Guardrails (Task T011)
- Each script calls `utils.stats.monitor_resources()` (via `psutil`) to check RAM every 30 s.  
- If RAM > 6 GB, the script automatically:  
  1. Truncates the genus matrix to the top‑200 most abundant taxa, **and**  
  2. Reduces permutation count to 500.  
- Adjustments are logged; the pipeline continues, ensuring SC‑004.  

### 3.11 Unified Results Assembly (Task T012)
- Merge `dataset` metadata, `correlations.json`, `model.json`, and (when available) `linear_regression.json` into `data/results/unified_results.json`.  
- Include `checksum_source` (SHA‑256 of the paired dataset) in the `dataset.metadata` block (fulfills FR‑011).  

### 3.12 Reporting (Task T013)
- Generate a human‑readable `data/results/summary.md` that:  
  - Reports the linkage/size check count and abort reason (if any).  
  - Summarizes the number of significant genus‑cognition associations (SC‑002).  
  - Shows model R², null‑distribution percentile, and significance flag (SC‑003).  
  - Summarizes linear regression coefficients (when applicable).  
  - Lists peak RAM usage vs the 6 GB limit (SC‑004).  
  - Embeds key figures (`correlation_heatmap.png`, `model_shap_summary.png`).  

## 4. Statistical Rigor
- **Multiple comparisons**: BH‑FDR for the correlation matrix; Holm‑Bonferroni for permutation‑derived model p‑value.  
- **Power**: Formal calculations (Task T010) with explicit warnings.  
- **Causality**: All results are labeled “associational”.  
- **Measurement validity**: Cognitive scores are taken directly from the paired dataset’s documentation; AGP 16S protocol is standard (assumption VI).  
- **Collinearity**: Pre‑CLR VIF > 5 flagged; post‑CLR Pearson |r| > 0.9 flagged; both reported.

## 5. Compute Feasibility (CPU‑first)
| Step | Estimated wall‑clock | Peak RAM |
|------|----------------------|----------|
| Download & checksum | < 15 min | < 200 MB |
| Load paired dataset & age filter | < 10 min | ≤ 4 GB |
| VIF & rarefaction | < 5 min | ≤ 3 GB |
| CLR + imputation | < 5 min | ≤ 3 GB |
| Correlation analysis | < 20 min | ≤ 2 GB |
| Random Forest + 1 000 permutations | 3–4 h | ≤ 6 GB |
| Linear regression | < 5 min | ≤ 2 GB |
| Sensitivity sweep | ~ 1 h | ≤ 4 GB |
| Total | ≤ 6 h | ≤ 6 GB |
All libraries run on CPU; no GPU is required.

## 6. Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| **Zero overlap between AGP & HRS** | The pipeline no longer attempts linkage; it requires a pre‑paired dataset. If such a dataset is not provided, the run aborts with a clear diagnostic and the spec must be revised. |
| **Checksum mismatch** | Expected checksums are version‑controlled; update `expected_checksums.json` only after intentional data updates. |
| **RAM overflow during permutations** | Guardrail T011 automatically truncates taxa and reduces permutation count, logging the change. |
| **Missing BMI for many participants** | MICE imputation plus `is_missing_bmi` flag; downstream sensitivity to imputation is reported. |
| **Multiple‑testing inflation** | BH‑FDR for correlations; Holm‑Bonferroni for model significance. |
| **Power insufficiency** | Formal power analysis (Task T010) emits warnings; results are interpreted accordingly. |
| **Collinearity** | VIF screening pre‑CLR; Pearson |r| > 0.9 post‑CLR flagged and reported. |
| **Covariate leakage in linkage** | Linkage step removed; covariates are only used for adjustment, eliminating leakage. |
| **Covariate omission** | Demographic covariates are explicitly included in both correlation residualisation and modeling. |

---



