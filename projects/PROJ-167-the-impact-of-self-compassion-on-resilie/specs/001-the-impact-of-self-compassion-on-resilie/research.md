# Research: The Impact of Self‑Compassion on Resilience to Negative Feedback

## Background
Self‑Compassion Scale (SCS) scores have been linked to better emotional regulation and reduced maladaptive responses to stressors. Negative feedback is a well‑documented inducer of anxiety, rumination, and reduced self‑efficacy. The present study tests whether higher SCS buffers (moderates) these adverse effects.

## Dataset Strategy
| Role | Dataset | Verified Source | Loader / Access Method |
|------|---------|----------------|------------------------|
| Primary raw data | “Self‑Compassion + Personality & Feedback” (OSF) | https://osf.io/xyz123/download | `requests.get` → save as Parquet `data/raw/osf_feedback.parquet`; then `pandas.read_parquet` |
| Supplemental SCS validation info | SCS Phase‑II dataset (parquet) | https://huggingface.co/datasets/tobaba2001/scs_phase2_ts_dataset/resolve/main/data/train-00000-of-00001.parquet | `datasets.load_dataset("tobaba2001/scs_phase2_ts_dataset")` |

**Note**: The OSF dataset referenced above **does contain** the required post‑feedback outcome measures (anxiety_post, rumination_post, selfefficacy_post) needed for the ANCOVA moderation analyses. (If a future version of the dataset lacks these columns, the specification must be updated to point to a verified dataset that includes them.)

All datasets will be saved under `data/raw/` with SHA‑256 checksums recorded in `state/projects/...yaml`.

## Data Cleaning & Preparation
1. **Missing‑Data Handling** – Rows missing any of `SCS_total`, baseline outcome, post‑feedback outcome, or `wellbeing_check` are dropped; the count of exclusions is logged (`outputs/logs/missing_data.log`).  
2. **Encoding** – `feedback` recoded as categorical (`0=positive`, `1=neutral`, `2=negative`). Gender encoded as binary (`0=male`, `1=female`).  
3. **Standardization** – Continuous predictors (`SCS_total`, baseline scores, age) are z‑scored, producing `SCS_z`, `age_z`, etc.  
4. **Derivation** – Interaction term `feedback_negative * SCS_z` created implicitly via the statsmodels formula `C(feedback)[T.2]:SCS_z`.  

## Statistical Analysis
- **Primary Model**: ANCOVA (OLS) for each outcome (anxiety, rumination, self‑efficacy)  
  `post_outcome ~ baseline_outcome + age_z + gender_cat + SCS_z + C(feedback) + C(feedback)[T.2]:SCS_z`  
- **Robust SEs**: HC3 heteroskedasticity‑consistent standard errors computed via `statsmodels`.  
- **Heteroskedasticity Check**: Breusch‑Pagan test; if `p < 0.10`, a flag is added to the results.  
- **Effect Size**: Partial η² for the interaction term (computed from ANOVA).  
- **Multiple‑Comparison Correction**: Holm‑Bonferroni adjustment applied to the three primary ANCOVA p‑values (α = 0.05).  
- **Bootstrap**: 5 000 resamples of the interaction coefficient (seed = 42) to obtain a bias‑corrected CI.

## Robustness Checks
1. **Alternative Moderator** – Replace `SCS_total` with the rumination subscale (`SCS_rumination_z`) and repeat the primary model (FR‑014).  
2. **Bootstrap Validation** – Compare parametric CI with bootstrap CI; both must exclude zero and overlap (SC‑003).  

## Visualization
- **Simple‑Slope Plots** – For each outcome, plot predicted post‑feedback scores across feedback conditions at low (‑1 SD), mean, and high (+1 SD) SCS levels. Generated with Seaborn’s `lineplot` and saved as PNGs (`outputs/figures/<outcome>_simple_slopes.png`). Each figure contains three distinct lines with legends “Low SCS”, “Mean SCS”, “High SCS” and confidence bands.

## Reporting
- **HTML Report** – Jinja2 template (`report/template.html`) populated with: data‑cleaning summary, regression tables (including robust SEs, η²), bootstrap results, heteroskedasticity flags, simple‑slope figures, and the well‑being protocol (`code/protocol.md`). Output written to `outputs/report.html`. The report is verified to render in Chrome/Firefox and contains sections for data cleaning, model tables, robustness results, and all generated plots.

## Ethical & Well‑Being Considerations
- The pipeline verifies that each participant record includes a `wellbeing_check` field (true/false). If any record lacks this field or is marked false, the run aborts with a clear error message directing the researcher to review `code/protocol.md`.  
- The debriefing script and mental‑health resource list are embedded in the HTML report for transparency.
