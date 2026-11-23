# Data Model: llmXive follow-up: extending "SynthDocBench" with Decoupled Retrieval

## Overview

This document defines the data structures used in the evaluation pipeline, including the input dataset schema, the retrieval index structure, and the output evaluation metrics. All data flows are designed to be compatible with the CPU-first, resource-constrained execution environment.

## Input Data Schema

### Synthetic Documents Dataset

The primary input is the locally generated synthetic dataset in Parquet format.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `doc_id` | `string` | Unique document identifier. | Generated |
| `page_number` | `integer` | Page index within the document (1-based). | Generated |
| `page_image` | `bytes` | Raw image bytes (JPEG/PNG) of the page. | Generated |
| `question` | `string` | The query question. | Generated |
| `answer` | `string` | Ground-truth answer. | Generated |
| `doc_length` | `integer` | Total number of pages in the document. | Generated |
| `question_position` | `string` | Categorical: "first", "middle", "last". | Derived |

*Derived Fields*:
- `doc_length`: Calculated by counting unique `doc_id` entries per document.
- `question_position`: Computed as:
  - "first": `page_number` ≤ `doc_length` / 3
  - "middle": `doc_length` / 3 < `page_number` ≤ 2 * `doc_length` / 3
  - "last": `page_number` > 2 * `doc_length` / 3

## Derived Data Structures

### OCR Text Index

A CPU-based index mapping page identifiers to text content for retrieval.

| Field | Type | Description |
| :--- | :--- | :--- |
| `doc_id` | `string` | Document identifier. |
| `page_number` | `integer` | Page index. |
| `page_text` | `string` | Extracted text via Tesseract. |
| `embedding` | `list[float]` | Optional: Sentence embedding for semantic search. |

*Storage*: In-memory FAISS index or serialized `.faiss` file.

### Evaluation Results

Aggregated metrics per model and condition.

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_name` | `string` | Identifier of the VLM used. |
| `context_size` | `integer` | Native context window size (4000, 8000, 32000). |
| `condition` | `string` | "baseline" or "retrieval_augmented". |
| `question_position` | `string` | "first", "middle", "last". |
| `total_questions` | `integer` | Count of questions evaluated. |
| `correct_count` | `integer` | Count of correct answers. |
| `accuracy` | `float` | `correct_count / total_questions`. |
| `retrieval_precision` | `float` | Precision of the retrieval mechanism. |
| `retrieval_recall` | `float` | Recall of the retrieval mechanism. |
| `retrieval_latency_ms` | `float` | Average retrieval latency in milliseconds. |

## Output Data Schema

### Statistical Analysis Report

Final results for the correlation analysis.

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_name` | `string` | VLM identifier. |
| `context_size` | `integer` | Context window size. |
| `baseline_middle_accuracy` | `float` | Accuracy in baseline condition for middle-third. |
| `retrieval_middle_accuracy` | `float` | Accuracy in retrieval condition for middle-third. |
| `accuracy_delta` | `float` | `retrieval_middle_accuracy - baseline_middle_accuracy`. |
| `correlation_coefficient` | `float` | Spearman r (computed across all models). |
| `p_value` | `float` | Significance of the correlation (reported descriptively). |
| `relationship_classification` | `string` | "inverse", "no significant", or "positive". |
| `p95_retrieval_latency_ms` | `float` | 95th percentile retrieval latency in milliseconds. |
| `sample_size_used` | `integer` | Number of documents actually processed. |
| `runtime_hours` | `float` | Total runtime in hours. |
| `feasibility_status` | `string` | "within_limit" or "exceeded_limit". |
| `limitation_note` | `string` | Note on statistical power if sample size < 200. |

## Data Flow

1. **Ingestion**: Run `code/doc_generator.py` → Generate Parquet → Store in `data/raw/`.
2. **Indexing**: Extract `page_text` via Tesseract → Build FAISS index.
3. **Evaluation**:
   - Baseline: Image + Question → VLM → Accuracy.
   - Retrieval: Query → FAISS → Snippet + Image + Question → VLM → Accuracy.
4. **Aggregation**: Compute deltas, correlation, and latency metrics → Output JSON/CSV.
5. **State Update**: `code/utils.py` updates `state/` YAML with content hashes.