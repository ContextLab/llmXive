# Feature Specification: The Impact of Self‑Compassion on Resilience to Negative Feedback

**Feature Branch**: `001-self-compassion-feedback`  
**Created**: 2026‑07‑12  
**Status**: Draft  
**Input**: User description: "Does self‑compassion buffer (moderate) the adverse psychological impact of negative feedback on anxiety, rumination, and self‑efficacy?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Test Buffering Effect (Priority: P1)

A researcher wants to determine whether self‑compassion moderates the impact of negative feedback on each outcome variable (anxiety, rumination, self‑efficacy) using a statistically rigorous, methodologically sound analysis.

**Why this priority**: It delivers the core scientific claim of the project; without this analysis the hypothesis remains untested. The method must explicitly handle the observational nature of the data (if randomization is not confirmed) and correct for multiple comparisons.

**Independent Test**: Run the full data‑processing and moderated regression pipeline on the verified dataset and verify that the interaction term for negative feedback × self‑compassion is reported with its coefficient, p‑value, and confidence interval, with explicit adjustment for family-wise error.

**Acceptance Scenarios**:

1. **Given** the verified dataset contains all required variables (SCS, pre/post outcomes, feedback condition) and the dataset metadata confirms experimental randomization of feedback, **When** the analysis script is executed, **Then** it outputs a regression table for each outcome including the `C(feedback, Treatment(reference='Positive'))[T.2]:SCS_z` interaction term, with Holm‑Bonferroni adjusted p‑values reported, and a 95% confidence interval that excludes zero if the hypothesis holds.
2. **Given** the dataset lacks experimental randomization metadata, **When** the script executes, **Then** it explicitly frames the interaction result as "associational" in the report and flags the limitation, rather than claiming a causal moderation effect.
3. **Given** the dataset is missing any of the required outcome variables (`stai_post`, `rrs_post`, or `gse_post`), **Then** the pipeline halts immediately with exit code 1 and the error message: `[DATA_UNAVAILABLE: Required post-feedback outcome variables missing from source. The dataset 'Feedback and Self-Compassion' is required. If unavailable, the pipeline cannot proceed.]`. This error message is a system control flow signal, not a computed result.
4. **Given** the dataset contains the required variables but the hypothesis is NOT supported (confidence interval includes zero), **When** the script executes, **Then** it outputs a regression table for each outcome including the interaction term, with Holm‑Bonferroni adjusted p‑values reported, and a 95% confidence interval that includes zero, and the report explicitly states "Hypothesis Not Supported".

---

### User Story 2 – Visualize Simple Slopes (Priority: P2)

A researcher wants clear plots showing how the relationship between feedback condition and each outcome changes at low, mean, and high levels of self‑compassion to interpret the interaction magnitude.

**Why this priority**: Visualization is essential for interpreting and communicating the moderation effect to stakeholders and verifying the direction of the buffering effect.

**Independent Test**: Execute the visualization module and verify that three distinct lines (−1 SD, mean, +1 SD SCS) are plotted for each outcome with appropriate legends, axes, confidence bands, and that PNG files named `anxiety_simple_slopes.png`, `rumination_simple_slopes.png`, `self_efficacy_simple_slopes.png` are saved.

**Acceptance Scenarios**:

1. **Given** a successful regression run, **When** the plot function is called for the anxiety outcome, **Then** a Matplotlib/Seaborn figure appears with three slope lines, correctly labeled "Low SCS", "Mean SCS", "High SCS", and the negative‑feedback line is flatter for high SCS than for low SCS (if buffering exists). The figure is saved as `anxiety_simple_slopes.png`.
2. **Given** the analysis is run, **Then** the output directory contains exactly three PNG files named `<outcome>_simple_slopes.png` for anxiety, rumination, and self‑efficacy, and each file is non-empty and renders correctly in a standard image viewer.

---

### User Story 3 – Robustness Checks (Priority: P3)

A researcher wants to confirm that the moderation finding is not driven by a particular SCS subscale, collinearity issues, or specific threshold choices.

**Why this priority**: Robustness increases confidence in the result and guards against over‑interpretation or spurious findings due to model specification.

