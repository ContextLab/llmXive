# Implementation Plan: The Impact of Parasocial Relationships with AI Companions on Loneliness

**Branch**: `001-ai-companion-loneliness-impact` | **Date**: 2026-10-16 | **Spec**: `specs/001-the-impact-of-parasocial-relationships-w/spec.md`  
**Input**: Feature specification from `/specs/001-the-impact-of-parasocial-relationships-w/spec.md`

## Summary
The project conducts a longitudinal observational study of how AI‑companion usage relates to self‑reported loneliness, controlling for baseline attachment style (proxied via the ECAR lexicon) **and** baseline mental‑health and socioeconomic status (SES). **Important feasibility note:** No publicly‑available *Reddit Loneliness Longitudinal Dataset* that includes validated UCLA Loneliness Scale scores **and** the required baseline raw text has been identified. If the Zenodo DOI cannot be fetched or the CSV lacks the required columns, the pipeline will abort with a clear **“Data Linkage Impossible”** error (see Phase 0). This explicit check prevents the study from proceeding with fabricated or incomplete data.

The pipeline will:

1. **Ingest** the Reddit Loneliness Longitudinal Dataset **if** a verified open source is found; otherwise abort with the error above. Pull AI interaction logs from the public Pushshift API using streaming and exponential back‑off.  
2. **Match** users across the two sources using SHA‑256 hashes of **normalized** Reddit usernames (lower‑cased, stripped of whitespace). A secondary fuzzy‑hash fallback is applied for usernames that differ due to case or minor edits; unresolved mismatches are reported and those users are excluded.  
3. **Engineer** weekly usage metrics (frequency, session duration) and extract attachment‑style proxies using the **validated ECAR lexicon** (Rashkin et al., 2023). Baseline mental‑health (e.g., PHQ‑9) and SES indices are also incorporated. Users lacking baseline text or any required covariate are excluded (FR‑004b, FR‑009).  
4. **Fit** a pre‑specified linear mixed‑effects model with random intercepts for `User` and random slopes for `UsageFrequency`, controlling for prior loneliness (`prev_loneliness_score`), attachment scores, baseline mental‑health, SES, age, and gender. The lagged predictor structure uses usage at week *t* to predict loneliness at week *t + 1*.  
5. **Bootstrap** **1 000** iterations (seed = 42) using `joblib` parallelism to generate robust 95 % confidence intervals for all coefficients (FR‑006). Holm‑Bonferroni correction is applied to the set of fixed‑effect tests.  
6. **Run** a subgroup analysis for users aged ≥ 60 **after** a formal power check (minimum 80 users, [deferred] power). If the power criterion fails, the subgroup analysis is skipped with a warning.  
7. **Validate** all steps against contracts and report diagnostics (normality, homoscedasticity, collinearity, selection‑bias).  

All steps are **CPU‑first** and designed to finish within the GitHub Actions free‑tier limits (≤ 6 h, ≤ 7 GB RAM). Real data is fetched directly from open sources; if any required dataset is unavailable, the pipeline halts with a clear error (no synthetic stand‑ins).  

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `statsmodels`, `scikit-learn`, `datasets`, `requests`, `pyyaml`, `joblib` (for parallel bootstrap)  
- **Storage**: Local filesystem under `data/` – CSV/Parquet files.  
- **Testing**: `pytest` (unit, integration, contract validation)  
- **Target Platform**: Linux runner on GitHub Actions (2 CPU cores, ~7 GB RAM)  
- **Performance Goals**: Complete the full bootstrap (1 000 iterations) ≤ 6 h; memory footprint < 7 GB.  
- **Constraints**: No GPU; no gated datasets; strict PII handling (hash only); observational framing only.

## Constitution Check
| Principle | Compliance | Evidence / Action |
|---|---|---|
| I. Reproducibility | **COMPLIANT** | Fixed `requirements.txt`, pinned random seeds, deterministic data‑fetch URLs, and end‑to‑end scripts in `src/`. |
| II. Verified Accuracy | **CONDITIONAL** | Success depends on the Zenodo DOI delivering the required columns; the pipeline aborts with “Data Linkage Impossible” if not. |
| III. Data Hygiene | **COMPLIANT** | Checksums recorded for raw files; all transformations write new files; usernames hashed immediately; no PII persisted. |
| IV. Single Source of Truth | **COMPLIANT** | `data/processed/matched_users.parquet` is the sole source for modeling; `data/results/model_summary.json` is the sole source for paper statistics. |
| V. Versioning Discipline | **COMPLIANT** | Artifact hashes stored in `state/…yaml`; any change invalidates downstream review records. |
| VI. Longitudinal Analysis Integrity | **COMPLIANT** | Random intercept + random slope pre‑specified in `src/models/mixed_effects.py`; no post‑hoc tweaking. |
| VII. Self‑Report Instrument Validation | **COMPLIANT** | Validation step (`src/validation/validate_data.py`) checks UCLA Loneliness Scale completion rates and missing‑data handling before any modeling. |

