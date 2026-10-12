# Data Model: Evaluating the Impact of Code Generation on Code Review Time

## 1. Overview
All artifacts live under `data/` and are version‑checked via SHA‑256 checksums recorded in the project state file. Synthetic artifacts are isolated from raw GitHub data.

## 2. Core Entities

### 2.1 PullRequest
| Attribute | Type | Description | Source |
|---|---|---|---|
| `pr_id` | string | Unique identifier (`repo#123`) | PR parquet |
| `repo_id` | string | `owner/repo` | PR parquet |
| `author_type` | enum(`human`, `llm`) | Origin of the code | Derived |
| `generation_source` | enum(`generation-from-scratch`, `refactoring`, `null`) | Cohort label for LLM snippets | Generation config |
| `created_at` | datetime | PR creation timestamp | PR parquet |
| `first_comment_at` | datetime | First reviewer comment timestamp | PR parquet |
| `merge_at` | datetime | PR merge timestamp (used for outcome) | PR parquet |
| `review_latency` | float | Seconds between `created_at` and `merge_at` (full review time) | Calculated |
| `file_size_loc` | integer | Lines of code | `radon` |
| `complexity_score` | float | Cyclomatic complexity | `radon` |
| `repo_activity_level` | integer | Number of PRs in the repo (proxy for activity) | Derived |
| `workflow_type` | enum(`ci-visible`, `no-ci`) | CI presence flag | Derived |
| `semantic_similarity` | number (‑1 → 1) | Cosine similarity to original human snippet (exploratory) | CodeBERT embeddings |
| `source_code` | string | Full code diff (human) or generated snippet (LLM) | Raw / synthetic |
| `primary_language` | string | Detected programming language of the PR | `guesslang` or similar |
| `commit_message_length` | integer | Character count of the commit message (pre‑treatment covariate) | Extracted from PR metadata |

### 2.2 CodeSnippet
| Attribute | Type | Description |
|---|---|---|
| `snippet_id` | string | UUID for the snippet |
| `pr_id` | string | Foreign key to `PullRequest` |
| `generation_source` | enum(`human`, `llm`) |
| `code_content` | string |
| `complexity_metrics` | object (`cyclomatic`: float, `lines`: integer) |
| `is_valid_syntax` | boolean |
| `model_version` | string |
| `generation_params` | object (temperature, max_tokens, intent_prompt) |
| `semantic_similarity` | number (‑1 → 1) (optional) |

### 2.3 MatchedPair
| Attribute | Type | Description |
|---|---|---|
| `pair_id` | string |
| `human_pr_ref` | string |
| `llm_pr_ref` | string |
| `complexity_diff` | float |
| `size_diff` | float |
| `activity_diff` | float |
| `balance_verified` | boolean |

## 3. Data Flow
1. **Raw PRs** → `data/raw/*.parquet` (unchanged).  
2. **Feature Extraction** → `data/processed/features.parquet`.  
3. **Synthetic Generation** → `data/synthetic/llm_snippets.jsonl`.  
4. **Matched Pairs** → `data/processed/matched_pairs.parquet`.  
5. **Reports** → `data/reports/` (balance, statistical, visual, runtime, PDF).  

## 4. Constraints & Rules
- **Immutability**: Raw files never overwritten.  
- **Checksums**: Every file has an entry in `state/projects/...yaml`.  
- **PII**: No usernames or emails are stored; only anonymised IDs.  
- **Synthetic Isolation**: All LLM data resides under `data/synthetic/` with full provenance.  
- **Semantic Similarity** is marked *exploratory*; not used for matching (Methodological Override).  

---


