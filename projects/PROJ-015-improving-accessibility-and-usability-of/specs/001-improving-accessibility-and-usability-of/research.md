# Research: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

## 1. Problem Statement
Complex computer systems, particularly those involving gene regulation, present significant usability barriers for people with disabilities. While Explainable AI (XAI) overlays (heatmaps, feature importance) are hypothesized to improve understanding, their impact on usability metrics (time, errors, SUS, explanation engagement) for this specific demographic is not well-quantified. This study aims to provide empirical evidence on whether XAI interfaces significantly improve usability compared to traditional interfaces for users with disabilities.

## 2. Methodology Overview
This is a **within-subjects experimental design**.
- **Participants**: N ≥ 30 individuals with disabilities, recruited via disability advocacy organizations (Constitution Principle VI).
- **Pilot Study**: N=5 participants will be recruited first to validate task difficulty and timing mechanisms, mitigating ceiling/floor effects.
- **Conditions**:
  1.  **Traditional Interface**: Standard gene regulation UI without overlays.
  2.  **Explainable Interface**: Same UI with XAI overlays (heatmaps, feature importance).
- **Counterbalancing**: Latin Square design to mitigate order effects (FR-004).
- **Metrics**:
  - **Completion Time**: Time to complete a defined gene regulation task.
  - **Error Count**: Number of incorrect actions or failed submissions.
  - **SUS (System Usability Scale)**: Standardized questionnaire (10 items, 5-point Likert).
  - **Explanation Engagement Time**: Time spent interacting with XAI overlays (FR-001).

## 3. Statistical Analysis Strategy
Per FR-002 and Constitution Principle VII, the analysis engine must:
1.  **Data Cleaning**: Exclude sessions with `status='incomplete'`. **Crucially, sessions with ANY missing SUS items are excluded entirely (no mean imputation)** to preserve the integrity of the SUS scoring formula (Brooke, 1996).
2.  **Normality Check**: Perform Shapiro-Wilk test on residuals.
    - **If Normal**: Perform **Repeated Measures ANOVA** for each metric (Time, Errors, SUS, Engagement) to test the main effect of `Interface Type`.
    - **If Non-Normal**: Perform **Friedman Test** (non-parametric alternative) for each metric.
3.  **Effect Size**: Calculate **Cohen's d** (for T-Test equivalent) or **Kendall's W** (for Friedman) to quantify the magnitude of the effect.
4.  **Correction**: Apply **Holm-Bonferroni** correction to the resulting p-values to control the family-wise error rate (FWER).
5.  **Power Analysis**: Compute observed power for the effect sizes to verify if N=30 was sufficient (FR-006).
6.  **Audit**: Log Shapiro-Wilk results and test choice rationale.

## 4. Dataset Strategy

### 4.1. Data Generation (Simulator)
Since this is a usability study requiring human interaction, no pre-existing public dataset exists that perfectly matches the "gene regulation + disability + XAI" scenario.
- **Strategy**: A **Streamlit-based simulator** (`code/app.py`) will be deployed to recruit real human participants.
- **Data Source**: Real-time interaction logs from human participants.
- **Synthetic Data**: Strictly forbidden for final claims (NFR-002). Synthetic data may only be used for *unit testing* the pipeline logic (e.g., `tests/test_analysis.py`) to ensure the code runs, but these results must be clearly labeled as "Test Data" and excluded from the final `data/processed` and `paper.md`.

### 4.2. Verified Datasets
*Note: As this is a primary data collection study, no external "Verified datasets" from the user message block are applicable for the main analysis. The study generates its own dataset.*

However, for the purpose of **unit testing** the statistical engine (ensuring the ANOVA, Friedman, and Holm-Bonferroni logic works correctly before real data arrives), we will use a small, deterministic synthetic dataset defined in `tests/fixtures/`. This is distinct from the "real data" required for claims.

**Dataset Verification Status**:
- **Primary Data**: Generated via `code/app.py` (Streamlit) with real human participants.
- **Test Data**: Synthetic, fixed-seed, used *only* for CI validation of the analysis pipeline.

## 5. Compute Feasibility

### 5.1. CPU-First Approach
The analysis pipeline (ANOVA/Friedman, Holm-Bonferroni, Power Analysis) is computationally lightweight.
- **Method**: `scipy.stats.f_oneway` (ANOVA), `scipy.stats.friedmanchisquare` (Friedman), `statsmodels.stats.power` (Power).
- **Resource Usage**: Negligible CPU/RAM for N=30.
- **Execution**: Will run successfully on GitHub Actions free-tier (2 CPU, 7GB RAM) in < 1 minute.
- **Decision**: **CPU-only**. No GPU escape hatch is required for statistical analysis or data processing.

### 5.2. Simulator Constraints
The Streamlit simulator (`code/app.py`) is a web application.
- **Hosting**: Deployed via Streamlit Cloud or GitHub Pages (static) + backend logic.
- **CI Integration**: The "Simulator" is a tool for data collection, not a CI job. The CI job runs the *analysis* on the collected data.

## 6. Risk Assessment

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Insufficient Sample Size (N < 30)** | Low power to detect effects. | Power analysis (FR-006) will be run. If power < 0.8, the report will explicitly state the limitation and not claim significance. Recruitment via advocacy orgs (Constitution VI) prioritized. |
| **Incomplete Sessions** | Data loss. | Strict validation (FR-005). Sessions with ANY missing SUS items are excluded. |
| **Order Effects** | Bias in results. | Latin Square counterbalancing (FR-004) ensures [deferred] start with Traditional, [deferred] with Explainable. |
| **Non-Normal Data** | ANOVA assumptions violated. | **Fallback to Friedman Test** if Shapiro-Wilk indicates severe non-normality. Normality checked (Shapiro-Wilk) for audit. |
| **Task Difficulty (Ceiling/Floor)** | ANOVA unable to detect effects. | **Pilot Study (N=5)** conducted before full recruitment to validate task difficulty. |

## 7. Decision Rationale

- **Why Repeated Measures ANOVA / Paired T-Test?** The study design involves the same participants testing both interfaces. Repeated Measures ANOVA is the standard for within-subject designs. For exactly two conditions, it is mathematically equivalent to the Paired T-Test (F = t^2). We use ANOVA as the primary test (per mandate) but report T-statistics and Cohen's d (standard in HCI) for direct interpretation of effect size.
- **Why Friedman Fallback?** If data is severely non-normal (common with small N and skewed time/error data), ANOVA Type I error rates become invalid. The Friedman test is the robust non-parametric alternative.
- **Why Holm-Bonferroni?** With four primary metrics (Time, Errors, SUS, Engagement), performing four tests increases the risk of Type I error. Holm-Bonferroni is less conservative than standard Bonferroni while maintaining strict FWER control.
- **Why No Mean Imputation for SUS?** SUS scoring relies on the specific pattern of responses (odd/even item weighting). Imputing a mean value distorts the variance and the specific item weighting required for the standard SUS formula, potentially biasing the final score. Exclusion is the statistically sound approach.
- **Why No External Dataset?** The specific combination of "gene regulation interface," "XAI overlays," and "participants with disabilities" is a novel experimental condition. No public dataset exists. Therefore, the research pipeline must be built around *collecting* this data via a simulator, not analyzing existing data.