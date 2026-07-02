# Data Model: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

## Entities & Attributes

### 1. Repository (Aggregated Level)
Represents a GitHub project. Used for LLM adoption flagging, control variables, and maturity proxies.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `repo_id` | String | Unique identifier (e.g., `owner/repo`) | GitHub API |
| `llm_adopted` | Boolean | 1 if config/keywords found, 0 otherwise | `code/ingest.py` |
| `lines_of_code` | Integer | Total LOC (snapshot) | GitHub API |
| `contributor_count` | Integer | Number of unique contributors | GitHub API |
| `domain_complexity` | Float | `log10(LOC) + log10(Contributors) + 1` | Derived (Stored only, NOT used in regression) |
| `language_primary` | String | Primary programming language | GitHub API |
| `repo_age_days` | Integer | Days since first commit | GitHub API |
| `repo_stars` | Integer | Number of stars (proxy for maturity/expertise) | GitHub API |
| `repo_fork_count` | Integer | Number of forks (proxy for maturity/expertise) | GitHub API |
| `exclude_from_analysis` | Boolean | True if PR count < 10 | Derived |

### 2. PullRequest (Transaction Level)
Represents a single Pull Request. Used for outcome variables.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `pr_id` | Integer | GitHub PR number | GitHub API |
| `repo_id` | String | Foreign Key to Repository | GitHub API |
| `comment_length_chars` | Integer | Average length of review comments | Derived (from comments) |
| `iteration_count` | Integer | Number of commits in PR | GitHub API |
| `revert_frequency` | Integer | Count of reverts within 7 days | Derived (cross-ref PRs) |
| `merge_date` | DateTime | Timestamp of merge | GitHub API |
| `exclude_from_analysis` | Boolean | Inherited from Repository | Derived |

### 3. AnalysisResult (Output Level)
Represents the output of the statistical model.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `model_type` | String | "LMM" or "Ridge LMM" | `code/analysis.py` |
| `coefficient_llm` | Float | $\beta_1$ for `llm_adopted` | Regression |
| `p_value` | Float | p-value for $\beta_1$ | Regression |
| `ci_lower` | Float | Lower bound of 95% CI | Regression |
| `ci_upper` | Float | Upper bound of 95% CI | Regression |
| `significant_at_0.05` | Boolean | True if p-value < 0.05 (SC-001) | Derived |
| `vif_max` | Float | Max VIF observed | VIF Check |
| `smd_max` | Float | Max Standardized Mean Difference | PSM Check |

### 4. ValidityResult (Output Level)
Represents the output of the construct validity check (FR-007).

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `corr_iteration_loc` | Float | Correlation between iteration_count and lines_of_code | Derived |
| `corr_revert_iteration` | Float | Correlation between revert_frequency and iteration_count | Derived |
| `revert_valid_proxy` | Boolean | True if `corr_revert_iteration` is significant (p < 0.05) | Derived |

## Data Flow

1.  **Ingest**: `GitHub API` -> `data/raw/repo_prs.json` (Raw JSON).
2.  **Preprocess**: `data/raw/repo_prs.json` -> `data/processed/cleaned_prs.csv` (Derived metrics, filtering, Stratified Sampling).
3.  **Validate**: `data/processed/cleaned_prs.csv` -> `results/validity.json` (Construct validity check).
4.  **Analyze**: `data/processed/cleaned_prs.csv` -> `results/regression.json` (LMM outputs).
5.  **Sensitivity**: `data/processed/cleaned_prs.csv` + `params` -> `results/sensitivity.json`.

## Constraints & Rules

- **Non-Null**: `comment_length_chars`, `iteration_count` must be ≥ 0.
- **Exclusion**: Any PR from a repo with `exclude_from_analysis=true` is dropped before regression.
- **Privacy**: No user emails or names stored; only `repo_id` and `pr_id`.
- **Collinearity**: `domain_complexity` is stored but **NOT** used as a predictor in the regression model.
- **Validity**: If `revert_valid_proxy` is False, `revert_frequency` is excluded from the primary regression model.