# Specification: Investigating the Correlation Between Code Churn and Technical Debt

## 1. Introduction
This project investigates the correlation between code churn (activity) and technical debt (quality) in software repositories. The goal is to determine if high-churn files accumulate more debt, controlling for project size and complexity.

## 2. Requirements

### 2.1 Functional Requirements (FR)

**FR-001: Data Collection**
The system shall automatically select repositories based on GitHub criteria (stars > 5,000 or citation presence) and clone them.

**FR-002: Static Analysis**
The system shall run static analysis tools to calculate debt scores.
- **Tool**: semgrep version 1.30.0.
- **Metric**: Sum of Code Smells + Cyclomatic Complexity (as reported by Semgrep).
- **Languages**: Python (Radon for CC/MI), Java, JS, TS, Go, Rust (Semgrep).

**FR-003: Git History Analysis**
The system shall calculate `total_lines_changed` for files over a defined period using `pydriller`.

**FR-004: Preprocessing**
The system shall filter non-source files and exclude files with `avg_loc` < 10.

**FR-005: Correlation Analysis**
The system shall calculate Pearson and Spearman correlations between `total_lines_changed` and `debt_score`, controlling for `avg_loc`.

**FR-006: Meta-Analysis**
The system shall perform a meta-analysis of Fisher-transformed r coefficients across repositories to determine the aggregate correlation, replacing Bonferroni correction.

**FR-007: Reporting**
The system shall generate a summary report including correlation coefficients, p-values, and meta-analysis results.

**FR-008: Sensitivity Analysis**
The system shall perform sensitivity analysis using **thresholds of 5, 10, and 20** for `avg_loc` to verify result stability.

### 2.2 System Constraints (SC)

**SC-001: Raw Metrics**
The system must report `total_lines_changed` and `debt_score` as raw metrics, not densities. `avg_loc` must be used as a covariate control.

**SC-002: Tool Validation**
Tool validity is confirmed by presence check of GitHub star count > 5,000 or existence of a citation in the literature.

**SC-003: Execution Time**
The pipeline must complete within 6 hours.

**SC-004: Data Integrity**
All outputs must be reproducible with pinned random seeds.

## 3. Data Model

- **Input**: GitHub Repositories (Git History, Source Code)
- **Intermediate**: `unified_metrics.csv` (Raw metrics + covariates)
- **Output**: `correlation_results.csv`, `sensitivity_analysis.csv`, `meta_analysis_results.csv`

## 4. Methodology

1. **Selection**: Filter repos by stars > 5,000 or citation presence.
2. **Extraction**: Clone, extract git churn, run static analysis.
3. **Preprocessing**: Aggregate per-file metrics. Apply `avg_loc` thresholds (5, 10, 20).
4. **Analysis**:
 - Check VIF for covariates.
 - Fit Mixed-Effects Model: `debt_score ~ total_lines_changed + avg_loc + C(project_age) + C(language) + contributor_count`.
 - Calculate Pearson/Spearman correlations (partial).
 - Meta-analysis: Fisher-transformed r coefficients.
5. **Sensitivity**: Re-run analysis for `avg_loc` thresholds 5, 10, 20.

## 5. Output Artifacts

- `data/processed/unified_metrics_loc{5,10,20}.csv`
- `data/results/correlation_results.csv`
- `data/results/sensitivity_analysis.csv`
- `data/results/meta_analysis_results.csv`
- `summary_report.txt`