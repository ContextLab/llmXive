# Research Methodology: Quantifying the Impact of Code Ownership on Software Quality

## Executive Summary

This document outlines the research methodology for analyzing the relationship between code ownership patterns and software quality metrics across open-source repositories. The study employs a rigorous statistical framework to identify correlations while explicitly maintaining an associational (non-causal) framing.

## Research Questions

### Primary Question

**RQ1**: Does code ownership concentration (measured by Gini coefficient) correlate with software quality metrics (bug density, complexity, churn)?

### Secondary Questions

**RQ2**: Is the relationship between code ownership and quality linear or non-linear?

**RQ3**: How robust are the findings across different statistical significance thresholds?

**RQ4**: Do confounding variables (module size, age) explain the observed relationships?

## Hypotheses

### Primary Hypothesis

**H1**: Higher code ownership concentration (lower Gini coefficient) is associated with lower bug density.

**Direction**: Negative correlation expected (Gini ↓ → Bugs ↓)

### Secondary Hypotheses

**H2**: The relationship exhibits non-linearity, with diminishing returns beyond a certain ownership threshold.

**H3**: Results remain robust across p-value cutoffs {0.01, 0.05, 0.1} and correlation magnitude thresholds {0.2, 0.3, 0.4}.

## Methodology

### Data Collection

#### Repository Selection

- **Sample Size**: ≥8 open-source repositories
- **Selection Criteria**: Active maintenance, Python codebase, accessible Git history
- **Time Window**: Commits up to cutoff date T, issues from T to T+1

#### Data Sources

1. **Git Repositories**: Cloned with depth=1000 (or full history if <1000 commits)
2. **Commit Logs**: Author, timestamp, file paths
3. **GitHub Issues**: Bug reports linked via path-based proximity

#### Quality Control

- **Commit Count Validation**: Reject repos with <1000 commits (unless total <1000)
- **Dataset Validation**: Verify committers, timestamps, file paths, line counts
- **Path Normalization**: Apply FR-009 (lowercase, strip extensions, normalize slashes)

### Metric Calculation

#### Ownership Metrics

**Gini Coefficient**:
- Measures inequality in code ownership distribution
- Range: [0, 1] (0 = perfect equality, 1 = perfect inequality)
- Calculation: Based on commit authorship per module

**Gini² Term**:
- Squared Gini coefficient for non-linearity testing
- Generated for use in quadratic model comparison

#### Quality Metrics

**Bug Density**:
- Normalized bugs per KLOC (thousand lines of code)
- Excludes modules with 0 lines of code

**Cyclomatic Complexity**:
- Calculated using Radon library
- Excludes non-Python files
- Validity threshold: ≥95% of modules must have valid scores

**Code Churn**:
- Lines added/deleted per module
- Captures development activity intensity

**Module Size & Age**:
- Size: KLOC (thousand lines of code)
- Age: Months since module creation

### Statistical Analysis

#### Correlation Analysis

**Spearman Rank Correlation**:
- Non-parametric measure of monotonic relationship
- Primary metric: Gini vs. bug density
- 95% confidence intervals calculated

**Multiple Comparison Correction**:
- Bonferroni or Benjamini-Hochberg procedure
- Controls family-wise error rate (FR-011)

#### Multicollinearity Diagnostics

**Variance Inflation Factor (VIF)**:
- Calculated for non-collinear predictors: Size, Age
- **Exclusion**: Gini and Gini² excluded due to mathematical collinearity
- Rationale: Standard VIF on Gini+Gini² yields infinite results (Plan: Complexity Tracking)
- Output: Valid VIF for Size/Age, "N/A (Excluded: Collinear)" for Gini terms

#### Non-linearity Testing

**Likelihood Ratio Test (LRT)**:
- Compares linear model (Outcome ~ Gini + Size + Age) vs. quadratic model (Outcome ~ Gini + Gini² + Size + Age)
- Primary metric: LRT p-value (FR-016)
- Secondary metric: t-test p-value for Gini² coefficient

#### Sensitivity Analysis

**P-value Sensitivity (SC-008)**:
- Sweep set: {0.01, 0.05, 0.1}
- For each cutoff: Count significant correlations, report total
- Output: `data/results/sensitivity_pvalue.csv`

**Correlation Magnitude Sensitivity (SC-011)**:
- Sweep set: {0.2, 0.3, 0.4}
- For each threshold: Count correlations exceeding magnitude
- Output: `data/results/sensitivity_rho.csv`

### Reproducibility Measures

#### Random Seed

- Fixed seed: 42 (configurable via `RANDOM_SEED` environment variable)
- Applied to all stochastic operations
- Logged in sensitivity analysis outputs

