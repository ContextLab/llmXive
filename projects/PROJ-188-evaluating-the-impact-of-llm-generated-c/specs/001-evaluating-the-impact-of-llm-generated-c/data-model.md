# Data Model: Evaluating the Impact of LLM-Generated Code Explanations

## Overview

This document defines the schema for all data artifacts in the project. It adheres to the "Single Source of Truth" principle. All data files must conform to these schemas.

## Schema Definitions

### 1. Snippet

Raw or curated code snippets used for the study.

| Field | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `snippet_id` | str | Unique identifier for the snippet. | PK, non-null, format `snip_{uuid}` |
| `code` | str | The source code snippet. | non-null |
| `docstring` | str | The original docstring (ground truth). | nullable |
| `complexity_score` | float | Calculated cyclomatic complexity score. | >= 0.0 |
| `complexity` | str | Categorical complexity label. | Enum: ['low', 'medium', 'high'] |

### 2. Response

Individual trial responses from participants.

| Field | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `participant_id` | str | Anonymized participant ID. | non-null, format `part_{uuid}` |
| `condition` | str | Experimental condition. | Enum: ['CodeOnly', 'CodeLLM', 'CodeDoc'] |
| `snippet_id` | str | FK to Snippet. | FK |
| `answer` | bool | The participant's binary answer (correct/incorrect). | non-null |
| `latency_ms` | int | Time to submit in milliseconds. | >= 0 |
| `timestamp` | str | ISO 8601 timestamp. | non-null |

### 3. ParticipantSummary

Aggregated statistics per participant.

| Field | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `participant_id` | str | FK to Participant. | PK |
| `total_responses` | int | Total number of responses for this participant. | >= 0 |
| `missing_count` | int | Count of missing/blank responses for this participant. | >= 0 |
| `avg_latency` | float | Average latency for this participant. | >= 0.0 |

### 4. Analysis Result

Aggregated statistical results from the GLMM and post-hoc tests.

| Field | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `threshold` | float | Significance threshold (e.g., 0.05). | non-null |
| `accuracy_mean` | float | Mean accuracy across conditions. | non-null |
| `latency_mean` | float | Mean latency across conditions. | non-null |
| `p_value_interaction` | float | P-value for condition*complexity interaction. | non-null |

## Data Flow

1. **Raw**: `data/raw/humaneval.csv` (Downloaded) or `data/raw/code_search_net` (Streamed)
2. **Intermediate**:
 * `data/intermediate/snippets_processed.csv` (Complexity added)
 * `data/intermediate/explanations.json` (Generated)
 * `data/intermediate/mock_responses.csv` (Simulated, row-level)
 * `data/intermediate/participant_summary.csv` (Aggregate, includes missing_count)
 * `data/intermediate/cleaned_responses.csv` (Filtered, row-level)
3. **Processed**: `data/processed/results.csv`, `data/processed/final_report.md`