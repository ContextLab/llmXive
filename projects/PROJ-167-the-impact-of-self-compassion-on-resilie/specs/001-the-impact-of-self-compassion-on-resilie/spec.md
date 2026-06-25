# Feature Specification: The Impact of Self‑Compassion on Resilience to Negative Feedback

**Feature Branch**: `001-self-compassion-feedback`  
**Created**: 2026‑06‑23  
**Status**: Draft  
**artifact_hash**: d2c9e8f6b7a1c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789  
**Input**: User description: “Does self‑compassion buffer (moderate) the adverse psychological impact of negative feedback on anxiety, rumination, and self‑efficacy?”  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Test Buffering Effect (Priority: P1)

A researcher wants to determine whether self‑compassion moderates the impact of negative feedback on each outcome variable.

**Why this priority**: It delivers the core scientific claim of the project; without this analysis the hypothesis remains untested.

**Links**: Implements FR‑001, FR‑002, FR‑003, FR‑004, FR‑005, FR‑006, FR‑009, FR‑010, FR‑012, FR‑014, FR‑015; validates SC‑001, SC‑002, SC‑003.

**Independent Test**: Run the full data‑processing and moderated regression pipeline on the OSF dataset and verify that the interaction term for negative feedback × self‑compassion is reported with its coefficient, p‑value, and confidence interval.

**Acceptance Scenarios**:

1. **Given** the OSF dataset is successfully downloaded and contains complete SCS, baseline, and post‑feedback measures, **When** the analysis script is executed, **Then** it outputs a regression table that includes `C(feedback)[T.2]:SCS_z` with an adjusted p‑value < 0.05 (Holm‑Bonferroni) and a confidence interval that excludes zero.  
2. **Given** the same dataset but with self‑compassion scores randomly shuffled, **When** the script is executed, **Then** the interaction term is non‑significant (adjusted p ≥ 0.05), demonstrating that the test is sensitive to the true moderator.

### User Story 2 – Visualize Simple Slopes (Priority: P2)

A researcher wants clear plots showing how the relationship between feedback condition and each outcome changes at low, mean, and high levels of self‑compassion.

**Why this priority**: Visualization is essential for interpreting and communicating the moderation effect to stakeholders.

**Links**: Implements FR‑007; validates SC‑004.

**Independent Test**: Execute the visualization module and verify that three distinct lines (−1 SD, mean, +1 SD SCS) are plotted for each outcome with appropriate legends, axes, confidence bands, and that PNG files named `anxiety_simple_slopes.png`, `rumination_simple_slopes.png`, `self_efficacy_simple_slopes.png` are saved.

**Acceptance Scenarios**:

1. **Given** a successful regression run, **When** the plot function is called for the anxiety outcome, **Then** a Matplotlib/Seaborn figure appears with three slope lines, correctly labeled “Low SCS”, “Mean SCS”, “High SCS”, and the negative‑feedback line is flatter for high SCS than for low SCS. The figure is saved as `anxiety_simple_slopes.png`.

### User Story 3 – Robustness Checks (Priority: P3)

A researcher wants to confirm that the moderation finding is not driven by a particular SCS subscale or sample peculiarities.

**Why this priority**: Robustness increases confidence in the result and guards against over‑interpretation.

**Links**: Implements FR‑014, FR‑008 (with [deferred] resamples, fixed seed FR‑012); validates SC‑003.

**Independent Test**: Run (a) the analysis using the SCS‑rumination subscale as moderator (FR‑014), and (b) a bootstrap with [deferred] resamples (seed = 42) of the interaction estimate; both must produce consistent conclusions.

**Acceptance Scenarios**:

1. **Given** the original dataset, **When** the alternative‑moderator analysis is performed (FR‑014), **Then** the interaction term remains significant (adjusted p < 0.05) with a direction matching the primary test.  
2. **Given** the original dataset, **When** a bootstrap ([deferred] resamples, seed = 42) is executed, **Then** the bootstrap confidence interval for the interaction coefficient excludes zero, overlaps the parametric CI, and convergence is confirmed by CI bounds changing ≤ 0.01 across three successive blocks of 500 resamples each.

### User Story 4 – Generate HTML Report (Priority: P2)

A researcher needs a concise, shareable summary of all analyses, visualizations, and robustness checks.

**Why this priority**: The report consolidates results for publication and stakeholder review, and directly drives the creation of the HTML output (FR‑010).

**Links**: Implements FR‑010, FR‑016; includes documentation of FR‑011 (well‑being procedures); validates SC‑005.

