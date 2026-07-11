# Data Model: llmXive Follow-up: Logical Dependency vs. Semantic Curvature in Many-Shot ICL

## Overview
This document defines the data structures used in the `001-logical-dependency-icl` feature. It ensures consistency between the parser, prompt generator, inference engine, and analysis modules.

## Entities

### 1. CoT Trace
Raw input from the dataset.
- **Fields**: `id` (str), `problem` (str), `cot_trace` (str), `source` (str), `split` (enum: "gold", "train", "test").

### 2. DAG Node
Atomic step in the reasoning process.
- **Fields**: `node_id` (int), `text` (str), `step_type` (enum: "premise", "derivation", "conclusion", "unknown").

### 3. DAG Edge
Dependency relationship between nodes.
- **Fields**: `source_node_id` (int), `target_node_id` (int), `relation_type` (str).

### 4. Logical Difficulty Score
Computed metric for a trace.
- **Fields**: `trace_id` (str), `max_depth` (int), `node_count` (int), `is_valid` (bool), `error_msg` (str, optional).

### 5. Gold Standard Annotation
Human-annotated complexity for validation (FR-007).
- **Fields**: `trace_id` (str), `expert_id` (str), `complexity_rating` (int: 1-5), `comments` (str).
- **Storage**: `data/processed/gold_standard_annotations.json`.

### 6. Prompt Configuration
A generated prompt for a specific seed and strategy.
- **Fields**: `prompt_id` (str), `strategy` (enum), `seed` (int), `examples` (list of `CoT Trace`), `target_question` (str).

### 7. Inference Result
Output from the model.
- **Fields**: `prompt_id` (str), `model_id` (str), `accuracy` (bool), `latency_ms` (float), `timestamp` (datetime).

## Data Flow

1. **Raw Data** (`data/raw/`) → **Parser** (`src/parser.py`) → **DAG Manifest** (`data/processed/dags.json`).
2. **DAG Manifest** + **Config** → **Prompt Generator** (`src/prompt_gen.py`) → **Prompts** (`data/processed/prompts/`).
3. **Prompts** + **Models** → **Inference Runner** (`src/inference.py`) → **Results** (`data/results/inference_log.csv`).
4. **Results** → **Analyzer** (`src/analysis.py`) → **Stats Report** (`data/results/stats_report.json`).

## Validation Rules

- **DAG Validity**: Must be acyclic. Max depth ≥ 1.
- **Prompt Integrity**: Must contain exactly 64 examples.
- **Inference**: `accuracy` must be 0 or 1.
- **Seeds**: Must be integers in range [0, 9].
- **Gold Standard**: Must have at least 2 expert ratings per trace.

## File Formats

- **Input**: JSONL (from HuggingFace).
- **Intermediate**: JSON (DAGs), JSONL (Prompts), JSON (Gold Standard).
- **Output**: CSV (Inference logs), JSON (Stats).
