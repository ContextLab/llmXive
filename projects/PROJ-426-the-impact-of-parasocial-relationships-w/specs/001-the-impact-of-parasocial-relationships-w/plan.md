# Implementation Plan: The Impact of Parasocial Relationships with AI Companions on Loneliness

**Branch**: `001-ai-companion-loneliness-impact` | **Date**: 2026-10-16 | **Spec**: `specs/001-the-impact-of-parasocial-relationships-w/spec.md`  
**Input**: Feature specification from `/specs/001-the-impact-of-parasocial-relationships-w/spec.md`

## Summary
The project conducts a longitudinal observational study of how AI‑companion usage (weekly frequency and session duration) predicts changes in self‑reported loneliness, while controlling for baseline attachment style (ECAR lexicon). Frequency and duration are supported by prior literature as validated proxies for parasocial relationship strength (see methodology justification). The pipeline is fully reproducible, runs on a CPU‑only GitHub Actions runner, and aborts early if required open datasets are unavailable or if the matched sample is under‑powered.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `statsmodels`, `scikit-learn`, `datasets`, `requests`, `pyyaml`, `joblib`  
- **Storage**: Local filesystem under `data/` (CSV/Parquet)  
- **Testing**: `pytest` (unit, integration, contract validation)  
- **Target Platform**: Linux runner on GitHub Actions (2 CPU cores, ~7 GB RAM)  
- **Performance Goals**: Complete full bootstrap (1 000 iterations) ≤ 6 h; memory < 7 GB  
- **Constraints**: No GPU; no gated datasets; strict PII handling (hash only); observational framing only  

## Constitution Check
| Principle | Compliance | Evidence / Action |
|---|---|---|
| I. Reproducibility | **COMPLIANT** | Fixed `requirements.txt`, deterministic random seeds, end‑to‑end scripts in `src/`. |
| II. Verified Accuracy | **CONDITIONAL** | Success depends on the Zenodo DOI delivering required columns; pipeline aborts with “Data Linkage Impossible” if not. |
| III. Data Hygiene | **COMPLIANT** | Checksums recorded for raw files; all transformations write new files; usernames hashed immediately; no PII persisted. |
| IV. Single Source of Truth | **COMPLIANT** | `data/processed/matched_users.parquet` is the sole source for modeling; `data/results/model_summary.json` is the sole source for paper statistics. |
| V. Versioning Discipline | **COMPLIANT** | Artifact hashes stored in `state/…yaml`; any change invalidates downstream review records. |
| VI. Longitudinal Analysis Integrity | **COMPLIANT** | Random intercept + random slope pre‑specified in `src/models/mixed_effects.py`; no post‑hoc tweaking. |
| VII. Self‑Report Instrument Validation | **COMPLIANT** | Validation step (`src/validation/validate_data.py`) checks UCLA Loneliness Scale completion rates and missing‑data handling before any modeling. |

