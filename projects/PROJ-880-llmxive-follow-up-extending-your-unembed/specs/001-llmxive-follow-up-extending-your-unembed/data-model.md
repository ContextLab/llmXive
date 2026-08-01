# Data Model: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

## 1. Entities & Relationships

### 1.1 Models
- **Entity**: `Model`
- **Attributes**: `model_id` (str), `name` (str), `language_primary` (str), `vocab_size` (int), `embedding_dim` (int).
- **Relationship**: One-to-Many with `Subspace`.
- **Persistence**: Stored in `tinydb` database (`data/processed/models.db`).

### 1.2 Subspaces
- **Entity**: `Subspace`
- **Attributes**: `subspace_id` (str), `model_id` (str), `k` (int), `singular_vectors` (array of float), `singular_values` (array of float).
- **Relationship**: One-to-Many with `SimilarityMetric`.
- **Persistence**: Stored in `tinydb` database (`data/processed/subspaces.db`).

### 1.3 Similarity Metrics
- **Entity**: `SimilarityMetric`
- **Attributes**: `metric_id` (str), `subspace_a_id` (str), `subspace_b_id` (str), `cosine_similarity` (float), `method` (str), `intersection_size` (int).
- **Relationship**: One-to-Many with `ValidationMetric`.
- **Persistence**: Stored in `tinydb` database (`data/processed/similarities.db`).

### 1.4 Token Frequencies
- **Entity**: `TokenFrequency`
- **Attributes**: `language` (str), `token_id` (int), `frequency` (float), `source` (str).
- **Relationship**: One-to-Many with `MeanEmbedding`.
- **Persistence**: Stored as JSON files (`data/raw/token_freqs/*.json`).

### 1.5 Mean Embeddings
- **Entity**: `MeanEmbedding`
- **Attributes**: `mean_embedding_id` (str), `language` (str), `model_id` (str), `vector` (array of float), `individual_projections` (array of float, top-N).
- **Relationship**: One-to-One with `ShiftVector`.
- **Persistence**: Stored in `tinydb` database (`data/processed/embeddings.db`).
- **Note**: `individual_projections` stores the top-N projected vectors $p_t$ to ensure reproducibility of the diagnostic metric.

### 1.6 Shift Vectors
- **Entity**: `ShiftVector`
- **Attributes**: `shift_id` (str), `language_a` (str), `language_b` (str), `vector` (array of float).
- **Relationship**: One-to-Many with `ValidationMetric`.
- **Persistence**: Stored in `tinydb` database (`data/processed/shifts.db`).

### 1.7 Validation Metrics
- **Entity**: `ValidationMetric`
- **Attributes**: `metric_id` (str), `shift_id` (str), `wals_correlation` (float), `senteval_correlation` (float), `p_value` (float), `null_method` (str).
- **Relationship**: N/A.
- **Persistence**: Stored in `tinydb` database (`data/processed/validation.db`).

### 1.8 Token Projections (Diagnostic)
- **Entity**: `TokenProjection`
- **Attributes**: `projection_id` (str), `token_id` (int), `token_text` (str), `projected_vector` (array of float), `logit_weight` (float).
- **Relationship**: Many-to-One with `MeanEmbedding` (via `mean_embedding_id`).
- **Persistence**: Stored in `tinydb` database (`data/processed/token_projections.db`).

## 2. Data Flow

1. **Input**: Model weights (HF), Raw text (RedPajama, OSCAR).
2. **Process**:
   - Load $W_U$, $W_E$.
   - Compute SVD -> `Subspace` (stored in `tinydb`).
   - Count tokens -> `TokenFrequency` (stored as JSON).
   - Project -> `MeanEmbedding` (stored in `tinydb`) AND `TokenProjection` (stored in `tinydb`).
   - Compute Similarity -> `SimilarityMetric` (stored in `tinydb`).
   - Compute Shift -> `ShiftVector` (stored in `tinydb`).
   - Correlate with WALS/SentEval -> `ValidationMetric` (stored in `tinydb`).
3. **Output**: JSON reports, CSV files, YAML schemas.

## 3. File Formats

- **SVD Results**: `data/processed/svd_results/{model_id}_svd.json`
  - Schema: `contracts/svd_result.schema.yaml`
- **Similarity Report**: `data/processed/subspace_metrics/similarity_matrix.json`
  - Schema: `contracts/similarity_metric.schema.yaml`
- **Token Attribution**: `data/processed/token_attribution/{language}_top_tokens.json`
  - Schema: `contracts/token_attribution.schema.yaml`
- **Validation Report**: `data/processed/validation_metrics/validation_report.json`
  - Schema: `contracts/validation_metric.schema.yaml`

## 4. Constraints

- **Integrity**: All `model_id` must exist in the `models.db` `tinydb` database.
- **Consistency**: `k` (number of singular vectors) must be consistent across all subspace comparisons.
- **Precision**: Floating point values stored as `float64`.
- **Referential Integrity**: Enforced by `tinydb` queries checking foreign keys before insertion.
