# Research: The Impact of Digital Decluttering on Cognitive Performance and Well-being

## Research Question
Does a one-week period of intentionally reduced digital engagement (digital decluttering) improve sustained attention, working memory capacity, and self-reported stress and mood compared to baseline levels?

## Methodological Approach

### Study Design
- **Type**: Within-subjects (Pre-Post) experimental design.
- **Intervention**: 7-day digital decluttering (≤30 min social media, no news, notifications off).
- **Participants**: N ≈ 34-50 (Pilot Feasibility Study target).
- **Power Analysis**: 
  - **Method**: Monte Carlo Simulation.
  - **Status**: Explicitly calculated via simulation in Phase 0.
  - **Justification**: A sample size of N=34-50 provides limited power to detect small-to-medium effects (d=0.2-0.3) after Holm-Bonferroni correction for 4 outcomes. 
  - **Primary Goal**: To estimate effect size variance and feasibility metrics (attrition, compliance) to inform a future full-scale power analysis. The simulation will quantify the probability of detecting a medium effect (d=0.5) under the planned analysis conditions.

### Metrics & Instruments
1.  **Sustained Attention**: SART (Sustained Attention to Response Task).
    -   *Metric*: Commission errors (failures to inhibit response).
    -   *Validation*: Standard scoring algorithm (v2.1+) verified against OSF reference implementation (code logic, not pre-existing data).
2.  **Working Memory**: Ospan (Operation Span).
    -   *Metric*: Span score (accuracy-weighted).
    -   *Validation*: Standard scoring algorithm (v2.1+) verified against OSF reference implementation.
3.  **Stress**: PSS-10 (Perceived Stress Scale).
    -   *Metric*: Total score (0-40).
    -   *Validation*: Standard scoring.
4.  **Mood**: PANAS (Positive and Negative Affect Schedule).
    -   *Metric*: Positive Affect and Negative Affect subscale scores.
    -   *Validation*: Standard scoring.

### Statistical Analysis Plan
- **Primary Method**: Bootstrapped Confidence Intervals (a large number of resamples) for mean change scores.
    -   *Rationale*: Pre-registered as the primary method to avoid data-dependent switching (Type I error inflation) and to handle non-normality inherent in small N cognitive data. **This method is used regardless of normality test results.**
    -   *Constraint*: This method is robust and pre-registered; no preliminary tests (e.g., Shapiro-Wilk) will trigger a change in method.
- **Fallback Method**: Wilcoxon signed-rank test.
    -   *Trigger*: Used **only** if bootstrapping fails to converge (e.g., due to data structure issues), NOT based on Shapiro-Wilk p-values.
- **Multiple Comparisons**: Holm-Bonferroni step-down correction applied to the four primary outcomes (SART, Ospan, PSS, PANAS).
- **Effect Size**: Cohen's d with 95% CI for each outcome.
- **Success Criteria**:
    -   Holm-Bonferroni corrected p < 0.05.
    -   Cohen's d ≥ 0.2 (interpreted with caution due to power limitations).

### Dataset Strategy

| Variable Type | Source/Instrument | Verification Status | Usage in Plan |
| :--- | :--- | :--- | :--- |
| **SART Data** | OSF Task Repository (v2.1+) | **Verified** (Instrument Code) | Baseline & Post-test cognitive task. Scores validated against reference logic. No pre-existing dataset available; real data collected during study. |
| **Ospan Data** | OSF Task Repository (v2.1+) | **Verified** (Instrument Code) | Baseline & Post-test cognitive task. Scores validated against reference logic. No pre-existing dataset available; real data collected during study. |
| **PSS-10 Data** | Standard Instrument | **Verified** (Instrument Logic) | Baseline & Post-test stress survey. |
| **PANAS Data** | Standard Instrument | **Verified** (Instrument Logic) | Baseline & Post-test mood survey. |
| **Compliance Logs** | Self-Report (System Generated) | *Internal* | Intervention fidelity check. |

**Note on Data Sources**:
-   **Instrument vs. Dataset**: The OSF repository provides the *instrument code* (the tasks), not a pre-existing dataset of participant responses. There is **no verified public dataset** containing pre-post intervention SART/Ospan/PANAS scores for this specific protocol.
-   **Validation Strategy**: 
    1.  **Code Correctness**: Synthetic data is generated to match the expected psychometric distributions (e.g., skewed commission errors) to validate that the scoring and analysis pipelines function correctly (unit tests).
    2.  **Statistical Sensitivity**: A **Monte Carlo simulation study** will be performed to validate the statistical power of the analysis pipeline under the expected noise conditions, rather than relying on synthetic data to "validate" the effect.

**Data Limitations**:
-   **Self-Report Bias**: Compliance logs are self-reported and subject to bias. They are treated as a **proxy** for the intervention, not a ground-truth measure. The sensitivity analysis (FR-011) is a primary validity check, not a post-hoc mitigation. The study measures the impact of *self-reported* decluttering; any discrepancy between self-report and objective screen time dilutes the treatment effect, biasing results toward the null.
-   **Sample Size**: The study is explicitly a pilot. Results will be reported with effect sizes and confidence intervals, emphasizing the need for replication and the results of the power simulation.
-   **Dataset Fit**: No single public dataset contains all required variables. The analysis pipeline is validated against synthetic data generated from the instrument specifications.

## Risk Mitigation

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Non-compliance** | Low validity of intervention | Log all deviations; include in analysis but flag. |
| **Attrition** | Reduced power | Retain baseline data for descriptive stats; exclude from paired tests. |
| **Normality Violation** | Invalid parametric tests | Use bootstrapping (primary, pre-registered) and Wilcoxon (fallback for convergence only). **No Shapiro-Wilk trigger.** |
| **Multiple Testing** | Inflated Type I error | Holm-Bonferroni correction. |
| **Compute Limits** | Pipeline failure | Use CPU-only libraries; sample data if necessary (not expected). |
| **Underpowered Design** | False negatives | Explicitly report as a limitation; focus on effect size estimation and feasibility metrics; use Monte Carlo simulation to quantify power. |
| **Self-Report Validity** | Dilution of treatment effect | Explicitly acknowledge in discussion; FR-011 sensitivity analysis; frame conclusions around *self-reported* behavior change. |