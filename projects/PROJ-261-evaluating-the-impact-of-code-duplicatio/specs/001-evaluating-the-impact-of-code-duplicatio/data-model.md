# Data Model: Evaluating the Impact of Code Duplication on LLM Code Understanding

**Branch**: `001-evaluate-code-duplication-llm-understanding` | **Date**: 2026-05-12

## Entity Relationship Diagram

```
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│  CodeSegment    │────▶│  CloneDensityMetric │     │  ModelMetric    │
│                 │     │                     │     │                 │
│ - file_path     │     │ - segment_id        │     │ - segment_id    │
│ - line_start    │     │ - clone_density     │     │ - perplexity    │
│ - line_end      │     │ - threshold         │     │ - log_probs     │
│ - ast_hash      │     │ - duplicate_count   │     │ - bug_detected  │
│ - content_hash  │     │ - total_subtrees    │     │ - pass@1        │
└─────────────────┘     └─────────────────────┘     └─────────────────┘
         │                                                   │
         └───────────────────────┬───────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   CorrelationResult     │
                    │                         │
                    │ - metric_pair           │
                    │ - spearman_coefficient  │
                    │ - p_value               │
                    │ - sample_size           │
                    │ - significance          │
                    └─────────────────────────┘
```

## Data Files

### Raw Data (immutable)

| File | Location | Format | Checksum |
|------|----------|--------|----------|
| github-code-sample | `data/raw/github-code-sample.csv` | CSV | SHA-256 recorded in state manifest |

### Processed Data (derived)

| File | Location | Format | Derivation |
|------|----------|--------|------------|
| clone_metrics | `data/processed/clone_metrics.csv` | CSV | AST subtree matching on raw data |
| perplexity_scores | `data/processed/perplexity_scores.csv` | CSV | Model inference on code segments |
| bug_detection_results | `data/processed/bug_detection_results.csv` | CSV | HumanEval evaluation |

### Analysis Output (final)

| File | Location | Format | Purpose |
|------|----------|--------|---------|
| correlation_results | `data/analysis/correlation_results.csv` | CSV | Spearman correlation coefficients |
| figures | `data/analysis/figures/` | PNG | Scatter plots with regression lines |
| parse_failures | `data/processed/parse_failures.csv` | CSV | Files that failed AST parsing |

## Key Entities

### CodeSegment

Represents a discrete unit of Python code (function body).

| Attribute | Type | Description |
|-----------|------|-------------|
| segment_id | string | Unique identifier (file_path + line_start + line_end) |
| file_path | string | Path to source file in dataset |
| line_start | integer | Starting line number (1-indexed) |
| line_end | integer | Ending line number (1-indexed) |
| ast_hash | string | SHA-256 hash of AST representation |
| content_hash | string | SHA-256 hash of raw code content |

### CloneDensityMetric

Represents computed syntactic clone density for a code segment.

| Attribute | Type | Description |
|-----------|------|-------------|
| segment_id | string | Foreign key to CodeSegment |
| clone_density | float | Percentage (0-100) of duplicate subtrees |
| threshold | float | Clone detection threshold used (0.0-1.0) |
| duplicate_count | integer | Number of matching subtrees |
| total_subtrees | integer | Total subtrees analyzed |

### ModelMetric

Represents LLM performance measurement for a code segment.

| Attribute | Type | Description |
|-----------|------|-------------|
| segment_id | string | Foreign key to CodeSegment |
| perplexity | float | Token-level perplexity value |
| log_probs | array | Array of log-probability values per token |
| bug_detected | boolean | Whether bug was detected (HumanEval) |
| pass_1 | boolean | Whether pass@1 test passed |

### CorrelationResult

Represents statistical correlation output.

| Attribute | Type | Description |
|-----------|------|-------------|
| metric_pair | string | Pair of metrics being correlated (e.g., "clone_density,perplexity") |
| spearman_coefficient | float | Spearman's rank correlation coefficient (-1 to 1) |
| p_value | float | Statistical significance (0 to 1) |
| sample_size | integer | Number of data points in correlation |
| significance | boolean | Whether p < 0.05 (True/False) |

## Schema Compliance

All data files MUST conform to the YAML schemas in `specs/001-evaluate-code-duplication-llm-understanding/contracts/`. Contract tests validate schema compliance before data is written to `data/`.
