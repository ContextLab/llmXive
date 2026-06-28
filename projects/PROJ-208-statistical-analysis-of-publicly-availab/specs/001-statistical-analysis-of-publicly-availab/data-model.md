# Data Model: Statistical Analysis of GitHub Issue Resolution Times

## Entity Definitions

### Issue (Core Entity)

Represents a single GitHub issue with computed resolution time.

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `issue_id` | integer | GitHub API | Unique issue identifier within repository |
| `repository` | string | GitHub API | Repository path (owner/repo) |
| `created_at` | datetime | GitHub API | Issue creation timestamp (ISO 8601) |
| `closed_at` | datetime | GitHub API | Issue closure timestamp (ISO 8601) |
| `labels` | string | GitHub API | Comma‑separated label names |
| `assignee` | string | GitHub API | Assignee username or null |
| `comments_count` | integer | GitHub API | Number of comments on issue |
| `resolution_time_hours` | float | Computed | `closed_at - created_at` in hours |
| `resolution_time_log` | float | Computed | Natural log of resolution time |
| `is_outlier` | boolean | Computed | True if resolution time >30 days **or** >3 SD above the mean resolution time of its repository (repository‑specific threshold) |
| `is_valid` | boolean | Computed | True if `closed_at >= created_at` and no missing timestamps |

### Repository (Core Entity)

Represents a GitHub project with metadata.

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `repository` | string | GitHub API | Repository path (owner/repo) |
| `language` | string | GitHub API | Primary programming language |
| `star_count` | integer | GitHub API | Number of repository stars |
| `contributor_count` | integer | GitHub API | Number of contributors |
| `repo_created_at` | datetime | GitHub API | Repository creation timestamp |

### AnalysisResult (Derived Entity)

Represents a statistical test outcome.

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `test_type` | string | Computed | Type of test (e.g., "kruskal‑wallis", "mixed‑effects") |
| `predictor` | string | Computed | Name of predictor variable |
| `p_value` | number | Computed | Raw p‑value from test |
| `effect_size` | number | Computed | Effect size metric (e.g., eta‑squared, coefficient) |
| `ci_lower` | number | Computed | Lower bound of confidence interval |
| `ci_upper` | number | Computed | Upper bound of confidence interval |
| `adjusted_p_value` | number | Computed | Holm‑Bonferroni adjusted p‑value |
| `is_significant` | boolean | Computed | True if adjusted p < 0.05 |

## Data Flow Diagram

```
GitHub API (raw) → collect/github_collector.py → data/raw/issues.json
                                                      ↓
                                        collect/preprocess.py
                                                      ↓
                                        data/processed/issues_clean.csv
                                                      ↓
                        ┌─────────────────────────────┼─────────────────────────────┐
                        ↓                             ↓                             ↓
        analysis/distribution_fitting.py    analysis/hypothesis_testing.py    analysis/mixed_effects_model.py
                        ↓                             ↓                             ↓
        data/processed/distribution_metrics.json  data/processed/test_results.json  data/processed/model_results.json
                                                      ↓
                        ┌─────────────────────────────┴─────────────────────────────┐
                        ↓                                                     ↓
        diagnostics/collinearity.py                                 diagnostics/sensitivity_analysis.py
                        ↓                                                     ↓
        data/processed/collinearity_report.json                 data/processed/sensitivity_report.json
```

## Transformations

| Transformation | Input | Output | Script |
|----------------|-------|--------|--------|
| Timestamp parsing | `created_at`, `closed_at` (string) | `created_at`, `closed_at` (datetime) | `preprocess.py` |
| Resolution time computation | `created_at`, `closed_at` | `resolution_time_hours` | `preprocess.py` |
| Log transformation | `resolution_time_hours` | `resolution_time_log` | `preprocess.py` |
| Outlier flagging | `resolution_time_hours` per repository | `is_outlier` | `preprocess.py` |
| Validity filtering | `created_at`, `closed_at` | `is_valid` | `preprocess.py` |
| Label parsing | `labels` (string) | `labels` (list) | `preprocess.py` |

## Quality Constraints

| Constraint | Threshold | Enforcement |
|------------|-----------|-------------|
| Dataset completeness | ≥95% of issues have all required columns | SC‑001 |
| Resolution time validity | `closed_at >= created_at` | FR‑003 |
| API rate limit handling | ≥60 s wait before retry | FR‑003 |
| Total runtime | ≤6 h | FR‑009 |
| Peak memory | ≤7 GB | FR‑009 |
| No GPU usage | [deferred] | FR‑010 |