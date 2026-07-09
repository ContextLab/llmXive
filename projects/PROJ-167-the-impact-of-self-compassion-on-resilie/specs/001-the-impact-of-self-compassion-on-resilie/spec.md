# Feature Specification: The Impact of Self‑Compassion on Resilience to Negative Feedback

**Feature Branch**: `001-self-compassion-feedback`
**Created**: 2026‑06‑28
**Status**: Draft
**Input**: User description: “Does self‑compassion buffer (moderate) the adverse psychological impact of negative feedback on anxiety, rumination, and self‑efficacy?”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Test Buffering Effect (Priority: P1)

A researcher wants to determine whether self‑compassion moderates the impact of negative feedback on each outcome variable (anxiety, rumination, self‑efficacy) using a statistically rigorous, methodologically sound analysis.

**Why this priority**: It delivers the core scientific claim of the project; without this analysis the hypothesis remains untested. The method must explicitly handle the observational nature of the data (if randomization is not confirmed) and correct for multiple comparisons.

**Independent Test**: Run the full data‑processing and moderated regression pipeline on the verified dataset and verify that the interaction term for negative feedback × self‑compassion is reported with its coefficient, p‑value, and confidence interval, with explicit adjustment for family-wise error.

**Acceptance Scenarios**:

1. **Given** the verified dataset contains all required variables (SCS, pre/post outcomes, feedback condition) and the dataset metadata confirms experimental randomization of feedback, **When** the analysis script is executed, **Then** it outputs a regression table for each outcome including the `C(feedback)[T.2]:SCS_z` interaction term, with Holm‑Bonferroni adjusted p‑values reported, and a 95% confidence interval that excludes zero if the hypothesis holds.
2. **Given** the dataset lacks experimental randomization metadata, **When** the script executes, **Then** it explicitly frames the interaction result as "associational" in the report and flags the limitation, rather than claiming a causal moderation effect.
3. **Given** the dataset is missing any of the required outcome variables (post-feedback anxiety, rumination, or self-efficacy), **Then** the pipeline halts immediately with exit code 1 and the error message: `[DATA_UNAVAILABLE: Required post-feedback outcome variables missing from source. The dataset 'Feedback and Self-Compassion' (OSF ID: k9r2) is required. If unavailable, the pipeline cannot proceed.]`.
4. **Given** the dataset contains the required variables but the hypothesis is NOT supported (confidence interval includes zero), **When** the script executes, **Then** it outputs a regression table for each outcome including the interaction term, with Holm‑Bonferroni adjusted p‑values reported, and a 95% confidence interval that includes zero, and the report explicitly states "Hypothesis Not Supported".

---

### User Story 2 – Visualize Simple Slopes (Priority: P2)

A researcher wants clear plots showing how the relationship between feedback condition and each outcome changes at low, mean, and high levels of self‑compassion to interpret the interaction magnitude.

**Why this priority**: Visualization is essential for interpreting and communicating the moderation effect to stakeholders and verifying the direction of the buffering effect.

**Independent Test**: Execute the visualization module and verify that three distinct lines (−1 SD, mean, +1 SD SCS) are plotted for each outcome with appropriate legends, axes, confidence bands, and that PNG files named `anxiety_simple_slopes.png`, `rumination_simple_slopes.png`, `self_efficacy_simple_slopes.png` are saved.

**Acceptance Scenarios**:

1. **Given** a successful regression run, **When** the plot function is called for the anxiety outcome, **Then** a Matplotlib/Seaborn figure appears with three slope lines, correctly labeled “Low SCS”, “Mean SCS”, “High SCS”, and the negative‑feedback line is flatter for high SCS than for low SCS (if buffering exists). The figure is saved as `anxiety_simple_slopes.png`.
2. **Given** the analysis is run, **Then** the output directory contains exactly three PNG files named `<outcome>_simple_slopes.png` for anxiety, rumination, and self‑efficacy, and each file is non-empty and renders correctly in a standard image viewer.

---

