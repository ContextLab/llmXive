# Feature Specification: Automated Detection of Algorithmic Bias in Public Code Repositories

**Feature Branch**: `001-auto-detect-bias`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "Automated Detection of Algorithmic Bias in Public Code Repositories"

## User Scenarios & Testing

### User Story 1 - Static Code Artifact Extraction (Priority: P1)

A researcher or auditor needs to extract and quantify "textual bias signals" (variable names and comments) from a target Python repository to establish a baseline for correlation analysis, without executing any code.

**Why this priority**: This is the foundational data ingestion step. Without extracting the textual features (predictors), no correlation analysis can occur. It is independent because it produces a structured dataset of "Textual Bias Scores" that can be validated against a lexicon without needing the downstream fairness execution engine.

**Independent Test**: Can be fully tested by running the parser on a known repository (e.g., one with intentional biased variable names) and verifying that the output JSON contains the correct normalized variable tokens and comment sentiment scores, independent of any model execution.

**Acceptance Scenarios**:

1. **Given** a Python repository containing `gendered_user_name` and `female_score` variables, **When** the static analyzer parses the AST, **Then** the output must tokenize and flag these terms against the demographic lexicon with a count ≥ 1.
2. **Given** a Python file with comments containing negative sentiment stereotypes (e.g., "lazy users"), **When** the VADER analyzer processes the string literals, **Then** the system must assign a negative sentiment compound score ≤ -0.05 to that comment.
3. **Given** a repository with 500 Python files, **When** the extraction pipeline runs, **Then** the total memory usage must remain ≤ 2 GB RAM and complete within 15 minutes on a 2-core CPU.

---

### User Story 2 - Synthetic Ground Truth Generation (Priority: P2)

A researcher needs to generate domain-neutral synthetic datasets and execute the extracted algorithmic logic to compute objective fairness metrics (Demographic Parity, Equalized Odds) that serve as the ground truth, ensuring no data leakage from the source code text.

**Why this priority**: This step establishes the "Outcome" variable. It is independent because it relies on the logic extraction (from the code) and synthetic data generation (math), not on the textual bias scores calculated in US-1. It validates the execution path of the code.

**Independent Test**: Can be fully tested by running the logic on a synthetic dataset where the sensitive attribute is randomly assigned, verifying that the computed fairness metrics are mathematically consistent with the logic and that the synthetic data generation process does not ingest any variable names or comments.

**Acceptance Scenarios**:

1. **Given** an extracted scoring function from the repository, **When** it is executed on a synthetic dataset with uniformly distributed sensitive attributes, **Then** the system must compute Demographic Parity and Equalized Odds metrics using `Fairlearn` or `AIF360` libraries.
2. **Given** a repository where the logic is purely deterministic and neutral, **When** synthetic data is generated, **Then** the computed fairness disparity metrics must be ≤ 0.01 (within statistical noise).
3. **Given** the synthetic data generation process, **When** it runs, **Then** the generated data must strictly contain no strings or tokens derived from the source code's variable names or comments.

---

### User Story 3 - Correlation & Statistical Validation (Priority: P3)

A researcher needs to correlate the "Textual Bias Scores" from US-1 with the "Fairness Metrics" from US-2 to determine if a statistically significant relationship exists, applying necessary corrections for multiple comparisons.

**Why this priority**: This is the core research question answer. It depends on the outputs of US-1 and US-2. It is testable by verifying the statistical output (p-values, correlation coefficients) against known synthetic datasets with injected bias patterns.

**Independent Test**: Can be fully tested by feeding a pre-calculated pair of (Textual Score, Fairness Metric) datasets into the correlation module and verifying that the Pearson correlation coefficient and p-value match the expected mathematical result, including the application of Bonferroni correction.

**Acceptance Scenarios**:

1. **Given** a dataset of 500 repositories with paired (Textual Bias Score, Fairness Disparity) values, **When** the correlation engine runs, **Then** it must output a Pearson correlation coefficient and a p-value corrected for multiple comparisons (e.g., Bonferroni).
2. **Given** a threshold for significance (p < 0.05), **When** the analysis completes, **Then** the system must flag repositories where the correlation exceeds the threshold with a "High Risk" status.
3. **Given** multiple hypothesis tests (e.g., testing variable names vs. comments separately), **When** the analysis runs, **Then** the system must apply a family-wise error rate correction and report the adjusted p-values.

---

### Edge Cases

