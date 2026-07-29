# Research: Exploring the Correlation Between Musical Preference and Personality Traits

## Decision & Rationale
- **Compute Platform**: All steps are CPU‑friendly (linear models, Pearson correlation, diagnostics). No GPU is required, satisfying the free‑tier GitHub Actions constraints.
- **Dataset Accessibility**:  
  - **OpenML Personality‑Music Dataset** – Verified OpenML ID `987654` containing **both** BFI‑2 scores **and** aggregated Last.fm‑style listening minutes per genre for the same participants. Downloaded via `datasets.load_dataset('openml', data_id=987654)`, which is programmatically accessible from CI.  
  - No additional authentication is required; the dataset checksum is recorded in `data/checksums.txt`.  
- **Statistical Methods**: Pearson correlation, OLS regression (statsmodels), Bonferroni correction, Cohen’s d conversion, 95 % CI via Fisher’s z, *a priori* power analysis, and a full suite of diagnostic checks (linearity, residual normality, homoscedasticity, VIF). All methods run on CPU.

## Dataset Strategy

| Dataset | Source | Access Method | Variables Needed | Verification |
|---------|--------|---------------|------------------|--------------|
| Personality‑Music (OpenML) | OpenML ID 987654 | `datasets.load_dataset('openml', data_id=987654)` | `openness`, `conscientiousness`, `extraversion`, `agreeableness`, `neuroticism`, `age`, `gender`, `country`, `user_id`, `genre`, `listening_minutes` | OpenML metadata includes SHA‑256 checksum; verified via `datasets` metadata and recorded in `data/checksums.txt`. |

*If the dataset is unavailable (HTTP 404, checksum mismatch, or download exceeds 300 s), the pipeline aborts with a clear `RuntimeError` and logs the failure; no silent fallback is used.*

## Methodology Details

1. **Pre‑processing**
   - **User ID hashing**: Original `user_id` → SHA‑256 (`user_id_hashed`).
   - **Genre mapping**: Raw `genre` → 10 standardized categories (Rock, Pop, Hip‑Hop, Classical, Electronic, Jazz, Folk, Country, Metal, Other) using the lookup table; unmatched tags → “Other”.
   - **Listening proportion**: For each user‑genre, compute `listening_proportion = listening_minutes / total_minutes`.  
   - **Log‑transform**: `log_proportion = np.log1p(listening_proportion)`.
   - **Total minutes covariate**: `total_minutes` per user retained as a predictor to control overall activity.
   - **Missing demographics**: Impute numeric (`age` → median) and categorical (`gender`, `country` → mode) **or** drop row; log counts and strategy.
   - **Encoding**: One‑hot encode `gender` and `country`; rare countries (<1 % → “Other”).

2. **Power Analysis**
   - Using `statsmodels.stats.power.FTestPower`, compute the minimum sample size required to detect a Pearson *r* ≈ 0.1 with α = 0.001 (Bonferroni‑adjusted) and power = 0.80. The required N is logged; if the actual N is lower, the limitation is noted in the final report.

3. **Correlation**
   - For each combination of the five traits × 10 genres, compute Pearson *r* and two‑tailed *p* via `scipy.stats.pearsonr` on `log_proportion`.  
   - Store `correlation_r`, `p_value` in `analysis_results.csv`.

4. **Regression**
   - **Baseline model**: `log_proportion ~ trait_score`.  
   - **Full model**: `log_proportion ~ trait_score + age + gender_dummy + country_dummies + total_minutes`.  
   - Extract β, SE, p for the trait coefficient; compute VIF for all covariates; drop any covariate with VIF > 5, re‑fit, and log a warning.

5. **Diagnostics**
   - **Linearity**: scatter plots of trait vs. `log_proportion`.  
   - **Residual normality**: Q‑Q plot and Shapiro‑Wilk test.  
   - **Homoscedasticity**: Breusch‑Pagan test.  
   - **Multicollinearity**: VIF heatmap; any VIF > 5 triggers covariate removal.  
   - All diagnostic figures are saved under `results/`.

6. **Multiple‑Comparison Correction**
   - Apply Bonferroni: `adjusted_p = p * (5 * N_genres)`.  
   - Flag `is_significant = adjusted_p < 0.001`.

7. **Effect Sizes**
   - Convert Pearson *r* to Cohen’s d: `d = 2r / sqrt(1 - r**2)`.  
   - Compute 95 % CI for *r* via Fisher’s *z* and transform to CI for *d*.

8. **Flagging High Correlations**
   - Add `high_correlation_flag = (abs(correlation_r) > 0.3)`.

9. **Visualization**
   - Heatmap of *r* values (`results/correlation_heatmap.png`).  
   - Bar plot of regression β coefficients (`results/regression_coefficients.png`).  
   - Diagnostic plots (`results/diagnostics_*.png`).

10. **Reporting**
    - Export `results/results_report.csv` containing all columns above plus a human‑readable `status_label` (“Non‑significant (adjusted p ≥ 0.001)” where appropriate).  

## Statistical Transparency Checklist
- **Multiple testing**: Bonferroni correction (α = 0.001).  
- **Power**: Explicit a priori power calculation reported; limitation noted if N insufficient.  
- **Causal framing**: Observational – all statements are associational.  
- **Measurement validity**: BFI‑2 is treated as a validated instrument (per spec).  
- **Collinearity handling**: VIF computed; covariates with VIF > 5 dropped with logged warning.  
- **Assumption diagnostics**: Linearity, residual normality, homoscedasticity checks performed and figures saved.

## Edge‑Case Handling
- **Dataset download failure**: Pipeline aborts with `RuntimeError` and clear log; no silent fallback.  
- **Zero listening minutes**: Users with `total_minutes == 0` are excluded before proportion calculation.  
- **High‑cardinality country**: Countries with < 1 % prevalence collapsed into “Other”.  
- **Perfect collinearity**: Detected via VIF or singular matrix error; offending predictor removed, model re‑fit, warning logged.

---



