# Data Model: Evaluating the Impact of Code Generation on Code Review Quality with LLM Assistance

## Overview
This document defines the data structures used throughout the pipeline: extraction, inference, alignment, and reporting. All data is stored in JSON/Parquet formats with strict schema validation.

## Core Entities

### 1. PullRequest (Raw & Processed)
Represents a single GitHub PR extracted from the dataset.

```yaml
pr_id: string       # Unique identifier (e.g., "repo_name#12345")
repo_name: string   # Repository name (e.g., "microsoft/vscode")
diff_text: string   # The full git diff content
human_review_comments: list[object]
  - comment_id: string
  - author: string
  - body: string
  - line_start: integer
  - line_end: integer
  - is_bug_report: boolean  # Flagged if human explicitly mentions a bug
linked_issue_ids: list[string] # Empty list if none
reviewer_count: integer # Count of unique authors in human_review_comments
is_llm_generated: boolean # Flagged via heuristic detection (FR-016)
status: string # "processed", "timeout", "error"
ground_truth_status: string # "verified", "unverified", "potential"
```

### 2. BugDetection
Represents a bug reported by either Human or LLM.

```yaml
bug_id: string        # Unique ID (e.g., "pr_id_source_line")
source: string        # "human" or "llm"
file_path: string     # Relative path in repo
line_start: integer   # Start line of the bug
line_end: integer     # End line of the bug
severity: string      # "critical", "major", "minor", "style"
description: string   # Natural language description of the bug
confidence: float     # (Optional) Model confidence score
is_llm_only: boolean  # True if not matched to any human bug
```

### 3. AlignmentResult
Represents the match between an LLM bug and a Human bug.

```yaml
llm_bug_id: string
human_bug_id: string
match_score: float    # Cosine similarity of descriptions
location_overlap: float # Jaccard index of line sets (with tolerance)
is_valid_match: boolean # True if match_score >= threshold AND overlap >= 0.5
match_type: string    # "exact", "fuzzy", "none"
line_shift_tolerance: integer # The tolerance used (e.g., 5)
```

### 4. AnalysisMetrics
Aggregated results for a specific threshold.

```yaml
threshold: float      # The similarity threshold used (0.80, 0.85, 0.90)
precision: float
recall: float
f1_score: float
llm_only_recall: float # Recall of bugs found ONLY by LLM (FR-017)
mcnemar_p_value: float
chi_square_p_value: float
chi_square_statistic: float
effect_size: float
sensitivity_to_noise: object # Results from high-confidence vs full-set analysis
```

## Data Flow

1. **Input:** `data/raw/prs.parquet` (from HF)
2. **Extraction:** `data/derived/prs_cleaned.json` (Validated PRs)
3. **Annotation:** `data/annotations/human_annotations.json` (Rubric-based labels)
4. **LLM Detection:** `data/derived/llm_code_flags.json` (FR-016)
5. **Inference:** `data/derived/llm_bugs.json` (LLM predictions)
6. **Alignment:** `data/derived/alignments.json` (Matched pairs)
7. **Aggregation:** `data/derived/metrics_threshold_{X}.json` (Results)
8. **Output:** `results/final_report.json` (Consolidated stats)

## Validation Rules

- **Severity:** Must be one of `["critical", "major", "minor", "style"]`.
- **Lines:** `line_start` and `line_end` must be integers ≥ 1.
- **Thresholds:** Must be in `{0.80, 0.85, 0.90}` for sensitivity analysis.
- **Ground Truth:** A bug is only "Ground Truth" if it meets FR-011 criteria (linked issue OR confirmed human comment).