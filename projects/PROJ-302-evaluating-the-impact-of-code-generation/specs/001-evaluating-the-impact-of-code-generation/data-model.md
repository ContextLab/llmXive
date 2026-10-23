# Data Model: Evaluating the Impact of Code Generation on Code Review Time

## Overview
All artifacts live under `data/` and are immutable once written. Checksums (SHA‑256) are recorded in the project state file to guarantee reproducibility (Constitution I). Synthetic data are isolated in `data/synthetic/` (Constitution VI).

## Core Entities

### PullRequest
| Attribute | Type | Description | Source |
|---|---|---|---|
| `pr_id` | string | Unique PR identifier (`repo#123`) | PR parquet |
| `repo_id` | string | Repository identifier (`owner/repo`) | PR parquet |
| `author_type` | enum(`human`, `llm`) | Origin of the code | Derived |
| `generation_source` | enum(`generation-from-scratch`, `refactoring`, `null`) | Cohort label for LLM snippets | Generation config |
| `created_at` | datetime | PR creation timestamp | PR parquet |
| `first_comment_at` | datetime | First reviewer comment timestamp (human) **or** observed timestamp from evaluation PR (LLM) | PR parquet / evaluation PR |
| `merge_at` | datetime | PR merge timestamp (used for outcome) | PR parquet |
| `review_effort_duration` | number | Seconds from `first_comment_at` to `merge_at` (primary outcome) | Direct / observed from evaluation PR |
| `total_review_duration` | number | Seconds from `created_at` to `merge_at` (secondary outcome) | Direct |
| `file_size_loc` | integer | Lines of code (computed from `diff`) | Feature extraction |
| `complexity_score` | number | Cyclomatic complexity (radon) | Feature extraction |
| `repo_activity_level` | integer | Number of PRs in the repository (proxy for activity) | Aggregated per repo |
| `ci_build_time` | number | CI build duration in seconds | PR parquet |
| `semantic_similarity` | number (‑1 → 1) | Cosine similarity between snippet embedding and **repository‑level centroid embedding** | Feature extraction |
| `source_code` | string | Full code diff (human) or generated snippet (LLM) | Raw / synthetic |
| `primary_language` | string | Detected programming language (e.g., `python`) | Feature extraction |
| `commit_message_length` | integer | Length (characters) of the commit message | Prompt engineering |
| `evaluation_pr_url` | string | URL of the pull request opened in the sandbox evaluation repository (for LLM snippets) | Evaluation repo module |

### CodeSnippet
| Attribute | Type | Description |
|---|---|---|
| `snippet_id` | string | UUID for the snippet |
| `pr_id` | string | Foreign key to the associated PullRequest |
| `generation_source` | enum(`human`, `llm`) | Origin |
| `code_content` | string | Raw code text |
| `complexity_metrics` | object | `{ "cyclomatic": number, "lines": number }` |
| `is_valid_syntax` | boolean | Result of AST parsing |
| `model_version` | string | CodeLlama model identifier (`CodeLlama-7B-4bit-GGUF`) |
| `generation_params` | object | Parameters **t** = `{ temperature : 0.7, max_tokens : 512, intent_prompt : … }` (example) |
| `semantic_similarity` | number (‑1 → 1) | Cosine similarity to repo centroid (optional) |
| `evaluation_pr_url` **(optional)** | string | URL of the evaluation PR for this snippet (if LLM‑generated) |

### MatchedPair
| Attribute | Type | Description |
|---|---|---|
| `pair_id` | string | Unique identifier |
| `human_pr_ref` | string | `pr_id` of the human PR |
| `llm_pr_ref` | string | `pr_id` of the LLM PR (prompt‑only or context‑based) |
| `complexity_diff` | number | Human – LLM cyclomatic complexity |
| `size_diff` | number | Human – LLM LOC |
| `activity_diff` | number | Human – LLM repository activity |
| `ci_build_diff` | number | Human – LLM CI build time |
| `semantic_similarity_diff` | number | Human – LLM semantic similarity |
| `balance_verified` | boolean | True if this pair satisfied the covariate balance criteria |

## File Layout
| Path | Description |
|---|---|
| `data/raw/` | Immutable API‑downloaded PR parquet files |
| `data/processed/` | `features.parquet`, `merged_features.parquet`, `matched_pairs.parquet` |
| `data/synthetic/` | Generated snippets + provenance JSONL, predicted outcomes |
| `data/reports/` | PDFs, PNGs, JSON summaries, runtime_report.json |
| `data/evaluation/` | Pull request URLs and timestamp logs for LLM evaluation PRs |

All files are versioned via SHA‑256 checksums recorded in `state/projects/PROJ-302-evaluating-the-impact-of-code-generation.yaml`.

---

