# Data Model: Evaluating the Impact of Code Generation on Code Review Quality with LLM Assistance

## Overview
This document defines the JSON/Parquet schemas used throughout the pipeline. All files are validated against the contracts in the appropriate evaluation specifications directory (e.g., `specs/*-eval-llm-review-quality/contracts/`).

## Core Entities

### 1. PullRequest (Raw & Processed) – `src/extraction/schema.py`
```yaml
pr_id: string                 # e.g., "repo_name#12345"
repo_name: string
diff_text: string
human_review_comments:
  - comment_id: string
    author: string
    body: string
    line_start: integer      # >= 1
    line_end: integer        # >= 1
    is_bug_report: boolean
linked_issue_ids: [string]    # empty list if none
reviewer_count: integer       # unique comment authors
is_llm_generated: boolean
status: string                # "processed", "timeout", "error"
ground_truth_status: string   # "verified", "unverified", "potential"
```

### 2. BugDetection – `src/detection/schema.py`
```yaml
bug_id: string
source: string                # "human" or "llm"
file_path: string
line_start: integer           # >= 1
line_end: integer             # >= 1
severity: string              # "critical", "major", "minor", "style"
description: string
confidence: number            # optional, 0.0–1.0
is_llm_only: boolean
```

### 3. AlignmentResult
```yaml
llm_bug_id: string
human_bug_id: string
match_score: number           # cosine similarity (0.0–1.0)
location_overlap: number      # Jaccard index of line sets (with tolerance)
is_valid_match: boolean       # match_score >= threshold AND overlap >= 0.5
match_type: string            # "exact", "fuzzy", "none"
line_shift_tolerance: integer # e.g., 5
```

### 4. AnalysisMetrics (per similarity threshold)
```yaml
threshold: number             # 0.80, 0.85, or 0.90
precision: number             # 0.0–1.0
recall: number                # 0.0–1.0
f1_score: number              # 0.0–1.0
llm_only_recall: number       # 0.0–1.0 (0.0 if no manual set)
mcnemar_p_value: number
chi_square_p_value: number
chi_square_statistic: number
effect_size: number           # e.g., Cramér's V
total_runtime_seconds: integer
sensitivity_to_noise:
  high_confidence_p_value: number
  full_set_p_value: number
```

### 5. RunLogEvent – `src/pipeline/logging_utils.py`
```yaml
timestamp: string            # ISO‑8601 UTC timestamp of the event
event: string                # Event type (e.g., 'cli_start', 'timeout', 'pr_skipped', 'retry', 'pr_processed', 'seed_used')
pr_id: string                # Optional PR identifier the event concerns
status: string               # Outcome status (e.g., 'ok', 'timeout', 'error')
detail: string               # Optional human-readable detail
```

## Data Flow
1. **Raw API payloads** → `data/raw/` (validated by `pr_schema`).  
2. **Pre‑processing** → `data/derived/prs_cleaned.json`.  
3. **Human annotation extraction** → `data/annotations/human_annotations.json`.  
4. **LLM‑generated flag** → `data/derived/llm_code_flags.json`.  
5. **LLM inference** → `data/derived/llm_bugs.json`.  
6. **Alignment** → `data/derived/alignments.json`.  
7. **Metrics & stats** → `data/derived/metrics_threshold_{X}.json`.  
8. **Runtime record** → `data/results/runtime.json`.  
9. **Final report** → `data/results/final_report.json`.  
10. **Logs** → `logs/pipeline.jsonl`, `logs/timeout.log` (each line conforms to `run_log_event_schema`).  

## Validation Rules
- **Severity** must be one of `["critical","major","minor","style"]`.  
- **Line numbers** ≥ 1 and `line_start ≤ line_end`.  
- **Threshold** values limited to `{0.80,0.85,0.90}`.  
- **Ground truth**: only bugs meeting FR‑011 criteria are labeled `"verified"`; others are `"unverified"` and excluded from primary metrics.  
- **Log events**: every line in `logs/*.log` must be valid JSON and match `run_log_event_schema`.  

## Scientific Soundness Notes
- When only triangulated ground truth is available, precision/recall/F1 are interpreted as **consistency** measures.  
- When the manual validation set exists, the same fields become true **detection‑performance** metrics.  
- `llm_only_recall` quantifies novel detections without circularity.

---