#### Version Control

- Ownership attribution CSVs version-controlled per Constitution Principle VI
- Content hashes recorded in `state/` directory
- Raw git clones excluded from version control (disk constraints)

#### State Management

- Intermediate ownership CSVs tracked in version control
- Other intermediate files ignored (temporary processing artifacts)
- Gitignore configured to track `*_ownership.csv` while ignoring `data/intermediate/`

## Data Hygiene

### Temporal Separation

- **Predictors (T)**: Ownership metrics calculated from commits up to cutoff T
- **Outcomes (T+1)**: Bug counts from issues in window T to T+1
- Ensures no data leakage from future to past

### Module Filtering

- **FR-008 Compliance**: Modules deleted between T and T+1 excluded from BOTH predictor and outcome calculations
- Prevents bias from transient modules

### Memory Management

- Peak RAM constraint: ≤7 GB
- Disk-based storage for intermediate CSVs
- Batch processing for large repositories

## Limitations

### Scope Limitations

1. **Observational Nature**: Correlational analysis cannot establish causality
2. **Repository Bias**: Open-source projects may not represent proprietary software
3. **Language Specificity**: Focus on Python may not generalize to other languages
4. **Time Window**: Single cutoff date may miss temporal dynamics

### Methodological Constraints

1. **Path-Based Proximity**: Issue linking via file paths may miss semantic connections
2. **Shallow History**: Depth=1000 may exclude long-term ownership patterns
3. **Gini Interpretation**: Low Gini (equality) may indicate collaborative development OR lack of ownership

### Statistical Limitations

1. **Sample Size**: ≥8 repos may limit statistical power
2. **Confounding Variables**: Unmeasured factors may influence both ownership and quality
3. **Non-linearity Detection**: Quadratic model may not capture complex relationships

## Ethical Considerations

### Associational Framing

All findings are explicitly framed as **associational rather than causal** (FR-010):
- Language: "correlates with", "associated with", "linked to"
- Avoids: "causes", "leads to", "results in"
- Final report includes explicit disclaimer

### Data Privacy

- Public repositories only
- No personal information extracted beyond commit authors
- GitHub API usage respects rate limits and terms of service

## Expected Deliverables

### Data Products

1. `data/intermediate/ownership.csv` - Ownership attribution per module
2. `data/results/metrics.csv` - Calculated metrics per module
3. `data/results/correlation_results.csv` - Spearman correlation results
4. `data/results/sensitivity_pvalue.csv` - P-value sensitivity analysis
5. `data/results/sensitivity_rho.csv` - Correlation magnitude sensitivity
6. `data/results/final_report.json` - Comprehensive analysis report

### Visualizations

- Scatter plots with regression lines (≥300 DPI)
- Minimum 8 repositories visualized
- Files saved to `figures/` directory

### Documentation

- `docs/README.md` - Project overview and usage
- `specs/001-code-ownership-analysis/research.md` - This document
- Code comments and docstrings

## Validation Criteria

### Data Collection

- [ ] ≥8 repositories processed successfully
- [ ] All repos have ≥1000 commits (or full history if <1000)
- [ ] Intermediate CSVs generated for each repo
- [ ] Dataset variable fit validation passed

### Metric Calculation

- [ ] Gini coefficient ∈ [0, 1] with precision ≥3 decimals
- [ ] Cyclomatic complexity valid for ≥95% of Python modules
- [ ] Bug density calculated for modules with >0 KLOC
- [ ] Gini² term generated for non-linearity testing

### Statistical Analysis

- [ ] Spearman correlation coefficients calculated
- [ ] 95% confidence intervals computed
- [ ] VIF calculated for Size/Age, excluded for Gini/Gini²
- [ ] LRT p-value reported for non-linearity
- [ ] Sensitivity analyses completed for both sweep sets

### Reproducibility

- [ ] Random seed 42 logged in outputs
- [ ] Ownership CSVs version-controlled
- [ ] State snapshot generated with content hashes

## References

1. Plan Document: PROJ-062 Implementation Plan
2. Feature Specification: 001-code-ownership-analysis/spec.md
3. Data Model: 001-code-ownership-analysis/data-model.md
4. Constitution Principles: llmXive Research Pipeline
5. FR-009: Path Normalization Requirements
6. FR-010: Associational Framing Requirement
7. FR-011: Multiple Comparison Correction
8. FR-013: VIF Calculation Requirements
9. FR-016: Non-linearity Testing Requirements
10. SC-008: P-value Sensitivity Analysis
11. SC-011: Correlation Magnitude Sensitivity Analysis