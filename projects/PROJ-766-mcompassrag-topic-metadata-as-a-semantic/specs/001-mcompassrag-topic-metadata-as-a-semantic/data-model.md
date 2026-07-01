# Data Model: MCompassRAG

## 1. Overview

This document defines the data models and schemas used in the MCompassRAG pipeline. It ensures consistency across data loading, topic modeling, retrieval, and metric reporting.

## 2. Key Entities

### 2.1 RetrievalArtifact

Represents the output of the retrieval phase, containing query results, document IDs, similarity scores, and latency metrics.

**Fields**:
- `query_id`: Unique identifier for the query (string).
- `retrieved_doc_ids`: List of document IDs retrieved for the query (list of strings).
- `similarity_scores`: List of similarity scores corresponding to the retrieved documents (list of floats).
- `latency_ms`: Time taken to retrieve the documents in milliseconds (float).
- `timestamp`: ISO 8601 timestamp of the retrieval (string).
- `retriever_type`: Enum ["baseline", "mcompass"] indicating which model generated this result (string).

### 2.2 TopicModelConfig

Configuration object for the topic modeling step.

**Fields**:
- `model_type`: Type of topic model (e.g., "LDA", "CWTM") (string).
- `num_topics`: Number of topics to generate (integer).
- `max_iter`: Maximum number of iterations for convergence (integer).
- `random_state`: Seed for reproducibility (integer).
- `device`: Target device ("cpu") (string).
- `synthetic`: Boolean flag indicating if topics were synthesized (string).

### 2.3 BenchmarkSubset

A sampled portion of the benchmark dataset used for validation.

**Fields**:
- `source_dataset`: Name or URL of the source dataset (string).
- `sample_size`: Number of rows (queries/documents) in the subset (integer).
- `sampling_method`: Method used for sampling (e.g., "stratified_by_topic_density", "stratified_by_length") (string).
- `timestamp`: ISO 8601 timestamp of the sampling (string).
- `variables`: List of variables included in the subset (list of strings).
- `topic_generation_method`: Description of how topic metadata was derived (e.g., "synthesized_LDA", "pre_existing") (string).

## 3. Data Flow

1.  **Input**: `BenchmarkSubset` loaded from verified datasets or local cache.
2.  **Processing**:
    - If `topic_generation_method` is "synthesized_LDA", run LDA on the corpus.
    - Apply `TopicModelConfig` to generate topic metadata.
    - Run **Baseline Retriever** (without metadata).
    - Run **MCompass Retriever** (with metadata).
3.  **Output**: `RetrievalArtifact` (for both baseline and mcompass) saved to disk.

## 4. Schema Definitions

Schemas are defined in the `contracts/` directory as YAML files for validation.

- `contracts/retrieval_artifact.schema.yaml`: Validates `RetrievalArtifact`.
- `contracts/topic_model_config.schema.yaml`: Validates `TopicModelConfig`.
- `contracts/benchmark_subset.schema.yaml`: Validates `BenchmarkSubset`.