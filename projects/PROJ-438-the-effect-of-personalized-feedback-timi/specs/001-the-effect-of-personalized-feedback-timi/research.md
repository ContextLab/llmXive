# Research: The Effect of Personalized Feedback Timing on Skill Acquisition

## Research Question
How does the temporal spacing of personalized feedback (immediate vs. delayed) affect learner performance and course completion rates in online learning environments?

## Dataset Strategy

| Dataset | Source (Verified URL) | Relevance | Access Method | Notes |
|:--- |:--- |:--- |:---:--- |
| **OULAD** | ` | Primary source for learner submission timestamps, forum activity, final grades, completion status, and course metadata. | `requests` (download JSON) -> `pandas` (load) | **Critical Check**: The raw OULAD schema typically lacks explicit `response_timestamp` (instructor feedback) fields. **The plan treats `response_timestamp` as conditional.** If missing, the primary predictor will be derived from the closest available proxy: **forum reply time** (time between student post and first instructor reply) or system log events. If no proxy exists, the dataset is flagged as insufficient for the specific hypothesis regarding *personalized* feedback timing. |

**Dataset Fit Verification**:
- **Required Variables**: `student_id`, `course_id`, `submission_timestamp`, `proxy_response_timestamp` (derived from forum replies or system logs), `final_grade`, `is_complete`.
- **Verification Status**: The implementation will inspect the schema of the specific JSON file. If explicit feedback timestamps are missing, the code will automatically switch to the `proxy_response_timestamp` logic. The primary analysis relies on this proxy if direct timestamps are absent.
- **Sample Size**: Target ≥10,000 learners. If the specific JSON run is smaller, the analysis will report the actual N and adjust power expectations.

## Methodology & Statistical Plan

### 1. Data Preprocessing (US-1, FR-001, FR-002)
- **Download**: Fetch OULAD JSON from the verified URL. Cache locally. Compute checksum.
- **Filter**: Retain only courses with both "assessment" and "forum" interaction events.
- **Extract**: Pull `student_id`, `course_id`, `submission_timestamp`, and the **best available response proxy** (instructor reply timestamp or system feedback event).
- **Handling Missing**: Learners with no response proxy are **flagged but retained** with a null indicator (`missing_response_flag=1`) to allow for sensitivity analysis and descriptive statistics. Courses with <50 learners are excluded (logging count).

### 2. Interval Calculation & Binning (US-2, FR-003, FR-004)
- **Calculation**: Compute `interval_hours = (response_proxy_timestamp - submission_timestamp) / 3600`. Precision ≥0.1h.
- **Binning**:
 - **Immediate**: `interval < 2.0` hours.
 - **Delayed**: `2.0 ≤ interval ≤ 48.0` hours.
 - **Variable**: `interval > 48.0` hours.
- **Logic**: Use the median interval per learner for binning if multiple submissions exist.
- **Theoretical Grounds**: These thresholds (2h/48h) are grounded in educational psychology literature (e.g., Hattie & Timperley, 2007) distinguishing between "immediate" consolidation windows and "delayed" reflection periods. This justifies the binning over a purely continuous model for the primary hypothesis.

### 3. Statistical Modeling (US-3, FR-005, FR-006)
- **Method**: **Cluster-Robust Ordinary Least Squares (OLS)**.
 - **Justification of Random Effect Structure**: The data hierarchy has learners nested in courses. The predictor (feedback group) is aggregated at the student level (one value per student). A Linear Mixed-Effects Model (LMM) with `(1 | student_id)` is **statistically invalid** because there is no within-student variation in the predictor (a student cannot be in multiple groups). A course-level random effect `(1 | course_id)` is theoretically appropriate, but given the aggregated nature of the predictor, **Cluster-Robust OLS** (OLS with standard errors clustered by `course_id`) is the robust, equivalent, and simpler solution to handle non-independence.
 - **Fixed Effects**: `feedback_group` (Immediate, Delayed, Variable), `engagement_level` (covariate), `course_difficulty` (covariate if available).
 - **Outcome**: `final_grade` (continuous).
 - **Inference**:
 - **Primary**: Fixed effect estimates, p-values, Cohen's d.
 - **Correction**: Tukey HSD for pairwise comparisons (Immediate vs Delayed, Immediate vs Variable, Delayed vs Variable) to control family-wise error rate (SC-002).
 - **Framing**: Results framed as **associational** (observational study), not causal.

### 4. Confounding Control (Endogeneity)
- **Issue**: The definition of the feedback group (median interval) may be confounded with general engagement (highly engaged students might receive faster feedback or interact more frequently).
- **Control**: The model will include `submission_count` and `forum_activity_count` as covariates to partial out the effect of general engagement, separating it from the timing effect.
- **Limitation**: The plan acknowledges that residual confounding may remain if engagement and timing are intrinsically linked in the platform's design.

### 5. Sensitivity Analysis (FR-007, SC-003)
*Updated to address scientific soundness: Replaces trivial numerical shifts with meaningful window definition sweeps.*
- **Procedure**:
 1. **Window Definition Sweep**: Vary the "Immediate" and "Delayed" cutoffs to test robustness of the categorization logic.
 - **Scenario A**: 1h / 24h (Stricter immediate definition).
 - **Scenario B**: 4h / 72h (More lenient immediate definition).
 - **Scenario C**: 3h / 36h (Alternative standard).
 2. **Continuous Check**: Fit a secondary model using `interval_hours` as a continuous predictor with **natural splines** (df=3) to check for non-linear relationships and avoid arbitrary binning entirely.
 3. **Null Proxy Check**: Run the model excluding learners with `missing_response_flag=1` to ensure results are not driven by the proxy derivation.
- **Metric**: "Significance stability" (proportion of shifts where the primary hypothesis p-value remains <0.05) and "significance flip rate".

### 6. Validity Check (FR-008)
- **Action**: Include a literature citation or sensitivity check in the report validating "final grade" as a proxy for "skill acquisition".
- **Fallback**: If no external validation data exists to correlate OULAD grades with external skill assessments, the report will explicitly state this as a **threat to construct validity** rather than assuming validity.

## Compute Feasibility
- **Environment**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM, ≤6h).
- **Strategy**:
 - **Model**: Cluster-Robust OLS is computationally lightweight and CPU-tractable for N=10k.
 - **Sampling**: If runtime exceeds 6h or RAM > 7GB, sample to N=5,000 learners (power-adequate subset) as per Assumption.
 - **No GPU**: All operations are CPU-based.
 - **Libraries**: `pandas`, `numpy`, `statsmodels`, `scipy`.

## Assumptions & Limitations
- **Observational Nature**: No random assignment; claims are associational.
- **Proxy Validity**: Final grade is a valid proxy for skill acquisition (requires FR-008 citation; if not possible, explicitly stated as a limitation).
- **Timestamp Availability**: Explicit `response_timestamp` is likely missing; the analysis relies on the **forum reply proxy** if direct timestamps are absent. This is a primary constraint, not an edge case.
- **Boundary Justification**: 2h/48h boundaries are based on community standards (requires literature citation in report).
- **Endogeneity**: Residual confounding between engagement and timing may persist despite covariate control.