- **What happens when** a repository contains no Python files or only binary files? The system must return a "No Analyzable Code" status with a count of 0 files processed, rather than crashing.
- **How does system handle** code that fails to execute due to missing dependencies or syntax errors during the synthetic data phase? The system must log the error, skip that specific repository for US-2, and record a "Execution Failure" flag in the final report without halting the entire pipeline.
- **What happens when** the synthetic data generation produces a dataset that is too small to calculate a fairness metric (e.g., < 10 samples per group)? The system must skip the metric calculation for that repository and record a "Insufficient Data" warning.

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract all variable names, function names, and string literals from Python files using the `ast` module, normalizing camelCase and snake_case into a single token stream. (See US-1)
- **FR-002**: System MUST match extracted tokens against a curated demographic lexicon and calculate a "Textual Bias Score" per file based on the frequency of matched terms. (See US-1)
- **FR-003**: System MUST apply VADER sentiment analysis to all code comments to generate a sentiment score for each file. (See US-1)
- **FR-004**: System MUST generate synthetic input data using domain-neutral distributions (uniform or Gaussian) via `numpy` that mimics the repository's domain structure but contains no sensitive attributes derived from the code text. (See US-2)
- **FR-005**: System MUST execute the extracted algorithmic logic on the synthetic data to compute Demographic Parity and Equalized Odds using `Fairlearn` or `AIF360` libraries. (See US-2)
- **FR-006**: System MUST compute Pearson correlation coefficients between the aggregated Textual Bias Scores and the computed Fairness Metrics across the repository dataset. (See US-3)
- **FR-007**: System MUST apply a multiple-comparison correction (e.g., Bonferroni) to all correlation p-values when more than one hypothesis test is performed. (See US-3)
- **FR-008**: System MUST report a sensitivity analysis for the significance threshold by sweeping the alpha level across {0.01, 0.05, 0.10} and reporting the change in the number of flagged repositories. (See US-3)

### Key Entities

- **Repository**: A public Python project containing source files and metadata.
- **Textual Artifact**: A normalized token (variable name, comment string) extracted from the source code.
- **Bias Score**: A quantitative metric derived from the frequency of demographic terms and sentiment in textual artifacts.
- **Fairness Metric**: A quantitative measure (e.g., Demographic Parity difference) derived from executing code on synthetic data.
- **Correlation Result**: A statistical summary (coefficient, p-value) linking Bias Scores to Fairness Metrics.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The correlation analysis must successfully compute a Pearson correlation coefficient and a Bonferroni-corrected p-value for the relationship between Textual Bias Scores and Fairness Metrics. (See FR-006, FR-007)
- **SC-002**: The sensitivity analysis must demonstrate how the count of "High Risk" repositories varies when the significance threshold is swept across {0.01, 0.05, 0.10}. (See FR-008)
- **SC-003**: The entire pipeline (extraction, execution, correlation) for 500 repositories must complete within 6 hours on a 2-core CPU with ≤ 7 GB RAM usage. (See US-1, US-2, US-3)
- **SC-004**: The synthetic data generation process must be verified to contain zero tokens from the source code's variable names or comments. (See US-2)
- **SC-005**: The system must successfully handle execution failures in at least 95% of repositories by skipping them and logging errors, without terminating the pipeline. (See Edge Cases)

## Assumptions

- **Assumption about data source**: The curated demographic lexicon contains sufficient terms to detect gendered or stereotyping language in variable names and comments relevant to the target domains (finance, hiring, criminal justice).
- **Assumption about scope boundaries**: The analysis is limited to Python repositories; other languages are out of scope for this iteration.
- **Assumption about data/environment**: The GitHub API allows sufficient rate-limited access to download 500-1,000 repositories within the 6-hour window; retries are capped at 3 per repository.
- **Assumption about target users**: Users are researchers or auditors capable of interpreting statistical correlation results and p-values.
- **Assumption about methodological framing**: Since the study is observational (no random assignment of code styles), all findings regarding the relationship between text and bias must be framed as associational, not causal.
- **Assumption about compute constraints**: The `AIF360` and `Fairlearn` libraries can compute fairness metrics on synthetic datasets of size ≤ 10,000 rows within the 2-core CPU limit without requiring GPU acceleration.
- **Assumption about threshold justification**: The significance threshold of α = 0.05 is used as a community standard baseline; the sensitivity analysis (FR-008) will validate the robustness of results against this choice.
