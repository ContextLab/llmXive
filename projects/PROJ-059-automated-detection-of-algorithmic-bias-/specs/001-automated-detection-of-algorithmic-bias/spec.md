# Feature Specification: Automated Detection of Algorithmic Bias in Public Code Repositories

**Feature Branch**: `001-auto-detect-bias`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "Automated Detection of Algorithmic Bias in Public Code Repositories"

## User Scenarios & Testing

### User Story 1 - Static Code Artifact Extraction (Priority: P1)

A researcher or auditor needs to extract and quantify "Textual Bias Scores" (variable names and comments) from a target Python repository to establish a baseline for correlation analysis, without executing any code.

**Why this priority**: This is the foundational data ingestion step. Without extracting the textual features (predictors), no correlation analysis can occur. It is independent because it produces a structured dataset of "Textual Bias Scores" that can be validated against a lexicon without needing the downstream fairness execution engine.

**Independent Test**: Can be fully tested by running the parser on a known repository (e.g., one with intentional biased variable names) and verifying that the output JSON contains the correct normalized variable tokens and comment sentiment scores, independent of any model execution.

**Acceptance Scenarios**:

1. **Given** a Python repository containing `gendered_user_name` and `female_score` variables, **When** the static analyzer parses the AST, **Then** the output must tokenize and flag these terms against the demographic lexicon with a count ≥ 1.
2. **Given** a Python file with comments containing negative sentiment stereotypes (e.g., "lazy users"), **When** the VADER analyzer processes the string literals, **Then** the system must assign a negative sentiment compound score ≤ -0.5 to that comment, consistent with standard VADER thresholds for strongly negative sentiment.
3. **Given** a repository with 500 Python files, **When** the extraction pipeline runs, **Then** the total memory usage must remain ≤ 2 GB RAM and complete within 15 minutes on a 2-core CPU.

---

### User Story 2 - Simulated Bias Injection & Fairness Proxy (Priority: P2)

A researcher needs to generate domain-neutral synthetic datasets with realistic class imbalances and simulate a bias injection model based on a controlled, independent parameter to compute objective fairness metrics (Demographic Parity, Equalized Odds) that serve as the ground truth proxy.

**Why this priority**: This step establishes the "Outcome" variable via simulation. It is independent because it relies on a controlled 'injected_skew_magnitude' parameter (not the Textual Bias Score) and synthetic data generation (math), not on executing the actual (often broken) repository code. It validates the correlation hypothesis by controlling the bias injection level independently of the predictor.

**Independent Test**: Can be fully tested by running the simulation on a synthetic dataset where the sensitive attribute is randomly assigned and the injected skew is fixed, verifying that the computed fairness disparity matches the injected bias level mathematically.

**Acceptance Scenarios**:

1. **Given** a Textual Bias Score from US-1 and a fixed `injected_skew_magnitude` of 0.1, **When** the simulation engine runs, **Then** it must generate synthetic data with a positive class rate derived from the median class imbalance of the target domain corpus and inject bias proportional to the `injected_skew_magnitude`, independent of the Textual Bias Score.
2. **Given** a repository where the injected skew is 0, **When** synthetic data is generated and the simulation runs, **Then** the computed fairness disparity metrics must be ≤ 0.01 (within statistical noise for N=1000 samples).
3. **Given** the synthetic data generation process, **When** it runs, **Then** the generated data must strictly contain no strings or tokens derived from the source code's variable names or comments.

---

### User Story 3 - Correlation & Statistical Validation (Priority: P3)

A researcher needs to correlate the "Textual Bias Scores" from US-1 with the "Simulated Fairness Metrics" from US-2 to determine if a statistically significant relationship exists, applying necessary corrections for multiple comparisons.

**Why this priority**: This is the core research question answer. It depends on the outputs of US-1 and US-2. It is testable by verifying the statistical output (correlation coefficients, p-values) against known synthetic datasets with injected bias patterns.

**Independent Test**: Can be fully tested by feeding a pre-calculated pair of (Textual Score, Fairness Metric) datasets into the correlation module and verifying that the Spearman correlation coefficient and p-value match the expected mathematical result, including the application of Bonferroni correction.