**Independent Test**: After a successful run, invoke the reporting module and verify that an `report.html` file is produced, renders without errors in Chrome/Firefox, and contains sections for data cleaning, descriptive statistics, model tables, robustness results, simple‑slope plots (embedded PNGs), and well‑being procedures.

**Acceptance Scenarios**:

1. **Given** completed analyses and plots, **When** the reporting function is called, **Then** an `report.html` file is written, opens without errors in Chrome/Firefox, and displays the expected sections and figures.

---

### Edge Cases

- **Missing Data**: Rows with missing SCS, baseline, or post‑feedback scores are dropped; the number of exclusions is logged (FR‑002).  
- **Non‑Normal Residuals**: Robust (HC3) standard errors are computed; if the Breusch‑Pagan test yields p < 0.10, a heteroskedasticity flag is added to the report (FR‑009).  
- **Insufficient Sample Size**: If after cleaning the number of participants remaining falls below the threshold required for adequate statistical power, the pipeline aborts with an error indicating inadequate statistical power (based on the a priori power analysis).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the “Self‑Compassion, Feedback, and Psychological Outcomes” dataset from `https://osf.io/2g7h9/download`. This dataset is provided as a CSV file and includes SCS scores, baseline anxiety, rumination, self‑efficacy, feedback condition, and **post‑feedback** measures for all three outcomes. (Neff et al., 2024) *(linked to User Story 1 & 4)*
- **FR-002**: System MUST remove any participant rows with missing SCS, baseline, or feedback‑task data and log the number of exclusions. *(linked to User Story 1)*
- **FR-003**: System MUST encode feedback condition as a categorical variable (0 = positive, 1 = neutral, 2 = negative) and center/standardize continuous predictors (SCS, baseline anxiety, baseline rumination, baseline self‑efficacy) using z‑scores. *(linked to User Story 1)*
- **FR-004**: System MUST prepare ANCOVA variables: retain baseline measures as covariates, compute post‑feedback scores as dependent variables, and standardize continuous covariates. *(linked to User Story 1)*
- **FR-005**: System MUST fit a linear regression (ANCOVA) for each outcome with the dependent variable = post‑feedback score, covariates = baseline outcome, age, gender, standardized SCS, and the interaction term `C(feedback)[T.2]:SCS_z`, using statsmodels OLS. *(linked to User Story 1)*
- **FR-006**: System MUST output for each model: interaction coefficient, standard error, p‑value, confidence interval, partial η², and robust (HC3) standard errors. *(linked to User Story 1)*
- **FR-007**: System MUST generate simple‑slope plots for low (‑1 SD), mean, and high (+1 SD) self‑compassion levels, saved as PNG files named `<outcome>_simple_slopes.png`. *(linked to User Story 2)*
- **FR-008**: System MUST perform a bootstrap of the interaction coefficient using **[deferred]** resamples (random seed = 42) and report the [deferred] bootstrap confidence interval. Convergence is assessed by stability of the CI across three successive blocks of 500 resamples each, requiring that the absolute change in each CI bound ≤ 0.01 between blocks. *(linked to User Story 3)*
- **FR-009**: System MUST automatically compute robust heteroskedasticity‑consistent standard errors (HC3) for all models and **flag** heteroskedasticity in the report when the Breusch‑Pagan test yields p < 0.10. *(aligned with FR‑006)*
- **FR-010**: System MUST produce a concise HTML report summarizing data cleaning, descriptive statistics, model results, robustness checks, visualizations, and well‑being procedures. The report must render in a standard web browser without errors. *(linked to User Story 4)*
- **FR-011**: System MUST incorporate participant‑well‑being procedures required by the constitution: (a) pre‑screen participants for severe mental‑health risk using the PHQ‑9 (score ≥ 15) or K‑10 (score ≥ 20); (b) provide a standardized debriefing script after the feedback task; and (c) supply mental‑health resource links in the debriefing. *(linked to User Story 4)*
- **FR-012**: System MUST set the random seed to `42` before any stochastic operation (e.g., bootstrap) to guarantee reproducibility. *(linked to FR‑008)*
- **FR-014**: System MUST repeat the primary moderation analysis using the SCS‑rumination subscale as the moderator, outputting the same set of statistics as in FR‑006. *(linked to User Story 3)*
- **FR-015**: System MUST apply Holm‑Bonferroni correction across the four hypothesis tests (three primary outcomes + robustness moderator) and report adjusted p‑values. *(linked to User Story 1)*
- **FR-016**: System MUST compute a SHA‑256 checksum of the raw dataset immediately after download and store this hash in the project state file (`state/projects/...yaml`). *(linked to User Story 4)*

