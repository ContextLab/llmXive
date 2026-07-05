# Feature Specification: Evaluating the Impact of Code Generation Models on Code Testability

## User Stories

### US1: Data Acquisition and Paired Analysis Pipeline
As a researcher, I want to download HumanEval, generate code using LLMs, and compute metrics (Complexity, Halstead, Coverage) so that I can create a paired JSON dataset for analysis.

### US2: Statistical Comparison and Hypothesis Testing
As a researcher, I want to perform Wilcoxon, McNemar, Fisher, and Permutation tests with Power Analysis so that I can validate the statistical significance of differences between models.

### US3: Visualization, Reporting, and Sensitivity Analysis
As a researcher, I want to generate automated Markdown reports with figures and perform sensitivity analysis using different CodeLlama models so that I can communicate findings effectively.

## Functional Requirements
- FR-001: Download HumanEval dataset and verify SHA256 checksums
- FR-002: Generate code using Salesforce/codegen-mono with retry logic
- FR-003: Calculate cyclomatic complexity and Halstead volume
- FR-004: Perform statistical hypothesis testing
- FR-005: Execute test suites and record pass rates
- FR-006: Generate Markdown reports with figures
- FR-007: Setup logging with timestamp and task ID tracking
- FR-008: Implement power analysis (A Priori and Post-Hoc)
- FR-009: Implement sensitivity analysis with CodeLlama models
- FR-010: Validate citations in generated reports
- FR-011: Track artifact integrity with SHA256 hashes

## Data Model
- Metrics JSON: Contains cyclomatic_complexity, halstead_volume, branch_coverage_pct, pass_rate
- Artifact Hashes: YAML file tracking checksums of all generated artifacts
