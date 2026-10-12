# Data Model: Evaluating the Impact of Code Generation on Code Review Time

## Overview
All data artifacts reside under `data/` and are version‑checked via SHA‑256 checksums recorded in the project state file. Synthetic artifacts are isolated from raw GitHub data per Constitution Principle VI.

## Core Entities

### PullRequest
| Attribute | Type | Description | Source |
|---|---|---|---|
| `pr_id` | string | Unique identifier (`repo#123`) | PR parquet |
| `repo_id` | string | `owner/repo` | PR parquet |
| `author_type` | enum(`human`, `llm`) | Origin of the code | Derived |
| `generation_source` | enum(`generation-from-scratch`, `refactoring`, `null`) | Cohort label for LLM snippets | Generation config |
| `created_at` | datetime | PR creation timestamp | PR parquet |
| `first_comment_at` | datetime | First reviewer comment timestamp | PR parquet (human) **or simulated for LLM** |
| `merge_at` | datetime | PR merge timestamp | PR parquet |
| `review_effort_duration` | float | Seconds from first reviewer comment to merge (synthetic for LLM via simulation) |
| `total_review_duration` | float | Seconds from PR creation to merge |
| `file_size_loc` | integer | Lines of code |
| `complexity_score` | float | Cyclomatic complexity |
| `repo_activity_level` | integer | Number of PRs in the repository (proxy for activity) |
| `ci_build_time` | float | CI build duration in seconds |
| `semantic_similarity` | number (‑1 → 1) | Cosine similarity between snippet embedding and **repository‑level centroid embedding** |
| `source_code` | string | Full code diff (human) or generated snippet (LLM) |
| `primary_language` | string | Detected programming language |
| `commit_message_length` | integer | Length of the commit message (pre‑treatment covariate) |
| `review_effort_duration` | float | Seconds between `first_comment_at` and `merge_at` (primary outcome) |
| `total_review_duration` | float | Seconds between `created_at` and `merge_at` (secondary outcome) |
| `file_size_loc` | integer | **---** |
| **---** | **---** | **---** |

### CodeSnippet
| Attribute | Type | Description |
|---|---|---|
| `snippet_id` | string | UUID |
| `pr_id` | string | Foreign key to `PullRequest` |
| `generation_source` | string | **---** |
| `code_content` | string | Raw code |
| `complexity_metrics` | object |
| `is_valid_syntax` | boolean | |
| `model_version` | string |
| `generation_params` | object |
| `semantic_similarity` | number (‑1 → 1) (optional ) |
| **---** | --- | --- |

### Matched Pair ( — )

| Attribute | Type | Description |
|---|---|---|
| pair_id | string | Unique identifier |
| human_pr_ref | string | Reference |
| llm_pr_ref | string | Reference |
| complex | ... | ... |

*Note: The above * ** * *-