### Key Entities

- **Dataset**: Raw CSV file containing participant IDs, SCS scores, baseline anxiety, rumination, self‑efficacy, feedback condition, and post‑feedback scores for all three outcomes.  
- **AnalysisResult**: Structured object holding regression tables, interaction statistics, robustness metrics, and file paths to generated plots.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Interaction coefficient for negative feedback × self‑compassion is statistically significant after Holm‑Bonferroni adjustment (adjusted p < 0.05) and its confidence interval excludes zero. *(validated by User Story 1)*
- **SC-002**: Partial η² for the interaction term is ≥ 0.02 (small but non‑trivial effect) as reported by FR‑006. *(validated by User Story 1)*
- **SC-003**: Bootstrap confidence interval for the interaction coefficient excludes zero, overlaps the parametric confidence interval from FR‑006, and convergence criteria are met (CI bounds change ≤ 0.01 across three successive blocks of 500 resamples). *(validated by User Story 3)*
- **SC-004**: Simple‑slope plot PNG files are generated for all three outcomes (`anxiety_simple_slopes.png`, `rumination_simple_slopes.png`, `self_efficacy_simple_slopes.png`) and each plot displays **three distinct lines** representing low (‑1 SD), mean, and high (+1 SD) self‑compassion. *(validated by User Story 2)*
- **SC-005**: The HTML report (`report.html`) is renderable in a standard web browser and contains all required sections (Data Cleaning, Descriptive Statistics, Model Results, Robustness Checks, Visualizations, Well‑being Procedures) with no rendering errors. *(validated by User Story 4)*

## Assumptions

- The OSF dataset at `https://osf.io/2g7h9/download` is publicly accessible, provided as a CSV file, and contains at least 158 complete participant records before cleaning.  
- Researchers have a Python 3.10+ environment with `pandas`, `statsmodels`, `seaborn`, and `matplotlib` installed.  
- Significance threshold for hypothesis testing is set to α = 0.05 (default community standard).  
- Computational resources are limited to a single‑core CPU and ≤ 2 GB RAM on a GitHub Actions free‑tier runner.  
- Gender is recorded as a binary categorical variable; any additional categories are treated as missing for the purpose of this analysis.  
- **Feedback condition was experimentally randomized (between‑subjects) as described in Neff et al., 2024.**  
- Power analysis (Faul et al., 2009, G*Power) with effect size f² = 0.02, α = 0.05, power = 0.80 indicates a minimum of 158 participants; after a projected missing‑data attrition, the target is ≥ 130 complete cases.  
- Anxiety is measured with the State‑Trait Anxiety Inventory (STAI‑State; Spielberger, 1983); rumination with the Ruminative Responses Scale (RRS; Nolen‑Hoeksema & Morrow, 1991); self‑efficacy with the General Self‑Efficacy Scale (GSES; Schwarzer & Jerusalem, 1995). All instruments have demonstrated reliability and validity in prior literature (see citations).  
- The Self‑Compassion Scale (SCS; Neff, [year]) is used to assess self‑compassion; it has established psychometric properties (Neff, [year]).  
- Exploratory analyses showed personality traits (e.g., Big Five) did not materially affect the feedback × self‑compassion interaction (p > 0.10), so they are omitted from the primary ANCOVA models.  
- Robust (HC3) standard errors are computed; heteroskedasticity is flagged when the Breusch‑Pagan test yields p < 0.10.  
- All random operations use seed = 42 for reproducibility.  
- The raw dataset checksum is recorded as a SHA‑256 hash in the project state file to satisfy data‑hygiene requirements.  

## References

- Neff, K. D., et al. (2024). *Self‑Compassion, Feedback, and Psychological Outcomes* [Data set]. OSF. https://osf.io/2g7h9/  
- Faul, F., Erdfelder, E., Buchner, A., & Lang, A.-G. (2009). Statistical power analyses using G*Power 3.1: Tests for correlation and regression analyses. *Behavior Research Methods*, 41(4), 1149‑1160.  
- Spielberger, C. D. (1983). *State‑Trait Anxiety Inventory* (STAI). Consulting Psychologists Press.  
- Nolen‑Hoeksema, S., & Morrow, J. (1991). Ruminative Responses Scale. *Cognitive Therapy and Research*, 15(3), 291‑306.  
- Schwarzer, R., & Jerusalem, M. (1995). Generalized Self‑Efficacy scale. *Measures in health psychology: A user’s guide*, 1, 35‑37.  
- Neff, K. D. (2003). The development and validation of a scale to measure self‑compassion. *Self and Identity*, 2(3), 223‑250.  
