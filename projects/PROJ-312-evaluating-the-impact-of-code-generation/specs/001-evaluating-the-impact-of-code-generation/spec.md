# Feature Specification: Evaluating the Impact of Code Generation on Code Review Turnaround Time

**Feature Branch**: `001-evaluating-the-impact-of-code-generation`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Code Generation on Code Review Turnaround Time"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing (Priority: P1)

The system MUST fetch pull request metadata from a representative set of top Python and JavaScript repositories, fetch the list of commits for each PR, filter for AI-assisted contributions based on commit messages and labels, and calculate turnaround times in total calendar hours.

**Why this priority**: Without accurate data acquisition and preprocessing, no statistical analysis can be performed. This is the foundational step that enables the entire research study.

**Independent Test**: Can be fully tested by verifying that the script successfully fetches data from the GitHub API, correctly identifies AI vs. human contributions via commit messages and specific labels, and outputs a CSV file with calculated turnaround times.

**Acceptance Scenarios**:

1. **Given** a list of top 10 Python and JavaScript repositories, **When** the data acquisition script runs, **Then** it must successfully fetch PR metadata including created_at, merged_at, labels, and commit messages for all public, non-archived repositories.
2. **Given** fetched PR data, **When** the filtering logic executes, **Then** it must correctly classify PRs as AI-assisted if commit messages contain "copilot" or "ai-generated" or if labels "ai-generated", "copilot-assisted", or "llm-code" are present, and as non-AI-labeled otherwise.
3. **Given** PR creation and merge timestamps, **When** turnaround time calculation executes, **Then** it must compute the duration in total calendar hours (wall-clock time) (merged_at minus created_at) for each PR, without excluding weekends or holidays.

---

### User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

The system MUST perform descriptive statistics, remove outliers using the IQR method per group, and execute a Mann-Whitney U test to compare turnaround times between AI-labeled and non-AI-labeled PR groups.

**Why this priority**: This is the core analytical component that directly addresses the research question. Without proper statistical testing, the study cannot determine if there is a significant difference in review times.

**Independent Test**: Can be fully tested by running the analysis on a sample dataset and verifying that the Mann-Whitney U test produces statistically valid results with appropriate p-values and effect size calculations, and that outliers are removed per group.

**Acceptance Scenarios**:

1. **Given** preprocessed PR data with turnaround times, **When** descriptive statistics are calculated, **Then** it must output mean, median, standard deviation, and quartiles for both AI and non-AI-labeled PR groups.
2. **Given** turnaround time distributions, **When** outlier removal executes, **Then** it must identify and exclude outliers using the IQR method (values beyond Q1 - 1.5×IQR or Q3 + 1.5×IQR) calculated separately for each group (AI and non-AI-labeled) and log the count of outliers removed per group.
3. **Given** cleaned datasets for AI and non-AI-labeled PR groups, **When** the Mann-Whitney U test executes, **Then** it must return the U statistic, p-value, and effect size (r) to assess whether the difference in distributions is statistically significant.

---

### User Story 3 - Visualization and Reporting (Priority: P3)

The system MUST generate a boxplot comparing the distribution of turnaround times between AI and non-AI-labeled PR groups and save the visualization to the artifacts directory.

**Why this priority**: Visualizations are essential for communicating research findings and validating the statistical results. This enables stakeholders to quickly understand the distribution differences.

**Independent Test**: Can be fully tested by verifying that the script generates a clear, labeled boxplot showing both distributions and successfully saves it to the designated artifacts directory.

**Acceptance Scenarios**:

1. **Given** the statistical analysis results, **When** the visualization script executes, **Then** it must generate a boxplot with properly labeled axes (turnaround time in hours vs. PR type) showing both AI and non-AI-labeled distributions.
2. **Given** the generated plot, **When** it is saved to the artifacts directory, **Then** it must be saved as a PNG file with sufficient resolution (≥300 DPI) for publication-quality output.
3. **Given** the complete analysis pipeline, **When** all steps execute successfully, **Then** the final report must include the boxplot, statistical test results, key descriptive statistics, and a validation summary of the classification heuristic in a single output file.

### Edge Cases

- What happens when a repository has fewer than 50 PRs after filtering? The system MUST skip the repository, log a warning with the specific count (e.g., "Skipping repo X: only Y PRs found, threshold 50"), and exclude it from the final analysis.
- How does the system handle repositories where no AI-assisted PRs are found? The system must log this scenario and exclude the repository from the final analysis rather than crashing.
- What happens when GitHub API rate limits are exceeded? The system must implement exponential backoff with a maximum of 3 retries before failing gracefully.
- How does the system handle PRs with missing merged_at timestamps (still open)? The system must exclude these PRs from the turnaround time calculation and log the exclusion count.

## Requirements

### Functional Requirements

