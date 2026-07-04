# Research: Analyzing the Prevalence of Unmaintained Dependencies in Popular NPM Packages

## Research Question
To what extent does the age of unmaintained dependencies in popular NPM packages correlate with exposure to unpatched security vulnerabilities in the JavaScript software supply chain?

## Dataset Strategy

The study relies on two primary data sources: the NPM Registry for package metadata and the GitHub API for maintenance timestamps. Vulnerability data is sourced primarily from the live `npm audit` API to ensure version-specific accuracy.

### Primary Data Sources

| Dataset | Description | Source URL | Usage |
|:--- |:--- |:--- |:--- |
| **Top NPM Packages** | List of packages sorted by weekly download count. | ` | Initial seed list for dependency traversal. |
| **NPM Package Metadata** | Detailed metadata (versions, dependencies) fetched via NPM API. | N/A (API) | Resolving transitive dependencies and version constraints. |
| **GitHub Repository Metadata** | Last commit and release tag timestamps. | N/A (API) | Calculating "dependency age" (days since last release). |
| **npm audit API** | Live vulnerability status for specific package versions. | N/A (API) | **Primary Source** for counting *currently unpatched* CVEs per dependency version. |
| **CVE Database (Static)** | Public vulnerability records (CVE IDs, descriptions). | ` | **Secondary/Enrichment Only**: Used for historical context if audit API fails, NOT for primary 'unpatched' count. |

**Note on CVE Sources**: The plan explicitly rejects using static datasets (like `Nganlt/CVEs_10`) to determine the *current* 'unpatched' status of a specific version, as these datasets lack the version-specific logic of `npm audit`. The `npm audit` API is the authoritative source for whether a specific version is vulnerable and if a fix exists. The static dataset is used only for enrichment or as a fallback if the audit API is unreachable.

### Data Collection Strategy
1. **Seed Selection**: Load `npm_packages.csv` to identify the top $N$ packages (e.g., top [deferred]).
2. **Dependency Traversal**: For each seed, query the NPM API to recursively resolve the dependency tree. Flatten to unique dependencies.
3. **Maintenance Metadata**: For each unique dependency, query the GitHub API (using the `repository_url` from NPM metadata) to retrieve `last_release_date`.
 - **Fallback**: If GitHub is unavailable, use NPM `time.modified` (last publish date) but flag the record as `proxy_age`.
 - **Sensitivity**: A sensitivity analysis will compare results using only 'GitHub Age' vs. the full dataset (including NPM proxy age).
4. **Vulnerability Count**: Query the `npm audit` API for each package version.
 - **Metric Definition**: `vulnerability_count` = number of CVEs where the specific version is vulnerable AND no fixed version exists (or the user's version is older than the fix).
 - **Fallback**: If `npm audit` fails, use the static `Nganlt/CVEs_10` dataset to count *historical* CVEs for the package name (not version) and flag as `historical_proxy`. This data will be excluded from the primary analysis.
5. **Rate Limiting**: Implement exponential backoff (max 3 retries) for all API calls (FR-009).

## Statistical Methodology

### Primary Analysis
- **Metric**: Spearman rank correlation coefficient ($\rho$) between `age_in_days` (continuous) and `vulnerability_count` (continuous, non-negative).
- **Hypothesis**: $H_0: \rho = 0$ (No correlation). $H_1: \rho \neq 0$.
- **Significance**: $\alpha = 0.05$.
- **Correction**: As this is a single primary test, no family-wise error correction is applied to the main result. However, stratified analyses (US-3) will apply Bonferroni correction if >10 categories are tested.

### Zero-Inflated Data Handling
- **Issue**: `vulnerability_count` is expected to be highly zero-inflated (many packages have 0 vulnerabilities). Standard Spearman correlation may be biased or lack power for this distribution.
- **Mitigation**:
 1. **Headline Result**: Report Spearman $\rho$ with explicit caveats regarding zero-inflation.
 2. **Robustness Check**: Perform a **Zero-Inflated Negative Binomial (ZINB)** regression where `vulnerability_count` is the dependent variable and `age_in_days` is the predictor. This models the excess zeros and the count distribution separately.
 3. **Sensitivity**: Compare the significance and direction of the ZINB coefficient with the Spearman result. If they diverge, the ZINB result will be highlighted as the more robust finding.

### Stratified Analysis
- **Grouping**: Dependencies categorized by keyword matching (e.g., "framework", "utility", "build tool") or dependency graph topology.
- **Threshold**: Only categories with a sufficient number of samples to ensure statistical power will be analyzed.
- **Output**: Correlation coefficient and p-value per category (Spearman) and ZINB coefficients where applicable.

### Validity & Circularity
- **Distinction**: The plan distinguishes between 'age' (maintenance signal: time since last activity) and 'vulnerability_count' (security signal: known flaws in the current version).
- **Circularity Check**: While both relate to version history, they are not tautological. An old package (high age) might have 0 vulnerabilities if it is stable and rarely targeted, or many if it is a common target. The `npm audit` API provides the *current* state, independent of the *time* since the last release.
- **Historical vs. Unpatched**: The metric is strictly "currently unpatched" (from `npm audit`), not "total historical CVEs". This prevents the trivial correlation of "older packages have had more time to accumulate CVEs".

### Power & Sample Size
- **Target**: Power sufficient for detecting a moderate effect size ($\rho \geq 0.2$).
- **Assumption**: With the top [deferred] packages and their transitive dependencies, the sample size $N$ is expected to be in the tens of thousands, which is sufficient for the target power.
- **Limitation**: If API rate limits restrict the dataset to a smaller $N$, the study will report the achieved power as a limitation.

## Computational Feasibility
- **Environment**: GitHub Actions Free Tier (2 CPU, ~7GB RAM, no GPU).
- **Strategy**:
 - Data is processed in chunks to fit memory.
 - Statistical tests (Spearman, ZINB) are computationally efficient for $N < 100k$.
 - API calls are the bottleneck; backoff and caching are critical.
 - No heavy ML models are used; only standard statistical libraries (`scipy`, `statsmodels`).