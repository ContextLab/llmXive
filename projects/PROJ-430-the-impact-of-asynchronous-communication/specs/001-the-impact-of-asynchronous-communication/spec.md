# Feature Specification: The Impact of Asynchronous Communication Delays on Team Cohesion

**Feature Branch**: `001-asynchronous-delays-cohesion`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "How does response-time variability in asynchronous communication channels influence perceived team cohesion and trust in distributed software teams?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Metric Derivation (Priority: P1)

As a research analyst, I need to download public repository metadata (issues, pull requests, comments) for a sample of active open-source projects and parse timestamps to calculate inter-arrival times and response latencies for each contributor pair, so that I can establish the raw predictor variables (response-time variance and mean delay) for the study.

**Why this priority**: This is the foundational step. Without accurate derivation of the timing metrics from the raw event logs, no subsequent analysis or correlation with cohesion can occur. It represents the minimum viable dataset preparation.

**Independent Test**: Can be fully tested by executing the data ingestion script against a known subset of repositories (e.g., 5 projects) and verifying that the output CSV contains calculated `response_time_variance` and `mean_delay` columns with non-null, positive numeric values. Additionally, verify accuracy against a ground-truth subset of 10 manually calculated pairs with a tolerance of ≤ 0.01.

**Acceptance Scenarios**:

1. **Given** a list of candidate repository IDs, **When** the ingestion script runs, **Then** it fetches issue, PR, and comment metadata via the GitHub API and outputs a unified event log.
2. **Given** a valid event log with timestamps, **When** the metric derivation module runs, **Then** it calculates `response_time_variance` and `mean_delay` per contributor pair and outputs a summary table with no NaN values for projects with sufficient activity.
3. **Given** a repository with fewer than [deferred: min_events] total events, **When** the script runs, **Then** it flags the project as "insufficient_data" and excludes it from the final analysis dataset without crashing.

---

### User Story 2 - Cohesion Proxy Calculation (Priority: P2)

As a research analyst, I need to apply VADER sentiment analysis to the text content of comments and derive a project-level cohesion proxy score, so that I have a quantifiable measure of team dynamics to correlate with the timing metrics.

**Why this priority**: This provides the dependent variable. While timing data (P1) is necessary, the study cannot proceed without the psychological proxy (cohesion/trust) to test the hypothesis.

**Independent Test**: Can be fully tested by processing a small, manually annotated set of comments (e.g., 20 positive, 20 negative) and verifying that the calculated project-level sentiment score correlates with the manual annotation trend (positive comments yield higher scores).

**Acceptance Scenarios**:

1. **Given** a dataset of comment texts, **When** the VADER analysis module runs, **Then** it outputs a sentiment score (compound) for each comment and aggregates them to a project-level `cohesion_proxy_score`.
2. **Given** a project with mixed sentiment comments, **When** the aggregation runs, **Then** the resulting `cohesion_proxy_score` falls within the theoretical range of [-1, 1] and reflects the weighted average of individual comment sentiments.
3. **Given** a project with no text content (e.g., only binary commits), **When** the module runs, **Then** it assigns a neutral score (0) or flags the project as "no_text_data" for exclusion.

---

### User Story 3 - Statistical Correlation and Visualization (Priority: P3)

As a research analyst, I need to perform Spearman rank correlation and linear regression (controlling for team size and project age) between delay variance and cohesion scores, and generate scatter plots with 95% confidence intervals, so that I can visualize and quantify the relationship.

**Why this priority**: This delivers the core research output. It synthesizes the data from P1 and P2 to answer the research question, providing the final evidence for the study.

**Independent Test**: Can be fully tested by running the analysis on a pre-generated static dataset (CSV) and verifying that the output includes a correlation coefficient, p-value, regression coefficients, and a PNG scatter plot.

**Acceptance Scenarios**:

1. **Given** a dataset with `response_time_variance`, `mean_delay`, and `cohesion_proxy_score`, **When** the correlation module runs, **Then** it outputs a Spearman correlation coefficient and p-value indicating the strength and significance of the relationship.
2. **Given** the same dataset, **When** the regression module runs, **Then** it produces a model controlling for `team_size` and `project_age`, outputting coefficients that isolate the effect of delay variance.
3. **Given** the statistical results, **When** the visualization module runs, **Then** it generates a scatter plot with `response_time_variance` on the X-axis, `cohesion_proxy_score` on the Y-axis, and includes a regression line with a 95% confidence interval ribbon.

---

### Edge Cases

