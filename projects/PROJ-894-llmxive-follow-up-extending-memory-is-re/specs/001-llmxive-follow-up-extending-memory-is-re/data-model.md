# Data Model: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

## Overview

This document defines the data structures used for input (datasets), intermediate processing (graphs), and output (results) for the graph memory traversal study.

## Input Data

### 1. LoCoMo Benchmark Task
**Source**: `Aman279/Locomo` (HuggingFace)  
**Format**: Dataset object (converted to DataFrame)  
**Schema**:
- `task_id`: string (unique identifier)
- `question`: string (the multi-hop query)
- `context`: string (the full context text or list of paragraphs)
- `answer`: string (ground truth answer)
- `metadata`: JSON (optional, e.g., difficulty, source)

### 2. Synthetic Noise Parameters
**Source**: Config file (`config.yaml`)  
**Format**: YAML  
**Schema**:
- `noise_density`: float (fraction of random edges to add, e.g., 0.05)
- `random_seed`: integer (for reproducibility)
- `subgraph_radius`: integer (max hops to consider for noise injection, default 3)

## Intermediate Data

### 3. Memory Graph
**Format**: `networkx.DiGraph` serialized to JSON or Pickle (for internal use) or represented as an edge list in `data/processed/`.  
**Attributes**:
- **Nodes**:
  - `node_id`: string
  - `text`: string (the fact/content)
  - `position`: integer (index in original context)
- **Edges**:
  - `source`: string (node_id)
  - `target`: string (node_id)
  - `weight`: float (similarity score or confidence)
  - `type`: string ("original" or "noise")

## Output Data

### 4. Execution Log (Results)
**Format**: CSV (`data/processed/results.csv`)  
**Schema**:
- `task_id`: string
- `strategy`: string (one of: "Full", "Lazy", "Greedy")
- `accuracy`: float (0.0 or 1.0)
- `nodes_visited`: integer
- `inference_time_seconds`: float
- `token_count`: integer (total tokens generated/consumed)
- `status`: string ("completed", "timeout", "unresolved", "degenerate", "invalid_graph")
- `noise_variant`: boolean (true if run on noisy graph)

### 5. Statistical Report
**Format**: JSON (`data/processed/statistics.json`)  
**Schema**:
- `baseline_accuracy`: float
- `baseline_nodes_avg`: float
- `lazy_accuracy`: float
- `lazy_nodes_avg`: float
- `lazy_accuracy_delta`: float
- `lazy_nodes_reduction_pct`: float
- `lazy_p_value`: float
- `lazy_test_statistic`: float
- `greedy_accuracy`: float
- `greedy_nodes_avg`: float
- `greedy_accuracy_delta`: float
- `greedy_nodes_reduction_pct`: float
- `greedy_p_value`: float
- `greedy_test_statistic`: float
- `point_biserial_correlation`: float (Baseline only)
- `complexity_threshold_nodes`: float (LOESS estimated threshold, or null)
- `timeout_count`: integer
- `total_tasks`: integer
- `power_analysis_note`: string (if N < 30)

## Data Flow Diagram

```mermaid
graph TD
    A[LoCoMo HF Dataset] --> B(Data Downloader)
    B --> C[Raw Data]
    C --> D[Graph Builder]
    D --> E[Memory Graph (Clean)]
    D --> F[Memory Graph (Noisy)]
    E --> G[Traversal Engine]
    F --> G
    G --> H[Execution Log CSV]
    H --> I[Statistical Analyzer]
    I --> J[Statistical Report JSON]
```