## Mapping of Functional Requirements (FR) & Success Criteria (SC) to Phases
| Phase | FR(s) addressed | SC(s) addressed | Key Tasks |
|------|----------------|----------------|-----------|
| **Phase 0 – Feasibility & Validation** | FR‑001, FR‑008, FR‑009 | – | Validate ECAR lexicon (cite Rashkin et al., 2023); inspect Zenodo CSV for required columns; abort with “Data Linkage Impossible” if missing. |
| **Phase 0 – Dynamic Window Calculation** | FR‑002 | – | Derive earliest & latest survey timestamps → define Pushshift query window (strictly preceding surveys). |
| **Phase 1 – Data Ingestion & Matching** | FR‑001, FR‑002, FR‑003 | SC‑001 | Download Zenodo dataset (if available); stream Pushshift logs (exponential back‑off, max 5 retries, 30 s timeout); normalize usernames, hash with SHA‑256, perform fuzzy‑hash fallback; compute match rate; if < 80 % or matched users < 500, halt “Power Insufficient”. |
| **Phase 1 – Feature Engineering** | FR‑004, FR‑004b, FR‑009, FR‑b (baseline mental‑health, SES) | – | Weekly aggregation (`usage_metrics.py`); ECAR lexicon scan (`attachment_proxy.py`); compute `baseline_mental_health_score` and `ses_index`; exclude users lacking any required covariate. |
| **Phase 2 – Baseline Model & Power Check** | – | SC‑002, SC‑004 | Fit intercept‑only LMM; compute marginal R²; run formal Monte‑Carlo power simulation for mixed‑effects with random slopes (target power ≥ 0.80 for effect size d = 0.5). |
| **Phase 2 – Primary Mixed‑Effects Model** | FR‑005, FR‑b (prev_loneliness_score, baseline mental‑health, SES) | SC‑003 | Fit LMM with random intercept & random slope; fixed effects include `UsageFrequency`, `SessionDuration`, `AttachmentAnxietyScore`, `AttachmentAvoidanceScore`, `prev_loneliness_score`, `baseline_mental_health_score`, `ses_index`, `Age`, `Gender`; if convergence fails, fallback to random‑intercept‑only model (logged warning). |
| **Phase 2 – Bootstrap Resampling** | FR‑006 | SC‑003 | **1 000** bootstrap iterations (seed = 42) using `joblib` parallelism; store 95 % CIs; apply Holm‑Bonferroni to fixed‑effect p‑values. |
| **Phase 3 – Subgroup & Robustness** | FR‑007 | – | Power check for ≥ 60 subgroup (requires ≥ 80 users, [deferred] power); if sufficient, re‑fit LMM on the subgroup and compare effect sizes; otherwise skip with warning. |
| **Phase 3 – Diagnostics & Bias** | – | – | Normality & homoscedasticity checks; collinearity diagnostics (VIF); selection‑bias report comparing excluded vs. included users. |
| **Phase 4 – Results Aggregation** | – | – | Consolidate fixed effects, p‑values, CIs, marginal R² into `model_summary.json` (conforms to `model_output.schema.yaml`). |

## Complexity Tracking (Justification for “non‑trivial” steps)
| Violation | Why Needed | Simpler Alternative Rejected |
|---|---|---|
| **Bootstrap (1 000 iters)** | Required by FR‑006 for robust CIs; 1 000 chosen after profiling to stay < 6 h. | Asymptotic SEs would ignore non‑normal residuals. |
| **Pushshift Retry Policy** | Handles API rate‑limit edge case; required for reliable data download. | Simple retry would cause frequent failures. |
| **Lexicon Validation** | FR‑008 mandates halting if ECAR missing; validation ensures construct validity. | Using a fallback keyword list would breach FR‑008. |
| **Dynamic Window Calculation** | Guarantees lagged predictor validity (FR‑002). | Fixed window would mis‑align usage vs. survey dates. |
| **Formal Power Simulation** | Addresses SC‑002 and prevents under‑powered study (methodology‑42585992). | Heuristic match‑rate only is insufficient. |
| **Subgroup Power Check** | Prevents unreliable age‑moderation conclusions (methodology‑184f9d06). | Running subgroup regardless of power would produce noisy estimates. |
| **Additional Covariates** | Controls for baseline mental health and SES to reduce omitted variable bias (methodology‑b47ef3e1). | Ignoring them would risk confounded estimates. |
| **Model Convergence fallback** | Guarantees a result even on sparse data; logs warning for transparency. | Aborting would leave the study without any quantitative finding. |
| **Selection‑Bias Analysis** | Needed to assess impact of excluded users (FR‑009). | Ignoring bias would hide a hidden validity threat. |

---


