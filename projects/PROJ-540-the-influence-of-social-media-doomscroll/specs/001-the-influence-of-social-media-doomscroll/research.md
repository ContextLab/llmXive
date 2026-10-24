# Research: The Influence of Social Media “Doomscrolling” on Anticipatory Anxiety

## Research Question
*Does the frequency of negative news consumption on social media associate with elevated anticipatory anxiety scores, independent of baseline anxiety and demographic factors?*  
All statements are explicitly **associational** because the data are observational.

## Theoretical Background
“Doomscrolling” refers to the habitual consumption of negative news on social platforms. Prior work suggests that such exposure may heighten anticipatory anxiety, but few studies have simultaneously controlled for baseline anxiety, age, gender, and broader socioeconomic factors.

## Dataset Strategy

### Verified Sources (the ONLY citable URLs)

| Dataset | Verified URL | Contains required variables? |
|---------|--------------|------------------------------|
| mini‑xlsum text corpus | `https://huggingface.co/datasets/gsstein/mini-xlsum/resolve/main/data/test-00000-of-00001.parquet` | **NO** – NLP summarization data; lacks all survey variables |
| 0‑percent‑human text corpus | `https://huggingface.co/datasets/gsstein/0-percent-human-dataset-og/resolve/main/data/test-00000-of-00001.parquet` | **NO** – human‑vs‑AI text data; no relevant variables |
| 100‑percent‑human text corpus | `https://huggingface.co/datasets/gsstein/100-percent-human-dataset/resolve/main/data/test-00000-of-00001.parquet` | **NO** – same as above |
| YouGov surveys | — (no verified source) | **NO** – not programmatically downloadable |

**Dataset‑variable fit conclusion (fatal):** *None* of the verified datasets includes the six required columns (`news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`, `social_media_engagement`). Consequently, the pipeline will **download the three files, record their true column inventories, and halt at schema validation** (FR‑001 edge case). A suitable open dataset must be supplied for any statistical analysis to proceed. No synthetic data are generated.

*Future data provision*: When a verified open survey dataset (e.g., a Pew Research “Social Media Use & Mental Health” CSV hosted on HuggingFace with a direct URL) is added to the spec, the pipeline will automatically ingest, clean, and analyze it according to the plan.

### Variable Mapping (applies when a suitable dataset is added)

| Spec Variable | Expected Column | Validation Rules |
|---------------|----------------|------------------|
| `news_exposure_freq` | `news_exposure_freq` | numeric ≥ 0, non‑null |
| `anxiety_score` | `anxiety_score` | numeric ≥ 0, non‑null |
| `baseline_anxiety` | `baseline_anxiety` | numeric ≥ 0, may be null if instrument overlaps with outcome |
| `age` | `age` | integer 18–100, non‑null |
| `gender` | `gender` | categorical, non‑null |
| `social_media_engagement` | `social_media_engagement` | numeric ≥ 0, optional (required only for robustness check) |
| `SES` | `SES` | categorical, optional confounder |
| `total_media_use` | `total_media_use` | numeric ≥ 0, optional confounder |
| `instrument_source` | `instrument_source` | string identifying the anxiety scale (must be on a validated whitelist) |
| `measurement_timepoint` | `measurement_timepoint` | string (e.g., “pre”, “post”, “trait”) |
| `proxy_flag` | `proxy_flag` | boolean – true if `anxiety_score` is a proxy for anticipatory anxiety (FR‑008) |
| `proxy_validated` | `proxy_validated` | boolean – true if the proxy instrument is on the validated whitelist |
| `coupling_risk` | `coupling_risk` | boolean – true if baseline and outcome anxiety may be mathematically coupled |

If only a **general anxiety** measure is present, `proxy_flag = true` and the construct‑validity limitation is recorded (FR‑008). If the proxy instrument is not on the validated whitelist, `proxy_validated = false` and the results are flagged accordingly.

## Data Hygiene & Missing Data
- **Checksum**: SHA‑256 recorded for every raw file under `data/raw/`.  
- **Listwise deletion** on rows missing `news_exposure_freq` or `anxiety_score`; hard stop if resulting N < 30 (FR‑002).  
- **Low‑power warning** if 30 ≤ N < 100 (spec‑defined).  
- **Missing‑data diagnostics**: Little’s MCAR test (T015) is run after cleaning; if the test indicates non‑MCAR (p < 0.05), binary missingness indicator variables are added to the regression and a bias warning is logged. Additionally, an optional multiple‑imputation sensitivity analysis (10‑fold) is executed to assess robustness (addressing methodology‑fdd0a1d0).

## Statistical Methodology

### Primary Model (OLS)
\[
\text{anxiety\_score} = \beta_0 + \beta_1\text{NewsFreq} + \beta_2\text{BaselineAnx} + \beta_3\text{Age} + \beta_4\text{Gender} + \beta_5\text{SES} + \beta_6\text{TotalMediaUse} + \beta_7\text{PriorMH} + \varepsilon
\]

- **Distinctness check**: `baseline_anxiety` is retained only if `instrument_source` **or** `measurement_timepoint` differs from those of `anxiety_score`, using `variable_metadata.csv` (FR‑003). If they match, `coupling_risk = true`, the variable is dropped, and a flag is added (FR‑003).  
- **Proxy handling**: The `proxy_validated` flag is recorded; if `proxy_flag` is true and `proxy_validated` is false, the pipeline halts (FR‑008). If validated, a construct‑validity warning is attached but analysis proceeds.  
- **Assumption checks**: residual‑vs‑fitted (linearity), Breusch‑Pagan (homoscedasticity), Shapiro‑Wilk (normality of residuals), VIF > 10 flag (collinearity) (FR‑007).  
- **Correlation**: Shapiro‑Wilk on both `news_exposure_freq` and `anxiety_score`; if both p > 0.05, report **Pearson** r, otherwise **Spearman** ρ (FR‑004).  
- **Robustness check**: Compute correlation between `social_media_engagement` and `news_exposure_freq`; if the absolute correlation |r| > 0.3 **and** the variable exists, refit the OLS on participants whose `social_media_engagement` falls in the top percentile; record coefficient, p‑value, and flag any sign flip or loss of significance (FR‑006). If the gate fails, log a warning.  
- **Multiple‑comparison correction**: **None** (SC‑001 explicitly states no Bonferroni correction).  
- **Effect‑size thresholds**: SC‑001 requires β ≥ 0.10 **or** incremental f² ≥ 0.02 **and** p < 0.05 for `news_exposure_freq`. Both statistical significance and at least one of the effect‑size thresholds must be satisfied.  
- **Causal framing**: All outputs include `"associational_only": true`.

## Decision / Rationale (Compute)
All steps run on CPU using pandas, statsmodels, and matplotlib; the dataset size (three parquet files ≈ < 1 GB) comfortably fits the free‑tier runner. The *real* computation performed in this revision is the download, checksum, schema‑validation, and a graceful halt record. This respects the fabrication‑result policy: no numbers are invented; the pipeline reports the genuine mismatch.

## Fabrication‑Result Policy (rev. 2)
- **No synthetic data** are generated.  
- When a required variable is missing, the pipeline **halts** and records a detailed `halt_report`.  
- All JSON, CSV, and plot artifacts contain only values derived from real files.  
- Success‑criteria validation (`code/validate_sc.py`) is executed on the actual outputs; the resulting log is the evidence for SC‑001 – SC‑005.

---


