# Architecture Overview

This document describes the high-level architecture of the llmXive drift detection system.

## System Components

### 1. Data Ingestion Layer
- **Responsibility**: Fetching raw data from external sources (Hugging Face, OWASP).
- **Modules**: `data_loader.py`
- **Outputs**: `data/raw/` directory containing JSON/JSONL files.

### 2. Taxonomy Processing Layer
- **Responsibility**: Mapping external taxonomies to the internal schema and computing embeddings.
- **Modules**: `taxonomy_builder.py`
- **Outputs**: `data/processed/taxonomy_centroids.json`

### 3. Scoring Engine
- **Responsibility**: Computing drift scores (cosine distance) for input logs.
- **Modules**: `drift_scoring.py`
- **Outputs**: `data/processed/drift_scores.csv`

### 4. Annotation Interface
- **Responsibility**: Stratifying data and preparing blinded batches for human review.
- **Modules**: `annotator_interface.py`
- **Outputs**: `data/processed/blinded_annotation_batches/`

### 5. Validation & Analysis
- **Responsibility**: Statistical analysis of drift scores against ground truth.
- **Modules**: `validation.py`
- **Outputs**: `data/processed/validation_stats.json`, `data/processed/merged_annotations.csv`

### 6. Baseline Comparison
- **Responsibility**: Running a local zero-shot LLM classifier for performance comparison.
- **Modules**: `comparison.py`
- **Outputs**: Comparison metrics in `data/processed/comparison_report.json`

## Data Flow

1. **Raw Data** is fetched and stored in `data/raw/`.
2. **Taxonomy** is mapped and centroids are built, stored in `data/processed/`.
3. **Logs** are scored against centroids, producing `drift_scores.csv`.
4. **Stratification** selects extreme cases for human annotation.
5. **Human Annotations** are ingested and merged with scores.
6. **Validation** runs statistical tests to confirm the drift detection efficacy.
7. **Baseline** comparison runs to benchmark against a standard zero-shot classifier.

## Memory Management

- The system is designed to run within a **7GB RAM** limit.
- **Batch Processing**: Logs are processed in batches (default size 32) to minimize memory footprint.
- **Streaming**: Large datasets are streamed from Hugging Face rather than fully loaded into memory.
- **Tracemalloc**: Memory usage is monitored during centroid generation and batch processing.

## Extensibility

- **New Taxonomies**: Can be added by implementing a mapping function in `data_loader.py`.
- **New Models**: The embedding model (`all-MiniLM-L6-v2`) and baseline model (`facebook/bart-large-mnli`) are configurable in `config.py`.
- **New Metrics**: Statistical validation metrics can be extended in `validation.py`.

## Security & Integrity

- **Checksums**: All raw data files are verified against `data/checksums.json`.
- **Blinding**: Drift scores are removed before human annotation to prevent bias.
- **Reproducibility**: Random seeds are fixed, and inference caching is implemented for baseline comparisons.
