# Research: The Influence of Social Media “Doomscrolling” on Anticipatory Anxiety

## Research Question
*Does the frequency of negative news consumption on social media associate with elevated anticipatory anxiety scores, independent of baseline anxiety and demographic factors?*  
All conclusions are explicitly **associational** because the data are observational.

## Theoretical Background
“Doomscrolling” describes prolonged consumption of negative news on social platforms. Prior work links media exposure to heightened anxiety, but few studies have simultaneously controlled for baseline anxiety, age, and gender. This project tests that association while respecting psychometric and ethical constraints.

## Dataset Strategy

### Verified Sources (the ONLY citable URLs)

| Dataset | Verified URL | Contains required variables? |
|---------|--------------|------------------------------|
| mini‑xlsum (GSS‑style) | `https://huggingface.co/datasets/gsstein/mini-xlsum/resolve/main/data/test-00000-of-00001.parquet` | **NO** – lacks all required survey columns |
| 0‑percent‑human | `https://huggingface.co/datasets/gsstein/0-percent-human-dataset-og/resolve/main/data/test-00000-of-00001.parquet` | **NO** – text‑corpus, no survey variables |
| 100‑percent‑human | `https://huggingface.co/datasets/gsstein/100-percent-human-dataset/resolve/main/data/test-00000-of-00001.parquet` | **NO** – text‑corpus, no survey variables |
| YouGov | — (no verified source) | **NO** – not programmatically downloadable |

**Dataset‑variable fit conclusion (fatal):** *None* of the verified datasets provides the six required columns (`news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`, `social_media_engagement`). Consequently, the pipeline halts at **Schema Validation** (FR‑001 edge case) and records a detailed `halt_report`. No synthetic data are generated.

*Future data provision*: When a verified open‑access survey (e.g., a Pew Research “Social Media Use & Mental Health” CSV hosted on HuggingFace) becomes available, the same pipeline will automatically ingest, clean, and analyze it.

### Variable Mapping (applies once a suitable dataset is added)

| Spec Variable | Expected Column | Validation Rules |
|---------------|----------------|------------------|
| `news_exposure_freq` | `news_exposure_freq` | numeric ≥ 0, non‑null |
| `anxiety_score` | `anxiety_score` | numeric ≥ 0, non‑null |
| `baseline_anxiety` | `baseline_anxiety` | numeric ≥ 0, may be null if instrument overlaps |
| `age` | `age` | integer 18–100, non‑null |
| `gender` | `gender` | categorical, non‑null |
| `social_media_engagement` | `social_media_engagement` | numeric ≥ 0, optional (robustness) |
| `instrument_source` | `instrument_source` | string identifying the anxiety scale |
| `measurement_timepoint` | `measurement_timepoint` | string (`pre`, `post`, `trait`) |
| `proxy_flag` | `proxy_flag` | boolean – true if `anxiety_score` is a proxy (FR‑008) |
| `proxy_validated` | `proxy_validated` | boolean – true if proxy instrument is on whitelist |
| `coupling_risk` | `coupling_risk` | boolean – true if baseline & outcome may be mathematically coupled |

If only a **general anxiety** measure is present, `proxy_flag = true` and a construct‑validity limitation is recorded (FR‑008). If the proxy instrument is not on the validated whitelist, the pipeline halts (FR‑008).

## Data Hygiene & Missing Data
- **Checksum**: SHA‑256 recorded for each raw file under `data/raw/`.  
- **Listwise deletion** on rows missing `news_exposure_freq` or `anxiety_score`; hard stop if resulting N < 30 (FR‑002).  
- **Low‑power warning** when 30 ≤ N < 100 (per SC‑001 power note).  
- **Missing‑data diagnostics**: Little’s MCAR test (T015). If MCAR fails (p < 0.05), binary missingness indicators are added and a 10‑fold multiple‑imputation sensitivity analysis is run (methodological safeguard).  

## Statistical Methodology

### Primary Model (OLS)

\[
\text{anxiety\_score}= \beta_0 + \beta_1\text{NewsFreq} + \beta_2\text{BaselineAnx} + \beta_3\text{Age} + \beta_4\text{Gender}_{\text{(one‑hot)}} + \varepsilon
\]

- **Distinctness check** (FR‑003): `baseline_anxiety` is retained only if its `instrument_identifier` **or** `measurement_timepoint` differs from `anxiety_score`. If not, it is dropped and `coupling_risk=True`.  
- **Proxy handling** (FR‑008): If `proxy_flag=True` and `proxy_validated=False`, the run halts. If validated, a construct‑validity warning flag is attached.  
- **Assumption checks** (FR‑007): residual‑vs‑fitted linearity, Breusch‑Pagan homoscedasticity, Shapiro‑Wilk normality of residuals, VIF > 10 flag.  
- **Correlation choice** (FR‑004): Pearson r if both `news_exposure_freq` and `anxiety_score` are normal (Shapiro‑Wilk p > 0.05); otherwise Spearman ρ.  
- **Robustness check** (FR‑006): Compute correlation between `social_media_engagement` and `news_exposure_freq`. If |r| > 0.3, refit the OLS on the top‑percentile (75th) of engagement; otherwise log a warning.  
- **Effect‑size thresholds** (SC‑001): Report statistical significance (p < 0.05) **and** either β ≥ 0.10 **or** incremental f² ≥ 0.02. Both must hold for a PASS.  
- **Causal framing**: All output JSON fields include `"associational_only": true`.  

## Decision / Rationale (Compute)
All steps are CPU‑only, using `pandas`, `statsmodels`, and `matplotlib`. The three parquet files together are < 1 GB, well within the free‑tier runner limits. Because the current verified sources lack the required variables, the pipeline **intentionally halts** after schema validation and records a comprehensive `halt_report`. This respects the fabrication‑result policy: no numbers are invented; the halt is a truthful, reproducible outcome.

## Fabrication‑Result Policy (rev. 2)
- **No synthetic data** are generated.  
- When a required variable is missing, the pipeline **halts** and records a detailed `halt_report`.  
- All JSON, CSV, and plot artifacts contain only values derived from real files.  
- Success‑criteria validation (`code/validate_sc.py`) runs on the actual outputs; the resulting log is the evidence for SC‑001 – SC‑005.  

---
