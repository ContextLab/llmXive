# Data Model: Investigating the Correlation Between Code Churn and Technical Debt

## Unified Metrics Schema

This schema defines the structure of the intermediate and final datasets used in the analysis. All metrics are **raw** (not density) but will be log-transformed for analysis.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `repo_id` | string | Unique identifier (GitHub org/repo) | Metadata |
| `file_path` | string | Relative path of the file | Git Log |
| `total_lines_changed` | integer | Sum of lines added + removed (Raw Churn) | `git log --numstat` |
| `debt_score` | float | Z-Score normalized debt score (Complexity + MI) | Semgrep |
| `avg_loc` | float | Average Lines of Code for the file | Git Log / Semgrep |
| `contributor_count` | integer | Number of unique contributors to the file | Git Log |
| `language` | string | Programming language (Python, Java, JS, etc.) | Filename / Semgrep |
| `repo_language` | string | Primary language of the repository | Metadata |
| `star_count` | integer | GitHub stars (for validation) | GitHub API |
| `z_cc` | float | Z-Score of Cyclomatic Complexity | Derived |
| `z_mi` | float | Z-Score of Maintainability Index | Derived |

## Output Schema (Correlation Results)

| Field | Type | Description |
|-------|------|-------------|
| `metric_type` | string | "log-log", "density", "meta" |
| `beta_value` | float | Slope coefficient from regression |
| `p_value` | float | P-value of the slope |
| `n` | integer | Sample size (number of files) |
| `threshold` | integer | LOC threshold used (for sensitivity analysis) |
| `z_score` | float | Fisher-transformed Z-score (for meta-analysis) |
| `weight` | float | Weight (1 / SE^2) for meta-analysis |
| `fdr_adjusted` | boolean | Whether FDR correction was applied |

## Data Flow

1. **Raw Input**: GitHub Repos (Git History, Source Code).
2. **Extraction**:
   - `data/raw/git_history/`: Per-repo raw log files.
   - `data/raw/static_analysis/`: Per-repo Semgrep JSON.
3. **Processing**:
   - `data/processed/unified_metrics.csv`: Merged raw metrics.
   - `data/processed/unified_metrics_loc5.csv`: Filtered by avg_loc >= 5.
   - `data/processed/unified_metrics_loc10.csv`: Filtered by avg_loc >= 10.
   - `data/processed/unified_metrics_loc20.csv`: Filtered by avg_loc >= 20.
   - `data/processed/correlation_results.csv`: Per-repo regression slopes.
4. **Aggregation**:
   - `data/processed/meta_analysis_results.csv`: Final aggregated statistics.
5. **Reporting**:
   - `data/logs/constitution_exception.log`: Records deviations from Constitution.
   - `data/logs/validation.log`: Records simplified tool validation.
   - `data/processed/summary_report.txt`: Human-readable summary.

## Data Hygiene & Versioning

- **Checksums**: All files in `data/raw` and `data/processed` are checksummed (SHA-256) and recorded in `state/`.
- **Immutability**: Raw data is never modified. Derived data is written to new files.
- **PII**: No PII is collected. Git logs are sanitized to remove email addresses if necessary (default `git log` does not expose emails in `--numstat`).
