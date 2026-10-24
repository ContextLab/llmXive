# Research: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

## Research Question
*Does the frequency of negative news consumption on social media associate with elevated anticipatory anxiety scores, independent of baseline anxiety and demographic factors?*  
All statements are explicitly **associational** because the data are observational.

## Theoretical Background
“Doomscrolling” refers to the habitual consumption of negative news on social platforms, which prior work suggests may heighten anticipatory anxiety. Few studies have isolated **negative‑news frequency** while simultaneously controlling for **baseline anxiety**, **age**, and **gender**.

## Dataset Strategy

### Verified Sources (the ONLY citable URLs)

| Dataset | Verified URL | Contains required variables? |
|---------|--------------|------------------------------|
| mini‑xlsum text corpus | `https://huggingface.co/datasets/gsstein/mini-xlsum/resolve/main/data/test-00000-of-00001.parquet` | **NO** – NLP summarization data; lacks all survey variables |
| 0‑percent‑human text corpus | `https://huggingface.co/datasets/gsstein/0-percent-human-dataset-og/resolve/main/data/test-00000-of-00001.parquet` | **NO** – human‑vs‑AI text data; no relevant variables |
| 100‑percent‑human text corpus | `https://huggingface.co/datasets/gsstein/100-percent-human-dataset/resolve/main/data/test-00000-of-00001.parquet` | **NO** – same as above |
| YouGov surveys | — (no verified source) | **NO** – not programmatically downloadable |

**Dataset‑variable fit conclusion (fatal):** *None* of the verified datasets includes the six required columns (`news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`, `social_media_engagement`). Consequently, the pipeline will **download the three verified files, record their true column inventories, and halt at schema validation** (FR‑001 edge case). No statistical analysis can be performed until a verified open dataset with the required schema is supplied or the spec is formally re‑scoped.

### Variable Mapping (applies when a suitable dataset is added)

| Spec Variable | Expected Column | Validation Rules |
|---------------|----------------|------------------|
| `news_exposure_freq` | `news_exposure_freq` | numeric ≥ 0, non‑null |
| `anxiety_score` | `anxiety_score` | numeric ≥ 0, non‑null |
| `baseline_anxiety` | `baseline_anxiety` | numeric ≥ 0, may be null if instrument overlaps with outcome |
| `age` | `age` | integer 18–100, non‑null |
| `gender` | `gender` | categorical, non‑null |
| `social_media_engagement` | `social_media_engagement` | numeric ≥ 0, optional (required only for robustness check) |
| `instrument_source` | `instrument_source` | string identifying the anxiety scale |
| `measurement_timepoint` | `measurement_timepoint` | string (e.g., “pre”, “post”, “trait”) |

If only a **general anxiety** measure is present, `proxy_flag = true` and the construct‑validity limitation is recorded (FR‑008).

## Data Hygiene & Missing Data
- **Checksum**: SHA‑256 recorded for every raw file under `data/raw/`.  
- **Listwise deletion** on rows missing `news_exposure_freq` or `anxiety_score`; hard stop if resulting N < 30 (FR‑002).  
- **Low‑power warning** if 30 ≤ N < 100 (spec‑defined).  
- No imputation is performed.

## Statistical Methodology

### Primary Model (OLS)
\[
\text{anxiety\_score} = \beta_0 + \beta_1\text{NewsFreq} + \beta_2\text{BaselineAnx} + \beta_3\text{Age} + \beta_4\text{Gender} + \varepsilon
\]

- **Assumption checks**: residuals‑vs‑fitted (linearity), Breusch‑Pagan (homoscedasticity), Shapiro‑Wilk (normality of residuals), VIF > 10 flag (collinearity).  
- **Multiple‑comparison correction**: Bonferroni for the four predictors (α = 0.05/4) as required by SC‑001.  
- **Power**: N thresholds enforced; no external power calculation beyond the spec’s thresholds.  
- **Causal framing**: All outputs include `"associational_only": true`.

### Correlation
- Perform Shapiro‑Wilk on both variables; if both p > 0.05, report **Pearson** r with 95 % CI; otherwise report **Spearman** ρ with CI (FR‑004).

### Robustness Check (FR‑006)
1. Compute `r_engage = corr(social_media_engagement, news_exposure_freq)`.  
2. If `r_engage > 0.3` **and** the variable exists, refit the OLS on participants whose `social_media_engagement` falls in the top [deferred] percentile.
3. Compare sign and significance of β₁ between full sample and subset; record outcome in `robustness_result`.  
4. If the gate fails, log a warning and set `status = "SKIPPED_R_LOW"`.

### Multiple Comparisons
Only the primary hypothesis (β₁) is tested; Bonferroni correction is applied across the four predictors per SC‑001.

### Power & Sample‑size
- **Hard stop** at N < 30 (FR‑002).  
- **Low‑power flag** for 30 ≤ N < 100 (SC‑001, SC‑005).  
- No a‑priori sample‑size target is invented.

### Collinearity
VIF computed for each predictor; VIF > 10 triggers a `High VIF` flag and suppresses independent‑effect claims (edge case in FR‑003).

## Decision / Rationale (Compute)
All steps run on CPU using pandas, statsmodels, and matplotlib; the dataset size (three parquet files ≈ < 1 GB) comfortably fits the free‑tier runner. No GPU escape hatch is needed. The *real* computation performed in this revision is the download, checksum, and schema‑validation of the three verified files, leading to an honest halt record. This respects the fabrication‑result policy: no numbers are invented; the pipeline reports the genuine mismatch.

## Fabrication‑Result Policy (rev. 2)
- **No synthetic data** are generated.  
- When a required variable is missing, the pipeline **halts** and records a detailed `halt_report`.  
- All JSON, CSV, and plot artifacts contain only values derived from real files.  
- Success‑criteria validation (`code/validate_sc.py`) is executed on the actual outputs; the resulting log is the evidence for SC‑001 – SC‑005.

---
