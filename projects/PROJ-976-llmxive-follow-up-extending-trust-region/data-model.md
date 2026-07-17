# Data Model: Diversity Profile Extension

## Entities

### TrainingInstance
Represents a single data point for analysis.
```yaml
type: object
properties:
 id: string # Unique identifier
 source: string # 'book_corpus' or 'beir'
 text: string # Tokenized text or raw text
 features: object # Lexical and syntactic metrics
 proxy_target: number # Relevance score or text length
 proxy_label: string # 'low_relevance' or 'high_relevance'
```

### FeatureVector
```yaml
type: object
properties:
 distinct_4_ratio: number
 ngram_entropy: number
 syntactic_variation_score: number
 parse_tree_depth_variance: number
```

## Proxy Targets
- **Book Corpus**: `text_length` (number of tokens)
- **BEIR**: `relevance_score` (float)

## Schema Validation
All data must conform to `specs/001-llmxive-trb-diversity-profile/contracts/dataset.schema.yaml`.
