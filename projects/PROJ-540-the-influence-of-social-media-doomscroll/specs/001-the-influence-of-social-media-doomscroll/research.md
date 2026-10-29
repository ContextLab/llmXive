# Research: The Influence of Social Media “Doomscrolling” on Anticipatory Anxiety

## Research Question
*Is the frequency of negative news consumption on social media **associated** with elevated anticipatory anxiety scores, independent of baseline anxiety and demographic factors?*  
All conclusions are explicitly **associational** because the data are observational; no causal language is used in any downstream artifact.

## Theoretical Background
“Doomscrolling” describes prolonged consumption of negative news on social platforms. Prior work links media exposure to heightened anxiety, but few studies have simultaneously controlled for baseline anxiety, age, and gender. This project tests that association while respecting psychometric and ethical constraints.

## Dataset Strategy

### Verified Sources (the ONLY citable URLs)

| Dataset | Verified URL | Contains required variables? |
|---------|--------------|------------------------------|
| mini‑xlsum (GSS‑style) | `https://huggingface.co/datasets/gsstein/mini-xlsum/resolve/main/data/test-00000-of-00001.parquet` | **NO** – lacks required survey columns |
| 0‑percent‑human | `https://huggingface.co/datasets/gsstein/0-percent-human-dataset-og/resolve/main/data/test-00000-of-00001.parquet` | **NO** – text corpus, no survey variables |
| 100‑percent‑human | `https://huggingface.co/datasets/gsstein/100-percent-human-dataset/resolve/main/data/test-00000-of-00001.parquet` | **NO** – text corpus, no survey variables |
| YouGov | — (no verified source) | **NO** – not programmatically downloadable |

**Dataset‑variable fit conclusion (fatal):** *None* of the verified datasets provides the six required columns (`news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`, `social_media_engagement`). Consequently, the pipeline **halts** at **Schema Validation** (FR‑001 edge case) and records a detailed `halt_report`. No synthetic data are generated.

**Future Data Provision**  
When a verified open‑access survey (e.g., a Pew Research “Social Media Use & Mental Health” CSV hosted on HuggingFace) becomes available that includes the required variables **and** a validated anxiety instrument (e.g., GAD‑7), the pipeline will automatically ingest, clean, and analyze it. The acquisition task **T010a_acquire_valid_dataset** in the implementation plan will handle this.

### Variable Mapping (applies once a suitable dataset is added)

| Spec Variable | Expected Column | Validation Rules |
|---------------|----------------|------------------|
| `news_exposure_freq` | `news_exposure_freq` | numeric ≥ 0, non‑null |
| `anxiety_score` | `anxiety_score` | numeric ≥ 0, non‑null |
| `baseline_anxiety` | `baseline_anxiety` | numeric ≥ 0, may be null if instrument overlaps |
| `age` | `age` | integer 18–100, non‑null |
| `gender` | `gender` | categorical, non‑null |
| `social_media_engagement` | `social_media_engagement` | numeric ≥ 0, optional (robustness) |
| `instrument_source` | `instrument_source` | non‑null string |
| `measurement_timepoint` | `measurement_timepoint` | `pre`, `post`, or `trait` |
| `proxy_flag` | `proxy_flag` | boolean |
| `proxy_validated` | `proxy_validated` | boolean |
| `coupling_risk` | `coupling_risk` | boolean |
| `missingness_indicator_<var>` | boolean \| null | Indicator for non‑MCAR missingness for each predictor (added when MCAR test fails) | optional |
| `vif_score` | number \| null | VIF for the variable after model fit (added for diagnostics) | optional |

If only a **general anxiety** measure is present, `proxy_flag = true` and a construct‑validity limitation is recorded (FR‑008). If the proxy instrument is not on the validated whitelist, the run halts (FR‑008).

## Data Hygiene & Missing Data
- **Checksum**: SHA‑256 recorded for each raw file under `data/raw/`.  
- **Missingness**: Little’s MCAR test is performed. If MCAR fails **and** the missingness proportion for `news_exposure_freq` or `anxiety_score` is ≤ 10 % (the threshold for FR‑009), binary missingness indicators are added and a 10‑fold `IterativeImputer` is used as a **sensitivity** analysis; primary analysis remains listwise deletion (required N ≥ 30).  
- **Listwise deletion** is used only when MCAR holds and the resulting N ≥ 30 (hard stop if N < 30 per FR‑002).  

