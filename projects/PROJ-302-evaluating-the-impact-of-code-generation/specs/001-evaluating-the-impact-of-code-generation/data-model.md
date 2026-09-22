# Data Model: Evaluating the Impact of Code Generation on Code Review Time

## 1. Overview

This document defines the data structures, schemas, and relationships used in the project. All data artifacts are stored in `data/` with checksums. Synthetic data is isolated in `data/synthetic/`.

## 2. Core Entities

### 2.1 PullRequest
Represents a GitHub Pull Request (Human or Synthetic).

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `pr_id` | String | Unique PR identifier (e.g., `repo#123`) | BigQuery / API |
| `repo_id` | String | Repository identifier (e.g., `owner/repo`) | BigQuery / API |
| `author_type` | Enum | `human` or `llm` | Derived |
| `generation_source` | Enum | `generation-from-scratch` or `refactoring` (if `llm`) | Generation Config |
| `created_at` | DateTime | PR creation timestamp | BigQuery / API |
| `first_comment_at` | DateTime | First reviewer comment timestamp | BigQuery / API |
| `merge_at` | DateTime | PR merge timestamp | BigQuery / API |
| `review_latency` | Float | Duration in seconds (`first_comment_at` - `created_at`) | Calculated |
| `file_size_loc` | Integer | Lines of Code | `radon` |
| `complexity_score` | Float | Cyclomatic Complexity | `radon` |
| `workflow_type` | Enum | `ci-enabled` or `no-ci` | Derived |
| `semantic_similarity` | Float | Cosine similarity to human original (Optional, Exploratory) | Embeddings (CodeBERT) |
| `source_code` | String | Raw code content (from BigQuery `diff`) | BigQuery (Mandatory) |

### 2.2 CodeSnippet
Represents the code artifact associated with a PR.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `snippet_id` | String | Unique snippet identifier | Generated |
| `pr_id` | String | Foreign key to `PullRequest` | Link |
| `source_code` | String | Raw code content (Human or LLM generated) | BigQuery / LLM |
| `generation_params` | JSON | Model version, temperature, max_tokens, **intent_prompt** | Generation Config |
| `is_valid_syntax` | Boolean | True if AST parsing succeeds | Validation |

### 2.3 MatchedPair
Represents a statistical unit for analysis.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `pair_id` | String | Unique pair identifier | Generated |
| `human_pr_ref` | String | Reference to Human PR | Matching |
| `llm_pr_ref` | String | Reference to LLM PR | Matching |
| `complexity_diff` | Float | `human.complexity` - `llm.complexity` | Calculated |
| `size_diff` | Float | `human.size` - `llm.size` | Calculated |
| `activity_diff` | Float | `human.activity` - `llm.activity` | Calculated |
| `balance_verified` | Boolean | True if all SMD < 0.1 | Validation |

**Note on Matching Covariates**: `semantic_similarity` is **excluded** from the `MatchedPair` calculation and matching process to avoid "bad control" bias. Matching is performed only on `file_size_loc`, `complexity_score`, `workflow_type`, and `repo_activity`.

## 3. Data Flow

1.  **Raw**: `data/raw/github_prs.parquet` (Streamed from BigQuery, includes `diff` field).
2.  **Processed**: `data/processed/features.parquet` (Extracted features).
3.  **Synthetic**: `data/synthetic/llm_snippets.jsonl` (Generated code + metadata).
4.  **Matched**: `data/processed/matched_pairs.parquet` (Final analysis dataset).
5.  **Reports**: `data/reports/covariate_balance.json`, `data/reports/statistical_results.json`, `data/reports/matching_failure_report.json`, `data/reports/runtime_report.json`.

## 4. Constraints & Rules

- **Immutability**: Raw data files are never modified. Derivations create new files.
- **Checksums**: Every file in `data/` must have a corresponding entry in `state/` with its SHA-256 hash.
- **PII**: No user names or emails are stored; only anonymized IDs.
- **Synthetic Isolation**: Synthetic data must have a `generation_source` tag and be stored in a distinct directory.
- **Semantic Similarity**: Marked as **Optional** and **Exploratory**. Not used for matching.