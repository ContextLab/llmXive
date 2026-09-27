# Data Model: Zero-Shot Drift Detection

## Overview
This document defines the data structures, schemas, and transformation logic for the AgentDoG 1.5 drift detection pipeline.

## Entities

### 1. Log Entry
The raw input from the safety taxonomy dataset.
- `log_id`: Unique identifier for the log.
- `content`: Text content of the log.
- `label`: Ground truth category (Safety, Privacy, Bias, Jailbreak) or `null` if unlabeled.

### 2. Centroid
The aggregate embedding for a safety category.
- `category`: String (e.g., "Safety").
- `embedding`: List of floats (dimensions for MiniLM).
- `n_samples`: Integer count of logs used.

### 3. Drift Score
The output of the drift detection phase.
- `log_id`: Reference to Log Entry.
- `drift_score`: Cosine distance to the nearest centroid (0.0 = identical, 2.0 = maximally different).
- `nearest_centroid`: String (Category name).
- `review_flag`: Boolean indicating if the score exceeds the threshold.

### 4. Human Annotation
The validation data ingested from human reviewers.
- `log_id`: Reference to Log Entry.
- `annotator_id`: String.
- `is_novel`: Boolean (1 = novel/harmful, 0 = benign).
- `confidence`: Float (0-1).
- **Novelty Definition**: `is_novel=1` is assigned ONLY if the annotator confirms the pattern is **outside the scope** of the 4 safety categories (Safety, Privacy, Bias, Jailbreak).

## Schemas

### Input Schema (Dataset)
```yaml
type: object
properties:
  log_id:
    type: string
  content:
    type: string
  label:
    type: ["string", "null"]
required:
  - log_id
  - content
```

### Output Schema (Drift Score)
```yaml
type: object
properties:
  log_id:
    type: string
  drift_score:
    type: number
    minimum: 0.0
    maximum: 2.0
  nearest_centroid:
    type: string
    enum: ["Safety", "Privacy", "Bias", "Jailbreak"]
  review_flag:
    type: boolean
required:
  - log_id
  - drift_score
  - nearest_centroid
  - review_flag
```

### Validation Schema (Human Annotation)
```yaml
type: object
properties:
  log_id:
    type: string
  annotator_id:
    type: string
  is_novel:
    type: integer
    enum: [0, 1]
  confidence:
    type: number
    minimum: 0.0
    maximum: 1.0
required:
  - log_id
  - annotator_id
  - is_novel
```

## Transformation Logic

1. **Centroid Generation**:
   - Group logs by `label`.
   - Generate embeddings for each group.
   - Compute mean vector for each group.
   - Store as `Centroid`.

2. **Drift Scoring**:
   - For each `log_id`, generate embedding.
   - Compute cosine distance to all 4 centroids.
   - Select minimum distance as `drift_score`.
   - Set `review_flag` if `drift_score > threshold`.
   - **Novelty Logic**: A log is considered "Novel" (for validation) if `drift_score` is high (far from ALL centroids) AND the human annotator confirms it is outside the 4 categories.

3. **Stratification**:
   - Sort logs by `drift_score`.
 - Select **top [deferred]** (High Drift) and **bottom [deferred]** (Low Drift) for human annotation.
   - Create `annotation_batch` for human review.
   - **Rationale**: The 10% threshold captures the extreme tails of the distribution where novelty is most likely to be found, balancing sensitivity and specificity.

4. **Validation Metrics**:
   - **Cohen's Kappa**: Compute between `is_novel` (Human) and `review_flag` (System).
   - **Mann-Whitney U**: Compare `drift_score` distribution between `is_novel=1` (Human-Labeled Novel) and `is_novel=0` (Human-Labeled Benign).
   - **Logistic Regression**: Estimate odds ratio of `is_novel=1` given `drift_score`.

## Constraints

- **Batch Size**: 64 (Fixed).
- **Random Seed**: 42.
- **Max RAM**: 7GB (Streaming enforced).
- **Threshold**: `review_flag` threshold is a parameter, not a hardcoded constant, to allow tuning.
- **Novelty Definition**: `is_novel=1` requires explicit human confirmation of "outside scope".
