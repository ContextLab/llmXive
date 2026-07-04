# Feature Specification: Assessing the Impact of Code Style Consistency on LLM Code Understanding

**Feature Branch**: `001-assess-code-style-impact`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Assessing the Impact of Code Style Consistency on LLM Code Understanding"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compute Style Consistency Metrics (Priority: P1)

As a researcher, I want to automatically calculate a normalized style-consistency score for every code file in the target datasets (CodeSearchNet and Defects4J) using static analysis tools, so that I can stratify the data into high, medium, and low consistency groups for subsequent analysis.

**Why this priority**: This is the foundational data preparation step. Without quantified style scores, no stratification or correlation analysis can occur. It is the prerequisite for all downstream LLM inference and statistical testing.

**Independent Test**: Can be fully tested by running the style-scoring script on a small, known subset of Python files and verifying the output CSV contains valid scores between 0.0 and 1.0, with correct mapping of pylint and radon metrics.

**Acceptance Scenarios**:

1. **Given** a directory of Python source files, **When** the style-scoring script is executed, **Then** a CSV file is generated with columns for file path, pylint indentation variance, radon line-length variance, and a normalized composite score (0.0–1.0).
2. **Given** a file with mixed indentation (spaces and tabs), **When** the script processes it, **Then** the normalized composite score reflects a lower consistency value (e.g., < 0.5) compared to a file with uniform indentation.
3. **Given** a file with no syntax errors, **When** the script encounters a parse error, **Then** the script logs the error and assigns a default low consistency score or skips the file, ensuring the batch process does not crash.

---

### User Story 2 - Execute LLM Inference on Stratified Data (Priority: P2)

As a researcher, I want to run the StarCoder 1B model on the stratified code samples to generate summaries and bug-localization predictions, so that I can collect performance metrics (BLEU, Precision/Recall) linked to specific style-consistency levels.

**Why this priority**: This is the core experimental action. It generates the dependent variable data required to answer the research question. It depends on the successful completion of User Story 1 (stratification).

**Independent Test**: Can be fully tested by running the inference script on a single stratified group (e.g., "high consistency") with a limit of 5 samples, verifying that output JSONL files contain generated text and line-number predictions without exceeding memory limits or runtime timeouts.

**Acceptance Scenarios**:

1. **Given** a stratified dataset group (e.g., "high consistency") and the StarCoder 1B model loaded in CPU mode, **When** the inference script processes the samples, **Then** the output file contains a generated summary (max 64 tokens) and a predicted bug line number for each input.
2. **Given** a sample that triggers a model timeout or memory error, **When** the script encounters it, **Then** the script logs the failure, skips the sample, and continues processing the remaining batch without halting.
3. **Given** a code snippet with no reference docstring (CodeSearchNet), **When** the script attempts to compute BLEU, **Then** the script records the inference output but marks the BLEU metric as `null` rather than crashing.

---

### User Story 3 - Perform Statistical Analysis and Reporting (Priority: P3)

As a researcher, I want to run ANCOVA and t-tests on the collected performance metrics to determine if style consistency significantly impacts LLM accuracy, so that I can conclude whether style enforcement yields measurable gains.

**Why this priority**: This synthesizes the raw data into the final research answer. It is the final step that delivers the "Expected Results" defined in the idea.

**Independent Test**: Can be fully tested by feeding a synthetic dataset with known statistical properties (e.g., distinct means between groups) into the analysis script and verifying that the output report correctly identifies the significant difference and reports the correct p-value, effect size, and covariate coefficients.

**Acceptance Scenarios**:

1. **Given** the collected BLEU scores stratified by consistency group, **When** the ANCOVA script runs, **Then** the output includes the F-statistic, p-value, Cohen's d effect size, and coefficients for code complexity and file age covariates.
2. **Given** the bug-localization F1 scores for high vs. low consistency groups, **When** the t-test script runs, **Then** the output includes the t-statistic, p-value, and 95% confidence interval for the difference in means.
3. **Given** a result where p > 0.05, **When** the report is generated, **Then** the report explicitly states "No statistically significant difference found" rather than implying a null effect without statistical backing.

---

### Edge Cases

