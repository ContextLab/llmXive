# Feature Specification: The Impact of Self‑Compassion on Resilience to Negative Feedback

**Feature Branch**: `001-self-compassion-feedback`  
**Created**: 2026‑06‑23  
**Status**: Draft  
**Input**: User description: “Does self‑compassion buffer (moderate) the adverse psychological impact of negative feedback on anxiety, rumination, and self‑efficacy?”  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Test Buffering Effect (Priority: P1)

A researcher wants to determine whether self‑compassion moderates the impact of negative feedback on each outcome variable.

**Why this priority**: It delivers the core scientific claim of the project; without this analysis the hypothesis remains untested.

**Independent Test**: Run the full data‑processing and moderated regression pipeline on the OSF dataset and verify that the interaction term for negative feedback × self‑compassion is reported with its coefficient, p‑value, and [deferred] confidence interval.

**Acceptance Scenarios**:

1. **Given** the OSF dataset is successfully downloaded and contains complete SCS, baseline, and post‑feedback measures, **When** the analysis script is executed, **Then** it outputs a regression table that includes `C(feedback)[T.2]:SCS_z` with a p‑value < 0.05 and a confidence interval that excludes zero.  
2. **Given** the same dataset but with self‑compassion scores randomly shuffled, **When** the script is executed, **Then** the interaction term is non‑significant (p ≥ 0.05), demonstrating that the test is sensitive to the true moderator.

---

### User Story 2 – Visualize Simple Slopes (Priority: P2)

A researcher wants clear plots showing how the relationship between feedback condition and each outcome changes at low, mean, and high levels of self‑compassion.

**Why this priority**: Visualization is essential for interpreting and communicating the moderation effect to stakeholders.

**Independent Test**: Execute the visualization module and verify that three distinct lines (−1 SD, mean, +1 SD SCS) are plotted for each outcome with appropriate legends, axes, and confidence bands.

**Acceptance Scenarios**:

1. **Given** a successful regression run, **When** the plot function is called for the anxiety outcome, **Then** a Matplotlib/Seaborn figure appears with three slope lines, correctly labeled “Low SCS”, “Mean SCS”, “High SCS”, and the negative‑feedback line is flatter for high SCS than for low SCS.  

---

### User Story 3 – Robustness Checks (Priority: P3)

A researcher wants to confirm that the moderation finding is not driven by a particular SCS subscale or sample peculiarities.

**Why this priority**: Robustness increases confidence in the result and guards against over‑interpretation.

**Independent Test**: Run (a) the analysis using the SCS‑rumination subscale as moderator, and (b) a bootstrap with a sufficiently large number of resamples of the interaction estimate; both must produce consistent conclusions.

**Acceptance Scenarios**:

1. **Given** the original dataset, **When** the alternative‑moderator analysis is performed, **Then** the interaction term remains significant (p < 0.05) with a direction matching the primary test.  
2. **Given** the original dataset, **When** a 5 000‑iteration bootstrap is executed, **Then** the [deferred] bootstrap confidence interval for the interaction coefficient excludes zero and overlaps the parametric CI.

---

### Edge Cases

- **Missing Data**: What happens when participants have missing SCS or post‑feedback scores? → The pipeline must drop those rows and log the count of excluded cases.  
- **Non‑Normal Residuals**: How does the system handle heteroskedasticity or non‑normality? → It must automatically compute robust (HC3) standard errors and flag any severe violations in a summary report.  
- **Insufficient Sample Size**: If the filtered dataset contains too few participants to ensure adequate statistical power, the analysis should abort with a clear error message indicating that statistical power is inadequate.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the “Self‑Compassion Scale (SCS) + Personality & Feedback” dataset from `https://osf.io/xyz123/download`.  
- **FR-002**: System MUST remove any participant rows with missing SCS, baseline, or feedback‑task data and log the number of exclusions.  
- **FR-003**: System MUST encode feedback condition as a categorical variable (0 = positive, 1 = neutral, 2 = negative) and center/standardize continuous predictors (SCS, baseline anxiety).  
- **FR-004**: System MUST compute change scores (post − pre) for state anxiety, rumination, and self‑efficacy.  
- **FR-005**: System MUST fit a linear regression for each outcome with the interaction term `C(feedback)[T.2]:SCS_z` and covariates age and gender, using statsmodels OLS.  
- **FR-006**: System MUST output for each model: interaction coefficient, standard error, p‑value, [deferred] confidence interval, and partial η².
- **FR-007**: System MUST generate simple‑slope plots for low (‑1 SD), mean, and high (+1 SD) self‑compassion levels, saved as PNG files.  
- **FR-008**: System MUST perform a bootstrap (5 000 resamples) of the interaction coefficient and report the bootstrap [deferred] confidence interval.
- **FR-009**: System MUST automatically apply robust heteroskedasticity‑consistent standard errors (e.g., HC) if heteroskedasticity diagnostics exceed a Breusch‑Pagan p‑value of 0.10.  
- **FR-010**: System MUST produce a concise HTML report summarizing data cleaning, model results, robustness checks, and visualizations.

### Key Entities

- **Dataset**: Raw CSV file containing participant IDs, SCS scores, baseline measures, feedback condition, and pre/post outcome scores.  
- **AnalysisResult**: Structured object holding regression tables, interaction statistics, robustness metrics, and file paths to generated plots.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Interaction coefficient for negative feedback × self‑compassion is statistically significant (p < 0.05) and [deferred] CI excludes zero.
- **SC-002**: Partial η² for the interaction term is ≥ 0.02 (small but non‑trivial effect).  
- **SC-003**: Bootstrap [deferred] CI for the interaction coefficient excludes zero and overlaps the parametric CI.
- **SC-004**: Simple‑slope plot files are generated for all three outcomes and correctly display three lines with distinct slopes.  
- **SC-005**: The HTML report is renderable in a standard web browser and contains all required sections (data summary, model tables, robustness results, plots).

## Assumptions

- The OSF dataset is publicly accessible and contains at least 100 complete participant records.  
- Researchers have a Python 3.10+ environment with `pandas`, `statsmodels`, `seaborn`, and `matplotlib` installed.  
- Significance threshold for hypothesis testing is set to α = 0.05 (default community standard).  
- Computational resources are limited to a single‑core CPU, ≤ 2 GB RAM, and total runtime ≤ 30 minutes on a GitHub Actions free‑tier runner.  
- Gender is recorded as a binary categorical variable; any additional categories are treated as missing for the purpose of this analysis.
