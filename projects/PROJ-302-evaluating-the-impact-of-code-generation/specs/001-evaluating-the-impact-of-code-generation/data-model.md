# Data Model: Evaluating the Impact of Code Generation on Code Review Time

## Overview

This document defines the data model for the project, including entities, attributes, relationships, and transformations. It ensures alignment with the specification and supports reproducibility.

## Entities

### 1. PullRequest

Represents a GitHub PR with metadata and review metrics.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `pr_id` | str | Unique PR identifier (e.g., `repo#123`) | GitHub API |
| `repo_id` | str | Repository identifier (e.g., `owner/repo`) | GitHub API |
| `author_type` | str | `human` (all PRs in this study are human-written) | Derived (Classification) |
| `llm_style_score` | float | Probability of "LLM-like" style (0-1) | Derived (Classifier) |
| `created_at` | datetime | PR creation timestamp | GitHub API |
| `first_comment_at` | datetime | First reviewer comment timestamp | GitHub API |
| `review_latency` | float | Duration (hours) from `created_at` to `first_comment_at` | Derived |
| `file_size` | int | Lines of code (LOC) | Derived (radon) |
| `complexity_score` | float | Cyclomatic complexity | Derived (radon) |
| `repo_stars` | int | Repository star count | GitHub API |
| `repo_pr_count` | int | Total PRs in repository | GitHub API |

### 2. CodeSnippet

Represents a code artifact (human-written, classified by style).

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `snippet_id` | str | Unique snippet identifier | Generated |
| `source_commit` | str | Original commit hash | GitHub API |
| `generation_source` | str | `human` (always) | Config |
| `code_content` | str | Code text | GitHub API |
| `complexity_metrics` | dict | `{'cyclomatic': float, 'lines': int, ...}` | Derived (radon) |
| `llm_style_score` | float | Probability of "LLM-like" style | Derived (Classifier) |
| `model_version` | str | Classifier version (e.g., `codebert-base`) | Config |

### 3. MatchedPair

Represents a statistical unit (Human-LLM-like pair after matching).

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `pair_id` | str | Unique pair identifier | Generated |
| `human_pr_ref` | str | Reference to "Human-typical" PR | Matched |
| `llm_like_pr_ref` | str | Reference to "LLM-like" PR | Matched |
| `complexity_diff` | float | `human_complexity - llm_complexity` | Derived |
| `size_diff` | float | `human_size - llm_size` | Derived |
| `activity_diff` | float | `human_activity - llm_activity` | Derived |
| `balance_verified` | bool | `True` if all SMD < 0.1 | Validation |

## Transformations

### 1. Raw Data → Processed Features

- **Input**: GitHub API metadata (Parquet).
- **Output**: `data/processed/features.parquet`.
- **Steps**:
  1. Fetch raw file content via GitHub API for sampled PRs.
  2. Extract `created_at`, `first_comment_at` → compute `review_latency`.
  3. Compute LOC and complexity via `radon`.
  4. Fetch repository stars/PR count via GitHub API.

### 2. Feature Extraction → Style Classification

- **Input**: `data/processed/features.parquet` (subset).
- **Output**: `data/processed/classified_snippets.parquet`.
- **Steps**:
  1. Run `codebert-base` classifier on code content.
  2. Assign "LLM-like" or "Human-typical" label based on threshold.
  3. Log classifier version.

### 3. Matching → Statistical Analysis

- **Input**: `data/processed/classified_snippets.parquet`.
- **Output**: `data/processed/matched_pairs.parquet`.
- **Steps**:
  1. Compute propensity scores (logistic regression) on LOC, complexity, activity.
  2. Perform 1:1 nearest neighbor matching.
  3. Verify covariate balance (SMD < 0.1).
  4. Compute review latency differences.

### 4. Analysis → Visualization

- **Input**: `data/processed/matched_pairs.parquet`.
- **Output**: `data/processed/visualizations/` (box plots, CDFs).
- **Steps**:
  1. Stratify by star quartiles.
  2. Run statistical tests (t-test / Mann-Whitney).
  3. Generate plots (matplotlib/seaborn).

## Data Hygiene

- **Raw Data**: Preserved unchanged in `data/raw/`.
- **Derived Data**: New files with checksums (e.g., `features_v1.parquet`).
- **Checksums**: Recorded in `data/checksums.yaml`.

## Schema Validation

- All data files validated against `contracts/` schemas (see `contracts/`).
- Invalid rows excluded with logging.