# Data Model: Mechanistic Interpretability of CTCF Binding-Site Selection

**Status**: Placeholder. The data model cannot be instantiated due to missing verified data sources.

## Entities

### GenomicWindow
*Represents a fixed-length region of the genome. [BLOCKED]*
- **id**: `str` (Unique identifier, e.g., "chr1:1000-2000")
- **sequence**: `str` (DNA sequence, length 1000 or 500)
- **label**: `float` (Binding probability or binary label 0/1) - **MISSING VERIFIED SOURCE**
- **motif_score**: `float` (Canonical CTCF motif score)
- **cell_type**: `str` (If available, else "Unknown")
- **source**: `str` (Dataset source URL) - **MISSING VERIFIED SOURCE**

### LatentFeature
*Represents a learned feature from the SAE. [BLOCKED]*
- **id**: `int` (Feature index)
- **weights**: `List[float]` (Projection weights back to input space)
- **activation_pattern**: `str` (Description of the pattern, e.g., "High ATAC", "Motif variant")
- **correlation_canonical**: `float` (Correlation with canonical motif score)
- **correlation_binding**: `float` (Correlation with binding label)
- **significance_p**: `float` (P-value from permutation test)

### AttributionMap
*Maps input features to the model output. [BLOCKED]*
- **window_id**: `str`
- **input_attribution**: `Dict[str, float]` (Nucleotide-level attribution)
- **latent_attribution**: `Dict[int, float]` (Feature-level attribution)

## Data Flow

1.  **Ingestion**: **BLOCKED** (No verified multi-modal source).
2.  **Preprocessing**: **BLOCKED**.
3.  **Training**: **BLOCKED**.
4.  **SAE**: **BLOCKED**.
5.  **Interpretation**: **BLOCKED**.

## Schema Constraints

- **Sequence**: Must contain only {A, C, G, T, N}. Length fixed.
- **Label**: Binary (0/1) or Probability (0.0-1.0). **No verified source exists.**
- **P-value**: Must be < 0.05 to be considered significant. **Cannot be computed.**

## Note on Data Availability

The data model assumes the existence of a `GenomicWindow` with a `label` derived from verified ChIP-seq data and `cell_type` derived from verified ATAC-seq/Histone data. As no such verified sources exist in the current context, this data model is currently unimplementable.