# Data Model: llmXive follow-up: extending "AI for Auto-Research: Roadmap & User Guide"

## 1. Overview

This document defines the data structures, schemas, and transformation pipelines for the project. All data flows from `data/raw/` (downloaded benchmark or synthetic) to `data/processed/` (graphs, features, labels) and finally to `output/` (reports).

## 2. Raw Data Schema

The raw data is expected to be a CSV or JSON file containing:
- `id`: Unique identifier for the research idea.
- `literature_review_text`: The text of the AI-generated literature review.
- `failure_label`: Binary label (0 = Valid, 1 = Failure/Novelty Degradation).
- `metadata`: Optional fields (e.g., generation timestamp, model version).

**Example (CSV)**:
```csv
id,literature_review_text,failure_label
1,"This paper explores...",1
2,"We propose a novel...",0
```

## 3. Intermediate Data Structures

### 3.1 Graph Object (NetworkX)
- **Nodes**: Concepts/Methods (string labels).
- **Edges**: Claims (directed, from concept to method).
- **Attributes**:
  - `cycle_density`: Float (0.0 to 1.0).
  - `isolation_ratio`: Float (0.0 to 1.0). **(Corrected from 'isolation_score')**
  - `semantic_distance`: Float (≥ 0.0).
  - `num_nodes`: Integer.
  - `num_edges`: Integer.

### 3.2 Feature Matrix (Pandas DataFrame)
| Column | Type | Description |
|--------|------|-------------|
| `id` | str | Unique identifier |
| `cycle_density` | float | Ratio of cycles |
| `isolation_ratio` | float | Fraction of nodes with in-degree zero |
| `semantic_distance` | float | Mean pairwise cosine distance within components |
| `num_nodes` | int | Graph size |
| `num_edges` | int | Edge count |
| `failure_label` | int | Target variable (0/1) |

## 4. Transformation Pipeline

1. **Ingestion**: Download raw data to `data/raw/` or generate synthetic data. Checksum and record in `data/checksums.json`.
2. **Graph Construction**:
   - Parse text with `spaCy`.
   - Extract triplets and **validate against source text**.
   - Build `networkx.DiGraph`.
   - Handle edge cases (empty text → default metrics).
3. **Metric Extraction**:
   - Compute cycle density, isolation ratio, semantic distance.
   - Store metrics in a DataFrame.
4. **Label Mapping**:
   - Join metrics with `failure_label`.
   - Exclude rows with missing labels.
5. **Model Input**:
   - Split into features (X) and labels (y).
   - Save to `data/processed/feature_matrix.csv`.

## 5. Data Hygiene Rules

- **No In-Place Modification**: Raw data is never changed. All transformations write to new files.
- **Checksums**: Every file in `data/` is checksummed (SHA-256).
- **PII Scan**: No PII allowed in `data/` or `output/`.
- **Versioning**: Each processed file includes a timestamp and content hash in its filename or metadata.