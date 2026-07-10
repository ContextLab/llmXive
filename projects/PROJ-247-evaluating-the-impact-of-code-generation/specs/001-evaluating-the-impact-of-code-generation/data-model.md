# Data Model: Evaluating the Impact of Code Generation on Long-Term Code Maintainability

## Overview
This document defines the data structures used throughout the project. All data is stored in `data/` directory. Raw data is immutable; derived data is versioned.

## Entities

### 1. Repository
Represents a GitHub repository.
- `repo_id`: Unique identifier (owner/repo).
- `language`: Primary language (Python/JavaScript).
- `stars`: Star count (int).
- `created_at`: ISO8601 timestamp.
- `updated_at`: ISO8601 timestamp.
- `is_active`: Boolean (≥1 commit in 90 days).
- `total_loc`: Total lines of code in the repository (int). **Added to satisfy FR-008.**

### 2. CodeBlock
Represents a function or class within a repository.
- `block_id`: Unique identifier (repo_id + file_path + start_line + end_line).
- `origin_label`: "LLM" or "Human".
- `confidence`: Float (0.0 - 1.0) from CodeBERT.
- `complexity`: Cyclomatic complexity (int).
- `nesting_depth`: Max nesting depth (int).
- `loc`: Lines of code (int).
- `introduction_commit`: Commit hash.
- `introduction_timestamp`: ISO8601 timestamp.

### 3. MatchedPair
Result of propensity score matching.
- `pair_id`: Unique identifier.
- `llm_block_id`: Reference to LLM code block.
- `human_block_id`: Reference to Human code block.
- `propensity_score`: Float (score used for matching).
- `repo_id`: Parent repository.
- `repo_stars`: Star count (covariate).
- `repo_total_loc`: Total lines of code in the repo (covariate).

### 4. MaintenanceEvent
Record of code modification or bug fix.
- `event_id`: Unique identifier.
- `block_id`: Reference to CodeBlock.
- `event_type`: "churn" or "bug_fix".
- `timestamp`: ISO8601 timestamp.
- `lines_added`: Int.
- `lines_deleted`: Int.
- `issue_number`: Int (for bug_fix, linked via "Fixes #N").
- `latency_days`: Float (calculated for bug_fix).

### 5. GroundTruth
Manual verification labels.
- `block_id`: Reference to CodeBlock.
- `manual_label`: "LLM" or "Human".
- `verifier_id`: Identifier of human expert.

## Data Flow

1.  **Raw Data**: `data/raw/repos.json`, `data/raw/git_logs/`, `data/raw/issues.json`.
2.  **Processed Data**:
    - `data/processed/tagged_blocks.csv` (Block-level metrics + labels).
    - `data/processed/matched_pairs.csv` (FR-008 output).
    - `data/processed/metrics.csv` (Churn and Latency).
3.  **Analysis Data**: `data/analysis/results.json` (Test statistics, p-values).

## Constraints

- **Immutability**: Raw data files are never modified. Derivations create new files.
- **Checksums**: All files in `data/` must have a corresponding checksum in `state/`.
- **PII**: No user emails or personal names are stored in `data/`.