- **FR-001**: System MUST fetch pull request metadata from the GitHub REST API for the top 10 Python and JavaScript repositories by star count, including created_at, merged_at, labels, and commit messages, AND fetch the list of commits for each PR to inspect commit messages (See US-1)
- **FR-002**: System MUST classify PRs as AI-assisted if commit messages contain "copilot" or "ai-generated" keywords or if labels "ai-generated", "copilot-assisted", or "llm-code" are present; otherwise, classify as non-AI-labeled (See US-1)
- **FR-003**: System MUST calculate turnaround time in total calendar hours (wall-clock time) as the difference between merged_at and created_at timestamps, without excluding weekends or holidays (See US-1)
- **FR-004**: System MUST perform descriptive statistics (mean, median, standard deviation, quartiles) for both AI and non-AI-labeled PR groups (See US-2)
- **FR-005**: System MUST identify and exclude outliers using the IQR method (values beyond Q1 - 1.5×IQR or Q3 + 1.5×IQR) calculated separately for each group (AI and non-AI-labeled) and log the count of outliers removed per group (See US-2)
- **FR-006**: System MUST execute a Mann-Whitney U test to compare turnaround time distributions between AI and non-AI-labeled PR groups, returning U statistic, p-value, and effect size (See US-2)
- **FR-007**: System MUST generate a boxplot visualization comparing turnaround time distributions for AI and non-AI-labeled PR groups with properly labeled axes (See US-3)
- **FR-008**: System MUST save all generated visualizations to the artifacts directory as PNG files with ≥300 DPI resolution (See US-3)
- **FR-009**: System MUST implement exponential backoff with a maximum of 3 retries when GitHub API rate limits are exceeded (See US-1)
- **FR-010**: System MUST exclude PRs with missing merged_at timestamps from turnaround time calculations and log the exclusion count (See US-1)
- **FR-011**: System MUST perform a manual spot-check of a stratified random sample (n=50) of PRs classified as 'non-AI-labeled' to estimate the false-negative rate of the classification heuristic (See US-1)
- **FR-012**: System MUST include a limitation statement in the final report if the estimated false-negative rate from FR-011 exceeds 10% (See US-3)
- **FR-013**: System MUST report the median star count and median number of contributors for the selected repositories as descriptive statistics to document the 'complexity' control strategy (See US-1)

### Key Entities

- **PullRequest**: Represents a GitHub pull request with attributes including PR ID, repository name, creation timestamp, merge timestamp, labels, and commit message
- **TurnaroundTime**: Represents the calculated duration in total calendar hours (wall-clock time) between PR creation and merge, with associated classification (AI-assisted or non-AI-labeled)
- **StatisticalResult**: Represents the output of the Mann-Whitney U test including U statistic, p-value, effect size, and sample sizes for both groups

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Turnaround time difference between AI-assisted and non-AI-labeled PRs is measured against the null hypothesis of no difference using the Mann-Whitney U test (See US-2)
- **SC-002**: Distribution characteristics of turnaround times are measured against descriptive statistics (mean, median, standard deviation, quartiles) for both PR groups (See US-2)
- **SC-003**: Data quality is measured against the percentage of successfully processed PRs relative to total fetched PRs, with a success threshold of ≥ 95% and logging of exclusion reasons (See US-1)
- **SC-004**: Statistical significance is measured against the p-value threshold of α = 0.05 for the Mann-Whitney U test comparing AI and non-AI-labeled PR groups (See US-2)
- **SC-005**: Visualization quality is measured against the successful generation and saving of boxplot images with proper labels and ≥300 DPI resolution (See US-3)

## Assumptions

- The top 10 Python and JavaScript repositories by star count on GitHub contain sufficient numbers of both AI-assisted and non-AI-labeled PRs for meaningful statistical analysis
- GitHub API rate limits for authenticated users will not prevent complete data acquisition within the standard execution window..
- The GitHub API provides consistent and accurate timestamps for PR creation and merge events across all repositories
- Commit message keywords ("copilot", "ai-generated") and specific PR labels ("ai-generated", "copilot-assisted", "llm-code") provide primary indicators of AI-assisted contributions, subject to validation via manual spot-check (See FR-011)
- The Mann-Whitney U test is appropriate for comparing turnaround time distributions given the expected non-normal distribution of the data
- Total calendar hours (wall-clock time) is the standard definition of 'review turnaround time' in software engineering research for asynchronous processes
- The 14GB disk space and 7GB RAM limits of the GitHub Actions free-tier runner are adequate for processing the expected dataset size (<500MB)
- No GPU acceleration is required as the analysis relies on classical statistical methods (pandas, scipy) that execute efficiently on CPU
- The GitHub API v3 provides all necessary metadata fields (created_at, merged_at, labels, commit messages) for the analysis
- Private and archived repositories are correctly excluded from the analysis based on API response metadata