# Research: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

## 1. Research Question
Does the integration of Explainable AI (XAI) overlays in gene regulation interfaces significantly improve usability (measured by SUS, completion time, and error rates) for users with disabilities compared to traditional interfaces, when controlling for order effects via Latin Square counterbalancing?

## 2. Background & Context
Gene regulation interfaces are complex, requiring users to interpret multi-dimensional data. For users with disabilities (visual, cognitive, motor), the cognitive load of these interfaces can be prohibitive. XAI techniques (heatmaps, feature importance) aim to reduce this load. However, the effectiveness of XAI in accessibility contexts is under-researched, particularly with rigorous statistical validation (ANOVA) rather than anecdotal evidence.

## 3. Dataset Strategy

### 3.1 Primary Data Source
The primary data source is **Human Participant Data** generated via the project's own `streamlit` simulator (FR-007).
- **Source Type**: Primary Data Collection (Simulator).
- **Acquisition Method**: Participants recruited via disability advocacy organizations (Constitution Principle VI) will interact with the simulator.
- **Format**: JSON logs per session, aggregated to CSV.
- **Feasibility**: This approach is fully feasible on the GitHub Actions runner for analysis. The simulator runs on the user's local machine; the runner only processes the resulting data files.
- **Constraint**: No synthetic data will be used for final claims (NFR-002).

### 3.2 Secondary Data (Benchmarking)
*Note: No external "verified" HCI benchmark datasets for "gene regulation accessibility" were found in the provided verified datasets block. Therefore, the study relies on primary data collection as per the spec's FR-007.*

### 3.3 Data Variables
| Variable | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `session_id` | String | Unique identifier | Simulator |
| `participant_id` | String | Anonymized ID | Simulator |
| `interface_type` | Categorical | 'traditional' or 'explainable' | Simulator (Latin Square) |
| `order` | Categorical | 'T->X' or 'X->T' | Simulator |
| `completion_time` | Float | Seconds to complete task | Simulator |
| `error_count` | Integer | Number of incorrect steps | Simulator |
| `sus_score` | Float | System Usability Scale (0-100) | Simulator (Survey) |
| `status` | Categorical | 'complete' or 'incomplete' | Simulator |

## 4. Statistical Methodology

### 4.1 Primary Test: Repeated Measures ANOVA
Per FR-002 and Constitution Principle VII, the primary analysis will use **Repeated Measures ANOVA**.
- **Rationale**: Since each participant interacts with *both* interface types, the data is paired. A standard t-test ignores the within-subject correlation. Repeated Measures ANOVA accounts for individual variability, increasing statistical power.
- **Implementation**: The RM-ANOVA will be implemented manually using `numpy` and `scipy.stats`, calculating sums of squares (SS) between subjects. This implementation will be validated against a known standard reference implementation in R using the `aov` function to ensure correctness of calculations. *Refinement*:  The spec mandates `scipy.stats`. We are implementing RM-ANOVA manually with numpy and scipy for F distribution p-value calculation.
*Decision*: The statistical engine will calculate the RM-ANOVA through custom code based on standard texts (e.g., Keppel, 1985).

### 4.2 Multiple Comparison Correction
- **Method**: Holm-Bonferroni correction.
- **Rationale**: We are testing multiple metrics (Time, Errors, SUS). Without correction, the family-wise error rate (FWER) inflates. Holm-Bonferroni is more powerful than standard Bonferroni while controlling FWER.
- **Implementation**: `statsmodels.stats.multitest.multipletests` (method='holm') or manual implementation if `statsmodels` is excluded. *Decision*: `statsmodels` is a standard scientific Python library and will be included in `requirements.txt`.

### 4.3 Assumptions & Checks
- **Normality**: Shapiro-Wilk test (`scipy.stats.shapiro`) on the difference scores. *Note*: Per spec, this is for audit only and does not change the test choice (ANOVA is mandated). However, if a severe violation of sphericity or normality is detected, we will consider a non-parametric alternative such as Friedman's test.
- **Sphericity**: Mauchly's test (if applicable). If violated, Greenhouse-Geisser correction will be applied.

### 4.4 Power Analysis
- **Method**: G*Power-style calculation using `statsmodels.stats.power` or manual calculation of effect size (Cohen's d or f) and power.
- **Goal**: Verify if N=30 (Constitution Principle VI) provides sufficient power (typically >0.80) for the observed effect size.
- **Output**: `data/processed/power_report.md`.

## 5. Ethical Considerations
- **Recruitment**: Participants must be recruited through disability advocacy organizations (Constitution Principle VI).
- **Informed Consent**: The simulator will include a consent form before data collection.
- **Data Privacy**: No PII will be stored. Participant IDs will be anonymized.

## 6. Decision/Rationale
- **CPU vs GPU**: The analysis is purely statistical (ANOVA, p-values) and operates on small tabular data (<1000 rows). This is **CPU-first**. No GPU is required.
- **Dataset**: Primary data collection via simulator is the only viable path as no open "gene regulation accessibility" dataset exists. This aligns with FR-007.
- **Statistical Method**: Repeated Measures ANOVA is chosen over t-tests because it accounts for the within-subjects design, increasing power. Holm-Bonferroni is chosen to control FWER across the three primary metrics.
