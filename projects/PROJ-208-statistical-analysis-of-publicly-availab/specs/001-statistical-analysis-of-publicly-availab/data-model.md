# Data Model: Statistical Analysis of GitHub Issue Resolution Times

## Entity-Relationship Diagram

```
┌─────────────────────────────────┐
│           Repository            │
├─────────────────────────────────┤
│ repo_id (PK)                    │
│ owner                           │
│ name                            │
│ language                        │
│ star_count                      │
│ contributor_count               │
│ created_at                      │
│ issue_count                     │
└─────────────────────────────────┘
                │
                │ 1:N
                ▼
┌─────────────────────────────────┐
│              Issue              │
├─────────────────────────────────┤
│ issue_id (PK)                   │
│ repo_id (FK)                    │
│ created_at                      │
│ closed_at                       │
│ resolution_time_hours           │
│ resolution_time_log             │
│ labels (JSON)                   │
│ assignee (nullable)             │
│ comments_count                  │
│ excluded_flag                   │
│ zero_resolution_flag            │
└─────────────────────────────────┘
                │
                │ 1:N
                ▼
┌─────────────────────────────────┐
│        AnalysisResult           │
├─────────────────────────────────┤
│ result_id (PK)                  │
│ test_type                       │
│ predictor                       │
│ p_value                         │
│ adjusted_p_value                │
│ effect_size                     │
│ ci_lower                        │
│ ci_upper                        │
│ vif (nullable)                  │
│ sensitivity_cutoff              │
└─────────────────────────────────┘
```

## Entity Definitions

### Issue

**Purpose**: Represents a single GitHub issue with resolution time and metadata.

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| issue_id | integer | Yes | Unique issue identifier | PK, ≥1 |
| repo_id | integer | Yes | Foreign key to Repository | FK, ≥1 |
| created_at | datetime | Yes | Issue creation timestamp | ISO 8601, UTC |
| closed_at | datetime | Yes | Issue closure timestamp | ISO 8601, UTC |
| resolution_time_hours | float | Yes | `(closed_at - created_at) / 3600` | ≥0, excluded if <0 |
| resolution_time_log | float | Yes | `log(resolution_time_hours + 1)` | For distribution fitting |
| labels | array[string] | Yes | Issue labels | May be empty array |
| assignee | string | No | Assigned user login | Nullable |
| comments_count | integer | Yes | Number of comments | ≥0 |
| excluded_flag | boolean | Yes | Flag for excluded issues | False if valid |
| zero_resolution_flag | boolean | Yes | Flag for zero resolution time | True if created_at == closed_at |

**Validation Rules**:
- `resolution_time_hours >= 0` (FR-003)
- `created_at < closed_at` (preprocessing filter)
- `labels` may be empty but column must be populated (SC-001)
- **Repositories with <10 issues excluded from mixed-effects modeling**
- **Zero resolution times: log(x+1) transform applied for distribution fitting only**

### Repository

**Purpose**: Represents a GitHub project with metadata.

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| repo_id | integer | Yes | Unique repository identifier | PK, ≥1 |
| owner | string | Yes | Repository owner | Not empty |
| name | string | Yes | Repository name | Not empty |
| language | string | No | Primary programming language | Nullable (SC-001) |
| star_count | integer | Yes | Star count | ≥0 |
| contributor_count | integer | Yes | Contributor count | ≥1 |
| created_at | datetime | Yes | Repository creation timestamp | ISO 8601, UTC |
| issue_count | integer | Yes | Number of closed issues | ≥10 for mixed-effects modeling |

**Validation Rules**:
- `language` may be null (handled as missing data per spec)
- `contributor_count >= 1` (at least owner)
- **issue_count >= 10 required for inclusion in mixed-effects modeling**

### AnalysisResult

**Purpose**: Represents a statistical test outcome.

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| result_id | integer | Yes | Unique result identifier | PK, ≥1 |
| test_type | string | Yes | Test name (e.g., "Kruskal-Wallis", "LMM") | Enum |
| predictor | string | Yes | Predictor variable name | Not empty |
| p_value | float | Yes | Raw p-value | 0 ≤ p ≤ 1 |
| adjusted_p_value | float | Yes | Holm-Bonferroni adjusted p-value | 0 ≤ p ≤ 1 |
| effect_size | float | Yes | Effect size metric | Varies by test |
| ci_lower | float | Yes | Confidence interval lower bound | Numeric |
| ci_upper | float | Yes | Confidence interval upper bound | Numeric |
| vif | float | No | Variance inflation factor | Flag if ≥5 (FR-006) |
| sensitivity_cutoff | float | No | Alpha cutoff for sensitivity analysis | ∈ {0.01, 0.05, 0.1} |

**Validation Rules**:
- `0 <= p_value <= 1` and `0 <= adjusted_p_value <= 1`
- `ci_lower <= ci_upper`
- `test_type` must match expected enum values

## File Formats

### Raw Data (data/raw/)

| File | Format | Checksum | Description |
|------|--------|----------|-------------|
| `issues_raw_{repo_id}.json` | JSON | SHA-256 | Raw API response per repository |
| `repositories_raw.json` | JSON | SHA-256 | Repository metadata |

### Processed Data (data/processed/)

| File | Format | Checksum | Description |
|------|--------|----------|-------------|
| `issues_clean.parquet` | Parquet | SHA-256 | Cleaned, analysis-ready issues |
| `repositories_clean.parquet` | Parquet | SHA-256 | Cleaned repository metadata |
| `analysis_results.parquet` | Parquet | SHA-256 | All statistical test results |

### Figures (data/figures/)

| File | Format | Description |
|------|--------|-------------|
| `ecdf_resolution_time.png` | PNG | ECDF plot with log scale |
| `distribution_fit_comparison.png` | PNG | Log-normal vs Weibull fit |
| `vif_heatmap.png` | PNG | Predictor collinearity heatmap |
| `loo_cv_performance.png` | PNG | LOO-CV MAE and R² across folds |

## Data Flow

```
GitHub API (REST)
    │
    ▼ (FR-001)
data/raw/issues_raw_{repo_id}.json (checksummed)
    │
    ▼ (FR-002, FR-003)
data/processed/issues_clean.parquet
    │
    ├──────────────────────────────────────┐
    ▼ (Phase 2)                           ▼ (Phase 3)
data/figures/ecdf_*.png              data/processed/analysis_results.parquet
    │                                   │
    └───────────────────────────────────┘
                ▼ (Phase 4)
    data/figures/vif_*.png, loo_cv_*.png
```

## Constraints & Validation

- **SC-001**: Dataset completeness ≥95% (all required columns populated)
- **SC-002**: KS test p-value reported for at least one parametric family
- **SC-003**: Significant associations only when adjusted p<0.05
- **SC-004**: LOO-CV MAE and R² reported with standard deviation
- **SC-005**: Runtime ≤6h, memory ≤7GB, no GPU usage
- **Power**: ≥10 issues per repository required for mixed-effects modeling