### User Story 3 – Robustness Checks (Priority: P3)

A researcher wants to confirm that the moderation finding is not driven by a particular SCS subscale, collinearity issues, or specific threshold choices.

**Why this priority**: Robustness increases confidence in the result and guards against over‑interpretation or spurious findings due to model specification.

**Independent Test**: Run (a) the analysis using the SCS‑Self‑Kindness subscale as moderator, (b) a collinearity diagnostic (VIF), and (c) a sensitivity analysis sweeping the interaction significance threshold, and verify consistent conclusions.

**Acceptance Scenarios**:

1. **Given** the original dataset, **When** the alternative‑moderator analysis is performed (using SCS‑Self‑Kindness), **Then** the interaction term is reported with the same statistics as the primary test, and the report notes whether the direction and significance match the primary SCS‑Total result.
2. **Given** the regression models, **When** Variance Inflation Factors (VIF) are computed for predictors, **Then** the report explicitly states the VIF values for `SCS_z` and `C(feedback)[T.2]`, and if any VIF > 5, a warning is logged indicating potential collinearity.
3. **Given** the primary interaction p-value, **When** a sensitivity analysis is run sweeping the significance threshold (e.g., α ∈ {0.01, 0.05, 0.10}), **Then** the report displays how the number of significant findings changes across these thresholds.

---

### User Story 4 – Generate HTML Report (Priority: P2)

A researcher needs a concise, shareable summary of all analyses, visualizations, robustness checks, and methodological caveats.

**Why this priority**: The report consolidates results for publication and stakeholder review, and directly drives the creation of the HTML output.

**Independent Test**: After a successful run, invoke the reporting module and verify that an `report.html` file is produced, renders without errors in Chrome/Firefox, and contains sections for data cleaning, descriptive statistics, model tables, robustness results, simple‑slope plots (embedded PNGs), and methodological caveats.

**Acceptance Scenarios**:

1. **Given** completed analyses and plots, **When** the reporting function is called, **Then** an `report.html` file is written, opens without errors in Chrome/Firefox, and displays the expected sections including a "Methodological Caveats" section that explicitly states whether findings are causal or associational.

---

### Edge Cases

