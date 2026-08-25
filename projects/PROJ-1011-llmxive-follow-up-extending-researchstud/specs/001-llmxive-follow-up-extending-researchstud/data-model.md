# Data Model: llmXive follow-up: extending "ResearchStudio-Idea"

## 1. Overview

This document defines the data structures used for the `001-llmxive-extension` feature. All data is stored in JSON/JSONL format for portability and versioning.

## 2. Entities

### 2.1 Abstract
Represents a research proposal text with metadata.

```json
{
  "id": "string (unique hash)",
  "title": "string",
  "abstract": "string",
  "venue": "string",
  "domain": "string (ML, PublicHealth, Climate)",
  "acceptance_status": "string (accepted, rejected)",
  "source_url": "string",
  "checksum": "string",
  "source_type": "string (primary, fallback)"
}
```

### 2.2 PatternCard
Represents one of the 15 ML-derived ideation patterns.

```json
{
  "id": "string (pattern-001 to pattern-015)",
  "name": "string",
  "description": "string",
  "structural_constraints": ["string", "string"],
  "embedding_vector": "list[float]"
}
```

### 2.3 ProblemStatement
A non-ML problem statement extracted from the corpus.

```json
{
  "id": "string",
  "abstract_id": "string (foreign key to Abstract)",
  "problem_text": "string",
  "domain": "string"
}
```

### 2.4 Proposal
A generated research idea.

```json
{
  "id": "string",
  "problem_statement_id": "string",
  "type": "string (pattern_guided, random_pattern, baseline)",
  "content": "string",
  "generation_metadata": {
    "model": "string",
    "patterns_used": ["string"],
    "timestamp": "string",
    "token_count": "integer",
    "generation_time_seconds": "float"
  }
}
```

### 2.5 Rating
Expert evaluation score.

```json
{
  "id": "string",
  "proposal_id": "string",
  "expert_id": "string",
  "metric": "string (feasibility, bottleneck, alignment)",
  "score": "integer (1-5)",
  "comments": "string (optional)"
}
```

## 3. Data Flow

1.  **Raw Data**: Downloaded from sources -> `data/raw/corpus.jsonl`.
2.  **Processed Data**: Parsed, validated, and filtered -> `data/processed/corpus_clean.jsonl`.
3.  **Embeddings**: Pattern cards and problem statements encoded -> `data/processed/embeddings.jsonl`.
4.  **Validation**: Pattern mapping hold-out set -> `data/processed/pattern_validation.jsonl`.
5.  **Generated Proposals**: LLM output -> `data/processed/proposals.jsonl`.
6.  **Ratings**: Expert input -> `data/processed/ratings.csv`.
7.  **Results**: Statistical output -> `data/processed/results.json`.

## 4. Constraints

*   **Uniqueness**: All `id` fields must be unique within their entity type.
*   **Validity**: `abstract` field must be non-empty. `score` must be 1-5.
*   **Privacy**: No PII in `data/`. Expert IDs are anonymized.
*   **Checksums**: Every file in `data/` must have a corresponding checksum in `state/`.
*   **IRR**: Ratings file must include a `krippendorff_alpha` field in the metadata header.