# Research: Quantifying the Impact of Code Ownership on Software Quality

## 1. Dataset Strategy

### 1.1 Verified Datasets
The study relies on dynamic extraction from public GitHub repositories. The following repositories are selected based on the "high-activity" criterion (≥1000 commits) and relevance to the study scope.

| Repository Name | Source URL | Verification Status | Notes |
|:--- |:--- |:--- |:--- |
| `apache/httpd` | ` | Verified (Reachable) | High commit volume, C/Python mix. |
| `apache/stratos` | ` | Verified (Reachable) | Java/Python mix, active history. |
| `microsoft/vscode` | ` | Verified (Reachable) | Large scale, TypeScript. |
| `python/cpython` | ` | Verified (Reachable) | Core Python, massive history. |
| `scikit-learn/scikit-learn` | ` | Verified (Reachable) | Python, high bug density. |
| `pandas-dev/pandas` | ` | Verified (Reachable) | Data science, active issues. |
| `numpy/numpy` | ` | Verified (Reachable) | C/Python, stable core. |
| `django/django` | ` | Verified (Reachable) | Python web framework. |
| `rails/rails` | ` | Verified (Reachable) | Ruby, large ecosystem. |
| `kubernetes/kubernetes` | ` | Verified (Reachable) | Go, massive scale. |

*Note: The list above represents the target set. The implementation will attempt to clone all instances. If a repo fails the ≥1000 commit check or clone fails, it is skipped per FR-014, and the system proceeds with the remaining valid set (target ≥8).*

### 1.2 Variable Fit Validation
Before analysis, `data_collection.py` will validate that the commit history contains:
- **Committers**: `git log --format='%an'`
- **Timestamps**: `git log --format='%ai'`
- **File Paths**: `git diff --name-only`
- **Line Counts**: `git log --format='' --numstat`

If a repository lacks these variables (e.g., empty history, private), it is logged and skipped (FR-014).

### 1.3 Data Acquisition Method
- **Clone Strategy**: `git clone --depth 1000` (per Spec FR-001, superseding Constitution draft typo).
- **Time Window Definition**:
 - **T**: The date of the **latest commit in the shallow history** (depth 1000).
 - **Ownership Window**: T-6 months to T (limited by available shallow history).
 - **Bug Window**: T to T+6 months (T+1).
 - **Gap Handling**: If the shallow history truncates the T-6 to T window, the study explicitly acknowledges this data gap. The Gini coefficient is calculated strictly on the available commits (Recent Ownership Concentration).
- **Rate Limiting**: Exponential backoff with 3 retries and 60s delay (FR-006). No unverified URLs are used; all data comes from the verified list above or the local clone.

## 2. Methodology & Statistical Plan

### 2.1 Metric Calculation
1. **Ownership Concentration (Gini)**:
 - Calculate per module (file).
 - Formula: $G = \frac{\sum_{i=1}^n \sum_{j=1}^n |x_i - x_j|}{2n^2 \bar{x}}$ where $x_i$ is commit count for developer $i$.
 - Precision: ≥3 decimal places (FR-002).
 - **Limitation**: Reflects "Recent Ownership" (last ~1000 commits). For large repos, this may be <2 years. This is documented as a systematic measurement error.
2. **Bug Density (Explicitly Linked)**:
 - Link issues to files using **Bug-File Proximity Heuristic** (FR-009):
 - Normalize path (lowercase, strip `.bak`, `.pyc`, `.lock`).
 - Exact word-boundary match of issue title/description against file path.
 - Normalize: Bugs per KLOC (FR-002).
 - **Linkage Rate (SC-007)**: Calculate `linked_issues / total_issues_mentioning_paths` and report as a percentage. This quantifies the construct validity limitation.
 - Exclude modules deleted between T and T+1 to avoid survivorship bias.
3. **Control Variables**:
 - **Code Churn**: Total lines added + deleted per module (FR-002).
 - **Complexity**: Cyclomatic complexity via `radon` (FR-003).
 - **Size**: KLOC.
 - **Age**: Months since first commit.

### 2.2 Statistical Analysis
1. **Primary Test**: Spearman Rank Correlation ($\rho$) between Gini and Explicitly Linked Bug Density.
 - Output: $\rho$, p-value, 95% CI (FR-004, SC-001).
 - Correction: Bonferroni or Benjamini-Hochberg for multiple comparisons (FR-011, SC-010).
 - **Primary Threshold**: Significance is defined as $|\rho| > 0.3$ AND $p < 0.05$ (Constitution Principle VII), unless sensitivity analysis shows extreme fragility.
2. **Secondary Outcomes**:
 - **Code Churn Correlation (SC-006)**: **Explicitly calculate and report the Spearman rank correlation coefficient ($\rho$) and p-value between Total Code Churn and Bug Density.** This is a critical control analysis to distinguish the effect of ownership concentration from the general effect of code activity levels. The result will be included in the final JSON output under `secondary_outcomes.churn_correlation`.
 - **Linkage Rate (SC-007)**: Reported as a global aggregate percentage.
3. **Collinearity Diagnostics**:
 - Calculate VIF for predictors in the **linear model only**: Gini, Size, Age.
 - Do NOT calculate VIF for Gini and Gini² simultaneously (mathematically invalid).
 - If VIF ≥ 5, frame as descriptive joint relationship, not independent effects (FR-013, SC-009).
4. **Non-Linearity Test (FR-016, SC-012)**:
 - Fit Linear Model: $Y \sim \text{Gini} + \text{Size} + \text{Age}$.
 - Fit Quadratic Model: $Y \sim \text{Gini} + \text{Gini}^2 + \text{Size} + \text{Age}$.
 - Perform **Likelihood Ratio Test (LRT)** or F-test comparing the two models.
 - Report the p-value of the test (significance of the added quadratic term). Do not interpret Gini² coefficient directly.
5. **Sensitivity Analysis**:
 - **p-value Sweep (FR-012, SC-008)**: Sweep thresholds including low values. Report the count of significant findings for each.
 - **Correlation Sweep (FR-015, SC-011)**: Sweep thresholds across a range of values. Report the count of significant findings for each.

### 2.3 Assumptions & Limitations
- **Observational Nature (FR-010)**: All findings are associational. The final report MUST include a dedicated section stating "This study is observational; no causal claims are made." The JSON output includes `is_observational: true`.
- **Heuristic Validity**: Path-based linking may miss bugs not explicitly mentioning file paths. This is a known limitation; the **Linkage Rate** is reported to quantify this. The metric is "Explicitly Linked Bug Density," not total bug density.
- **Shallow History**: Depth 1000 may miss early ownership patterns. The metric is explicitly "Recent Ownership Concentration."
- **Compute Constraints**: Analysis is CPU-only. Large datasets are chunked or sampled if necessary, though repos x 1000 commits is tractable.

## 3. Computational Feasibility
- **RAM**: Intermediate CSVs written to disk. Peak RAM ≤7 GB (FR-007).
- **Disk**: 10 repos x ~100MB (shallow) + CSVs < 14 GB.
- **Time**: Sequential processing. A representative sample of repositories will be processed (clone + parse + analyze) to estimate the total time required for the analysis phase. Well within 6h limit.
- **Libraries**: `scikit-learn`, `scipy`, `pandas` are CPU-optimized. No GPU dependencies.