- **Missing Data**: Rows with missing SCS, baseline, or post‑feedback scores are dropped via listwise deletion; the number of exclusions is logged and the final N is reported. If N < 92 (based on power analysis), the pipeline aborts with a power warning.
- **Non‑Normal Residuals**: Robust (HC3) standard errors are computed; if the Breusch‑Pagan test yields p < 0.10, a heteroskedasticity flag is added to the report and the robust SEs are used for inference.
- **Dataset Mismatch**: If the downloaded dataset lacks the required post‑feedback outcome columns, the pipeline terminates immediately with a specific error identifying the missing columns.
- **Collinearity**: If VIF > 5 for the interaction term predictors, the report explicitly flags this and refrains from claiming independent effects for the collinear variables.
- **Randomization Ambiguity**: If the dataset metadata does not confirm experimental randomization of the feedback condition, the system defaults to framing all interaction findings as "associational" rather than causal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the dataset from the verified OSF URL (https://osf.io/3k9r2/) and verify that it contains the columns: `scf_total`, `scf_self_judgment`, `scf_self_kindness`, `stai_pre`, `stai_post`, `rrs_pre`, `rrs_post`, `gse_pre`, `gse_post`, `feedback_cond`, `age`, `gender`, and personality traits (Big Five) if available. If any required column is missing, the system MUST abort with exit code 1 and the error message: `[DATA_UNAVAILABLE: Required columns missing from dataset. Expected: [list of missing columns]]`. The system MUST also verify that the total number of complete participant records (N) is ≥ 92. If N < 92, the system MUST abort with exit code 1 and the error message: `[POWER_INSUFFICIENT: Sample size (N) is less than the required 92 for adequate power (f²=0.02, α=0.05, power=0.80).]`. *(See US-1)*
- **FR-002**: System MUST remove any participant rows with missing SCS, baseline, or feedback‑task data (listwise deletion) and log the number of exclusions and the final sample size (N) in the report. *(See US-1)*
- **FR-003**: System MUST encode feedback condition as a categorical variable with 'Positive Feedback' as the reference level (0 = Positive, 1 = Neutral, 2 = Negative) and center/standardize continuous predictors (SCS, baseline anxiety, baseline rumination, baseline self‑efficacy) using z‑scores. *(See US-1)*
- **FR-004**: System MUST prepare the dependent variables as the post‑feedback scores (stai_post, rrs_post, gse_post) for anxiety, rumination, and self‑efficacy. The baseline scores (stai_pre, rrs_pre, gse_pre) will be used as covariates in the ANCOVA model. *(See US-1)*
- **FR-005**: System MUST fit a linear regression (ANCOVA) for each outcome with the dependent variable = post‑feedback score, covariates = baseline outcome, age, gender, standardized SCS, and the interaction term `C(feedback)[T.2]:SCS_z`, using statsmodels OLS. The reference level for feedback must be 'Positive Feedback'. *(See US-1)*
- **FR-006**: System MUST output for each model: interaction coefficient, standard error, p‑value, confidence interval, partial η², and robust (HC3) standard errors. *(See US-1)*
- **FR-007**: System MUST generate simple‑slope plots for low (‑1 SD), mean, and high (+1 SD) self‑compassion levels, saved as PNG files named `<outcome>_simple_slopes.png`. *(See US-2)*
- **FR-008**: System MUST perform a bootstrap of the interaction coefficient using 5,000 resamples (random seed = 42) and report the 95% bootstrap confidence interval. Convergence is assessed by stability of the standard error across the resamples. If convergence is not achieved within 10,000 total resamples, the system MUST abort with exit code 1 and the error message: `[BOOTSTRAP_CONVERGENCE_FAILED: Bootstrap did not converge within 10,000 resamples.]`. *(See US-3)*
- **FR-009**: System MUST automatically compute robust heteroskedasticity‑consistent standard errors (HC3) for all models and **flag** heteroskedasticity in the report when the Breusch‑Pagan test yields p < 0.10. *(See US-1)*
- **FR-010**: System MUST produce a concise HTML report summarizing data cleaning, descriptive statistics, model results, robustness checks, visualizations, and methodological caveats. The report must render in a standard web browser without errors. *(See US-4)*
- **FR-011**: System MUST apply Holm‑Bonferroni correction across the four hypothesis tests (three primary outcomes + robustness moderator) and report adjusted p‑values. *(See US-1)*
- **FR-012**: System MUST set the random seed to `42` before any stochastic operation (e.g., bootstrap) to guarantee reproducibility. *(See US-3)*
- **FR-013**: System MUST compute Variance Inflation Factors (VIF) for all predictors in the final models and report the values; if any VIF > 5, the report MUST explicitly flag potential collinearity. *(See US-3)*
- **FR-014**: System MUST repeat the primary moderation analysis using the SCS‑Self‑Kindness subscale as the moderator, outputting the same set of statistics as in FR‑006. *(See US-3)*
- **FR-015**: System MUST perform a sensitivity analysis by re-running the primary model with significance thresholds α ∈ {0.01, 0.05, 0.10} and report how the number of significant findings varies. *(See US-3)*
- **FR-016**: System MUST compute a SHA‑256 checksum of the raw dataset immediately after download and store this hash in the project state file (`state/projects/...yaml`). *(See US-4)*
- **FR-017**: System MUST verify that the dataset metadata or documentation explicitly states that the feedback condition was experimentally randomized. If not, the system MUST default to framing all findings as "associational" in the report. *(See US-1)*
- **FR-018**: System MUST include personality traits (Big Five) as covariates in the ANCOVA model if they are present in the dataset. If they are not present, the system MUST log a warning and proceed with the reduced model. *(See US-1)*

### Key Entities

- **Dataset**: Raw CSV file containing participant IDs, SCS scores, baseline and post‑feedback anxiety, rumination, self‑efficacy, feedback condition, demographics, and personality traits.
- **AnalysisResult**: Structured object holding regression tables, interaction statistics, robustness metrics, VIF values, and file paths to generated plots.
- **ReportArtifact**: The generated HTML file containing all results and methodological caveats.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The report includes the interaction coefficient for negative feedback × self‑compassion, its p‑value (adjusted), and its confidence interval. *(validated by User Story 1)*
- **SC-002**: The report includes the calculated Partial η² value for the interaction term. *(validated by User Story 1)*
- **SC-003**: The report includes the bootstrap confidence interval for the interaction coefficient, the parametric confidence interval, and a note on whether they overlap. If they do not overlap, a methodological caveat is added. *(validated by User Story 3)*
- **SC-004**: Simple‑slope plot PNG files are generated for all three outcomes (`anxiety_simple_slopes.png`, `rumination_simple_slopes.png`, `self_efficacy_simple_slopes.png`) and each plot displays **three distinct lines** representing low (‑1 SD), mean, and high (+1 SD) self‑compassion. *(validated by User Story 2)*
- **SC-005**: The HTML report (`report.html`) is renderable in a standard web browser and contains all required sections (Data Cleaning, Descriptive Statistics, Model Results, Robustness Checks, Visualizations, Methodological Caveats) with no rendering errors. *(validated by User Story 4)*
- **SC-006**: The report explicitly states whether findings are causal or associational based on the dataset's randomization metadata, and if VIF > 5, a collinearity warning is present. *(validated by User Story 1 & 3)*

## Assumptions

- The OSF dataset at `https://osf.io/3k9r2/` is publicly accessible, provided as a CSV file, and contains **at least 158 complete participant records** before cleaning to ensure adequate power for detecting a small interaction effect (f² = 0.02, α = 0.05, power = 0.80) across three outcomes. A minimum of 92 complete records is required after cleaning.
- If the dataset metadata does not explicitly confirm experimental randomization of the feedback condition, the analysis will frame all interaction findings as **associational** rather than causal, as required by methodological soundness.
- Researchers have a Python 3.10+ environment with `pandas`, `statsmodels`, `seaborn`, and `matplotlib` installed.
- Significance threshold for hypothesis testing is set to α = 0.05 (default community standard), with Holm‑Bonferroni correction applied for multiple comparisons.
- Computational resources are limited to a single‑core CPU and ≤ 2 GB RAM on a GitHub Actions free‑tier runner; the analysis is designed to complete efficiently.
- Gender is recorded as a binary categorical variable; any additional categories are treated as missing for the purpose of this analysis.
- Anxiety is measured with the State‑Trait Anxiety Inventory (STAI‑State; Spielberger); rumination with the Ruminative Responses Scale (RRS; Nolen‑Hoeksema & Morrow); self‑efficacy with the General Self‑Efficacy Scale (GSES; Schwarzer & Jerusalem). All instruments have demonstrated reliability and validity in prior literature.
- The Self‑Compassion Scale (SCS; Neff,) is used to assess self‑compassion; it has established psychometric properties.
- The dataset contains the specific post‑feedback measures for anxiety, rumination, and self‑efficacy required for the ANCOVA analysis. If the dataset lacks these, the pipeline will halt with a specific error.
- Robust (HC3) standard errors are computed; heteroskedasticity is flagged when the Breusch‑Pagan test yields p < 0.10.
- All random operations use seed = 42 for reproducibility.
- The raw dataset checksum is recorded as a SHA‑256 hash in the project state file to satisfy data‑hygiene requirements.
- A sensitivity analysis sweeping the significance threshold (α ∈ {0.01, 0.05, 0.10}) is computationally trivial and included to demonstrate robustness of the primary finding.
- The VIF threshold for flagging collinearity is set to 5, consistent with common social science standards.
- The dataset is provided as a CSV file.
- The 'Self-Kindness' subscale is used for the robustness check as it is a theoretically distinct component of self-compassion.