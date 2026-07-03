# Research: Quantifying the Association Between Code Authorship Diversity and Software Security

## Problem Statement

Does code authorship diversity (measured by unique contributors) **associate** with software security (measured by CVE count), after controlling for project size (KLOC) and other factors?

**Critical Note**: This is an **observational study**. No causal claims will be made. The goal is to quantify the association. Reverse causality (secure projects attract diverse contributors) is a known limitation; a **lagged variable analysis** (lagging `author_count` by 1 year) is included as a robustness check to partially mitigate this, though full causal inference would require instrumental variables not available here.

## Dataset Strategy

The project relies on **verified datasets** only, with strict adherence to Constitutional Principle VII (Official NVD Feed).

### 1. Target Repository List (Independent Variable Source)
- **Purpose**: Define the set of 500 repositories to analyze.
- **Source**: Generated via **GitHub API** using a **fixed seed and deterministic query**.
- **Strategy**:
  - The pipeline will execute a specific GitHub API query: `language:python stars:>1000 in:readme created:>=2015-01-01` (and similar for JS, Java) to ensure a reproducible, non-biased sample.
  - The query results will be sorted by a deterministic key (e.g., `updated_at` then `name`) and the first 500 unique URLs will be saved to `data/raw/target_list_seed.csv`.
  - This ensures the target list is **independent of CVE presence** (avoiding selection bias) and fully reproducible.
- **Metadata**: The API response provides `stargazers_count`, `created_at`, `language`, and `updated_at`.

### 2. Vulnerability Data (Outcome Variable Source)
- **Purpose**: Provide the `cve_count` for each repository.
- **Source**: **Official NVD/CVE JSON Feed** (Exclusive).
- **Strategy**:
  - The pipeline will download **ALL** yearly NVD JSON files (2002-2024) from `https://nvd.nist.gov/feeds/json/cve/1.1/`.
  - **Deduplication**: All files will be merged into a single in-memory dictionary keyed by `CVE-ID`. This ensures each CVE is counted exactly once, regardless of which yearly file it appears in.
  - **Matching**: Repository URLs will be matched against the `cveReferences` in the merged NVD data. Exact URL matching is required.
  - **Fallback**: **None**. If the NVD feed is unreachable or the merge fails, the pipeline **ABORTS** (exit code 1). No HuggingFace datasets are used.

### 3. Git History (Predictor Source)
- **Purpose**: Extract `unique_authors` and `kloc`.
- **Strategy**:
  - Clone each repo in `target_list_seed.csv` using `git clone --shallow-since=2015-01-01`. This satisfies Constitution Principle VI (shallow) while retrieving ~9 years of history sufficient for `unique_authors` calculation.
  - Run `cloc` on the shallow clone for `raw_line_count`.
  - Parse `git log` for `unique_authors` (filtering for authors with ≥1 line).

**Selection Bias Mitigation**:
The target list is generated via a broad language query with a deterministic sort, avoiding popularity-based filtering (e.g., min stars is used only to ensure activity, but the sample is not biased towards known CVEs). The independence of the selection criteria from the outcome (CVE count) is maintained.

## Statistical Methodology

### Primary Model
- **Type**: Generalized Linear Model (GLM) with Poisson or Negative-Binomial family.
- **Response**: `cve_count` (count data, non-negative integers).
- **Predictors**:
  - `author_count` (unique contributors).
  - Controls: `project_age` (years), `language` (one-hot), `release_count`, `num_dependencies`, `file_count` (proxy for complexity).
  - **Project Size**: `log(kloc)` is included as a **standard predictor** (free coefficient), **NOT** an offset. This allows the data to determine the relationship between size and CVEs, avoiding bias if the true slope is not 1.
- **Equation**: $log(E[Y]) = \beta_0 + \beta_1 \cdot \text{author\_count} + \beta_2 \cdot \log(\text{kloc}) + \beta_3 \cdot \text{age} + \dots$
- **Interaction**: `author_count * language` terms are included to test if the effect of diversity varies by language (replacing simple subsampling).

### Diagnostics & Rigor
1.  **Collinearity**: Calculate Variance Inflation Factor (VIF) for all predictors. Flag if VIF > 5 (Spec FR-005, SC-004).
2.  **Multiple Comparisons**: Apply Benjamini-Hochberg (BH) correction to p-values from the main model and all robustness tests (Spec FR-006, SC-005).
3.  **Power/Sample Size**:
    -   **Formal Power Analysis**: A simulation-based power calculation (using `statsmodels.stats.power`) will be performed.
 - **Method**: Simulate 1000 datasets with varying effect sizes for `author_count` (0.01 to 0.10) and zero-inflation rates (0.8 to 0.95) to estimate the Minimum Detectable Effect Size (MDES) at [deferred] power for N=500.
    -   **Limitation**: The plan will report the MDES and explicitly note if the study is underpowered for small effects.
4.  **Causal Claims**: This is **observational**. No causal claims will be made. Results will be framed as "associations."

### Robustness Checks (Spec US-3)
1.  **Lagged Variable Analysis**: Re-run the main model with `author_count` lagged by 1 year (using `created_at` and `updated_at` to approximate time windows). This mitigates reverse causality.
2.  **Alternative Metric**: Replace `author_count` with `Shannon Entropy` of commit distribution.
3.  **Non-linearity Check**: Fit a model with a quadratic term for `author_count` (`author_count^2`) and restricted cubic splines to test for diminishing returns or "too many cooks" effects.
4.  **Interaction Terms**: The main model includes `author_count * language` interactions to control for language-specific effects while maintaining power.
5.  **Hierarchical Model**: If interactions are insufficient, fit a mixed-effects model (random intercept for language) as a fallback.

### Validation & Circularity Avoidance
-   **Descriptive Only**: `cve_density` (`cve_count / kloc`) is calculated for descriptive purposes only and is **not** used as a dependent variable in the GLM.
-   **Model Diagnostics**: Validation focuses on residual analysis (e.g., Pearson residuals) and goodness-of-fit tests (Deviance, AIC/BIC). **No** comparison of predicted density to observed density is performed, as this would be circular (since `cve_density` is a deterministic function of `cve_count` and `kloc`).

## Compute Feasibility & Constraints
-   **Environment**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
-   **Memory**: Data processing (merging 500 rows + NVD feed) is trivial (<100 MB). NVD feed (all years) is of substantial size when uncompressed; processed in chunks to stay under 7GB.
-   **Time**:
    -   Downloading/merging NVD: ~ mins.
    -   Cloning a subset of repositories (`--shallow-since`): ~2-3 hours (network bound).
    -   GLM fitting: <1 minute.
    -   Total runtime within 6-hour limit.
-   **No GPU**: All statistical operations (`statsmodels`) are CPU-native.

## Decision Rationale
-   **Why Predictor, not Offset?**: Using `log(kloc)` as a predictor allows the model to learn the true relationship between size and CVEs. An offset forces a 1:1 slope, which may be false and bias the `author_count` coefficient. **This requires a spec amendment to FR-004**.
-   **Why No Fallbacks?**: Constitution Principle VII mandates the official NVD feed. Using fallbacks would violate the "MUST" clause. The pipeline aborts on failure to ensure strict compliance.
-   **Why Shallow-Since?**: Constitution Principle VI mandates shallow clone. `--depth=1` breaks `git log`. `--shallow-since=2015-01-01` satisfies the constraint while providing sufficient history for `unique_authors`.
-   **Why Lagged Variables?**: To address reverse causality in an observational study, lagging the predictor by 1 year provides a stronger temporal argument for the direction of association, even if it doesn't prove causality.
