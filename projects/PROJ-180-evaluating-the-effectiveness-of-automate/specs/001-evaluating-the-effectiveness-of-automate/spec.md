# Feature Specification: Evaluating Automated Code Review Tools Effectiveness

**Feature Branch**: `001-evaluating-code-review-tools`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Evaluating the Effectiveness of Automated Code Review Tools on Open‑Source Projects"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Collection and Tool Execution Pipeline (Priority: P1)

A researcher can retrieve a set of open-source repositories from GitHub., clone them, and execute static analysis tools (SonarQube Scanner, DeepSource CLI, CodeClimate Engine) to generate structured issue reports for each repository.

**Why this priority**: This is the foundational data acquisition step without which no comparison or metrics can be computed. All downstream analysis depends on this pipeline completing successfully.

**Independent Test**: Can be fully tested by running the pipeline on multiple sample repositories and verifying that JSON reports are generated for all tools without runtime errors.

**Acceptance Scenarios**:

1. **Given** a list of 30–40 GitHub repositories with valid licenses, **When** the data acquisition script runs against each repository, **Then** each repository is cloned at its latest `main` or `master` commit and all three analysis tools produce JSON output files
2. **Given** a repository with mixed Java/Python/JavaScript/Go code, **When** the static analysis tools execute, **Then** issues are captured with type, severity, file path, and line number for each detected defect

---

### User Story 2 - Human Review Baseline and Issue Alignment (Priority: P2)

A researcher can extract defect annotations from merged pull-request review comments, parse them using keyword heuristics, and align them with tool-reported issues by file and line number to establish a human-review baseline.

**Why this priority**: This establishes the ground truth against which automated tool performance is measured. Without human review annotations, precision and recall cannot be computed.

**Independent Test**: Can be fully tested by processing a single repository's PR comments, extracting defect tags, and verifying that at least 10% of comments are manually validated for annotation accuracy.

**Acceptance Scenarios**:

1. **Given** merged pull-request review comments for a repository, **When** the comment parsing script runs, **Then** defect annotations (bug, security, style) are extracted and matched to file/line locations
2. **Given** tool-reported issues and human-review annotations, **When** the alignment process completes, **Then** each tool issue is marked as matched or unmatched against the human baseline with ≥90% file/line matching accuracy

---

### User Story 3 - Metrics Computation and Statistical Analysis (Priority: P3)

A researcher can compute precision, recall, and F1 scores for each tool across defect categories, perform paired Wilcoxon signed-rank tests comparing tool performance, and fit fixed-effects regression models to identify project characteristic influences.

**Why this priority**: This delivers the final research output—quantitative evidence of tool effectiveness and modulating factors. It enables the research question to be answered.

**Independent Test**: Can be fully tested by running the analysis on a sample dataset of repositories and verifying that precision/recall metrics and regression tables are generated as CSV/PNG artifacts.

**Acceptance Scenarios**:

1. **Given** aligned tool issues and human annotations for 30+ repositories, **When** the metrics computation script runs, **Then** per-tool precision, recall, and F1 scores are calculated for security, bug, and style categories
2. **Given** per-project tool performance metrics, **When** statistical tests execute, **Then** permutation-based p-values and fixed-effects regression coefficients are output with p<0.05 significance thresholds applied

---

### Edge Cases

