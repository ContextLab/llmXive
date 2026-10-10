# Data Model: Evaluating the Impact of Code Generation on Code Review Quality with LLM Assistance

## Overview

This document defines the data structures used throughout the pipeline: extraction, inference, alignment, and reporting. All data is stored in JSON/Parquet with strict schema validation against `specs/001-eval-llm-review-quality/contracts/`.

## Core Entities

### 1. PullRequest (Raw & Processed) — defined in `src/extraction/schema.py`
Represents a single GitHub PR, extracted via the GitHub API.

```yaml
pr_id: string       # Unique identifier (e.g., "repo_name#12345")
repo_name: string   # Repository name
diff_text: string   # Full (possibly truncated) git diff content
human_review_comments: list[object]
  - comment_id: string
  - author: string
  - body: string
  - line_start: integer
  - line_end: integer
  - is_bug_report: boolean  # Rubric/keyword flag
linked_issue_ids: list[string] # Empty list if none (never null)
reviewer_count: integer # Count of unique comment authors
is_llm_generated: boolean # Flag indicating LLM‑generated code (detectgpt + metadata)
status: string # "processed", "timeout", "error"
ground_truth_status: string # "verified", "unverified", "potential"
```

### 2. BugDetection — defined in `src/detection/schema.py` (T006′)
Represents a bug reported by either Human or LLM.

```yaml
bug_id: string        # e.g., "pr_id_source_line"
source: string        # "human" or "llm"
file_path: string     # Relative path in repo
line_start: integer   # Start line (>= 1)
line_end: integer     # End line (>= 1)
severity: string      # "critical", "major", "minor", "style"
description: string   # Natural language description of the bug
confidence: float     # Optional (0.0-1.0)
is_llm_only: boolean  # True if not matched to any human bug (FR‑017)
```

### 3. AlignmentResult
Represents the match between an LLM bug and a Human bug.

```yaml
llm_bug_id: string
human_bug_id: string
match_score: float    # Cosine similarity of descriptions
location_overlap: float # Jaccard index of line sets (with tolerance)
is_valid_match: boolean # match_score >= threshold AND overlap >= 0.5
match_type: string    # "exact", "fuzzy", "none"
line_shift_tolerance: integer # e.g., 5
```

### 4. AnalysisMetrics
Aggregated results for a specific similarity threshold.

```yaml
threshold: float      # 0.80, 0.85, or 0.90
precision: float
recall: float
f1_score: float
llm_only_recall: float # Proportion of LLM‑only detections confirmed in the manual validation set (or reported as 0 when no manual set)
mcnemar_p_value: float
chi_square_p_value: float
chi_square_statistic: float
effect_size: float    # e.g., Cramér’s V
total_runtime_seconds: integer # Total wall‑clock time of the pipeline (SC‑004)
sensitivity_to_noise: object
  high_confidence_p_value: float
  full_set_p_value: float
```

### 5. RunLogEvent (new, T004′)
One JSON line written by `src/pipeline/logging_utils.py` to `logs/pipeline.jsonl` and `logs/timeout.log`.

```yaml
timestamp: string     # ISO‑8601 UTC timestamp
event: string         # Event type (e.g., "timeout", "pr_skipped", "retry", "pr_processed", "seed_used")
pr_id: string         # Optional PR identifier
status: string        # Outcome status (e.g., "ok", "timeout", "error")
detail: string        # Optional human‑readable detail
```

## Data Flow

1. **Input:** `data/raw/` JSON payloads from GitHub API (raw) + optional HF parquet cache.  
2. **Extraction:** `data/derived/prs_cleaned.json` (validated vs `contracts/pr_schema.schema.yaml`).  
3. **Annotation:** `data/annotations/human_annotations.json`.  
4. **LLM‑Generated Flag:** `data/derived/llm_code_flags.json`.  
5. **Inference:** `data/derived/llm_bugs.json` (validated vs `contracts/bug_detection_schema.schema.yaml`).  
6. **Alignment:** `data/derived/alignments.json` (validated vs `contracts/alignment_result_schema.schema.yaml`).  
7. **Aggregation:** `data/derived/metrics_threshold_{X}.json` (validated vs `contracts/analysis_metrics_schema.schema.yaml`).  
8. **Runtime Record:** `data/results/runtime.json` (contains `total_runtime_seconds`).  
9. **Output:** `data/results/final_report.json` (aggregated metrics, runtime, seed provenance, associational framing, limitations).  
10. **Logs:** `logs/pipeline.jsonl`, `logs/timeout.log` (each line conforms to `run_log_event_schema.schema.yaml`).

## Validation Rules

- **Severity:** Must be one of `["critical", "major", "minor", "style"]`.  
- **Lines:** `line_start`, `line_end` ≥ 1 and `line_start ≤ line_end`.  
- **Thresholds:** Must be one of `{0.80, 0.85, 0.90}` for sensitivity analysis.  
- **Ground Truth:** A bug is “verified” only when it meets FR‑011 criteria **or** is part of the manual validation set. Otherwise labeled “unverified” and excluded from primary metrics.  
- **Logs:** Every line in `logs/*.log` and `logs/*.jsonl` must parse as a single JSON object adhering to `run_log_event_schema.schema.yaml`.  

## Notes on Scientific Soundness

- When only triangulated ground truth is available, `precision`, `recall`, and `f1_score` are interpreted as **consistency** measures between LLM and human annotations.  
- When the manual validation set is present, the same fields become true **detection‑performance** metrics against an independent gold standard.  
- `llm_only_recall` quantifies the proportion of LLM‑only detections that are later verified in the manual set, avoiding circularity.  

