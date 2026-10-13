# Research: Mindfulness Components and Delivery Formats in ASD Social Skills

## Research Question
What is the efficacy of mindfulness-based interventions for improving social skills in children aged 6-12 with Autism Spectrum Disorder (ASD), and how do these effects vary by mindfulness component (breathing, body scan, mindful movement) and delivery format (caregiver-mediated vs. child-led)?

## Hypotheses
- **Primary**: Mindfulness-based interventions show a moderate positive effect size (Hedges' $g \ge 0.5$) on social skill outcomes compared to control conditions.
- **Secondary 1**: Interventions incorporating multiple mindfulness components (combined) show larger effect sizes than single-component interventions.
- **Secondary 2**: Caregiver-mediated delivery formats yield larger and more sustained effects at follow-up ($\ge 3$ months) compared to child-led formats.

## Dataset Strategy

| Dataset | Source | Access Method | Role |
|----------|--------|---------------|------|
| ClinicalTrials.gov | [https://clinicaltrials.gov/](https://clinicaltrials.gov/) | API (v2) | Primary source for RCTs |
| OSF | [https://osf.io/](https://osf.io/) | API | Supplementary pre-registered trials |

**Verification**: Both sources are public and programmatic. No access-gated data is used.

## Methodological Rigor

### Statistical Analysis
- **Effect Size**: Hedges' $g$ is used to account for small sample sizes common in ASD research.
- **Meta-Analysis Model**: 
    - **Fixed-effects**: Used if $I^2 \le 50\%$.
    - **Random-effects**: Used if $I^2 > 50\%$ to account for between-study heterogeneity.
- **Heterogeneity**: Quantified using Cochran's $Q$ and the $I^2$ statistic.
- **Publication Bias**: Assessed via Funnel Plots and Egger's regression test, provided $N \ge 10$ studies are included.
- **Multiple Comparisons**: P-values for subgroup analyses will be adjusted using Bonferroni correction.

### Multi-arm Study Handling
To prevent unit-of-analysis errors and artificial inflation of sample size, multi-arm studies will not be split proportionally. Instead, a single primary control group will be selected for each treatment arm. If multiple controls are available, the one most closely matching the study's primary control condition will be utilized to ensure independent observations.

### Data Extraction Strategy
To ensure construct validity, the extraction of mindfulness components and delivery formats will move beyond simple regex. A structured keyword-based pipeline will be used to identify candidates, and each entry will be assigned a confidence score. Entries falling below the confidence threshold will be flagged for manual verification.

### Inclusion/Exclusion Criteria
- **Inclusion**:
    - Population: Children aged 6-12 with a confirmed ASD diagnosis.
    - Intervention: Must include at least one core mindfulness component (breathing, body scan, or mindful movement).
    - Outcome: Validated social skill measure (e.g., SRS, VABS).
    - Design: RCT or quasi-experimental with a control group.
    - Date: Registered between 2015–2024.
- **Exclusion**:
    - Age outside 6-12.
    - No control group.
    - No social skill outcome reported.

## Compute Feasibility
- **CPU-First**: All calculations (Hedges' $g$, random-effects models) are performed using `scipy` and `statsmodels` which run efficiently on the GitHub Actions 2-core CPU.
- **Memory**: Data is processed as pandas DataFrames; the expected number of studies ($\le 100$) will easily fit within 7GB RAM.
- **Disk**: Raw and processed CSVs will occupy $< 100$MB, well within the 14GB limit.

## Decision Rationale
- **Hedges' $g$ over Cohen's $d$**: Chosen because ASD intervention studies often have small group sizes ($N < 20$), where Cohen's $d$ is biased upward.
- **Random-Effects Model**: Chosen as the primary approach because mindfulness interventions vary significantly in duration, intensity, and delivery, making a single "true" effect size unlikely.
- **Caregiver-Mediated Tagging**: Explicitly required by Constitution Principle VII to test the hypothesis regarding delivery mechanisms.