- What happens when a repository has no merged pull requests in the target commit range? → The pipeline must skip that repository and log the exclusion reason
- How does the system handle repositories where tool execution fails (e.g., incompatible dependencies)? → The pipeline must retry up to 2 times, then mark the repository as failed and continue with remaining repos
- What happens when file/line alignment between tool output and PR comments is ambiguous (e.g., multiple issues on same line)? → The alignment algorithm must use a tolerance window of appropriate length and flag ambiguous matches for manual review

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retrieve 30–40 public GitHub repositories stratified by language (Java, Python, JavaScript, Go) and activity level (commits within 1 year) (See US-1)
- **FR-002**: System MUST apply OSS PESTO criteria (open-source license, CI status, issue-tracker availability) to filter repositories before cloning (See US-1)
- **FR-003**: System MUST execute SonarQube Scanner, DeepSource CLI, and CodeClimate Engine on each cloned repository and capture JSON reports (See US-1)
- **FR-004**: System MUST parse merged pull-request review comments to extract defect annotations (bug, security, style) using keyword heuristics, then perform expert manual validation on a [deferred] stratified random sample of extracted annotations to establish ground truth (See US-2)
- **FR-005**: System MUST align tool-reported issues with human-review annotations using AST-based or diff-based semantic alignment (or ±5 line tolerance if AST unavailable) and output a validation status report for the aligned pairs (See US-2)
- **FR-006**: System MUST compute precision, recall, and F1 scores for each tool across all defect categories (See US-3)
- **FR-007**: System MUST perform Wilcoxon signed-rank tests comparing tool performance within the same project (See US-3)
- **FR-008**: System MUST perform permutation-based significance tests and fit fixed-effects regression models with tool, language, and project size as fixed effects (See US-3)
- **FR-009**: System MUST apply family-wise error correction when running multiple hypothesis tests (See US-3)
- **FR-010**: System MUST save all metrics, regression tables, and plots as CSV/PNG artifacts for workflow upload (See US-3)
- **FR-011**: System MUST calculate Cohen's κ inter-rater reliability on the expert-validated subset and report the value (See US-2)
- **FR-012**: System MUST perform a sensitivity analysis on the keyword heuristic threshold by sweeping the cutoff over a range of small values and reporting the variation in false-positive rates (See US-2)

### Key Entities

- **Repository**: GitHub project with attributes: owner, name, primary language, star count, commit activity, license type
- **Tool Issue**: Static analysis finding with attributes: tool name, issue type, severity, file path, line number, description
- **Human Annotation**: PR review comment with attributes: comment text, extracted defect type, file path, line number, validation status
- **Performance Metric**: Aggregated measure with attributes: tool name, defect category, precision, recall, F1 score, project ID

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Per-tool precision and recall metrics are measured against the expert-validated ground truth derived from the [deferred] stratified random sample (See US-3)
- **SC-002**: Statistical significance of tool differences is measured against p<0.05 threshold with Bonferroni correction applied for multiple comparisons (See US-3)
- **SC-003**: Pipeline runtime is measured against a threshold of ≤ 5.5 hours (See US-1)
- **SC-004**: Memory usage is measured against a peak threshold of ≤ 6 GB (See US-1)
- **SC-005**: Alignment accuracy is measured against a stratified random sample of ≥500 expert-validated annotations using line-range intersection, and the resulting accuracy must be ≥90% (See US-2)
- **SC-006**: Mixed-effects model fit is measured against project characteristic influence coefficients (See US-3)

## Assumptions

- GitHub REST API rate limits will not prevent retrieval of PR comments for a representative sample of repositories within a feasible time budget.. (sufficient request capacity available for authenticated users)
- Static analysis tools (SonarQube Scanner, DeepSource CLI, CodeClimate Engine) can be executed via Docker containers or binary releases on CPU-only GitHub Actions runners without GPU dependencies
- Keyword heuristics for defect annotation extraction (e.g., "bug", "security", "style" in PR comments) will capture relevant human-review findings, subject to expert validation of a [deferred] stratified random sample; the heuristic threshold sensitivity is analyzed via FR-012
- Repository codebases will fit within 7 GB RAM during concurrent analysis; if a repository exceeds this, it will be excluded and logged as a resource constraint failure
- The observational nature of this study (no randomization of tool usage) means all findings will be framed as associational rather than causal relationships
- A sample size of repositories provides adequate statistical power. for permutation-based tests and fixed-effects regression; random-effects models are avoided to prevent overfitting
- No post-task psychological variables (e.g., anxiety, rumination) are required since this study focuses on code quality metrics rather than human factors
- Project characteristics (language, size, activity) are definitionally independent predictors; collinearity diagnostics will be included in the regression analysis to confirm this assumption