**Acceptance Scenarios**:

1. **Given** a dataset of 500 repositories with paired (Textual Bias Score, Fairness Disparity) values, **When** the correlation engine runs, **Then** it must output a Spearman correlation coefficient and a Bonferroni-corrected p-value.
2. **Given** a threshold for significance (p < 0.05), **When** the analysis completes, **Then** the system must flag repositories where the correlation exceeds the threshold with a "High Risk" status.
3. **Given** multiple hypothesis tests (e.g., testing variable names vs. comments separately), **When** the analysis runs, **Then** the system must apply a family-wise error rate correction and report the adjusted p-values.

---

### User Story 4 - Manual Validation of VADER Thresholds (Priority: P2)

A researcher needs to validate the VADER sentiment thresholds against a manually labeled subset of comments to ensure the "Textual Bias Score" is a reliable construct before running the full analysis.

**Why this priority**: This step ensures the predictor variable (Textual Bias Score) is grounded in human-verified sentiment, reducing noise that could invalidate the correlation analysis. It is independent because it relies on a small, curated dataset and manual labeling, not the full pipeline.

**Independent Test**: Can be fully tested by running the validation script on the 'Validation Dataset' and verifying that the Cohen's Kappa score between VADER predictions and manual labels is ≥ 0.6.

**Acceptance Scenarios**:

1. **Given** a 'Validation Dataset' of 200 manually labeled comments, **When** the VADER validation script runs, **Then** the system must compute a Cohen's Kappa score ≥ 0.6 between VADER predictions and manual labels.
2. **Given** a VADER threshold that fails the validation (Kappa < 0.6), **When** the system runs, **Then** it must flag the threshold for adjustment and halt the full analysis until the threshold is re-calibrated.

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
- **FR-004**: System MUST generate synthetic input data using domain-neutral distributions with a realistic class imbalance (positive class rate derived from the median class imbalance of the target domain corpus) and a defined 'true label' structure via `numpy`, containing no sensitive attributes derived from the code text. (See US-2)
- **FR-005**: System MUST simulate a bias injection model on the synthetic data to compute Demographic Parity and Equalized Odds, where the bias magnitude is proportional to a controlled `injected_skew_magnitude` parameter, independent of the repository's Textual Bias Score. (See US-2)
- **FR-006**: System MUST compute Spearman's rank correlation coefficients between the aggregated Textual Bias Scores and the computed Fairness Metrics across the repository dataset to account for zero-inflated data distributions. (See US-3)
- **FR-007**: System MUST apply a multiple-comparison correction (Bonferroni) to all correlation p-values when more than one hypothesis test is performed. (See US-3)
- **FR-008**: System MUST report a sensitivity analysis for the significance threshold by sweeping the alpha level across {0.01, 0.05, 0.10} and reporting the change in the number of flagged repositories, applying the Bonferroni correction at each step. (See US-3)
- **FR-009**: System MUST aggregate per-file Textual Bias Scores into a single repository-level score using the arithmetic mean of all file scores (excluding files with 0 tokens). (See US-1)
- **FR-010**: System MUST validate the VADER sentiment threshold against a manually labeled subset of comments to confirm alignment with stereotyping definitions before running the full analysis. (See US-1)
- **FR-011**: System MUST define the simulation logic such that an `injected_skew_magnitude` of 0 results in a fairness disparity ≤ 0.01 (statistical noise) for N=1000 samples. (See US-2)
- **FR-012**: System MUST define the `injected_skew_magnitude` parameter as a controlled input to the simulation, allowing for a range of values to test the robustness of the correlation. (See US-2)
- **FR-013**: System MUST perform a manual validation of VADER thresholds against a 'Validation Dataset' of 200 manually labeled comments, requiring a Cohen's Kappa score ≥ 0.6 to proceed. (See US-4)
- **FR-014**: System MUST generate a 'curated set' of repositories with known syntax errors using a defined test harness and store the ground truth in a 'Error Injection Dataset' entity. (See Edge Cases)
- **FR-015**: System MUST perform an 'Independence Verification' step using a string-hash comparison between the synthetic data generator's seed parameters and the code token stream, requiring zero overlap. (See US-2)
- **FR-016**: System MUST derive the statistical noise threshold (0.01) from a pilot run or a cited statistical model for N=1000 samples. (See US-2)
- **FR-017**: System MUST explicitly reference the state file path `state/projects/PROJ-059-automated-detection-of-algorithmic-bias-.yaml` and the `CITATION_TITLE_OVERLAP_THRESHOLD` mechanism to ensure compliance with Constitution Principles II and V. (See Assumptions)

