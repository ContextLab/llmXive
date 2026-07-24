# Data Model: Semantic Divergence Diagnostic

## Overview

This document defines the data structures used for input, processing, and output in the Semantic Divergence Diagnostic pipeline. All data is processed in-memory or streamed to disk, adhering to constrained RAM resources.

## Core Entities

### 1. ProblemInstance
Represents a single multimodal reasoning task from the MathVista dataset.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `problem_id` | `str` | Unique identifier for the problem. | MathVista |
| `thinking_prefix` | `str` | The agent's internal thought trace. | MathVista |
| `simulated_failure` | `bool` | Ground truth outcome (True = Failure). | AXPO Simulation |
| `divergence_score` | `float` | Calculated semantic divergence (1 - cosine_sim). | Derived |
| `tool_count` | `int` | Number of tools retrieved by BM25. | Derived |

### 2. ToolDistribution
Represents the set of tools retrieved for a specific problem.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `problem_id` | `str` | Foreign key to ProblemInstance. | Derived |
| `retrieved_tool_descriptions` | `List[str]` | List of tool description strings. | BM25 Retrieval |
| `centroid_embedding` | `List[float]` | Vector average of retrieved tool embeddings. | Derived |

### 3. DivergenceMetric
The final calculated metric for a problem instance.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `problem_id` | `str` | Foreign key. | Derived |
| `cosine_similarity` | `float` | Similarity between thinking and tool centroid. | Derived |
| `semantic_divergence_score` | `float` | `1 - cosine_similarity`. | Derived |

## Data Flow

1. **Input**: `MathVista` (Parquet) + `Tool Mapping` (JSON).
2. **Processing**:
   - Stream `MathVista` -> Filter -> Extract `thinking_prefix`.
   - Load `Tool Mapping` -> Build BM25 Index.
   - Retrieve tools -> Embed tools -> Calculate Centroid.
   - Embed `thinking_prefix` -> Calculate Divergence.
   - Simulate AXPO -> Assign `simulated_failure`.
3. **Output**: `AnalysisResult` (JSON/Parquet) containing all entities.

## Constraints & Validation

- **Missing Data**: If `thinking_prefix` is missing, the record is skipped.
- **Zero Retrieval**: If BM25 returns 0 tools, `centroid_embedding` is a zero vector, and `divergence_score` is 1.0.
- **Sample Size**: Pipeline halts if final N < 30.
- **Memory**: Streaming enabled for dataset loading; embeddings processed in batches.
