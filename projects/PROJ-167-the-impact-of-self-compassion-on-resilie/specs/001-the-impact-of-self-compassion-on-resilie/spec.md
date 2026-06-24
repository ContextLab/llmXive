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

**Links**: Implements FR‑001, FR‑002, FR‑003, FR‑004, FR‑005, FR‑006, FR‑009; validates SC‑001 and SC‑002.

**Independent Test**: Run the full data‑processing and moderated regression pipeline on the OSF dataset and verify that the interaction term for negative feedback × self‑compassion is reported with its coefficient, p‑value, and confidence interval.

**Acceptance Scenarios**:

1. **Given** the OSF dataset is successfully downloaded and contains complete SCS, baseline, and post‑feedback measures, **When** the analysis script is executed, **Then** it outputs a regression table that includes `C(feedback)[T.2]:SCS_z` with a p‑value < 0.05 and a confidence interval that excludes zero.  
2. **Given** the same dataset but with self‑compassion scores randomly shuffled, **When** the script is executed, **Then** the interaction term is non‑significant (p ≥ 0.05), demonstrating that the test is sensitive to the true moderator.

### User Story 2 – Visualize Simple Slopes (Priority: P2)

A researcher wants clear plots showing how the relationship between feedback condition and each outcome changes at low, mean, and high levels of self‑compassion.

**Why this priority**: Visualization is essential for interpreting and communicating the moderation effect to stakeholders.

**Links**: Implements FR‑007; validates SC‑004.

**Independent Test**: Execute the visualization module and verify that three distinct lines (−1 SD, mean, +1 SD SCS) are plotted for each outcome with appropriate legends, axes, and confidence bands.

**Acceptance Scenarios**:

1. **Given** a successful regression run, **When** the plot function is called for the anxiety outcome, **Then** a Matplotlib/Seaborn figure appears with three slope lines, correctly labeled “Low SCS”, “Mean SCS”, “High SCS”, and the negative‑feedback line is flatter for high SCS than for low SCS.  

### User Story 3 – Robustness Checks (Priority: P3)

A researcher wants to confirm that the moderation finding is not driven by a particular SCS subscale or sample peculiarities.

**Why this priority**: Robustness increases confidence in the result and guards against over‑interpretation.

**Links**: Implements FR‑014, FR‑008 (with fixed seed FR‑012); validates SC‑003.

**Independent Test**: Run (a) the analysis using the SCS‑rumination subscale as moderator (FR‑014), and (b) a bootstrap with a sufficiently large number of resamples of the interaction estimate; both must produce consistent conclusions.

**Acceptance Scenarios**:

1. **Given** the original dataset, **When** the alternative‑moderator analysis is performed (FR‑014), **Then** the interaction term remains significant (p < 0.05) with a direction matching the primary test.  
2. **Given** the original dataset, **When** a 5 000‑iteration bootstrap (seed = 42) is executed, **Then** the bootstrap confidence interval for the interaction coefficient excludes zero and overlaps the parametric CI.

### User Story 4 – Generate HTML Report (Priority: P2)

A researcher needs a concise, shareable summary of all analyses, visualizations, and robustness checks.

**Why this priority**: The report consolidates results for publication and stakeholder review, and directly drives the creation of the HTML output (FR‑010).

**Links**: Implements FR‑010 and includes documentation of FR‑011 (well‑being procedures); validates SC‑005.

**Independent Test**: After a successful run, invoke the reporting module and verify that an HTML file is produced, renders in a standard browser, and contains sections for data cleaning, model tables, robustness results, and all generated plots.

**Acceptance Scenarios**:

1. **Given** completed analyses and plots, **When** the reporting function is called, **Then** an `report.html` file is written, opens without errors in Chrome/Firefox, and displays the expected sections and figures.

---

### Edge Cases