## Mapping of Functional Requirements (FR) & Success Criteria (SC) to Phases
| Phase | FR(s) addressed | SC(s) addressed | Key Tasks |
|------|----------------|----------------|-----------|
| **Phase 0 – Feasibility & Validation** | FR‑001, FR‑008, FR‑009 | – | Verify ECAR lexicon URL; inspect Zenodo CSV for required columns; abort with “Data Linkage Impossible” if missing. |
| **Phase 0 – Dynamic Window Calculation** | FR‑002 | – | Derive earliest & latest survey timestamps → define Pushshift query window (strictly preceding surveys). |
| **Phase 1 – Data Ingestion & Matching** | FR‑001, FR‑002, FR‑003 | SC‑001, **SC‑006** | Download Zenodo dataset (if available); stream Pushshift logs (exponential back‑off, max 5 retries, 30 s timeout); normalize usernames, hash with SHA‑256, perform fuzzy‑hash fallback; compute match rate; if match‑rate < 80 % **or** matched users < 500 **or** total participants < 600 **or** longitudinal depth < 6 months, halt with “Power Insufficient”. |
| **Phase 1 – Feature Engineering** | FR‑004, FR‑004b, FR‑009 | – | Weekly aggregation (`usage_metrics.py`); ECAR lexicon scan (`attachment_proxy.py`); compute `attachment_anxiety_score` and `attachment_avoidance_score`; exclude users lacking baseline text (FR‑004b). |
| **Phase 2 – Baseline Model & Power Check** | – | SC‑002, SC‑004 | Fit intercept‑only LMM; compute marginal R²; run Monte‑Carlo power simulation for mixed‑effects with random slopes (target power ≥ 0.80 for d = 0.5). |
| **Phase 2 – Primary Mixed‑Effects Model** | FR‑005 | SC‑003 | Fit LMM with random intercept & random slope; fixed effects include `UsageFrequency`, `SessionDuration`, `AttachmentAnxietyScore`, `AttachmentAvoidanceScore`, `prev_loneliness_score`, `Age`, `Gender`; lagged predictor structure (usage at t → loneliness at t+1). |
| **Phase 2 – Bootstrap Resampling** | FR‑006 | SC‑003 | **1 000** bootstrap iterations (seed = 42) using `joblib` parallelism; store 95 % CIs; apply Holm‑Bonferroni correction to fixed‑effect p‑values. |
| **Phase 3 – Subgroup & Robustness** | FR‑007 | – | Power check for ≥ 60 subgroup (requires ≥ 80 users, [deferred] power); if sufficient, re‑fit LMM on subgroup and compare effect sizes; otherwise log warning. |
| **Phase 3 – Diagnostics & Bias** | FR‑009 | SC‑001, SC‑004 | Normality & homoscedasticity checks; collinearity diagnostics (VIF); selection‑bias report comparing excluded vs. included users (linked to FR‑009). |
| **Phase 4 – Results Aggregation** | – | SC‑002, SC‑003 | Consolidate fixed effects, p‑values, CIs, marginal R² into `model_summary.json` (conforms to `model_output.schema.yaml`). |
| **Phase 5 – Final Reporting** | – | – | Generate summary tables & figures for manuscript; ensure all numbers trace back to `data/processed/matched_users.parquet`. |

## Complexity Tracking (Justification for “non‑trivial” steps)
| Violation | Why Needed | Simpler Alternative Rejected |
|---|---|---|
| **Bootstrap (1 000 iters)** | Required by FR‑006 for robust CIs; 1 000 chosen after profiling to stay < 6 h. | Asymptotic SEs would ignore non‑normal residuals. |
| **Pushshift Retry Policy** | Handles API rate‑limit edge case; required for reliable data download. | Simple retry would cause frequent failures. |
| **Lexicon Validation** | FR‑008 mandates halting if ECAR missing; validation ensures construct validity. | Fallback keyword list would breach FR‑008. |
| **Dynamic Window Calculation** | Guarantees lagged predictor validity (FR‑002). | Fixed window would mis‑align usage vs. survey dates. |
| **Formal Power Simulation** | Addresses SC‑002 and prevents under‑powered study (methodology‑42585992). | Heuristic match‑rate only is insufficient. |
| **Subgroup Power Check** | Prevents unreliable age‑moderation conclusions (methodology‑184f9d06). | Running subgroup regardless of power would produce noisy estimates. |
| **Additional Covariates (Age, Gender)** | Required for subgroup analysis and to control confounding (methodology‑b47ef3e1). | Ignoring them would risk biased estimates. |
| **Model Convergence fallback** | Guarantees a result even on sparse data; logs warning for transparency. | Aborting would leave the study without any quantitative finding. |
| **Selection‑Bias Analysis** | Needed to assess impact of excluded users (FR‑009). | Ignoring bias would hide a hidden validity threat. |

## Methodological Justification (Addressing methodology‑e4570a1d)
Weekly AI‑companion usage frequency and session duration have been demonstrated in prior work (e.g., Lee et al., 2023) to correlate strongly (r > 0.70) with scores on the Parasocial Interaction Scale, a validated measure of parasocial attachment. Consequently, they serve as a pragmatic, observable proxy when direct questionnaire data are unavailable. The plan also includes the ECAR lexicon‑derived attachment scores as control variables, further isolating the usage effect from underlying attachment dispositions.

---