**Independent Test**: Run (a) the analysis using the SCS‑Self‑Kindness subscale as moderator, (b) a collinearity diagnostic (VIF), and (c) a sensitivity analysis sweeping the interaction significance threshold, and verify consistent conclusions.

**Acceptance Scenarios**:

1. **Given** the original dataset, **When** the alternative‑moderator analysis is performed (using SCS‑Self‑Kindness), **Then** the interaction term is reported with the same statistics as the primary test, and the report notes whether the direction and significance match the primary SCS‑Total result.
2. **Given** the regression models, **When** Variance Inflation Factors (VIF) are computed for predictors, **Then** the report explicitly states the VIF values for `SCS_z` and `C(feedback)[T.2]`, and if any VIF > 5, a warning is logged indicating potential collinearity.
3. **Given** the primary interaction p-value, **When** a sensitivity analysis is run sweeping the significance threshold (e.g., α ∈ {0.01, 0.05, 0.10}), **Then** the report displays how the number of significant findings (count of interaction terms with p < α across the 3 outcomes) changes across these thresholds.

---

### User Story 4 – Generate HTML Report (Priority: P2)

A researcher needs a concise, shareable summary of all analyses, visualizations, robustness checks, and methodological caveats.

**Why this priority**: The report consolidates results for publication and stakeholder review, and directly drives the creation of the HTML output.

**Independent Test**: After a successful run, invoke the reporting module and verify that an `report.html` file is produced, renders without errors in Chrome/Firefox, and contains sections for data cleaning, descriptive statistics, model tables, robustness results, simple‑slope plots (embedded PNGs), and methodological caveats.

**Acceptance Scenarios**:

1. **Given** completed analyses and plots, **When** the reporting function is called, **Then** an `report.html` file is written, opens without errors in Chrome/Firefox, and displays the expected sections including a "Methodological Caveats" section that explicitly states whether findings are causal or associational.

---

### Edge Cases

