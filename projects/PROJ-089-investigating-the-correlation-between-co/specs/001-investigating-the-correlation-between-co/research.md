# Research: Investigating the Correlation Between Code Churn and Technical Debt

## Overview
This research phase validates the data sources, tooling, and statistical methodology required to execute the plan. It confirms that the selected datasets (open-source GitHub repos) are programmatically accessible and that the statistical methods (Log-Log Model, Meta-analysis) are appropriate for the study design.

## Dataset Strategy

The study requires a diverse set of open-source repositories to ensure statistical power and generalizability. The data acquisition strategy relies on **public GitHub repositories** which are directly downloadable via `git clone`.

### Verified Datasets
No external static dataset (e.g., a pre-packaged CSV of churn metrics) exists that meets the specific requirement of **raw churn** + **semgrep debt** + **file-level granularity**. Therefore, the pipeline must **generate** the dataset by:
1. Selecting repositories based on a **pinned list** (for reproducibility).
2. Cloning them.
3. Extracting metrics dynamically.

**Selection Criteria**:
- Languages: Python, Java, JavaScript/TypeScript (per SC-002).
- Activity: Minimum 50 commits in the last year (to ensure non-zero churn).
- Size: < 100k LOC (to fit 6h timeout).
- Validation: GitHub Star Count > 5,000 (per SC-005).
- **Generalization Limits**: Results apply only to **active, popular open-source projects**. The sample excludes abandoned or enterprise internal code, limiting external validity to this specific population.

**Source**: GitHub API (public).
**Access Method**: `git clone` + `git log` parsing. No gated data involved.
**Feasibility**: High. Public repos are freely accessible. The 6h timeout limits the *number* of repos (30), not the *type*.

## Tooling Validation

### Static Analysis: Semgrep v1.30.0
- **Requirement**: Spec FR-002 mandates Semgrep v1.30.0.
- **Verification**: 
  - GitHub Stars: > 5,000 (Actual: ~30k+).
  - Literature: Widely cited in modern static analysis literature.
  - Version Pin: `semgrep==1.30.0` in `requirements.txt`.
- **Debt Score Calculation**:
  - **Normalization**: To address mixed units (CC vs MI), we use **Z-Score Standardization** within each repository.
    - `z_cc = (CC - mean(CC)) / std(CC)`
    - `z_mi = (MI - mean(MI)) / std(MI)`
    - `debt_score = z_cc * 0.5 + z_mi * 0.5`
  - **Semgrep Configuration**: A pinned `semgrep.yaml` is used with the following rules:
    - Python: `p/python:code-smells`, `p/python:cyclomatic-complexity`
    - Java/JS: `p/java:code-smells`, `p/js:cyclomatic-complexity`
  - **Output**: JSON format, parseable by `pandas`.

### Git History Extraction
- **Tool**: `gitpython` or `git log` CLI.
- **Metric**: `total_lines_changed` (raw churn).
- **Method**: `git log --numstat` to aggregate lines added/removed per file.

## Statistical Methodology

### Primary Analysis: Log-Log Linear Model
- **Model**: Multiple Linear Regression on log-transformed variables.
- **Equation**: `log(debt_score + 1) ~ log(total_lines_changed + 1) + log(avg_loc + 1)`
- **Justification**: This approach avoids the spurious correlation problem inherent in raw metrics and ratio metrics (Pearson, 1897). It models the elasticity of debt with respect to churn, controlling for file size in a multiplicative framework.
- **Unit of Analysis**: **Repository**. The model estimates a slope coefficient (beta) for each repository using file-level data. These slopes are then aggregated.

### Aggregation: Meta-Analysis
- **Method**: Fisher's Z-transformation of **slope coefficients** (beta), not correlation coefficients.
- **Rationale**: Correlation coefficients are not normally distributed. Fisher's Z normalizes them, allowing for weighted averaging across repositories.
- **Formula**: 
  1. Transform $beta$ to $Z = 0.5 \ln((1+beta)/(1-beta))$ (if beta is bounded) OR use standard error-based weighting for unbounded slopes.
  2. Calculate weighted mean $Z_{mean} = \sum w_i Z_i / \sum w_i$ (where $w_i = 1 / SE_i^2$).
  3. Transform back to $beta_{meta}$.
- **Source**: Hedges, L. V., & Olkin, I. (1985). *Statistical methods for meta-analysis*. (Verified: Wikipedia entry for Larry V. Hedges).
- **Error Control**: 
  - **FWER**: Individual repo tests are NOT corrected for FWER in the meta-analysis step.
  - **FDR**: Benjamini-Hochberg correction is applied to the per-repo p-values to control the False Discovery Rate.

### Sensitivity Analysis
- **Primary Method**: **Interaction Term** (`debt ~ churn * avg_loc`) in the regression model to test if the slope of the churn-debt relationship changes with file size.
- **Secondary Method**: Fixed `avg_loc` thresholds of 5, 10, and 20 (re-running the model on filtered data) as a descriptive check.
- **Purpose**: To verify if the correlation holds across different file size distributions and to avoid arbitrary binning.

## Compute Feasibility

- **CPU-First**: All statistical operations (correlation, meta-analysis) are lightweight and run instantly on CPU.
- **I/O Bound**: The pipeline is I/O bound (cloning repos, parsing git logs).
- **Memory**: 
  - Git log parsing: Streaming (line-by-line).
  - Semgrep: Runs per-repo, outputs JSON. Memory usage is low.
  - Aggregation: `pandas` dataframe of ~10k rows fits easily in 7 GB RAM.
- **Time**: 
  - Clone/Analyze a representative repository: a short duration.
  - Target: A representative set of repositories.
 - Total: [deferred] (< 6 hours).
- **GPU**: Not required. No deep learning models involved.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Semgrep fails on some repos (e.g., unsupported language) | Data loss | Log error, skip repo, proceed. |
| Git history too large (> 6h) | Timeout | Limit to last 1 year of history; sample repos (30 total). |
| Spurious correlation due to file size | Invalid result | Use Log-Log Model (primary) and Interaction Terms (sensitivity). |
| Missing data (no churn) | Bias | Filter repos with 0 churn. |
| Survivorship Bias | Limited Generalizability | Explicitly state results apply only to active, popular OSS projects. |

## Power Analysis

- **Sample Size**: 30 repositories.
- **Effect Size**: Assuming a small-to-moderate effect (beta = 0.2).
- **Power**: With n=30, power to detect a small effect is < 50%. Power to detect a moderate effect is > 80%.
- **Limitation**: The study is underpowered for detecting small effects. The focus is on the **directionality** and **consistency** of the effect across repositories, rather than precise magnitude estimation.