- What happens when a repository has a massive number of comments (e.g., >100k) that exceeds the 7 GB RAM limit of the CI runner?
- How does the system handle projects where the GitHub API rate limit is hit during the initial data fetch?
- What happens if VADER sentiment analysis encounters text in a non-English language (e.g., code comments with variable names in other languages)?
- How does the system handle projects where the team size is effectively 1 (no inter-actor communication to measure)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch an initial pool of candidates sorted by star count descending, and iterate until a target sample of [deferred: sample_size] valid projects is identified, ensuring each project has at least [deferred: min_events] events. (See US-1)
- **FR-002**: System MUST calculate `response_time_variance` and `mean_delay` for each Contributor Pair (defined as any two distinct authors who have exchanged at least one message) by parsing timestamps, explicitly excluding internal system-generated events (e.g., automated bot comments identified by names ending in '[bot]' or IDs in the GitHub Apps registry). (See US-1)
- **FR-003**: System MUST apply VADER sentiment analysis to all English-only text-based comments (filtered by language detection with confidence ≥ 0.95) to derive a `cohesion_proxy_score` per project, using the standard compound score aggregation method. (See US-2)
- **FR-004**: System MUST perform a Spearman rank correlation between the project-level aggregated delay variance and `cohesion_proxy_score` to assess the non-linear relationship without assuming normal distribution. (See US-3)
- **FR-005**: System MUST execute a linear regression model controlling for `team_size` and `project_age` to isolate the specific effect of delay variance on cohesion. (See US-3)
- **FR-006**: System MUST generate a scatter plot visualization with a regression line and 95% confidence intervals, saved as a PNG file, to visualize the delay-cohesion relationship. (See US-3)
- **FR-007**: System MUST implement a multiple-comparison correction (e.g., Benjamini-Hochberg) for secondary hypothesis tests defined as stratified correlations by primary language (Python, JS, Go) and by project size tier (<10 contributors, ≥10 contributors). (See US-3)
- **FR-008**: System MUST halt the regression analysis and output a diagnostic warning if the Variance Inflation Factor (VIF) for any control variable exceeds 5, preventing the calculation of unstable coefficients. (See US-3)
- **FR-009**: System MUST perform a multi-modal validation of the cohesion proxy by comparing VADER scores against a manual coding of 50 comments per project for 'cohesion indicators' (e.g., 'thanks', 'great job', 'collaborative tone') to establish construct validity. (See US-2)
- **FR-010**: System MUST aggregate pair-level variances to a project-level metric by taking the median of all pair variances before correlation to ensure unit-of-analysis alignment. (See US-3)
- **FR-011**: System MUST filter comments to English-only using a language detection library (confidence ≥ 0.95) and log the exclusion rate for non-English text to support sensitivity analysis. (See US-2)

### Key Entities

- **Project**: Represents an open-source repository, containing attributes for ID, name, team size, and age.
- **Event**: Represents a discrete interaction (comment, PR, issue) with a timestamp, author ID, and text content.
- **Contributor Pair**: Represents a relationship between two distinct authors who have exchanged at least one message in a project.
- **Metric**: Represents the derived variables: `response_time_variance`, `mean_delay`, and `cohesion_proxy_score`.
- **StatisticalResult**: Represents the output of the analysis, including correlation coefficients, p-values, and regression parameters.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient between `response_time_variance` and `cohesion_proxy_score` is measured against the null hypothesis of no association (r=0) to determine statistical significance. (See US-3)
- **SC-002**: The regression coefficient for `response_time_variance` is measured against the controlled variables (`team_size`, `project_age`) to isolate the independent effect of delay. (See US-3)
- **SC-003**: The false discovery rate for secondary hypothesis tests is measured against the chosen correction threshold (e.g., q < 0.05) to ensure multiplicity control. (See US-3)
- **SC-004**: The computational feasibility of the analysis is measured against the CI runner constraints (2 CPU cores, 7 GB RAM, 6 hours) to ensure the pipeline completes without resource exhaustion, defined as peak RAM usage < 6.0 GB and total runtime < 5.5 hours. (See US-1, US-2, US-3)
- **SC-005**: The validity of the cohesion proxy is measured against manual coding of 'cohesion indicators' for a sample of comments per project, requiring a Spearman correlation ρ ≥ 0.5 between the proxy and the manual scores. (See US-2)

## Assumptions

- **Assumption about data source**: The GitHub API provides sufficient historical data for the selected [deferred: sample_size] projects to calculate meaningful response-time variances (minimum [deferred: min_events] events per project).
- **Assumption about measurement validity**: The VADER sentiment compound score serves as a valid proxy for "team cohesion and trust" in the context of open-source software development, provided it is validated against manual coding as per FR-009.
- **Assumption about inference framing**: The study treats the findings as associational only; no causal claims regarding delay causing trust erosion are made due to the observational nature of the data.
- **Assumption about compute constraints**: The dataset of [deferred: sample_size] projects with ~[deferred: min_events] events each will fit within the 7 GB RAM limit of the GitHub Actions free-tier runner without requiring sampling or chunking.
- **Assumption about threshold justification**: The threshold for "active" projects ([deferred: min_events]) is a community-standard default for small-scale observational studies; a sensitivity analysis will sweep this threshold over {50, 100, 200} events to verify stability.
- **Assumption about collinearity**: Team size and project age are assumed to be distinct from response-time variance; if high collinearity is detected (VIF > 5), the system halts and logs a warning as per FR-008.
- **Assumption about language**: The sentiment analysis is assumed to be robust enough for English-dominant code comments; non-English text will be excluded based on language detection confidence ≥ 0.95 as per FR-011.