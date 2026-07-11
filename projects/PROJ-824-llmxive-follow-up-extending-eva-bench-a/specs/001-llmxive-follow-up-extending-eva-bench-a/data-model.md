# Data Model: llmXive follow-up: extending "EVA-Bench: A New End-to-end Framework for Evaluating Voice Agents"

## 1. Overview

This document defines the data structures for the latency injection study. The data flow is:
`Raw EVA-Bench` -> `Injected Audio` -> `Evaluation Results` -> `Statistical Models`.

## 2. Entities

### 2.1 LatencyCondition
Represents a specific experimental condition.
-   `condition_id`: Unique string (e.g., `latency_800ms`).
-   `delay_ms`: Integer (200, 400, ..., 2000).
-   `jitter_profile`: String (e.g., "none", "uniform_50ms").

### 2.2 Scenario
Represents a single EVA-Bench test case.
-   `scenario_id`: String (from EVA-Bench JSONL).
-   `original_audio_path`: Path to raw audio.
-   `processed_audio_path`: Path to injected audio.
-   `metadata`: JSON object (topic, difficulty, etc.).

### 2.3 EvaluationMetric
The score generated for a specific Scenario under a specific Condition.
-   `scenario_id`: FK to Scenario.
-   `condition_id`: FK to LatencyCondition.
-   `metric_name`: String ("Turn-Taking", "Conversation Progression").
-   `score`: Float (0.0 - 1.0).
-   `timestamp`: ISO8601.

### 2.4 DegradationCurve
A derived entity summarizing the relationship.
-   `metric_name`: String.
-   `condition_type`: String ("latency", "acoustic").
-   `data_points`: List of `{delay, score}`.
-   `model_params`: JSON (breakpoint, slopes).
-   `auc`: Float.

## 3. File Formats

### 3.1 Input: EVA-Bench JSONL
Standard JSONL format from the dataset source.
```json
{"id": "scenario_001", "audio": "path/to/audio.wav", "turns": [...], "ground_truth": "..."}
```

### 3.2 Output: Results CSV
Aggregated scores for analysis.
```csv
scenario_id,latency_ms,turn_taking_score,conversation_progression_score,timestamp
scenario_001,200,0.95,0.92,2026-07-12T10:00:00Z
scenario_001,400,0.94,0.91,2026-07-12T10:00:05Z
...
```

### 3.3 Output: Model Parameters JSON
```json
{
  "metric": "Conversation Progression",
  "breakpoint_ms": 850,
  "slope_pre": -0.0001,
  "slope_post": -0.005,
  "r_squared": 0.89,
  "p_value": 0.002
}
```

## 4. Data Hygiene Rules

-   **Immutability**: Raw EVA-Bench files in `data/raw/` are never modified.
-   **Derivation**: Processed audio files in `data/processed/` are named with a hash of the source + parameters.
-   **Checksums**: All files in `data/` must have a corresponding entry in `checksums.json`.
-   **PII**: No PII is stored. Scenario IDs are anonymized if necessary.
