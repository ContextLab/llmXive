# Research: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

## Research Question
*How does the content diversity of algorithmic recommendations predict subsequent learner course‑topic diversity, controlling for baseline interests?*  
All statements are explicitly **associational** (FR‑006, Constitution Principle VI/VII).

## Dataset Strategy
| Role | Dataset | Verified URL | Mapping to Required Columns |
|------|---------|--------------|-----------------------------|
| Primary source | **Synthetic Recommendation‑Enrollment Dataset** (generated locally) | *No verified external source provides the required schema; a deterministic synthetic dataset is created by `code/data_fetcher.py`.* | `recommended_items` → `recommended_categories` (list of category tokens).<br>`enrolled_items` → `enrolled_categories` (list of category tokens). |
| Validation / sanity‑check | **CPU‑only benchmark parquet** | ` | Not used for primary analysis; confirms that the data‑fetcher can read a generic parquet with arbitrary columns. |

*If a future open dataset with the required columns becomes available, the data‑fetcher can be swapped out without altering downstream steps, satisfying FR‑007.*

## Methodology

### 1. Data Ingestion & Diversity Metric Construction
1. **Generate** a deterministic synthetic dataset (`synthetic_dataset.parquet`) containing the required columns (`user_id`, `session_id`, `recommended_items`, `enrolled_items`, plus optional covariates). The generation uses a fixed random seed for reproducibility.  
2. **Column Mapping** as described above.  
3. **Semantic Merging**:  
   - Compute sentence embeddings for each category token using `sentence‑transformers/all‑MiniLM‑L6‑v2`.  
   - Merge any pair whose cosine distance ≤ *threshold* (default **0.05**, justified in the plan). Implements FR‑009.  
4. **Shannon Entropy** (log₂ per Wikipedia) for each list → `recommendation_diversity_score` and `learner_diversity_score` (FR‑001).  
5. **Missing Enrollments**: If `enrolled_categories` is empty, set `learner_diversity_score` to `null`, log a warning, and exclude the row from downstream regression (US‑1).  

### 2. Baseline Interest Vector
- Use all rows **preceding** the current session (chronologically if `timestamp` exists; otherwise the first N rows per user) to compute frequency counts per category.  
- Normalize to obtain a probability distribution → `baseline_vector` (FR‑002).  
- Users with no prior rows receive a **uniform** distribution (documented in the final report).  

### 3. Generalized Propensity Score Weighting (GPSW)
Because the exposure (`Recommendation_Diversity`) is continuous, we adopt the **generalized propensity score** approach (Hirano & Imbens, 2004):
1. Fit a **Gaussian linear model**: `Recommendation_Diversity ~ Baseline_Vector + session_length + time_of_day + platform_version`.  
2. Compute the conditional density of each observed exposure given the baseline vector; the inverse of this density yields the **raw weight**.  
3. Stabilize weights by multiplying by the marginal density of the exposure.  
4. Diagnose extreme weights: flag any > 10 × median and report effective sample size reduction (US‑2).  

### 4. Weighted Linear Regression (or GLS fallback)
- Primary model: `Learner_Diversity = β₀ + β₁·Recommendation_Diversity + β₂·Baseline_Vector + ε`, weighted by GPSW.  
- If the number of unique users **N < 30**, automatically switch to **Generalized Least Squares (GLS)** with heteroskedastic‑consistent robust SEs (FR‑008).  
- Compute **Variance Inflation Factor (VIF)** for each baseline covariate; if any VIF > 5, record the limitation (SC‑004).  

### 5. Robustness Verification
1. **Permutation Test** (consistent procedure):  
   - For each of **[deferred]** iterations, randomly permute the `Learner_Diversity` outcome **before** recalculating GPSW weights.  
   - Fit the weighted regression on the permuted data and record the `Recommendation_Diversity` coefficient.  
   - Build a null distribution; compare the observed β₁ to the 95 % confidence interval (Bonferroni‑corrected across the three semantic‑threshold settings).  
2. **Sensitivity Analysis**: Run the full pipeline for semantic‑similarity thresholds **0.01, 0.05, 0.1**. Record β₁ and p‑value for each. The effect is deemed stable if p < 0.05 in at least **2/3** of the sweeps (SC‑002). If not, a “Sensitivity Warning” is appended to the report (US‑3).  

### 6. Statistical Rigor & Limitations
- **Multiple Comparisons**: Bonferroni correction across the three thresholds.  
- **Power**: No formal a‑priori power analysis; if N < 30, GLS fallback acknowledges limited power (SC‑005).  
- **Causal Framing**: All statements use “is associated with” per FR‑006 and Constitution Principles VI/VII.  
- **Collinearity**: VIF check (SC‑004).  
- **Measurement Validity**: Shannon entropy (log₂) is a standard diversity metric (Wikipedia source).  

## Compute Feasibility
All components run on CPU:
- Entropy & merging: linear in rows, negligible memory.  
- GPSW: single linear model (< 1 s).  
- Weighted regression: < 0.2 s per fit on ≤ 100 k rows.  
- Permutation test: numerous repetitions of the fitting procedure, taking [deferred] in total.
- Memory ≤ 5 GB using chunked parquet reads.  

## Decision/Rationale
- **Synthetic Dataset**: Addresses the reviewer’s data‑resource concern by providing a fully reproducible dataset that meets the required schema without relying on unavailable external sources.  
- **GPSW**: Resolves the earlier ambiguity about propensity scoring for a continuous exposure by explicitly using the generalized propensity score framework.  
- **Robustness suite** (permutation + sensitivity) satisfies the methodological panel’s rigor requirements.  

---