- **Missing Data**: What happens when participants have missing SCS or post‑feedback scores? → The pipeline must drop those rows and log the count of excluded cases.  
- **Non‑Normal Residuals**: How does the system handle heteroskedasticity or non‑normality? → It must automatically compute robust (HC3) standard errors and flag any severe violations in a summary report.  
- **Insufficient Sample Size**: If the filtered dataset contains too few participants to ensure adequate statistical power, the analysis should abort with a clear error message indicating that statistical power is inadequate.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the “Self‑Compassion Scale (SCS) + Personality & Feedback” dataset from `https://osf.io/xyz123/download`. *(linked to User Story 1 & 4)*
- **FR-002**: System MUST remove any participant rows with missing SCS, baseline, or feedback‑task data and log the number of exclusions. *(linked to User Story 1)*
- **FR-003**: System MUST encode feedback condition as a categorical variable (0 = positive, 1 = neutral, 2 = negative) and center/standardize continuous predictors (SCS, baseline anxiety). *(linked to User Story 1)*
- **FR-004**: System MUST prepare variables for ANCOVA: retain baseline measures, compute post‑feedback scores, and standardize continuous covariates. The post‑feedback outcome will be used as the dependent variable with baseline as a covariate. *(linked to User Story 1)*
- **FR-005**: System MUST fit a linear regression (ANCOVA) for each outcome with the dependent variable = post‑feedback score, covariates = baseline outcome, age, gender, standardized SCS, and the interaction term `C(feedback)[T.2]:SCS_z`, using statsmodels OLS. *(linked to User Story 1)*
- **FR-006**: System MUST output for each model: interaction coefficient, standard error, p‑value, confidence interval, partial η², and robust (HC3) standard errors. *(linked to User Story 1)*
- **FR-007**: System MUST generate simple‑slope plots for low (‑1 SD), mean, and high (+1 SD) self‑compassion levels, saved as PNG files. *(linked to User Story 2)*
- **FR-008**: System MUST perform a bootstrap (5 000 resamples) of the interaction coefficient using random seed 42 (as set by FR‑012) and report the bootstrap confidence interval. *(linked to User Story 3)*
- **FR-009**: System MUST automatically compute robust heteroskedasticity‑consistent standard errors (HC3) for all models and **flag** the results when the Breusch‑Pagan test yields p < 0.10, indicating heteroskedasticity. *(aligned with FR‑006)*
- **FR-010**: System MUST produce a concise HTML report summarizing data cleaning, model results, robustness checks, and visualizations. *(linked to User Story 4)*
- **FR-011**: System MUST incorporate participant‑well‑being procedures required by the constitution: (a) pre‑screen participants for severe mental‑health risk, (b) provide a standardized debriefing script after the feedback task, and (c) supply mental‑health resource links in the debriefing. *(linked to User Story 4)*
- **FR-012**: System MUST set the random seed to `42` before any stochastic operation (e.g., bootstrap) to guarantee reproducibility. *(linked to FR‑008)*
- **FR-014**: System MUST repeat the primary moderation analysis using the SCS‑rumination subscale as the moderator, outputting the same set of statistics as in FR‑006.  

### Key Entities

- **Dataset**: Raw CSV file containing participant IDs, SCS scores, baseline measures, feedback condition, and pre/post outcome scores.  
- **AnalysisResult**: Structured object holding regression tables, interaction statistics, robustness metrics, and file paths to generated plots.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Interaction coefficient for negative feedback × self‑compassion is statistically significant (p < 0.05) and its confidence interval excludes zero. *(validated by User Story 1)*
- **SC-002**: Partial η² for the interaction term is ≥ 0.02 (small but non‑trivial effect) as reported by FR‑006. *(validated by User Story 1)*
- **SC-003**: Bootstrap confidence interval for the interaction coefficient excludes zero and overlaps the parametric confidence interval from FR‑006. *(validated by User Story 3)*
- **SC-004**: Simple‑slope plot files are generated for all three outcomes and correctly display three lines with distinct slopes. *(validated by User Story 2)*
- **SC-005**: The HTML report (FR‑010) is renderable in a standard web browser and contains all required sections; this criterion is directly tied to User Story 4 and FR‑010.

## Assumptions

- The OSF dataset is publicly accessible and contains at least 100 complete participant records.  
- Researchers have a Python 3.10+ environment with `pandas`, `statsmodels`, `seaborn`, and `matplotlib` installed.  
- Significance threshold for hypothesis testing is set to α = 0.05 (default community standard).  
- Computational resources are limited to a single‑core CPU, ≤ 2 GB RAM, and total runtime ≤ 30 minutes on a GitHub Actions free‑tier runner.  
- Gender is recorded as a binary categorical variable; any additional categories are treated as missing for the purpose of this analysis.  
- The project complies with the constitution’s participant‑well‑being mandate via FR‑011 (pre‑screening, debriefing, mental‑health resources).  