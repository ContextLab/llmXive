# Data Model: llmXive follow-up: extending "CiteVQA"

## Overview

This document defines the data structures used for the CiteVQA extension project. It ensures that all inputs, intermediate states, and outputs conform to the **Strict Attributed Accuracy (SAA)** requirements, the **Visual Localization Accuracy (VLA)** requirements, and the **Constitution Principle VI** (Cross-Modal Attribution Fidelity).

## Entities

### 1. Document Chunk
A segment of text extracted from a PDF page, associated with a unique ID and bounding box.

```yaml
DocumentChunk:
  chunk_id: string (unique)
  page_id: string
  text: string
  bounding_box: BoundingBox
  embedding: vector (float32, 384-dim) # Optional, for retrieval
```

### 2. Query
A natural language question associated with a document page.

```yaml
Query:
  query_id: string
  page_id: string
  question: string
  ground_truth_answer: string
  ground_truth_chunk_id: string
  ground_truth_bounding_box: BoundingBox
```

### 3. Prediction
The output of the model (Text-Only or Visual-Only).

```yaml
Prediction:
  query_id: string
  model_type: enum [text-only, visual-only]
  predicted_answer: string
  predicted_chunk_id: string (or null if visual-only predicts box directly)
  predicted_bounding_box: BoundingBox (or null)
```

### 4. Evaluation Result
The computed metrics for a single QA pair.

```yaml
EvaluationResult:
  query_id: string
  model_type: enum [text-only, visual-only]
  
  # Text-Only Specific (SAA)
  answer_correct: boolean (Exact Match OR Sim >= 0.85 AND retrieved_context_contains_gt)
  spatial_correct: boolean (IoU > 0.5)
  iou_score: float
  semantic_similarity: float
  retrieved_context_contains_gt: boolean # NEW: Ensures retrieval-conditioned correctness
  saa_score: integer (0 or 1)
  error_type: enum [none, wrong_answer, wrong_box, both, retrieval_failure]
  
  # Visual-Only Specific (VLA)
  visual_localization_score: integer (0 or 1) # 1 if IoU > 0.5, else 0
  visual_only_predicted_box: BoundingBox (or null)
  
  # Aggregation
  saa_mean: float # Mean SAA for the dataset
  vla_mean: float # Mean VLA for the dataset
  bootstrap_ci_lower: float # Lower bound of 95% CI for SAA mean
  bootstrap_ci_upper: float # Upper bound of 95% CI for SAA mean
  baseline_scalar: float # Baseline SAA from CiteVQA paper
  is_significant: boolean # True if baseline_scalar is outside [ci_lower, ci_upper]
```

### 5. Baseline Reference
Immutable scalar from the original CiteVQA paper.

```yaml
BaselineReference:
  metric_name: "SAA"
  value: float
  source: "CiteVQA Original Paper"
```

## Data Flow

1.  **Raw Data**: PDFs + QA Pairs (CiteVQA) -> **Chunked JSON** (with BBoxes).
2.  **Retrieval**: Query + Chunked JSON -> **Top-K Chunks**.
3.  **Reasoning**: Top-K Chunks + Query -> **Prediction**.
4.  **Evaluation**: Prediction + Ground Truth -> **EvaluationResult**.
5.  **Aggregation**: EvaluationResults -> **Summary Statistics** (Mean SAA, VLA, Bootstrap CI).