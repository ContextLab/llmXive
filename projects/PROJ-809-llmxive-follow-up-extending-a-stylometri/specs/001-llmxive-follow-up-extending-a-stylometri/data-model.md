# Data Model: llmXive Follow-up: Extending "A Stylometric Application of Large Language Models"

## 1. Overview

This document defines the data structures, schemas, and flows for the `llmXive` follow-up project. The data model is designed to support the ingestion of arXiv abstracts, the training of character-level n-gram models, and the generation of evaluation metrics. All data is stored in the `data/` and `artifacts/` directories.

## 2. Data Entities

### 2.1 Raw Abstract
The fundamental unit of data, representing a single scientific abstract.

- **Fields**:
  - `id`: Unique identifier (string, derived from arXiv ID).
  - `lead_author`: String (exact match as in metadata).
  - `categories`: List of strings (e.g., `['cs.CL', 'physics.gen-ph']`).
  - `abstract_text`: Raw string content.
  - `processed_text`: Lowercased, punctuation-removed string.
  - `char_tokens`: List of characters (or string of chars).
  - `ngram_tokens`: List of n-gram strings (for a specific $n$).

### 2.2 Author Corpus
A collection of abstracts belonging to a single author.

- **Fields**:
  - `author_id`: String (normalized author name).
  - `abstracts`: List of `Raw Abstract` objects.
 - `train_abstracts`: List of `Raw Abstract` ([deferred] split).
 - `test_abstracts`: List of `Raw Abstract` ([deferred] split).
  - `model_n4`: Path to trained n-gram model (order 4).
  - `model_n5`: Path to trained n-gram model (order 5).
  - `model_n6`: Path to trained n-gram model (order 6).

### 2.3 Perplexity Matrix
A matrix storing the perplexity of every test abstract under every author's model.

- **Structure**:
  - Rows: Test Abstracts (indexed by `author_id` + `abstract_id`).
  - Columns: Author Models (indexed by `author_id`).
  - Values: Float (Perplexity score).

### 2.4 Hybrid Abstract
Synthetic data for robustness testing.

- **Fields**:
  - `id`: Unique identifier.
  - `source_author_1`: String.
  - `source_author_2`: String.
  - `original_text_1`: String.
  - `original_text_2`: String.
  - `hybrid_text`: String (Sentence swapped).
  - `swapped_sentence_index`: Integer.

## 3. Data Flow

1.  **Ingestion**: `arXiv` dataset $\to$ Filter (20 authors) $\to$ `data/raw/filtered.parquet`.
2.  **Preprocessing**: `filtered.parquet` $\to$ Clean/Tokenize $\to$ `data/processed/author_corpus.jsonl`.
3.  **Splitting**: `author_corpus.jsonl` $\to$ 80/20 Split $\to$ `data/processed/train/` & `data/processed/test/`.
4.  **Training**: `train/` $\to$ N-gram Models $\to$ `artifacts/models/`.
5.  **Evaluation**: `test/` + `models/` $\to$ Perplexity Matrix $\to$ `artifacts/metrics/perplexity_matrix.csv`.
6.  **Hybrid Generation**: `test/` $\to$ Swap Sentences $\to$ `data/hybrid/`.
7.  **Final Metrics**: `perplexity_matrix` + `hybrid/` $\to$ `artifacts/metrics/final_results.json`.

## 4. Schema Definitions

The following schemas define the contract for data validation.

### 4.1 Author Corpus Schema
```yaml
# contracts/author_corpus.schema.yaml
$schema: http://json-schema.org/draft-07/schema#
title: Author Corpus
type: object
properties:
  author_id:
    type: string
    description: "Normalized lead author name"
  total_abstracts:
    type: integer
    minimum: 10
  train_count:
    type: integer
    minimum: 8
  test_count:
    type: integer
    minimum: 2
  abstracts:
    type: array
    items:
      type: object
      properties:
        id:
          type: string
        processed_text:
          type: string
          minLength: 10
        char_tokens:
          type: array
          items:
            type: string
      required:
        - id
        - processed_text
        - char_tokens
required:
  - author_id
  - total_abstracts
  - train_count
  - test_count
  - abstracts
```

### 4.2 Perplexity Matrix Row Schema
```yaml
# contracts/perplexity_row.schema.yaml
$schema: http://json-schema.org/draft-07/schema#
title: Perplexity Matrix Row
type: object
properties:
  test_abstract_id:
    type: string
  true_author:
    type: string
  perplexities:
    type: object
    additionalProperties:
      type: number
      minimum: 0
      description: "Perplexity score under a specific author's model"
  predicted_author:
    type: string
  is_correct:
    type: boolean
required:
  - test_abstract_id
  - true_author
  - perplexities
  - predicted_author
  - is_correct
```

### 4.3 Final Results Schema
```yaml
# contracts/final_results.schema.yaml
$schema: http://json-schema.org/draft-07/schema#
title: Final Results
type: object
properties:
  ngram_accuracy:
    type: number
    minimum: 0
    maximum: 1
    description: "Classification accuracy of the best n-gram model"
  baseline_accuracy:
    type: number
    minimum: 0
    maximum: 1
    description: "Classification accuracy of the function-word baseline"
  mcnemar_p_value:
    type: number
    minimum: 0
    maximum: 1
  mcnemar_corrected_p_value:
    type: number
    minimum: 0
    maximum: 1
    description: "Bonferroni corrected p-value"
  is_significant:
    type: boolean
    description: "True if corrected p-value < 0.05"
  hybrid_accuracy_drop:
    type: number
    minimum: 0
    maximum: 1
    description: "Drop in accuracy on hybrid abstracts"
  best_n_order:
    type: integer
    enum: [4, 5, 6]
required:
  - ngram_accuracy
  - baseline_accuracy
  - mcnemar_p_value
  - mcnemar_corrected_p_value
  - is_significant
  - hybrid_accuracy_drop
  - best_n_order
```