- What happens when the `pylint` or `radon` tools fail to parse a specific Python file due to syntax errors or unsupported language features? (System must skip and log, not crash).
- How does the system handle code snippets that are too long for the StarCoder 1B context window? (System must truncate or skip, ensuring no runtime errors).
- How does the system handle the case where a dataset sample has no ground truth for the specific task (e.g., missing reference docstring for BLEU calculation)? (System must handle `null` metrics gracefully).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate a normalized style-consistency score (0.0 to 1.0) for each Python file by aggregating `pylint` (indentation/naming) and `radon` (line-length) metrics (See US-1).
- **FR-002**: System MUST stratify the dataset into three distinct groups: High (top [deferred]), Medium (middle [deferred]), and Low (bottom [deferred]) based on the calculated style-consistency scores (See US-1).
- **FR-003**: System MUST execute the StarCoder 1B model on CPU to generate natural-language summaries (max 64 tokens) and bug-localization predictions for each stratified sample (See US-2).
- **FR-004**: System MUST compute BLEU-4 scores for summarization tasks and Precision/Recall/F1 scores for bug-localization tasks, handling missing ground truth gracefully (See US-2).
- **FR-005**: System MUST perform a one-way ANCOVA on BLEU scores across the three style groups (controlling for code complexity and file age) and a two-sample t-test on F1 scores between High and Low groups, reporting p-values, effect sizes, and covariate coefficients (See US-3).
- **FR-006**: System MUST apply family-wise error rate correction: Tukey HSD for ANOVA post-hoc comparisons and Bonferroni correction for the family of distinct tests (ANOVA result + independent t-test) to control for Type I errors (See US-3).
- **FR-007**: System MUST enforce a strict runtime limit of 6 hours per job and memory limit of 7 GB RAM; the system MUST terminate processes exceeding 6 hours and log exit code 137 to ensure compatibility with free-tier GitHub Actions runners (See US-2, US-3).
- **FR-008**: System MUST perform an ablation analysis controlling for code complexity (cyclomatic complexity) to verify the style-consistency score predicts performance independently of complexity (See US-3).
- **FR-009**: System MUST verify group separation (effect size > 0.5) between High and Low groups before running main tests, and report statistical power estimates (See US-3).

### Key Entities

- **CodeSample**: Represents a single unit of analysis containing the source code, file path, computed style-consistency score, assigned consistency group, and covariates (complexity, file age).
- **InferenceResult**: Represents the output of an LLM run for a specific sample, containing the generated summary, predicted bug line, and associated metadata (model version, runtime).
- **PerformanceMetric**: Represents the quantitative evaluation result (BLEU, Precision, Recall, F1) linking an `InferenceResult` to a `CodeSample`.
- **StatisticalReport**: Represents the final aggregation of metrics, containing test statistics (F, t, p), effect sizes (Cohen's d), confidence intervals, and covariate coefficients.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation between the normalized style-consistency score and the BLEU-4 score is measured against the hypothesis that higher consistency yields higher scores, with reported statistical power (See US-3).
- **SC-002**: The difference in bug-localization F1 scores between the High and Low consistency groups is measured against the null hypothesis of no difference (See US-3).
- **SC-003**: The system MUST output the calculated Cohen's d effect size for each comparison (See US-3).
- **SC-004**: The validity of the style-consistency metric is measured by the variance explained (R²) when regressing performance metrics against the composite score, controlling for complexity (See US-3).
- **SC-005**: The robustness of the findings is measured by the consistency of results when repeating the analysis with a second model (CodeLlama 7B), defined as a Spearman correlation coefficient ≥ 0.8 between the direction of effects (See US-3).
- **SC-006**: The impact of confounding variables is measured by the magnitude and significance of the coefficients for code complexity and file age in the ANCOVA model (See US-3).

## Assumptions

- The CodeSearchNet Python dataset (Zenodo) and DefectsJ are publicly accessible and downloadable within the disk limit of the CI runner.
- The StarCoder model can be loaded and executed on a CPU-only environment with a limited number of cores and minimal RAM, without requiring CUDA or quantization libraries that depend on GPU drivers.
- The `pylint` and `radon` tools are compatible with the Python versions present in the target datasets and can be installed in the CI environment without excessive build time.
- The "style-consistency" definition derived from `pylint` and `radon` (indentation, naming, line length) is a sufficient proxy for the broader concept of "coding style" relevant to LLM understanding, subject to validation via the ablation study (FR-008).
- The sample size of the CodeSearchNet and Defects4J datasets is sufficient to achieve statistical power (≥ 0.8) for detecting a moderate effect size (Cohen's d ≈ 0.4) after stratification, given the 6-hour compute limit.
- The analysis will be framed as **associational** rather than causal, as the study uses observational data without random assignment of code style.
- Any threshold used for stratification (top [deferred], bottom [deferred]) is a community-standard heuristic for creating distinct groups and will be subject to a sensitivity analysis sweeping the cutoff (e.g., 15th/85th percentiles, 25th/75th percentiles) to ensure stability.