- **Missing Data**: Rows with missing SCS, baseline, or post‑feedback scores are dropped via listwise deletion; the number of exclusions is logged and the final N is reported. If N < 92 (based on power analysis for f²=0.02, α=0.05, power=0.80), the pipeline reports a "Power Insufficient" warning but continues to generate results with a caveat.
- **Non‑Normal Residuals**: Robust (HC3) standard errors are computed; if the Breusch‑Pagan test yields p < 0.10, a heteroskedasticity flag is added to the report and the robust SEs are used for inference.
- **Dataset Mismatch**: If the downloaded dataset lacks the required post‑feedback outcome columns, the pipeline terminates immediately with a specific error identifying the missing columns.
- **Collinearity**: If VIF > 5 for the interaction term predictors, the report explicitly flags this and refrains from claiming independent effects for the collinear variables.
- **Randomization Ambiguity**: If the dataset metadata does not confirm experimental randomization of the feedback condition, the system defaults to framing all interaction findings as "associational" rather than causal.
- **Homogeneity Violation**: If the homogeneity of regression slopes assumption is violated (p < 0.05) on the full dataset, the system reports a pre‑specified secondary analysis (including the covariate‑by‑factor interaction term) as supplemental information while retaining the original primary model as the main conclusion.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the dataset from the verified OSF URL (https://osf.io/3k9r2/) and verify that it contains the columns: `scs_total`, `scf_self_judgment`, `scf_self_kindness`, `stai_pre`, `stai_post`, `rrs_pre`, `rrs_post`, `gse_pre`, `gse_post`, `feedback_cond`, `age`, `gender`, and personality traits (Big Five) if available. The column `scs_total` shall be standardized to create the variable `SCS_z` used in models. If any required column is missing, the system MUST abort with exit code 1 and the error message: `[DATA_UNAVAILABLE: Required columns missing from dataset. Expected: [list of missing columns]]`. The system MUST verify that the total number of complete participant records (N) after listwise deletion is ≥ 92 for adequate power (f²=0.02, α=0.05, power=0.80). The order of operations is: 1. Load data → 2. Listwise deletion → 3. Power Check → 4. **Homogeneity Check (on full dataset)** → 5. Feedback Filtering → 6. Primary Model. **Crucially, the system MUST retain a copy of the dataset prior to filtering (Step 5) specifically for the homogeneity check (Step 4) and any secondary analysis.** If N < 92, the system MUST NOT abort but MUST calculate and report the detectable effect size (f²) for the observed N using the non-central F-distribution (α=0.05, power=0.80) and report the result, generate a report with a "Power Insufficient" warning explicitly stating: `[POWER_INSUFFICIENT: Sample size (N) is less than the required 92 for adequate power (f²=0.02, α=0.05, power=0.80). Results are reported with caution. The detectable effect size for this N is [calculated_f2]. The primary hypothesis test for f²=0.02 is underpowered.]`, and proceed with the analysis. *(See US-1)*
- **FR-002**: System MUST remove any participant rows with missing SCS, baseline, or feedback‑task data (listwise deletion) and log the number of exclusions and the final sample size (N) in the report. *(See US-1)*
- **FR-003**: System MUST encode feedback condition as a categorical variable with 'Positive Feedback' as the reference level (0 = Positive, 1 = Neutral, 2 = Negative) and center/standardize continuous predictors (SCS, baseline anxiety, baseline rumination, baseline self‑efficacy) using z‑scores. The model formula MUST explicitly use `C(feedback, Treatment(reference='Positive'))` to ensure the interaction term `C(feedback, Treatment(reference='Positive'))[T.2]:SCS_z` corresponds to the contrast between 'Negative Feedback' and the reference 'Positive Feedback'. The 'Neutral' condition is excluded from the *dataset subset* used for the primary interaction test (filtering to include ONLY rows where `feedback_cond` is 'Positive' or 'Negative') to isolate the extreme contrast (Negative vs Positive) as per the pre‑registered hypothesis. *(See US-1)*
- **FR-004**: System MUST prepare the dependent variables as the post‑feedback scores (stai_post, rrs_post, gse_post) for anxiety, rumination, and self‑efficacy. The baseline scores (stai_pre, rrs_pre, gse_pre) will be used as covariates in the ANCOVA model. *(See US-1)*
- **FR-005**: System MUST fit a linear regression (ANCOVA) for each outcome with the dependent variable = post‑feedback score, covariates = baseline outcome, age, gender (treated as a categorical factor with all observed levels), **main effect of SCS_z**, and the interaction term `C(feedback, Treatment(reference='Positive'))[T.2]:SCS_z`, using statsmodels OLS. The reference level for feedback must be 'Positive Feedback'. The system MUST NOT include the baseline:SCS interaction in the primary model unless the homogeneity assumption is violated (see FR-019). *(See US-1)*
- **FR-006**: System MUST output for each model: interaction coefficient, standard error, p‑value, confidence interval, partial η² (calculated using Type III sums of squares), and robust (HC3) standard errors. **Crucially, all statistical outputs (coefficients, p-values, CIs) MUST be computed directly from the empirical dataset loaded in memory. No simulated, hardcoded, or placeholder values are permitted for any analysis result. The system MUST raise an exception if any computed metric differs from the raw data source.** *(See US-1)*
- **FR-007**: System MUST generate simple‑slope plots for low (‑1 SD), mean, and high (+1 SD) self‑compassion levels, saved as PNG files named `<outcome>_simple_slopes.png`. *(See US-2)*
- **FR-008**: System MUST perform a bootstrap of the interaction coefficient using exactly 5,000 resamples (random seed = 42) and report the bias-corrected and accelerated (BCa) confidence interval. The bootstrap method MUST be 'case bootstrap' (resampling rows with replacement) to ensure reproducibility and validity for i.i.d. data. The system MUST NOT use a dynamic convergence check; the fixed resample count ensures stability for interaction effects. **If the BCa interval calculation fails (e.g., raises a 'zero variance' exception, 'non-convergent quantiles' error, or results in an infinite interval width), the system MUST fall back to a percentile bootstrap confidence interval.** *(See US-3)*
- **FR-009**: System MUST automatically compute robust heteroskedasticity‑consistent standard errors (HC3) for all models and **flag** heteroskedasticity in the report when the Breusch‑Pagan test yields p < 0.10. *(See US-1)*
- **FR-010**: System MUST produce a concise HTML report summarizing data cleaning, descriptive statistics, model results, robustness checks, visualizations, and methodological caveats. The report must render in a standard web browser without errors. *(See US-4)*
- **FR-011**: System MUST apply Holm‑Bonferroni correction across the three primary hypothesis tests (anxiety, rumination, self‑efficacy interaction terms) and report adjusted p‑values. *(See US-1)*
- **FR-011b**: System MUST apply Holm‑Bonferroni correction to the **Primary Family** (3 tests) and the **Robustness Family** (3 tests: SCS‑Self‑Kindness for each outcome) **separately**, as they test distinct hypotheses (Total SCS vs. Self‑Kindness subscale). The correction family size MUST be dynamically determined by the number of successfully executed tests in each family. *(See US-3)*
- **FR-012**: System MUST set the random seed to `42` before any stochastic operation (e.g., bootstrap) to guarantee reproducibility. *(See US-3)*
- **FR-013**: System MUST compute Variance Inflation Factors (VIF) for all predictors in the final models and report the values; if any VIF > 5, the report MUST explicitly flag potential collinearity. *(See US-3)*
- **FR-014**: System MUST repeat the primary moderation analysis using the SCS‑Self‑Kindness subscale as the moderator, outputting the same set of statistics as in FR‑006. *(See US-3)*
- **FR-015**: System MUST perform a sensitivity analysis by re-running the primary model with significance thresholds across a range of standard values (α ∈ {low, 0.05, 0.10}) and report the count of interaction terms with p < α across the 3 outcomes for each threshold. *(See US-3)*
- **FR-016**: System MUST compute a SHA‑256 checksum of the raw dataset immediately after download and store this hash in the project state file (`state/projects/...yaml`). *(See US-4)*
- **FR-017**: System MUST verify that the dataset metadata or documentation explicitly states that the feedback condition was experimentally randomized. If not, the system MUST default to framing all findings as "associational" in the report. *(See US-1)*
- **FR-018**: System MUST include gender as a categorical variable with **all observed categories** (including non‑binary) and include personality‑trait (Big Five) scores as covariates in the ANCOVA model if they are present in the dataset. If gender contains missing or unrecognised categories, they are treated as a separate level. If personality traits are absent, the system MUST log a warning and proceed with the reduced model. *(See US-1)*
- **FR-019**: System MUST test the homogeneity of regression slopes assumption by fitting an interaction term between the covariate (baseline score) and the feedback condition factor using the **full dataset** (all 3 levels: Positive, Neutral, Negative) **retained from the pre‑filtering state**. The homogeneity test uses a significance threshold of α = 0.05. If this interaction is significant (p < 0.05), the system MUST report a **pre‑specified secondary analysis** (including the covariate‑by‑factor interaction term) **as supplemental information** while retaining the original pre‑registered model as the primary conclusion. Both sets of results are included in the report for transparency. *(See US-1)*
- **FR-020**: System MUST enforce a strict "Real Data Only" policy for all statistical outputs. Any attempt to use non-computed values (simulated, hardcoded, or placeholder) for analysis results in the final report MUST trigger an exception and halt the pipeline. System error signals (e.g., `[DATA_UNAVAILABLE...]`) are exempt from this rule as they are control flow indicators, not analysis results. *(See US-1)*
- **FR-021**: System MUST ensure that every numeric result presented in the HTML report is derived from actual computations on the empirical dataset; any placeholder or hard‑coded value will cause the pipeline to raise an exception and abort execution. *(See US-1)*

### Key Entities

- **Dataset**: Raw CSV file containing participant IDs, SCS scores, baseline and post‑feedback anxiety, rumination, self‑efficacy, feedback condition, demographics, and personality traits.
- **AnalysisResult**: Structured object holding regression tables, interaction statistics, robustness metrics, VIF values, and file paths to generated plots. All values must be computed from the dataset, not hardcoded.
- **ReportArtifact**: The generated HTML file containing all results and methodological caveats.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The report includes the interaction coefficient for negative feedback × self‑compassion, its p‑value (adjusted), and its confidence interval. **If the homogeneity of slopes assumption is violated, the reported coefficient is from the secondary analysis model (full dataset).** *(See US-1)*
- **SC-002**: The report includes the calculated Partial η² value for the interaction term. *(See US-1)*
- **SC-003**: The report includes the bootstrap confidence interval for the interaction coefficient, the parametric confidence interval, and a note on whether they overlap. If they do not overlap, a methodological caveat is added. *(See US-3)*
- **SC-004**: Simple‑slope plot PNG files are generated for all three outcomes (`anxiety_simple_slopes.png`, `rumination_simple_slopes.png`, `self_efficacy_simple_slopes.png`) and each plot displays **three distinct lines** representing low, mean, and high levels of self‑compassion. *(See US-2)*
- **SC-005**: The HTML report (`report.html`) is renderable in a standard web browser and contains all required sections (Data Cleaning, Descriptive Statistics, Model Results, Robustness Checks, Visualizations, Methodological Caveats) with no rendering errors. *(See US-4)*
- **SC-006**: The report explicitly states whether findings are causal or associational based on the dataset's randomization metadata, and if VIF > 5, a collinearity warning is present. *(See US-1 & US-3)*
- **SC-007**: The system verifies that all statistical results in the final report are derived from the empirical dataset and contains no simulated, hardcoded, or placeholder values for analysis results. *(See US-1)*

## Assumptions

- The OSF dataset at `https://osf.io/k9r2/` is publicly accessible and provided as a CSV file.
- The analysis proceeds regardless of the final sample size (N); if N < 92, appropriate power caveats and detectable effect size calculations are generated.
- If the dataset metadata does not explicitly confirm experimental randomization of the feedback condition, the analysis will frame all interaction findings as **associational** rather than causal, as required by methodological soundness.
- Researchers have a Python 3.10+ environment with `pandas`, `statsmodels`, `seaborn`, and `matplotlib` installed.
- Significance threshold for hypothesis testing is set to α = 0.05 (default community standard), with Holm‑Bonferroni correction applied for multiple comparisons within each family of tests.
- Computational resources are limited to a single‑core CPU and ≤ 2 GB RAM on a GitHub Actions free‑tier runner; the analysis is designed to complete efficiently.
- Gender is recorded as a categorical variable; all observed categories (including non‑binary) are retained and encoded as separate levels in the model.
- Anxiety is measured with the State‑Trait Anxiety Inventory (STAI‑State; Spielberger); rumination with the Ruminative Responses Scale (RRS; Nolen‑Hoeksema & Morrow); self‑efficacy with the General Self‑Efficacy Scale (GSES; Schwarzer & Jerusalem). All instruments have demonstrated reliability and validity in prior literature.
- The Self‑Compassion Scale (SCS; Neff) is used to assess self‑compassion; it has established psychometric properties.
- The dataset contains the specific post‑feedback measures for anxiety, rumination, and self‑efficacy required for the ANCOVA analysis. If the dataset lacks these, the pipeline will halt with a specific error.
- Robust (HC3) standard errors are computed; heteroskedasticity is flagged when the Breusch‑Pagan test yields p < 0.10.
- All random operations use seed = 42 for reproducibility.
- The raw dataset checksum is recorded as a cryptographic hash in the project state file to satisfy data‑hygiene requirements.
- A sensitivity analysis sweeping the significance threshold (α) is computationally trivial and included to demonstrate robustness of the primary finding.
- The VIF threshold for flagging collinearity is set to 5, consistent with common social science standards.
- The dataset is provided as a CSV file.
- The 'Self-Kindness' subscale is used for the robustness check as it is a theoretically distinct component of self-compassion.
- The data is assumed to be independent and identically distributed (i.i.d.), justifying the use of case bootstrap (row-wise resampling) for the interaction term confidence intervals.
- The 'Neutral' feedback condition is treated as an intermediate control group; the primary hypothesis test specifically contrasts 'Negative' vs 'Positive' feedback to isolate the buffering effect, excluding 'Neutral' from the specific interaction term of interest.
- **Crucial Assumption**: The dataset provided contains genuine empirical measurements from human participants. The system does not generate or simulate data; all statistical outputs are strictly derived from the loaded CSV file.
