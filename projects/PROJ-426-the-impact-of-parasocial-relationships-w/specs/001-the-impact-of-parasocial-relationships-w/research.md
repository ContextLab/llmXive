# Research: The Impact of Parasocial Relationships with AI Companions on Loneliness

## Objective
Quantify the association between AI companion usage (frequency & session duration) and changes in self‑reported loneliness, while controlling for baseline attachment style and age. **Note**: As this is an observational study, all findings are framed as **associational**, not causal.

## Dataset Strategy

| Dataset | Source / URL (Verified) | Availability | Notes |
|---------|------------------------|--------------|-------|
| Reddit Loneliness Longitudinal Dataset | **Blocking Gap**: No specific Zenodo DOI verified in the "Verified datasets" block. | **Pre-flight Check Required**: Must contain `UCLA_Loneliness_Score`, `timestamp`, AND `username` or `username_hash`. If missing, pipeline halts. | If the dataset is de-identified (no user IDs), the study cannot proceed. |
| Pushshift Reddit interaction logs (subreddits `r/Replika`, `r/characterAI`, `r/AICompanions`) | Pushshift API (no static URL) | Streaming via API calls | Rate‑limited to 100 req/min; exponential back‑off implemented. |
| Attachment Style Proxy | **ECR-RS Keyword Proxy** (Derived from public ECR-RS items) | Bundled with code | **Validity Limitation**: This is a heuristic text-based proxy, NOT a validated psychometric instrument. It serves as a noisy control variable. |
| Demographics table (age) | Part of the Loneliness dataset | Same as above | Users missing age are excluded from subgroup analysis. |

> **Gap Notice**: The "Reddit Loneliness Longitudinal Dataset" is a **Blocking Gap** until a verified DOI with the required schema (longitudinal + linkable IDs) is confirmed. The plan includes a mandatory pre-flight check to abort if the schema is insufficient.

## Methods

| Step | Method | Rationale | Parameters |
|------|--------|-----------|------------|
| **Data Cleaning & Matching** | SHA‑256 hashing of Reddit usernames, inner join on hash | Guarantees anonymity while preserving longitudinal linkage. | Hash algorithm: SHA‑256 (Python `hashlib`). |
| **Weekly Usage Metrics** | **Frequency**: Count of AI‑related posts/comments per user per week.<br>**Session Duration**: **Total time span** (max timestamp - min timestamp) of all activity blocks in the week, capped at 24h. | Captures intensity and opportunity for engagement. Acknowledged as a proxy for "active time" due to asynchronous nature of Reddit. | Weekly aggregation; cap = 24 h. |
| **Attachment‑Style Proxy** | Normalized term‑frequency scoring using **ECR-RS Keyword Proxy** (anxiety & avoidance categories). | Provides a heuristic control for pre-existing relational dispositions. **Limitation**: Low construct validity compared to full psychometric scales. | Term list from public ECR-RS items; TF not used to keep interpretability. |
| **Mixed‑Effects Model** | Linear Mixed‑Effects (LME) via `statsmodels.MixedLM`. Fixed effects: **Lagged Usage (T)**, **Lagged Duration (T)**, **Attachment Anx/Avoid**, **Baseline Loneliness (T)**. Random intercepts for `User`; random slopes for `UsageFrequency` by `User`. | **Lagged Structure**: Models change (T -> T+1) while controlling for baseline (T) to reduce reverse causality bias. | Estimator: REML; optimizer: `lbfgs`. |
| **Bootstrap Confidence Intervals** | **Cluster Bootstrap** (1 000 resamples, seed = 42). **Resample at the User level** to preserve within-user correlation. | Provides robust CIs when model assumptions are violated. Resampling at the row level would invalidate the hierarchical structure. | Resample at the *user* level. |
| **Multiple‑Comparison Correction** | Bonferroni correction across the set of fixed‑effect tests (four primary predictors). | Controls family‑wise error rate. |
| **Power / Sample‑Size Justification** | **Pragmatic Target**: 500 matched users is set as a pragmatic upper bound to maximize power. **Limitation**: LME power is highly sensitive to ICC and time points. A medium effect (Cohen's d ≈ 0.5) typically requires >300 subjects, but 500 may still be underpowered for small effects or complex random-slope structures. The study will report effect sizes with CIs, acknowledging potential power limitations. | Aligns with FR‑001 acceptance scenario. |
| **Causal Framing** | Observational design; all statements will be *associational* (e.g., "higher usage is associated with lower loneliness"). | Consistent with Constitution Principle VII. |
| **Collinearity Check** | Variance Inflation Factor (VIF) computed for fixed effects; if VIF > 5, report collinearity and interpret coefficients descriptively. | Prevents misleading independent effect claims. |

## Validation & Robustness

1. **Model Diagnostics** – Residual normality (Shapiro‑Wilk), homoscedasticity (Breusch‑Pagan). If violated, cluster bootstrap CIs replace Wald CIs.  
2. **Subgroup (Age ≥ 60)** – Re‑fit LME on older users; compare effect sizes to full‑sample model (FR‑007).  
3. **Sensitivity to Missing Attachment** – Exclude rows where `missing_attachment_flag=True` and re‑run model; report any substantive changes.  
4. **Runtime Monitoring** – Log total CPU time; abort if > 6 h (SC‑004).  

## Expected Deliverables
- `data/unified_dataset.parquet` (matches FR‑001‑FR‑004)  
- `results/mixed_effects_summary.csv` (fixed effects, p‑values, bootstrap CIs)  
- `results/subgroup_60plus.csv`  
- `reports/analysis_report.html` (includes tables, diagnostic plots, runtime summary)  

---