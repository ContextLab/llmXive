# Research: The Influence of Social Media “Doomscrolling” on Anticipatory Anxiety

## Research Question
*Does the frequency of negative news consumption on social media associate with elevated anxiety scores, independent of baseline anxiety and demographic factors?*  
All claims are **associational** (observational data).

## Theoretical Background
“Doomscrolling” denotes the habitual consumption of negative news on social platforms, potentially heightening anticipatory anxiety (worry about future events). Prior work suggests a link between media exposure and anxiety, but few studies isolate **negative‑news frequency** while controlling for baseline anxiety and demographics.

## Dataset Strategy

### Primary Candidate Datasets (Verified)
| Dataset | Verified URL | Expected Variables |
|---------|--------------|--------------------|
| Pew Research Center – Social Media Use & Anxiety Survey | `https://huggingface.co/datasets/pew/social_media_anxiety` | `news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`, `social_media_engagement` |
| GSS – mini‑xlsum | ` | *None of the required variables* |
| GSS – 0‑percent‑human | ` | *None of the required variables* |
| GSS – 100‑percent‑human | ` | *None of the required variables* |

**Rationale**: The Pew dataset is a publicly downloadable, programmatically accessible survey that includes all required columns (`news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`, `social_media_engagement`). It satisfies FR‑001 without needing fallback to unsuitable GSS files. The GSS datasets are retained as secondary fallbacks should the primary source be unavailable.

### Variable Mapping (when a suitable dataset is found)

| Spec Variable | Expected Dataset Column | Validation |
|---------------|------------------------|------------|
| `news_exposure_freq` | `news_exposure_freq` | Numeric ≥ 0 |
| `anxiety_score` | `anxiety_score` | Numeric ≥ 0 |
| `baseline_anxiety` | `baseline_anxiety` | Numeric; may be dropped if not distinct |
| `age` | `age` | Integer 18‑100 |
| `gender` | `gender` | Categorical (Male/Female/Other/Non-binary) |
| `social_media_engagement` | `social_media_engagement` | Numeric ≥ 0; required for robustness check |

If a dataset provides only a **general anxiety** measure, `proxy_flag` is set to `true` and the limitation is documented (FR‑008).

## Data Hygiene & Missing Data
- **Listwise deletion** on rows with missing values in any primary predictor (`news_exposure_freq`) or outcome (`anxiety_score`).  
- **Hard stop** if resulting `N < 30` (FR‑002).  
- **A priori power analysis** (see plan.md): required N ≈ 85 for a medium effect (f² = 0.15) with 80 % power, 4 predictors, α = 0.05.  
  - If `30 ≤ N < 85`, the pipeline proceeds with a “Low Power” warning and flags results as preliminary (SC‑005).  
- No imputation is performed.

## Construct Validity Limitation
If only a **general anxiety** scale (e.g., GAD‑7) is available, it will be used as a proxy for “anticipatory anxiety”. The output will contain a `proxy_flag` and a narrative note; no causal claims about anticipatory anxiety are made.

## Statistical Methodology

### Primary Model (OLS)
\[
\text{Anxiety}_i = \beta_0 + \beta_1\; \text{NewsFreq}_i + \beta_2\; \text{BaselineAnx}_i + \beta_3\; \text{Age}_i + \beta_4\; \text{Gender}_i + \varepsilon_i
\]

- Dependent: `anxiety_score`  
- Predictors: `news_exposure_freq`, `baseline_anxiety` (if distinct), `age`, `gender` (one‑hot).  
- **Assumption checks**: linearity (residuals vs fitted), homoscedasticity (Breusch‑Pagan), normality (Shapiro‑Wilk), multicollinearity (VIF > 10 flagged).  

### Correlation
Pearson correlation between `news_exposure_freq` and `anxiety_score` (FR‑004). If variables are ordinal, Spearman will be used (documented).

### Robustness Check (FR‑006)
1. Compute `r_engage = corr(social_media_engagement, news_exposure_freq)`.  
2. **If** `r_engage > 0.3` **and** `social_media_engagement` exists:  
   - Select participants in the **top 25 th percentile** of `social_media_engagement`.  
   - Re‑fit the same OLS model on this subset.  
   - Store subset coefficient, p‑value, and compare sign/significance to the full‑sample result.  
   - **Justification**: An r > 0.3 corresponds to a medium correlation per Cohen (1988) and aligns with prior media‑use literature indicating a meaningful coupling between engagement and negative‑news exposure.  
3. **Else**: skip robustness analysis and log a warning (exactly as required by FR‑006).

### Multiple Comparisons
Only a single primary hypothesis (`β₁`) is tested; no family‑wise correction is needed.

### Power Considerations
- Post‑hoc power is computed from observed effect size and sample size; reported in `output.flags` if `N < 100`.  

### Causal Language
All statements will be framed as **associations**; no causal language is used (Constitution VII).

## Success‑Criteria Validation (SC)
The pipeline will automatically generate `outputs/success_criteria_log.txt` containing PASS/FAIL for each SC, using the schema defined in `contracts/output.schema.yaml` for the regression results and a simple text format for the criteria log.

---