## Statistical Methodology

### Primary Model (OLS)

\[
\text{anxiety\_score}= \beta_0 + \beta_1\text{NewsFreq}_{\text{std}} + \beta_2\text{BaselineAnx} + \beta_3\text{SocialEngage} + \beta_4\text{Age} + \beta_{5..}\text{Gender}_{\text{(one‑hot)}} + \varepsilon
\]

- `NewsFreq_std` is the **z‑score** of `news_exposure_freq`; this standardization makes the β ≥ 0.10 threshold scale‑independent (addresses scientific‑soundness concern).  
- **Distinctness check** (FR‑003): if `baseline_anxiety` and `anxiety_score` share the same instrument, `coupling_risk=True` and **baseline_anxiety is dropped** from the model; a warning flag is attached.  
- **Proxy handling** (FR‑008): if `proxy_flag=True`, performs exploratory factor analysis; requires loading ≥ 0.4 on an anticipatory‑anxiety factor **and** the instrument be on the whitelist. If the proxy instrument is not validated, the run halts. When a validated proxy is used, a construct‑validity warning flag is attached.  
- **Assumption checks** (FR‑005, FR‑007): residual‑vs‑fitted linearity, Breusch‑Pagan homoscedasticity, residual normality; VIF > 10 flag. Raw p‑values are stored; **if any assumption p‑value ≤ 0.05 the pipeline aborts**, enforcing SC‑004.  
- **Correlation** – selects Pearson or Spearman based on normality of `news_exposure_freq_std` and `anxiety_score`.  
- **Effect‑size thresholds** (SC‑001): Report statistical significance (p < 0.05) **and** either standardized β ≥ 0.10 **or** incremental f² ≥ 0.02. Both must hold for a PASS.  
- **Power analysis**: A priori power analysis (see plan) ensures minimum N for detecting β ≥ 0.10 (standardized) at [deferred] power; if N after cleaning falls below this target, the run halts with “Insufficient Power”.  
- **Causal framing**: All output JSON fields include `"associational_only": true`. A downstream scan (task **T025_causal_language_check**) ensures no causal verbs appear in any generated text.  

### Robustness Checks (FR‑006)

1. **High‑engagement subset** – if `social_media_engagement` exists and its Pearson correlation with `news_exposure_freq_std` is |r| > 0.3, refit OLS on the top [deferred] of engagement.  
2. **Sign‑consistency & significance** – after the subset model, **compare the sign of the `news_exposure_freq_std` coefficient and its p‑value to the full‑sample model**; if they differ, set a `"RobustnessSignMismatch"` flag. This explicit check satisfies SC‑003.  
3. **Alternative covariates** – if extra variables (e.g., personality) are present, run a model including them.  
4. **Robust regression** – run a Huber regression on the full sample as a further sensitivity check.

### Multiple‑Comparison
Only a single primary predictor (`news_exposure_freq_std`) is tested; no family‑wise correction is required.

### Causal‑Inference Assumptions
Data are observational; all statements are framed as associations, not causation.

### Measurement Validity
Anxiety instruments are cross‑checked against a whitelist (`GAD‑7`, `STAI‑Y`, `PHQ‑9`). If a proxy is used, factor‑analysis validation (see above) determines acceptability.  

## Decision / Rationale (Compute)
All steps are CPU‑only, using `pandas`, `statsmodels`, `scikit‑learn`, and `factor_analyzer`. The three parquet files together are < 1 GB, well within the free‑tier runner limits. Because the current verified sources lack the required variables, the pipeline **intentionally halts** after schema validation and records a comprehensive `halt_report`. This respects the fabrication‑result policy: no numbers are invented; the halt is a truthful, reproducible outcome.

## Fabrication‑Result Policy (rev. 2)
- **No synthetic data** are generated.  
- When a required variable is missing, the pipeline **halts** and records a detailed `halt_report`.  
- All JSON, CSV, and plot artifacts contain only values derived from real files.  
- Success‑criteria validation (`code/validate_sc.py`) runs on the actual outputs; the resulting log is the evidence for SC‑001 – SC‑005.  

---


