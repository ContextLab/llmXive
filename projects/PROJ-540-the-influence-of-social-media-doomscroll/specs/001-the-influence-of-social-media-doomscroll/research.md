# Research: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

## Research Question
*Does the frequency of negative news consumption on social media associate with elevated anxiety scores, independent of baseline anxiety and demographic factors?*
All claims are **associational** (observational data).

## Theoretical Background
"Doomscrolling" denotes habitual consumption of negative news on social platforms, potentially heightening anticipatory anxiety. Prior work suggests a media-exposure/anxiety link, but few studies isolate negative-news frequency while controlling for baseline anxiety and demographics.

## Dataset Strategy

### Verified sources (the ONLY citable URLs)

| Dataset | Verified URL | Contains required variables? |
|---------|--------------|------------------------------|
| mini-xlsum text corpus | `https://huggingface.co/datasets/gsstein/mini-xlsum/resolve/main/data/test-00000-of-00001.parquet` | **NO** — NLP text-summarization corpus; no `news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`, or `social_media_engagement` |
| 0-percent-human text corpus | `https://huggingface.co/datasets/gsstein/0-percent-human-dataset-og/resolve/main/data/test-00000-of-00001.parquet` | **NO** — human-vs-AI text corpus |
| 100-percent-human text corpus | `https://huggingface.co/datasets/gsstein/100-percent-human-dataset/resolve/main/data/test-00000-of-00001.parquet` | **NO** — human-vs-AI text corpus |
| YouGov surveys | (no verified source found — not citable) | Unknown |

Note: the three verified sources are NLP corpora unrelated to the General Social Survey; they are used only to exercise the real ingestion path.

**Correction (rev. 2)**: The prior revision cited `https://huggingface.co/datasets/pew/social_media_anxiety` as the primary dataset. That URL was **not** among the verified sources and must not be cited or used; it has been removed everywhere.

**Dataset-variable fit conclusion (fatal, stated explicitly)**: None of the verified sources contains the variables this study requires. The dataset-variable fit check therefore FAILS for every obtainable source. Per the methodology rules, we do **not** plan as if a dataset fits: the pipeline will download the three verified parquet files for real, record their actual column inventories and checksums, and halt at schema validation with an explicit mismatch error (exactly the FR-001 edge case). **The research question cannot be answered with currently available data.** Advancement to statistical results is conditional on (a) a verified dataset with the required variables being supplied, or (b) a formal spec re-scope; the executed halt record is interim ingestion evidence only, not a scientific deliverable. **No synthetic, simulated, or placeholder data will be substituted.**

### Variable Mapping (applies when a suitable verified dataset is added)

| Spec Variable | Required Column | Validation |
|---------------|----------------|------------|
| `news_exposure_freq` | same name | Numeric ≥ 0 |
| `anxiety_score` | same name | Numeric ≥ 0 |
| `baseline_anxiety` | same name | Numeric ≥ 0; dropped if not distinct from outcome |
| `age` | same name | Integer 18–100 |
| `gender` | same name | Categorical |
| `social_media_engagement` | same name | Numeric ≥ 0; needed only for the robustness check |

If only a general anxiety measure exists, `proxy_flag = true` and the construct-validity limitation is documented (FR-008).

## Data Hygiene & Missing Data
- Listwise deletion on missing predictor/outcome; hard stop if N < 30 (FR-002); "Low Power" preliminary flag for 30 ≤ N < 100 per the spec. (The prior revision's unsourced "required N ≈ 85" figure has been removed; the spec specifies only the 30/100 thresholds, and those are what the pipeline implements.)
- No imputation. Checksums (SHA-256) recorded for all raw files.

## Statistical Methodology

### Primary Model (OLS)
Anxiety = β₀ + β₁·NewsFreq + β₂·BaselineAnx + β₃·Age + β₄·Gender + ε

- Assumption checks: residuals-vs-fitted (linearity), Breusch-Pagan (homoscedasticity), Shapiro-Wilk (normality), VIF (collinearity; VIF > 10 flags instability per spec edge case).
- All fitted only if a verified dataset passes schema validation.

### Correlation
Pearson (Spearman if ordinal), reported with CI.

### Robustness Check (FR-006)
1. `r_engage = corr(social_media_engagement, news_exposure_freq)`.
2. If r_engage > 0.3 and the variable exists: refit OLS on the top-quartile engagement subset; compare coefficient sign and significance to the full sample (SC-003).
3. Else: skip and log a warning (per FR-006). The r > 0.3 threshold is taken directly from the spec, not invented here.

### Multiple Comparisons
Single primary hypothesis (β₁); no family-wise correction needed.

### Power
The spec's thresholds (N < 30 halt; 30 ≤ N < 100 preliminary) are implemented verbatim; post-hoc power is reported descriptively when a real sample exists. No numeric power targets beyond the spec are asserted.

### Causal Framing
Observational data → associational language only, enforced in output flags.

## Decision / Rationale (compute)
Everything runs on CPU (pandas/statsmodels/matplotlib on parquet files far below the runner limits; total runtime seconds). **No GPU escape hatch is needed or used.** The real computation performed in this revision is: download of the three verified parquet files, checksumming, column-inventory extraction, and schema validation — all real measurements on real data, whose honest outcome is a documented variable mismatch and pipeline halt. This halt record is interim ingestion evidence; it does not constitute a research result, and no statistical claim is advanced on its basis.

## Fabrication-Result Policy (rev. 2)
Research results must be REAL measurements. The prior tasks.md contained self-declared fabricated-metric language ("hard-coded result arrays", "uniform used in analysis"). This revision prohibits and removes all such patterns: no `random.*`-generated "results", no placeholder arrays, no hard-coded coefficients. Where data is unavailable, the pipeline reports BLOCKED-PENDING-DATA with the documented reason — it never invents numbers.

---