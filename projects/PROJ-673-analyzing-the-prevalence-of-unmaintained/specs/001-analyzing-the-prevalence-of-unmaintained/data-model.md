# Data Model: Analyzing the Prevalence of Unmaintained Dependencies in Popular NPM Packages

## Overview
This document defines the data structures used for the dependency analysis pipeline. The model supports the ingestion of raw API data, the creation of a unified analysis dataset, and the output of statistical results.

## Entities

### 1. Package (Seed)
Represents the initial set of popular NPM packages.
- `name` (string): The unique package identifier (e.g., "lodash").
- `weekly_downloads` (integer): Number of downloads in the last week.
- `category` (string): Broad category inferred from keywords or top-level classification.

### 2. Dependency
Represents a unique software component within the dependency tree.
- `name` (string): Package name.
- `version` (string): Specific version string (e.g., "4.17.21").
- `parent_package` (string): The seed package this dependency belongs to.
- `is_transitive` (boolean): True if not a direct dependency of the seed.
- `last_release_date` (datetime): Timestamp of the last release (from GitHub or NPM).
- `last_commit_date` (datetime): Timestamp of the last commit (from GitHub).
- `age_source` (string): Indicates source of age data: "github_release", "github_commit", "npm_publish_proxy".
- `vulnerability_count` (integer): Count of *currently unpatched* CVEs (from `npm audit`).
- `vuln_source` (string): Indicates source of vulnerability data: "npm_audit", "historical_proxy".
- `age_in_days` (float): Calculated as (Current Date - `last_release_date`). Null if release date is missing.
- `category` (string): Inferred category (e.g., "framework", "utility").
- `data_completeness_flags` (list<string>): Flags for missing data (e.g., "no_github_repo", "proxy_age_used", "historical_vuln_used").

### 3. AnalysisResult
Represents the output of the statistical analysis.
- `correlation_coefficient` (float): Spearman's $\rho$.
- `p_value` (float): Significance level.
- `sample_size` (integer): Number of dependencies analyzed.
- `methodology_notes` (string): Notes on data exclusions or corrections applied.

### 4. StratifiedResult
Represents the output of the category-specific analysis.
- `category` (string): The category name.
- `correlation_coefficient` (float): Spearman's $\rho$ for this category.
- `p_value` (float): Significance level for this category.
- `sample_size` (integer): Number of dependencies in this category.
- `zinb_coefficient` (float): Coefficient from Zero-Inflated Negative Binomial regression (if applicable).

## Data Flow
1. **Raw Ingestion**: API responses (JSON) are saved to `data/raw/`.
2. **Transformation**: Raw data is parsed into `Dependency` objects, `age_in_days` is calculated, and `vulnerability_count` is aggregated from `npm audit`.
3. **Filtering**: Dependencies with missing `last_release_date` are flagged but retained for vulnerability counting (FR-010). Those missing both release and commit dates are excluded from age-based correlation.
4. **Analysis**: The filtered dataset is passed to the statistical engine (Spearman + ZINB).
5. **Output**: Results are serialized to `data/processed/analysis_results.json`.