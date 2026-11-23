# Data Model Specification

This document defines the data schemas and field definitions used throughout the llmXive drift detection pipeline.

## Raw Data

### `data/raw/taxonomy_owasp.json`
The OWASP Top LLM taxonomy downloaded from the Hugging Face dataset `OWASP/Top-LLM`.

**Structure**:
```json
[
 {
 "category": "String",
 "description": "String",
 "examples": ["String",...]
 }
]
```

### `data/raw/taxonomy_agentdog.json`
The OWASP taxonomy mapped to the AgentDoG 1.5 safety schema.

**Structure**:
```json
[
 {
 "agentdog_category": "String",
 "owasp_category": "String",
 "mapping_confidence": "Float (0.0-1.0)"
 }
]
```

## Processed Data

### `data/processed/taxonomy_centroids.json`
Taxonomy categories with pre-computed centroid embeddings.

**Structure**:
```json
{
 "model": "all-MiniLM-L6-v2",
 "categories": [
 {
 "category": "String",
 "centroid": [Float, Float,...] // 384-dimensional vector
 }
 ]
}
```

### `data/processed/drift_scores.csv`
Results of the drift scoring pipeline.

**Columns**:
- `log_id`: Unique identifier for the log entry (String/UUID).
- `text`: The raw log text (String).
- `drift_score`: Cosine distance to the nearest centroid (Float, range 0.0 to 2.0).
- `review_flag`: Boolean flag indicating if the log requires manual review (True/False).

### `data/processed/blinded_annotation_batches/*.csv`
Stratified logs prepared for human annotation, with drift scores removed.

**Columns**:
- `log_id`: Unique identifier.
- `text`: The raw log text.
- `batch_id`: Identifier for the annotation batch.

### `data/processed/merged_annotations.csv`
Human annotations merged with drift scores for validation.

**Columns**:
- `log_id`: Unique identifier.
- `text`: The raw log text.
- `label`: Human-provided label (e.g., "benign", "attack").
- `drift_score`: The computed drift score.
- `batch_id`: Annotation batch identifier.

## Validation Outputs

### `data/processed/validation_stats.json`
Statistical validation results.

**Structure**:
```json
{
 "us01_stats": {
 "p_value": "Float",
 "cohen_d": "Float",
 "significant": "Boolean"
 },
 "us02_stats": {
 "logistic_regression": {
 "p_value": "Float",
 "odds_ratio": "Float"
 },
 "mann_whitney_u": {
 "u_statistic": "Float",
 "p_value": "Float"
 },
 "kappa": "Float"
 }
}
```

## Schemas

All JSON artifacts should ideally conform to the schemas defined in `specs/001-llmxive-drift-detection/contracts/`.

### Drift Result Schema
(Refer to `specs/001-llmxive-drift-detection/contracts/drift_result.schema.yaml` for the full YAML schema definition).

## Data Integrity

Raw data files are tracked in `data/checksums.json` to ensure integrity during downloads and processing.
