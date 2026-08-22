# Data Model: llmXive follow-up: extending "GENEB: Why Genomic Models Are Hard to Compare"

## Entities

### TaskDefinition

Represents a single biological task in the GENEB benchmark.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `task_id` | `string` | Unique identifier for the task (e.g., "clinvar_classification") | `problems.csv` |
| `raw_sequence` | `string` | Raw nucleotide sequence (A/C/G/T) | `sequences` split (FASTA) |
| `sequence_length` | `integer` | Length of the raw sequence | Derived from `raw_sequence` |
| `task_type` | `string` | Type of biological task (e.g., "disease_classification") | `problems.csv` |
| `model_architectures` | `list[string]` | List of model architectures evaluated on this task (e.g., ["Transformer", "Mamba"]) | `problems.csv` |
| `macro_mcc_scores` | `dict[string, float]` | Ground-truth macro-MCC scores for each architecture | `problems.csv` |

### SequenceFeatureSet

A vector of numeric values derived from a `TaskDefinition`. 
**Note**: `AT-Content` has been excluded due to perfect collinearity with `GC-Content`.

| Field | Type | Description | Range |
|-------|------|-------------|-------|
| `task_id` | `string` | Foreign key to `TaskDefinition` | - |
| `nucleotide_entropy` | `float` | Shannon entropy of A/C/G/T frequencies | [0.0, 2.0] |
| `dinucleotide_entropy` | `float` | Shannon entropy of 16 dinucleotide frequencies | [0.0, 4.0] |
| `gc_content` | `float` | Proportion of G and C bases | [0.0, 1.0] |
| `gc_content_variance` | `float` | Variance of GC-content across sliding windows (window_size=100) | [0.0, 0.25] |
| `kmer_entropy_3` | `float` | Shannon entropy of 64 3-mer frequencies | [0.0, 6.0] |
| `kmer_entropy_4` | `float` | Shannon entropy of 256 4-mer frequencies | [0.0, 8.0] |
| `repeat_density` | `float` | Proportion of sequence covered by tandem repeats | [0.0, 1.0] |
| `homopolymer_length` | `float` | Average length of consecutive identical bases | [1.0, 50.0] |
| `dinucleotide_skew` | `float` | ((G-C)/(G+C) + (A-T)/(A+T)) | [-2.0, 2.0] |
| `purine_pyrimidine_ratio` | `float` | (A+G)/(C+T) | [0.0, ∞) |
| `sequence_complexity` | `float` | Lempel-Ziv complexity estimate | [0.0, 1.0] |
| `low_complexity_density` | `float` | Proportion of sequence in SEG-masked regions | [0.0, 1.0] |
| `sequence_length_log` | `float` | Log-transformed sequence length | [0.0, ∞) |

### PerformancePrediction

The output of the regression model for a specific task and architecture.

| Field | Type | Description | Range |
|-------|------|-------------|-------|
| `task_id` | `string` | Foreign key to `TaskDefinition` | - |
| `architecture` | `string` | Model architecture (e.g., "Transformer") | - |
| `predicted_mcc` | `float` | Predicted macro-MCC score | [-1.0, 1.0] |
| `actual_mcc` | `float` | Ground-truth macro-MCC score | [-1.0, 1.0] |
| `residual` | `float` | `actual_mcc - predicted_mcc` | [-2.0, 2.0] |

### SensitivityReport

A data structure containing error rates at each threshold step.

| Field | Type | Description |
|-------|------|-------------|
| `threshold` | `float` | Decision threshold value (e.g., 0.6) |
| `false_positive_rate` | `float` | Proportion of low-performance tasks incorrectly classified as high-performance |
| `false_negative_rate` | `float` | Proportion of high-performance tasks incorrectly classified as low-performance |
| `accuracy` | `float` | Overall classification accuracy at this threshold |

## Data Flow

1.  **Download**: Raw data (`problems.csv`, `sequences` split) → `data/raw/`
2.  **Extract Features**: `TaskDefinition` + raw sequences → `SequenceFeatureSet` → `data/processed/features.csv`
3.  **Train Models**: `SequenceFeatureSet` + `macro_mcc_scores` → `PerformancePrediction` → `data/processed/predictions.csv`
4.  **Analyze**: `PerformancePrediction` → `SensitivityReport` → `outputs/reports/sensitivity.csv`

## Constraints

- All numeric fields must be finite (no NaN/Inf).
- `task_id` must be unique across all entities.
- `predicted_mcc` and `actual_mcc` must be within [-1.0, 1.0].
- `sequence_length_log` must be > 0.0 (log of positive integer).
- **Collinearity Constraint**: `AT-Content` is not present in this schema.