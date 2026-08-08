# Research: The Effect of Personalized Feedback Timing on Skill Acquisition

## Summary of Findings
This research investigates whether **student response latency** (time from assessment submission to next student action) influences skill acquisition in online learning environments. Using the Open University Learning Analytics Dataset (OULAD), we hypothesize that immediate response (<2h) correlates with higher final grades compared to delayed (2-48h) or variable (>48h) response.

**Critical Limitation**: The OULAD dataset does not contain instructor feedback timestamps. Therefore, "feedback timing" is redefined as "student response latency" (time to next forum post or assessment result). This measures **student engagement speed**, not instructor feedback delivery. The causal claim is limited to engagement, not feedback.

## Dataset Strategy

The study utilizes the **Open University Learning Analytics Dataset (OULAD)**. The verified data sources for this project are:

| Dataset Name | Verified Source URL | Loader Method | Notes |
|:--- |:--- |:--- |:--- |
| OULAD Students | ` | `pandas.read_csv` | Primary source for student demographics and final grades. |
| OULAD Events (Train 0) | ` | `pandas.read_parquet` | Contains event logs (submissions, forum posts) for interval calculation. |
| OULAD Events (Train 1) | ` | `pandas.read_parquet` | Engineered features; cross-referenced for completeness. |

**Data Availability Check**:
- **Required Variables**: `student_id`, `course_id`, `final_grade`, `is_complete`, `submission_timestamp`, `response_timestamp` (proxy).
- **Verification**: The `students_data.csv` contains `final_grade` and `id_student`. The Parquet files contain event logs.
- **Gap Analysis**: The spec assumes `response_timestamp` (instructor feedback) exists. **It does not.** The plan defines "response_timestamp" as the timestamp of the **next student event** (forum post or assessment result) following submission. This is a proxy for "feedback engagement."
- **Feasibility**: Data is <1GB per file; streaming is not strictly required but will be used for safety (`chunksize` or `streaming=True` if supported) to stay under a moderate RAM footprint.

## Statistical Methodology

### Primary Analysis
1. **Model**: Cluster-Robust Ordinary Least Squares (OLS).
 - **Dependent Variable**: `final_grade` (continuous).
 - **Independent Variable**: `feedback_group` (Categorical: Immediate, Delayed, Variable).
 - **Clustering**: `course_id` (to account for course-level heterogeneity).
 - **Covariates**: `num_of_past_attempts`, `gender`, `region`, `total_forum_posts`, `total_clicks` (to control for engagement confounding).
2. **Diagnostic: ICC Check**: Before fitting, calculate the Intra-Class Correlation (ICC) for `feedback_group` by `course_id`. If ICC is high (>0.5), the treatment effect may be absorbed by course clustering. In this case, switch to a course-level fixed effects model.
3. **Post-hoc**: Tukey HSD (Honest Significant Difference) to control family-wise error rate (FWER) across the 3 pairwise comparisons.

### Selection Bias Control (FR-007)
- **Propensity Score Matching (PSM) / Inverse Probability Weighting (IPW)**: To control for the confound that struggling students may receive (or wait for) delayed feedback, the plan will run a secondary analysis using IPW.
- **Metrics**: Compare results with and without weighting to assess robustness.

### Robustness & Sensitivity (FR-007)
- **Sweep**: Bin boundaries will be swept (e.g., Immediate: <1h to <5h; Delayed: 1h-24h to 5h-72h).
- **Metrics**:
 - **Significance Stability**: Proportion of sweeps where the primary effect (Immediate > Delayed) remains significant (p < 0.05).
 - **Significance Flip Rate**: Proportion of sweeps where the direction of the effect changes.
- **Note**: If the underlying construct (student response latency) is validly measured, the sweep tests robustness. If the construct is invalid, the sweep cannot rescue the premise.

### Power & Validity
- **Sample Size**: OULAD typically contains >20,000 students. With ~3 groups, power is sufficient to detect small effect sizes (d > 0.1) assuming [deferred] power.
- **Construct Validity**: `final_grade` is a standard academic metric. FR-008 mandates validation via the Reference-Validator Agent. **Note**: The "student response latency" proxy is explicitly acknowledged as a measure of engagement, not instructor feedback.
- **Collinearity**: Feedback timing (student response latency) is likely correlated with engagement. Controls for engagement (e.g., `total_forum_posts`) will be included to mitigate this.
- **Endogeneity**: Acknowledged that engaged students may act faster. The model includes engagement covariates to control for this bias.

## Proxy Validation Workflow (FR-008)
1. **Agent Execution**: The Reference-Validator Agent will run on the literature citations.
2. **Validation**: It will check title overlap (>=0.7) and validate "final grade" as a proxy for "skill acquisition" in OULAD context.
3. **Pass/Fail**: If the agent fails, the study is flagged. (Current plan: "final grade" is accepted as a standard proxy; the "student response latency" proxy is the primary limitation).

## Decision Rationale

- **CPU-First**: All statistical operations (OLS, Tukey HSD, PSM) are lightweight and run efficiently on minimal CPU resources. No GPU is required.
- **Data Streaming**: While OULAD is small enough to fit in memory, the pipeline will use `chunksize` or `streaming` where applicable to demonstrate robustness against larger datasets and adhere to the RAM constraint strictly.
- **Proxy Handling**: The plan explicitly defines `response_timestamp` as the next student event and documents this as a proxy for "feedback engagement," not "instructor feedback." This prevents fabrication.
