# Data Model: GitHub Issue Resolution Analysis

## 1. Entity Definitions

### Issue
Represents a single GitHub issue record after cleaning.
- **issue_id**: Unique identifier (int/string)
- **repository**: Repository path (string, e.g., "owner/repo")
- **created_at**: ISO 8601 timestamp (datetime)
- **closed_at**: ISO 8601 timestamp (datetime)
- **resolution_time_hours**: Computed duration (float, hours)
- **labels**: List of label strings (list of strings)
- **assignee**: Assignee username or null (string/null)
- **comments_count**: Number of comments (int)
- **state**: Issue state (string, e.g., "closed")
- **is_outlier**: Boolean flag for IQR outlier detection (bool)

### Repository (Derived)
Aggregated metadata for a repository (derived from Issue data).
- **repository**: Repository path (string)
- **issue_count**: Total issues in dataset (int)
- **mean_resolution_hours**: Average resolution time (float)
- **primary_language**: Inferred language (string) or "Unknown"

### AnalysisResult
Represents the output of a statistical test or model fit.
- **test_type**: Name of the test (string, e.g., "Kruskal-Wallis", "LME")
- **predictor**: Variable tested (string)
- **p_value**: Raw p-value (float)
- **adjusted_p_value**: Corrected p-value (float, if applicable)
- **effect_size**: Magnitude of effect (float)
- **ci_lower**: Lower bound of 95% CI (float)
- **ci_upper**: Upper bound of 95% CI (float)
- **convergence_status**: "Success" or "Failed" (string)
- **note**: Any caveats (e.g., "Associational only")

## 2. Data Flow

1. **Raw Input**: `github_issues_raw.parquet` (from HF)
2. **Cleaning**:
   - Parse timestamps.
   - Filter: `closed_at > created_at` AND `resolution_time > 0`.
   - Compute: `resolution_time_hours`.
   - Flag: `is_outlier` (IQR method).
3. **Output**: `cleaned_issues.csv`
4. **Analysis**:
   - Read `cleaned_issues.csv`.
   - Generate `analysis_results.json`.
   - Generate plots (PNG/SVG).

## 3. Constraints & Rules

- **Temporal Integrity**: `created_at` and `closed_at` must be parsed as UTC.
- **Zero Handling**: Issues with `resolution_time == 0` are excluded.
- **Missing Data**: Rows with missing `created_at` or `closed_at` are excluded.
- **Label Encoding**: Rare labels (<1% frequency) are grouped into "Other".
