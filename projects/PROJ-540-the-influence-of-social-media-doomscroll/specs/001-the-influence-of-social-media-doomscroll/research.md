# Research: The Influence of Social Media “Doomscrolling” on Anticipatory Anxiety

## Research Question
*Does the frequency of negative news consumption on social media associate with elevated anticipatory anxiety scores, independent of baseline anxiety and demographic factors?*  
All statements are explicitly **associational** because the data are observational.

## Theoretical Background
“Doomscrolling” refers to the habitual consumption of negative news on social platforms. Prior work suggests that such exposure may heighten anticipatory anxiety, but few studies have simultaneously controlled for baseline anxiety, age, and gender.

## Dataset Strategy

### Verified Sources (the ONLY citable URLs)

| Dataset | Verified URL | Contains required variables? |
|---------|--------------|------------------------------|
| mini‑xlsum text corpus | `https://huggingface.co/datasets/gsstein/mini-xlsum/resolve/main/data/test-00000-of-00001.parquet` | **NO** – NLP summarization data; lacks all survey variables |
| 0‑percent‑human text corpus | `https://huggingface.co/datasets/gsstein/0-percent-human-dataset-og/resolve/main/data/test-00000-of-00001.parquet` | **NO** – human‑vs‑AI text data; no relevant variables |
| 100‑percent‑human text corpus | `https://huggingface.co/datasets/gsstein/100-percent-human-dataset/resolve/main/data/test-00000-of-00001.parquet` | **NO** – same as above |
| YouGov surveys | — (no verified source) | **NO** – not programmatically downloadable |

**Dataset‑variable fit conclusion (fatal):** *None* of the verified datasets includes the six required columns (`news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`, `social_media_engagement`). Consequently, the pipeline will **download the three files, record their true column inventories, and halt at schema validation** (FR‑001 edge case). A suitable open dataset must be supplied for any statistical analysis to proceed.

### Variable Mapping (applies when a suitable dataset is added)

| Spec Variable | Expected Column | Validation Rules |
|---------------|----------------|------------------|
| `news_exposure_freq` | `news_exposure_freq` | numeric ≥ 0, non‑null |
| `anxiety_score` | `anxiety_score` | numeric ≥ 0, non‑null |
| `baseline_anxiety` | `baseline_anxiety` | numeric ≥ 0, may be null if instrument overlaps with outcome |
| `age` | `age` | integer 18–100, non‑null |
| `gender` | `gender` | categorical, non‑null |
| `social_media_engagement` | `social_media_engagement` | numeric ≥ 0, optional (required only for robustness check) |
| `instrument_source` | `instrument_source` | string identifying the anxiety scale (must be in validated whitelist) |
| `measurement_timepoint` | `measurement_timepoint` | string (e.g., “pre”, “post”, “trait”) |
| `proxy_flag` | `proxy_flag` | boolean – true if `anxiety_score` is a proxy for anticipatory anxiety (FR‑008) |
| `proxy_validated` | `proxy_validated` | boolean – true if the proxy instrument is on the validated whitelist (new field) |
| `coupling_risk` | `coupling_risk` | boolean – true if baseline and outcome anxiety may be mathematically coupled |

If only a **general anxiety** measure is present, `proxy_flag = true` and the construct‑validity limitation is recorded (FR‑008). If the proxy instrument is not on the validated whitelist, `proxy_validated = false` and the results are flagged accordingly. The flag influences interpretation: SC‑001 effect‑size thresholds are still evaluated, but any claim about *anticipatory* anxiety is qualified with a construct‑validity warning.

## Data Hygiene & Missing Data
- **Checksum**: SHA‑256 recorded for every raw file under `data/raw/`.  
- **Listwise deletion** on rows missing `news_exposure_freq` or `anxiety_score`; hard stop if resulting N < 30 (FR‑002).  
- **Low‑power warning** if 30 ≤ N < 100 (spec‑defined).  
- **Missing‑data mechanism assessment**: Little’s MCAR test is run after cleaning; the p‑value and a “MCAR” / “Not MCAR” flag are logged. No imputation is performed, but a non‑MCAR flag is reported to inform interpretation.  
- No imputation is performed.

## Statistical Methodology

### Primary Model (OLS)
\[
\text{anxiety\_score} = \beta_0 + \beta_1\text{NewsFreq} + \beta_2\text{BaselineAnx} + \beta_3\text{Age} + \beta_4\text{Gender} + \varepsilon
\]

- **Distinctness check**: `baseline_anxiety` is retained only if `instrument_source` **or** `measurement_timepoint` differs from those of `anxiety_score`. If they match, `coupling_risk = true`, the variable is dropped, and a flag is added (FR‑003).  
- **Proxy handling**: The `proxy_validated` flag is recorded; if `proxy_flag` is true and `proxy_validated` is false, all effect‑size claims are presented with a construct‑validity warning (FR‑008).  
- **A‑priori power analysis**: Before fitting, the pipeline computes the minimum N required to detect β ≥ 0.10 (or f² ≥ 0.02) at α = 0.05, power = 0.80 using `statsmodels.stats.power.FTestPower`. If the cleaned sample size is below this threshold, the analysis halts with a clear “Insufficient Power” error (new FR‑014).  
- **Assumption checks**: residual‑vs‑fitted (linearity), Breusch‑Pagan (homoscedasticity), Shapiro‑Wilk (normality of residuals), VIF > 10 flag (collinearity) (FR‑007).  
- **Correlation**: Shapiro‑Wilk on both `news_exposure_freq` and `anxiety_score`; if both p > 0.05, report **Pearson** r, otherwise **Spearman** ρ (FR‑004).  
- **Robustness check**: Compute normality‑aware correlation between `social_media_engagement` and `news_exposure_freq`; if the absolute correlation |r| > 0.3 **and** the variable exists, refit the OLS on participants whose `social_media_engagement` falls in the top percentile; record coefficient, p‑value, and flag any sign flip or loss of significance (FR‑006). If the gate fails, log a warning.  
- **Multiple‑comparison correction**: **None** (SC‑001 explicitly states no Bonferroni correction).  
- **Effect‑size thresholds**: SC‑001 requires β ≥ 0.10 **or** incremental f² ≥ 0.02 **and** p < 0.05 for `news_exposure_freq`. Both statistical significance and at least one of the effect‑size thresholds must be satisfied.  
- **Causal framing**: All outputs include `"associational_only": true`.

## Decision / Rationale (Compute)
All steps run on CPU using pandas, statsmodels, and matplotlib; the dataset size (three parquet files ≈ < 1 GB) comfortably fits the free‑tier runner. The *real* computation performed in this revision is the download, checksum, schema‑validation, power analysis, missingness test, and a graceful halt record. This respects the fabrication‑result policy: no numbers are invented; the pipeline reports the genuine mismatch.

## Fabrication‑Result Policy (rev. 2)
- **No synthetic data** are generated.  
- When a required variable is missing, the pipeline **halts** and records a detailed `halt_report`.  
- All JSON, CSV, and plot artifacts contain only values derived from real files.  
- Success‑criteria validation (`code/validate_sc.py`) is executed on the actual outputs; the resulting log is the evidence for SC‑001 – SC‑005.

---


