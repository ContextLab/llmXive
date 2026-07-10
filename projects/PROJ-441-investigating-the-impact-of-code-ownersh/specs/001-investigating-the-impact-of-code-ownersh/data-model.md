# Data Model: Investigating the Impact of Code Ownership on LLM Code Understanding

## 1. Entity Definitions

### RepositorySnapshot
Represents a specific version of a code repository.
- `repo_url` (string): Canonical URL of the repository.
- `git_history_hash` (string): SHA256 hash of the git log state used.
- `language` (string): Primary language (e.g., "Python", "Java").
- `status` (string): "active", "excluded", "error".
- `target_commit_sha` (string): The specific commit SHA used for temporal alignment.

### OwnershipMetrics
Derived from git history up to `target_commit_sha`.
- `repo_url` (string): Foreign key to RepositorySnapshot.
- `gini_coefficient` (float): Calculated LOC-weighted Gini coefficient (0.0 to 1.0).
- `developer_count` (int): Number of unique authors.
- `max_author_share` (float): Proportion of LOC by the top author (0.0 to 1.0).
- `window_size` (int): Number of commits considered (e.g., 100, 500).
- `target_commit_sha` (string): The commit up to which history was analyzed.

### CodeSnippet
Unit of analysis for complexity and inference.
- `snippet_id` (string): Unique identifier.
- `repo_url` (string): Foreign key.
- `file_path` (string): Path within the repo.
- `cyclomatic_complexity` (int): CC score from `radon`.
- `documentation_density` (float): Ratio of comment lines to total lines.
- `ground_truth_pair` (object): `{input_code: string, expected_output: string}`.
- `target_commit_sha` (string): The commit associated with this snippet.

### PerformanceScore
Result of LLM inference.
- `snippet_id` (string): Foreign key.
- `model_id` (string): e.g., "starcoder2-3b-cpu-4bit".
- `score` (float): BLEU score (normalized or raw).
- `logit_score` (float): Logit-transformed BLEU score for regression.
- `ground_truth` (string): The reference text.
- `status` (string): "success", "failed", "timeout".

## 2. Data Flow

1.  **Raw Data**: Git logs, CodeXGLUE samples.
2.  **Processed**: JSON files containing `OwnershipMetrics` and `CodeSnippet` attributes.
3.  **Derived**: `PerformanceScore` JSON.
4.  **Aggregated**: Snippet-level data for LMM (Repository as random effect).
5.  **Final**: Regression table and sensitivity plots.

## 3. Validation Rules

- `gini_coefficient`: Must be in range [0.0, 1.0].
- `documentation_density`: Must be in range [0.0, 1.0].
- `score` (BLEU): Must be in range [0.0, 100.0].
- `logit_score`: Must be finite (exclude 0 or 100 if logit undefined).
- `status`: Must be one of ["success", "failed", "timeout", "excluded"].
- `target_commit_sha`: Must match a valid commit in the repo history.