# Research: The Impact of Self‑Compassion on Resilience to Negative Feedback

## Background & Literature

Self‑compassion has been shown to buffer stress responses (Neff, 2003) and to reduce maladaptive rumination (Leary et al., 2007). However, its role in moderating the impact of **negative social feedback** on key psychological outcomes (anxiety, rumination, self‑efficacy) remains under‑explored. The present analysis leverages a publicly available OSF dataset that combines the Self‑Compassion Scale (SCS) with a controlled feedback manipulation.

## Methodological Overview

1. **Data Acquisition** – Download the OSF dataset (see Dataset Strategy).  
2. **Pre‑processing** – Remove rows with missing SCS, baseline, or post‑feedback scores (FR‑002). Encode feedback as categorical (0 = positive, 1 = neutral, 2 = negative) and standardize continuous predictors (FR‑003).  
3. **Modeling** – For each outcome (anxiety, rumination, self‑efficacy) fit an ANCOVA model with baseline covariates, age, gender, standardized SCS, and the interaction `C(feedback)[T.2]:SCS_z` (FR‑005). Compute robust HC3 SEs and flag heteroskedasticity via Breusch‑Pagan (FR‑009).  
4. **Robustness** – (a) Repeat analysis using the SCS‑rumination subscale (FR‑014). (b) Bootstrap the interaction coefficient 5 000 times with seed = 42 (FR‑008).  
5. **Visualization** – Generate simple‑slope plots for low (‑1 SD), mean, and high (+1 SD) SCS levels (FR‑007).  
6. **Reporting** – Assemble an HTML report containing data cleaning logs, regression tables, robustness checks, and all figures (FR‑010).  
7. **Well‑Being Protocol** – Document pre‑screening, debriefing, and mental‑health resources (FR‑011).

## Dataset Strategy

| Dataset | Description | Verified Source | Loader |
|---------|-------------|----------------|--------|
| OSF Feedback & Personality | Contains participant IDs, SCS total score, baseline anxiety/rumination/self‑efficacy, feedback condition, and post‑feedback outcomes. | https://huggingface.co/datasets/SreekarB/OSFData/resolve/main/FC_graph_covariate_data.csv | `pandas.read_csv` |
| Self‑Compassion Scale (SCS) Subscales (optional) | Provides item‑level SCS scores, enabling extraction of the rumination subscale for FR‑014. | https://huggingface.co/datasets/tobaba2001/scs_phase2_ts_dataset/resolve/main/data/train-00000-of-00001.parquet | `datasets.load_dataset(..., split="train")` |

*No other external datasets are required.*

## Expected Outcomes & Success Metrics

| Success Criterion | Metric | Threshold |
|-------------------|--------|-----------|
| SC‑001 | Interaction p‑value for negative feedback × SCS | < 0.05 |
| SC‑002 | Partial η² for interaction | ≥ 0.02 |
| SC‑003 | Bootstrap CI excludes zero & overlaps parametric CI | Yes |
| SC‑004 | Simple‑slope plots for all three outcomes | 3 lines per plot, correct labeling |
| SC‑005 | Renderable HTML report with all sections | No rendering errors in Chrome/Firefox |

## Risks & Mitigations

- **Missing Data**: Rows with missing key variables are dropped (FR‑002) and logged.  
- **Non‑Normal Residuals**: HC3 SEs are computed automatically; Breusch‑Pagan p < 0.10 triggers a flag in the report.  
- **Insufficient Power**: After cleaning, the pipeline checks `n >= 80`; if not, it aborts with a clear error message.  

---
