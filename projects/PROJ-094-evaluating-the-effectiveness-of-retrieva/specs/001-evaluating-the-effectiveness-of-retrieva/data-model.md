# Data Model: Evaluating the Effectiveness of Retrieval‑Augmented Generation for Code Search

## Entity Definitions

### CodeSnippet
Represents a single unit of code from the dataset.

| Field | Type | Description |
|-------|------|-------------|
| `doc_id` | string | Unique identifier (e.g., `python/path/to/file.py:func_name`) |
| `repo` | string | Repository name |
| `path` | string | File path within repo |
| `func_name` | string | Function/method name |
| `code` | string | Full source code (truncated to ≤256 tokens) |
| `language` | string | Programming language (e.g., "python", "java") |
| `docstring` | string | Natural language description (used as query) |
| `api_density` | float | Ratio of API calls to total tokens |
| `doc_density` | float | Ratio of comment tokens to total tokens |
| `naming_consistency` | float | Average pairwise cosine similarity of identifier embeddings (CodeBERT-base) |
| `truncated` | boolean | True if code was truncated |

### QueryResult
Represents the output of a retrieval attempt for a specific query.

| Field | Type | Description |
|-------|------|-------------|
| `query_id` | string | Unique identifier for the query |
| `method` | string | Retrieval method (e.g., "bm25", "dual_encoder", "rag") |
| `retrieved_ids` | list[string] | List of retrieved `doc_id`s in ranked order |
| `ground_truth_labels` | list[int] | Relevance labels for retrieved snippets (0/1) |
| `precision_at_10` | float | Precision@10 score |
| `recall_at_10` | float | Recall@10 score |
| `ndcg_at_10` | float | nDCG@10 score |

### PerformanceDelta
Derived entity representing the difference in metric scores between RAG and a baseline.

| Field | Type | Description |
|-------|------|-------------|
| `query_id` | string | Unique identifier for the query |
| `baseline_method` | string | Baseline method (e.g., "bm25", "dual_encoder") |
| `ndcg_delta` | float | RAG nDCG@10 − Baseline nDCG@10 |
| `precision_delta` | float | RAG Precision@10 − Baseline Precision@10 |
| `api_density` | float | API density of the query's code snippet |
| `doc_density` | float | Documentation density of the query's code snippet |
| `naming_consistency` | float | Naming consistency score of the query's code snippet |

### CorrelationResult
Statistical analysis output for descriptor vs. delta correlation.

| Field | Type | Description |
|-------|------|-------------|
| `descriptor` | string | Descriptor name (e.g., "api_density") |
| `rho` | float | Spearman correlation coefficient |
| `p_value` | float | p-value for the correlation |
| `significant` | boolean | True if p < 0.05 |

### NoiseEstimate
Output from the manual spot-check (FR-010).

| Field | Type | Description |
|-------|------|-------------|
| `sample_size` | int | Number of labels manually checked |
| `noise_rate` | float | Estimated percentage of mislabeled ground truth |
| `method` | string | "manual" or "heuristic" |

## Data Flow

1. **Raw Data**: Downloaded from CodeSearchNet (HuggingFace/`ir-datasets`) → `data/raw/`
2. **Preprocessing**: Truncation, ASCII stripping, tokenization → `data/processed/preprocessed_snippets.csv`
3. **Descriptor Calculation**: API density, doc density, naming consistency computed → `data/processed/descriptors.csv`
4. **Label Noise Estimation**: Manual spot-check of labels → `results/noise_estimate.json`
5. **Retrieval**: BM25, Dual-Encoder, RAG executed → `results/retrieval_results.json`
6. **Metrics**: Precision, Recall, nDCG calculated (noise-weighted) → `results/metrics.csv`
7. **Control Experiment**: Masked retrieval run → `results/control_metrics.csv`
8. **Analysis**: Correlation, significance testing → `results/correlation.json`
9. **Final Output**: Combined results → `results/final_results.csv`

## Schema Validation

All data files must conform to the schemas defined in `contracts/`:
- `dataset.schema.yaml`: Raw/processed dataset schema
- `metrics.schema.yaml`: Evaluation metrics schema
- `descriptors.schema.yaml`: Semantic descriptors schema

## Data Hygiene

- **Checksums**: All raw data files checksummed and recorded in `state/.../artifact_hashes`.
- **Immutable Raw Data**: Raw data never modified in place. Derivations written to new files.
- **PII Scan**: No PII allowed in committed data. `data/raw` excluded from git.