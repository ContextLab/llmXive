# Data Model: llmXive follow-up: extending "MemLens"

## 1. Overview
This document defines the data structures used for input (MemLens), intermediate processing (Memory Stores), and output (Evaluation Results). All data is stored in JSON/JSONL or CSV formats for easy inspection and validation.

## 2. Entity Definitions

### 2.1 Query (Input)
Represents a single reasoning task from the MemLens dataset.
- **`query_id`**: Unique identifier for the query.
- **`query_text`**: The natural language question.
- **`ground_truth`**: The correct answer string.
- **`task_type`**: Classification (e.g., "Multi-Session Reasoning", "Temporal Reasoning").
- **`session_ids`**: List of session IDs referenced by the query.
- **`image_paths`**: List of relative paths to images in the session.

### 2.2 MemoryStore (Intermediate)
A collection of context chunks for a specific granularity level.
- **`store_id`**: Unique ID (e.g., `session_1_coarse`, `session_1_fine`).
- **`granularity`**: One of `coarse`, `medium`, `fine`.
- **`chunks`**: List of context objects.
  - **`chunk_id`**: Unique ID.
  - **`content`**: The text content (summary, caption, or combined).
  - **`embedding`**: Float array (optional, stored separately in FAISS index).
  - **`metadata`**: Object containing source info (e.g., `{"type": "object", "label": "cat", "bbox": [x,y,w,h]}`).

### 2.3 EvaluationResult (Output)
A single record of the system's performance on a query for a specific store.
- **`query_id`**: Reference to the input query.
- **`store_granularity`**: The strategy used (`coarse`, `medium`, `fine`).
- **`generated_answer`**: The LLM's output string.
- **`exact_match`**: Boolean (1 if generated == ground truth, else 0).
- **`semantic_similarity`**: Float (0.0 to 1.0).
- **`retrieval_latency_ms`**: Time to fetch context.
- **`generation_latency_ms`**: Time to generate answer.
- **`peak_ram_mb`**: Peak memory usage during this step.

## 3. Data Flow
1.  **Raw Data** (`data/raw/memlens.json`) -> **Filtered Data** (`data/processed/filtered_queries.json`).
2.  **Filtered Data** -> **Memory Stores** (`data/processed/stores/{granularity}/`).
3.  **Memory Stores** + **Filtered Data** -> **Evaluation Results** (`outputs/results.csv`).

## 4. Constraints
- **Read-Only**: Raw data files are never modified.
- **Checksums**: All files in `data/` must have a corresponding hash in `state/`.
- **Schema Validation**: All output files must conform to `contracts/evaluation_result.schema.yaml`. Intermediate Fine Store outputs must conform to `contracts/fine_store_output.schema.yaml`.