### Key Entities

- **Repository**: A public Python project containing source files and metadata.
- **Textual Artifact**: A normalized token (variable name, comment string) extracted from the source code.
- **Textual Bias Score**: A quantitative metric derived from the frequency of demographic terms and sentiment in textual artifacts, aggregated per repository.
- **Fairness Metric**: A quantitative measure (e.g., Demographic Parity difference) derived from the simulated bias injection model.
- **Correlation Result**: A statistical summary (Spearman coefficient, p-value) linking Textual Bias Scores to Fairness Metrics.
- **Validation Dataset**: A curated set of 200 manually labeled comments used to validate VADER thresholds.
- **Error Injection Dataset**: A curated set of 100 repositories with known syntax errors, generated by a test harness.
- **Independence Verification Log**: A log file recording the results of the string-hash comparison between synthetic data and code tokens.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The correlation analysis must successfully compute a Spearman correlation coefficient and a Bonferroni-corrected p-value for the relationship between Textual Bias Scores and Fairness Metrics. (See FR-006, FR-007)
- **SC-002**: The sensitivity analysis must demonstrate how the count of "High Risk" repositories varies when the significance threshold is swept across {0.01, 0.05, 0.10} using Bonferroni-corrected p-values. (See FR-008)
- **SC-003**: The entire pipeline (extraction, simulation, correlation) for 500 repositories must complete within 6 hours on a 2-core CPU with ≤ 7 GB RAM usage. (See US-1, US-2, US-3)
- **SC-004**: The synthetic data generation process must be verified to contain zero tokens from the source code's variable names or comments by performing a diff check between the synthetic data generator's input stream and the code token stream. (See US-2)
- **SC-005**: The system must successfully handle execution failures in at least 95% of a curated set of 100 repositories with known syntax errors, without terminating the pipeline. (See Edge Cases)
- **SC-006**: The system must handle execution failures in at least 95% of the 'Error Injection Dataset' (100 repositories) generated by the test harness, as measured by the 'Error Handling Log'. (See FR-014)
- **SC-007**: The 'Independence Verification' step must confirm zero string-hash overlap between the synthetic data generator's seed parameters and the code token stream. (See FR-015)

## Assumptions

- **Assumption about data source**: The curated demographic lexicon contains sufficient terms to detect gendered or stereotyping language in variable names and comments relevant to the target domains (finance, hiring, criminal justice).
- **Assumption about scope boundaries**: The analysis is limited to Python repositories; other languages are out of scope for this iteration.
- **Assumption about data/environment**: The GitHub API allows sufficient rate-limited access to download a substantial number of repositories within the 6-hour window.; retries are capped at a limited number per repository.
- **Assumption about target users**: Users are researchers or auditors capable of interpreting statistical correlation results and p-values.
- **Assumption about methodological framing**: Since the study is observational (no random assignment of code styles), all findings regarding the relationship between text and bias must be framed as associational, not causal. The "Fairness Metric" is a simulated proxy, not a measurement of actual code execution. The simulation uses an independent 'injected_skew_magnitude' parameter to test the hypothesis that text predicts bias, rather than generating the outcome from the text itself.
- **Assumption about compute constraints**: The `Fairlearn` and `AIF360` libraries can compute fairness metrics on synthetic datasets of size ≤ 10,000 rows within the 2-core CPU limit without requiring GPU acceleration.
- **Assumption about threshold justification**: The significance threshold of α = 0.05 is used as a community standard baseline; the sensitivity analysis (FR-008) will validate the robustness of results against this choice.
- **Assumption about data distribution**: The synthetic data generation assumes a realistic class imbalance (minority positive class) to ensure Equalized Odds is mathematically valid and non-trivial.