# Data Model: llmXive Follow-up (Trust-Region Behavior Blending Extension)

## Overview

This document defines the core data structures used in the llmXive follow-up project,
specifically focusing on the `TrainingInstance` schema and related feature representations.
The model has been updated to reflect the **Proxy Strategy** (replacing ground-truth collapse labels
with proxy targets like relevance scores and text length).

## Core Entities

### TrainingInstance

Represents a single data point used for correlation analysis and profile generation.
Previously, this schema included `optimal_epsilon_0` and `collapse_label` derived from
ground-truth sweep logs. Since those logs are unavailable, the schema has been amended
to link diversity profiles to **proxy targets**.

**Schema Definition:**

```yaml
TrainingInstance:
 type: object
 required:
 - instance_id
 - source_text
 - profile_features
 - proxy_target
 properties:
 instance_id:
 type: string
 description: Unique identifier for the instance (e.g., 'book_001_sent_42')
 source_text:
 type: string
 description: The raw text content (teacher output or document chunk)
 profile_features:
 type: object
 description: Computed diversity metrics (lexical and syntactic)
 properties:
 distinct_4_ratio:
 type: number
 format: float
 description: Ratio of unique 4-grams to total 4-grams
 ngram_entropy:
 type: number
 format: float
 description: Shannon entropy of the 4-gram distribution
 syntactic_variation_score:
 type: number
 format: float
 description: Variance of parse tree depths in the text
 # Optional fallback if syntactic parsing fails
 parse_tree_depth_variance:
 type: number
 format: float
 nullable: true
 description: Fallback metric if full syntactic variation fails
 proxy_target:
 type: object
 description: The proxy value used instead of ground-truth collapse labels.
 # This object varies by dataset source
 oneOf:
 - $ref: '#/definitions/BookCorpusProxy'
 - $ref: '#/definitions/BEIRProxy'
 discriminator:
 propertyName: source_type
 mapping:
 book_corpus: '#/definitions/BookCorpusProxy'
 beir: '#/definitions/BEIRProxy'

definitions:
 BookCorpusProxy:
 type: object
 properties:
 source_type:
 type: string
 enum: [book_corpus]
 proxy_type:
 type: string
 enum: [text_length]
 text_length:
 type: integer
 description: Length of the source text (proxy for 'collapse' or 'stability')
 # Conceptual mapping: Shorter text may imply 'collapse' (low diversity/stability)
 # Longer text implies 'stability' (high diversity/stability)
 required:
 - source_type
 - proxy_type
 - text_length

 BEIRProxy:
 type: object
 properties:
 source_type:
 type: string
 enum: [beir]
 proxy_type:
 type: string
 enum: [relevance_score]
 relevance_score:
 type: number
 format: float
 description: Retrieval relevance score (proxy for 'collapse' or 'stability')
 # Conceptual mapping: Low relevance may imply 'collapse' (low utility/stability)
 # High relevance implies 'stability' (high utility/stability)
 required:
 - source_type
 - proxy_type
 - relevance_score
```

## Schema Evolution Notes

### Change Log

- **T006b Update (Current)**:
 - **Removed**: `optimal_epsilon_0` (float, optional) - No longer available from sweep logs.
 - **Removed**: `collapse_label` (boolean, optional) - Ground truth unavailable.
 - **Added**: `proxy_target` (object) - A polymorphic structure containing:
 - `source_type`: Identifies the dataset source (`book_corpus` or `beir`).
 - `proxy_type`: The nature of the proxy (`text_length` or `relevance_score`).
 - `text_length` OR `relevance_score`: The actual numeric proxy value.
 - **Rationale**: This change aligns the data model with the **Proxy Strategy** defined in
 `spec.md` (amended in T006a). It allows the pipeline to perform correlation analysis
 between `profile_features` and the available proxy targets without requiring
 non-existent ground-truth labels.

### Usage Guidelines

1. **Feature Extraction**: `code/pipelines/extract_features.py` populates `profile_features`.
2. **Target Assignment**:
 - For **Book Corpus** data, the `proxy_target` is set to `BookCorpusProxy` with `text_length`.
 - For **BEIR** data, the `proxy_target` is set to `BEIRProxy` with `relevance_score`.
3. **Analysis**: `code/pipelines/analyze_correlations.py` extracts the numeric value from
 `proxy_target` based on `proxy_type` to compute correlation coefficients against
 `profile_features`.

## Related Artifacts

- `specs/001-llmxive-trb-diversity-profile/spec.md`: Defines the functional requirements for proxy usage.
- `code/pipelines/extract_features.py`: Generates the `profile_features` portion of the instance.
- `code/pipelines/analyze_correlations.py`: Consumes the `proxy_target` for statistical analysis.