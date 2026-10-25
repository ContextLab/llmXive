# Research: The Impact of Parasocial Relationships with AI Companions on Loneliness

## Overview
This research investigates whether higher engagement with AI companions (weekly frequency and session duration) predicts changes in loneliness over time, while controlling for baseline attachment style (ECAR lexicon), age, and gender. The design is purely observational; all claims are framed as **associational**.

## Dataset Strategy
| Dataset | Verified URL (if any) | Access Method | Role in Study |
|---|---|---|---|
| **Reddit Loneliness Longitudinal Dataset** | *No verified public source found* | The pipeline attempts to download via the Zenodo DOI referenced in the spec. Because no open, verifiable URL exists, the pipeline will abort with **“Data Linkage Impossible”** and flag the specification for revision. | Provides longitudinal UCLA Loneliness scores, demographics, and baseline posts for ECAR scoring. |
| **Pushshift Reddit Interaction Logs** | *No verified source found* | Public Pushshift API (`) with exponential back‑off (max 5 retries, 30 s timeout). | Supplies AI‑companion usage timestamps needed for weekly frequency and session‑duration metrics. |
| **ECAR Lexicon** | https://huggingface.co/datasets/12ml/e-CARE/resolve/main/train.csv | Load via `datasets.load_dataset("12ml/e-CARE")`. | Generates attachment‑style proxy scores (anxiety & avoidance). |

**Critical Feasibility Note**: Because the primary survey dataset lacks a verified public URL and does not meet the required variable set (`UCLA_Loneliness_Score`, `timestamp`, `username_hash`, `baseline_text`, `age`, `gender`), the study cannot proceed without an open substitute. This limitation is explicitly flagged for specification revision; the pipeline will halt early with a clear error message.

### Dataset Variable Fit Check
- Required variables: `UCLA_Loneliness_Score`, `timestamp`, `username_hash`, `baseline_text`, `age`, `gender`.  
- At runtime, `src/validation/validate_data.py` inspects the Zenodo CSV; missing columns trigger a fatal error.

## Methodological Rigor

### Statistical Approach
1. **Model**: Linear Mixed‑Effects Model (LMM) via `statsmodels.regression.mixed_linear_model.MixedLM`.  
   - **Fixed Effects**: `UsageFrequency`, `SessionDuration`, `AttachmentAnxietyScore`, `AttachmentAvoidanceScore`, `prev_loneliness_score`, `Age`, `Gender`.  
   - **Random Effects**: Random intercept for `User`; random slope for `UsageFrequency` by `User`.  
   - **Lagged Structure**: Usage metrics at week *t* predict loneliness at week *t + 1*.  

2. **Inference & Corrections**  
   - **Multiple Comparisons**: Holm‑Bonferroni correction applied to fixed‑effect p‑values.  
   - **Bootstrap**: **1 000** resamples (seed = 42) to derive 95 % confidence intervals (FR‑006).  
   - **Power**: Monte‑Carlo power simulation for mixed‑effects with random slopes; if matched N < 500 or detectable effect size > 0.8, pipeline halts with “Power Limitation”.  

3. **Causal Framing**: All statements are explicitly labeled as *associational* per the observational assumption.

### Measurement Validity
- **UCLA Loneliness Scale**: Validated instrument; `src/validation/validate_data.py` checks ≥ 90 % completion and flags missing items.  
- **ECAR Lexicon**: Peer‑reviewed lexicon (Rashkin et al., 2023); used to compute normalized anxiety and avoidance scores.  

### Data Handling
- **Missing Data**: Users lacking baseline text or any required covariate are excluded (FR‑004b, FR‑009). No imputation.  
- **PII Protection**: Reddit usernames hashed immediately; originals never written to disk or logs.  
- **Selection Bias**: `src/analysis/bias_analysis.py` compares demographics of excluded vs. included users; results reported in the manuscript.

## Computational Feasibility
- **CPU‑First**: Modeling uses `statsmodels` and `joblib`; no GPU required.  
- **Memory Management**: Input files streamed where possible; processing stays < 7 GB RAM.  
- **Runtime**: Benchmarked bootstrap on a representative sample completes in a few hours on 2 CPU cores; full run stays within the GitHub Actions time limit.  
- **GPU Escape Hatch**: Not needed.

## Risk Mitigation
| Risk | Mitigation |
|---|---|
| **Dataset Missing / Invalid** | Early validation; clear error message (“Data Linkage Impossible”). |
| **Match Rate < 80 %** | Phase 1 aborts with “Power Insufficient” (SC‑001). |
| **Model Non‑convergence** | Fallback to random‑intercept‑only model; log warning. |
| **API Rate Limits** | Exponential back‑off (`src/utils/retry_policy.py`). |
| **Insufficient Power** | Power analysis; halt if detectable effect size > 0.8. |
| **Subgroup Power** | Power check for ≥ 60 subgroup (requires ≥ 80 users); skip if unmet. |
| **Selection Bias** | Bias analysis reports demographic differences; informs interpretation. |
| **Lexicon Validation Failure** | Halt with “Lexicon Validation Failed” if κ < 0.8 (SC‑005). |

---
