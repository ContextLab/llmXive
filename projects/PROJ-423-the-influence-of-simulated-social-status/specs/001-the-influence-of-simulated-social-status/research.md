# Research: Simulated Social Status & Risk-Taking

## Research Question
**Primary Question**: Does the experimental design (Status × Behavior) have sufficient statistical power to detect a hypothesized interaction effect on risk-taking?
**Context**: While the ultimate scientific question is "Does observing higher-status agents engaging in risky behavior increase an individual's subsequent risk-taking?", this project uses simulation to **validate the methodology and determine sample size requirements** for a future empirical study. The simulation results confirm the *pipeline's capability* to detect the effect, not the *existence* of the effect in the real world.

## Theoretical Background
Social status cues significantly influence risk perception and decision-making. High-status individuals are often perceived as more competent, potentially leading to "status-contagion" where their risky behavior is interpreted as calculated and safe. Conversely, low-status individuals engaging in risk may be viewed as desperate or reckless, leading observers to adopt conservative strategies. This study aims to quantify the interaction effect between `status_level` (High/Low) and `observed_behavior` (Risky/Conservative) on `risk_taking_score`.

**Limitations**: The findings from this simulation are strictly methodological. They demonstrate that *if* the hypothesized effect size exists in the population, the proposed experimental design and statistical pipeline are capable of detecting it. They do not provide empirical evidence for the existence of the effect itself.

## Dataset Strategy

### Primary Strategy: Simulation (FR-001)
Given the unavailability of a single public dataset with a fully crossed factorial design (Status × Behavior), this project will **simulate a synthetic dataset**.
- **Methodology**: Data will be generated using `numpy` and `pandas` based on *hypothesized* effect sizes derived from meta-analyses of social status and risk-taking literature.
- **Variables**:
  - `participant_id`: Unique identifier.
  - `status_level`: Categorical (High, Low). Randomly assigned.
  - `observed_behavior`: Categorical (Risky, Conservative). Randomly assigned.
  - `risk_taking_score`: Continuous or Binary, depending on the simulated instrument (e.g., BART pumps or binary choice).
- **Validity**: The simulation parameters (means, standard deviations, interaction effect sizes) will be set to reflect plausible effect sizes found in psychological literature (e.g., Cohen's d ~ 0.5 for main effects, smaller for interactions). **These parameters are treated as hypothetical for the purpose of power analysis and pipeline testing.**
- **Feasibility**: Simulation requires negligible compute resources and fits entirely within the GitHub Actions memory limits. It avoids the "fatal feasibility flaw" of attempting to scrape gated datasets.

### Alternative Strategy: Meta-Analysis (FR-001b)
If simulation is deemed insufficient for a specific sub-question, the project will aggregate data from separate randomized trials. However, this requires identifying multiple open-access studies with compatible variables. Given the specificity of the interaction, **Simulation is the primary and preferred strategy**.

### Verified Datasets
No open, directly-downloadable dataset exists that contains the specific fully crossed design required (Status × Behavior × Risk Outcome).
- **Note**: The "Verified datasets" block provided in the system prompt lists datasets (VIF, NOT) that are unrelated to social psychology or risk-taking. These are **not** used for this project.
- **Decision**: Proceed with **Simulation** as the only scientifically valid and computationally feasible approach for this methodology validation study.

## Statistical Methodology

### Model Specification
- **Model Type**: 
  - **Between-Subjects**: Ordinary Least Squares (OLS) / Fixed-Effects ANOVA. Formula: `risk_taking ~ status_level * observed_behavior`.
  - **Within-Subjects**: Linear Mixed Model (LMM). Formula: `risk_taking ~ status_level * observed_behavior + (1|participant_id)`.
- **Automatic Detection**: The code will inspect the data structure (unique `participant_id` count vs. total rows) to select the appropriate model.
- **Family**:
  - `gaussian` (Linear) if `risk_taking_score` is continuous.
  - `binomial` (Logistic) if `risk_taking_score` is binary.
- **Rationale**: Using LMM for purely between-subjects data (one observation per participant) leads to singular fit errors and meaningless variance estimates. OLS is the statistically correct choice for the default between-subjects simulation.

### Power & Sample Size (Addressing Methodology Concern)
- **Procedure**: Before main data generation, `power_analysis.py` will perform a power analysis using `statsmodels.stats.power`.
- **Target**: [deferred] power (0.80) to detect the hypothesized interaction effect size (e.g., Cohen's f = 0.25) at alpha = 0.05.
- **Output**: The calculated sample size (N) will be written to `code/config.py` and used as the seed for the main simulation. This ensures the study is neither underpowered nor overpowered.

### Handling Multicollinearity (FR-004)
- **VIF Calculation**: Variance Inflation Factors will be calculated for all fixed effects.
- **Threshold**: VIF > 5.0 will trigger a warning.
- **Design Control**: Since the simulation uses random assignment, predictors are expected to be orthogonal, minimizing VIF naturally.

### Sensitivity Analysis (FR-005)
- **Procedure**: The outlier exclusion threshold will be swept across {2.5, 3.0, 3.5} standard deviations from the cell mean.
- **Output**: A table reporting the interaction coefficient and p-value for each threshold.
- **Robustness**: If the interaction remains significant (p < 0.05) across all thresholds, the *pipeline* is considered robust to outlier definitions.

### Post-Hoc Analysis (FR-006)
- **Correction**: Bonferroni correction will be applied to all pairwise comparisons of the four condition combinations.
- **Reporting**: Adjusted p-values will be reported regardless of the primary interaction significance.

## Compute Feasibility & Escape Hatch
- **CPU-First**: All steps (simulation, cleaning, regression, plotting) are computationally lightweight and will run on the GitHub Actions CPU runner.
- **GPU Escape Hatch**: Not required. No deep learning or transformer models are used.
- **Memory**: The simulated dataset will be kept in memory (RAM < 1GB). No streaming is required for the simulated data.

## Risk Management
- **Risk**: Simulation parameters may not reflect reality.
  - **Mitigation**: Parameters will be explicitly documented as *hypothesized* values for power analysis. Sensitivity analysis will test the robustness of the findings to parameter variations.
- **Risk**: Model convergence issues.
  - **Mitigation**: Use of `statsmodels` with robust standard errors. Fallback to fixed-effects model if random effects cause singular fit (though OLS is preferred for between-subjects).
- **Risk**: Fabrication concerns.
  - **Mitigation**: The `structure_config.json` will be generated dynamically by the `validate_data_structure` function based on the actual data loaded, **not** hardcoded. The file will contain `type` and `n_subjects` only, derived from the dataset.