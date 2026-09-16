# Specification: Investigating the Correlation Between Code Churn and Technical Debt

## Overview
This project investigates the statistical correlation between code churn (lines changed) and technical debt scores (static analysis metrics) across a diverse set of open-source repositories.

## Methodological Correction (Plan Alignment)
To avoid spurious correlations driven by file size, this study calculates **raw metrics** (`total_lines_changed`, `debt_score`) rather than density metrics. File size (`avg_loc`) is included as a covariate in the statistical model.

## Scope & Constraints

### SC-001: Feasibility
The pipeline must run within a 6-hour timeout on standard CI infrastructure. Heavy tools like SonarQube are excluded in favor of lighter alternatives.

### SC-002: Language Support
Primary focus on Python, Java, JavaScript/TypeScript. Support for Go and Rust where tooling permits.

### SC-003: Time Limit
Total pipeline execution must not exceed 6 hours.

### SC-004: Data Sources
Repositories must be public on GitHub.

### SC-005: Tool Validation Criteria
Tools used for static analysis must be **verified** by a **presence check of GitHub star count > 5,000 or existence of a citation in the literature**. Independent verification of study quality is not feasible per project constraints.

## Functional Requirements

### FR-001: Raw Metric Calculation
The system must calculate `total_lines_changed` (raw churn) and `debt_score` (raw debt). Density metrics (divided by LOC) are replaced by raw metrics with `avg_loc` as a covariate.

### FR-002: Static Analysis Tooling
The system must use **semgrep version 1.30.0** for multi-language analysis.
**Debt Score Calculation**:
- Python: Sum(Cyclomatic Complexity) + (100 - Maintainability Index)
- Others: Sum(Code Smells + Cyclomatic Complexity) **as reported by Semgrep**.

### FR-006: Statistical Methodology
The system must perform a **Meta-analysis of Fisher-transformed r coefficients** to aggregate results across repositories, replacing Bonferroni correction for better control of family-wise error rate.

### FR-008: Sensitivity Analysis
The system must run sensitivity analysis using fixed **thresholds of 5, 10, and 20** for `avg_loc`, rather than varying average LOC continuously.

## Data Model

### Unified Metrics Schema
- `repo_id`: string
- `file_path`: string
- `total_lines_changed`: integer (Raw Churn)
- `debt_score`: float (Raw Debt)
- `avg_loc`: float (Covariate)
- `contributor_count`: integer
- `language`: string

### Output Schema
- `metric_type`: string (pearson/spearman/meta)
- `r_value`: float
- `p_value`: float
- `n`: integer
- `threshold`: integer (for sensitivity analysis)

## User Stories

### US1: Data Acquisition and Preprocessing
Automatically select repositories, clone them, extract git history and static analysis metrics, and produce a unified CSV with raw metrics and `avg_loc` as a covariate.

### US2: Statistical Correlation Analysis
Calculate correlation between raw churn and raw debt, controlling for `avg_loc` and other confounders, and perform meta-analysis.

### US3: Visualization and Reporting
Generate scatter plots with regression lines and a summary report including meta-analysis results.