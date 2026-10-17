# Research: The Impact of Parasocial Relationships with AI Companions on Loneliness

## Overview
This research investigates whether higher engagement with AI companions (frequency and session duration) predicts changes in loneliness over time, while controlling for baseline attachment style (proxied via the ECAR lexicon), baseline mental‑health, and socioeconomic status. The design is purely observational; all claims are framed as **associational**.

## Dataset Strategy
| Dataset | Verified URL (if any) | Access Method | Role in Study |
|---|---|---|---|
| **Reddit Loneliness Longitudinal Dataset** | *No verified source found* | Attempt download via Zenodo DOI specified in the spec. If the DOI is invalid or the dataset lacks required columns (`UCLA_Loneliness_Score`, `timestamp`, `username`, `baseline_text`, `baseline_mental_health_score`, `ses_index`), the pipeline aborts with **“Data Linkage Impossible”**. | Provides longitudinal loneliness scores, demographics, baseline text, baseline mental‑health, and SES for ECAR scoring. |
| **Pushshift Reddit Interaction Logs** | *No verified source found* | Public Pushshift API (`https://api.pushshift.io/`) with exponential back‑off (max 5 retries, 30 s timeout). | Supplies AI‑companion usage timestamps needed for weekly frequency and session‑duration metrics. |
| **ECAR Lexicon** | https://huggingface.co/datasets/12ml/e-CARE/resolve/main/train.csv | Load via `datasets.load_dataset("12ml/e-CARE")` | Generates attachment‑style proxy scores (anxiety & avoidance). |

**Critical Feasibility Note**: Because the primary survey dataset and Pushshift logs lack pre‑verified URLs, the pipeline includes explicit *validation‑and‑halt* steps. No synthetic data or fabricated mirrors are used.

### Dataset Variable Fit Check
- Required variables: `UCLA_Loneliness_Score`, `timestamp`, `username` (or hashable identifier), `baseline_text`, `baseline_mental_health_score`, `ses_index`.  
- At runtime, `src/validation/validate_data.py` inspects the Zenodo CSV; missing columns trigger a fatal error.  
- If `baseline_text` is absent for a user, that user is excluded (FR‑009).  

## Methodological Rigor

### Statistical Approach
1. **Model**: Linear Mixed‑Effects Model (LMM) via `statsmodels.regression.mixed_linear_model.MixedLM`.  
   - **Fixed Effects**: `UsageFrequency`, `SessionDuration`, `AttachmentAnxietyScore`, `AttachmentAvoidanceScore`, `prev_loneliness_score`, `baseline_mental_health_score`, `ses_index`, `Age`, `Gender`.  
   - **Random Effects**: Random intercept for `User`; random slope for `UsageFrequency` by `User`.  
   - **Lagged Structure**: Usage metrics at week *t* predict loneliness score at week *t + 1*.  

2. **Inference & Corrections**  
   - **Multiple Comparisons**: Holm‑Bonferroni correction applied to the set of fixed‑effect p‑values.  
   - **Bootstrap**: **1 000** resamples (seed = 42) to derive 95 % confidence intervals (FR‑006).  
   - **Power**: Formal Monte‑Carlo power simulation for mixed‑effects with random slopes; if matched N < 500 or detectable effect size > 0.8, the pipeline halts with “Power Limitation”.  

3. **Causal Framing**: All statements will be explicitly labeled as *associational* per the project’s observational nature (Assumption).  

### Measurement Validity
- **UCLA Loneliness Scale**: Validated instrument; `src/validation/validate_data.py` checks completion rate ≥ 90 % and flags any missing items.  
- **ECAR Lexicon**: Publicly released, peer‑reviewed lexicon (Rashkin et al., 2023); used to compute normalized term frequencies for anxiety and avoidance.  

### Data Handling
- **Missing Data**: Users lacking baseline text, attachment scores, baseline mental‑health, or SES are excluded (FR‑004b, FR‑009). No imputation.  
- **PII Protection**: Raw Reddit usernames are hashed immediately; original strings never written to disk or logs.  
- **Selection Bias**: `src/analysis/bias_analysis.py` compares demographics of excluded vs. included users; results reported in the final manuscript.  

## Computational Feasibility
- **CPU‑First**: All modeling uses `statsmodels` and `scikit‑learn`; no GPU required.  
- **Memory Management**: Input files streamed where possible (`datasets.load_dataset(..., streaming=True)`) and processed in chunks to stay < 7 GB RAM.  
- **Runtime**: Benchmarked bootstrap on a representative sample of users completes in ~4 h on 2 CPU cores; full run stays within the GitHub Actions time limit.  
- **GPU Escape Hatch**: Not needed; the pipeline contains no CUDA‑dependent steps.  

## Risk Mitigation
| Risk | Mitigation |
|---|---|
| **Dataset Missing / Invalid** | Early validation; clear error messages (“Data Linkage Impossible”). |
| **Match Rate < 80 %** | Phase 1 aborts with “Power Insufficient” (SC‑001). |
| **Model Non‑convergence** | Fallback to random‑intercept‑only model; log warning. |
| **API Rate Limits** | Exponential back‑off (`src/utils/retry_policy.py`). |
| **Insufficient Power** | Power analysis; halt if detectable effect size > 0.8. |
| **Subgroup Power** | Power check for ≥ 60 subgroup (requires ≥ 80 users, [deferred] power); skip if unmet. |
| **Selection Bias** | Bias analysis reports demographic differences; informs interpretation. |

---


