# Data Model: Evaluating the Effectiveness of Retrieval-Augmented Generation for Code Search

## Entities

### CodeSnippet
Represents a single unit of code from the dataset.

| Field | Type | Description |
|-------|------|-------------|
| `doc_id` | string | Unique identifier for the document. |
| `func_name` | string | Function name (if available). |
| `language` | string | Programming language (e.g., "python", "java"). |
| `path` | string | File path in the repository. |
| `repo` | string | Repository name. |
| `code` | string | Original code snippet. |
| `code_truncated` | string | Code snippet truncated to ≤ 256 tokens. |
| `api_density` | float | Ratio of API calls to total tokens (computed on query/GT). |
| `doc_density` | float | Ratio of comment tokens to total tokens (computed on query/GT). |
| `naming_consistency` | float | Average pairwise cosine similarity of identifier embeddings (computed on query/GT, orthogonalized). |

### QueryResult
Represents the output of a retrieval attempt. **Descriptors in this entity refer to the query and ground truth code, NOT the retrieved snippets.**

| Field | Type | Description |
|-------|------|-------------|
| `query_id` | string | Unique identifier for the query. |
| `query_text` | string | The search query (docstring). |
| `method` | string | Retrieval method ("bm25", "dual_encoder", "rag"). |
| `retrieved_ids` | list[string] | List of retrieved document IDs. |
| `relevance_labels` | list[int] | Ground truth relevance labels for retrieved docs (binary). |
| `ndcg_at_10` | float | Normalized Discounted Cumulative Gain at 10. |
| `precision_at_10` | float | Precision at 10. |
| `recall_at_10` | float | Recall at 10. |
| `api_density` | float | Descriptor value of the **query/GT** (not retrieved). |
| `doc_density` | float | Descriptor value of the **query/GT** (not retrieved). |
| `naming_consistency` | float | Descriptor value of the **query/GT** (not retrieved). |
| `bleu_score` | float | BLEU score of the generated answer (if RAG). |
| `rouge_score` | float | ROUGE-L score of the generated answer (if RAG). |

### PerformanceDelta
Derived entity for correlation analysis.

| Field | Type | Description |
|-------|------|-------------|
| `query_id` | string | Unique identifier for the query. |
| `method_baseline` | string | Baseline method name. |
| `method_rag` | string | RAG method name. |
| `delta_ndcg` | float | RAG nDCG - Baseline nDCG. |
| `delta_precision` | float | RAG Precision - Baseline Precision. |
| `api_density` | float | Descriptor value of the **query/GT**. |
| `doc_density` | float | Descriptor value of the **query/GT**. |
| `naming_consistency` | float | Descriptor value of the **query/GT** (orthogonalized). |

## Data Flow

1. **Raw Data**: `ir-datasets` → `data/raw/codesearchnet.jsonl` (checksummed).
2. **Processed Data**: Preprocessing script → `data/processed/snippets.csv` (with descriptors for query/GT only).
3. **Results**: Retrieval pipeline → `data/processed/results.csv` (metrics + descriptors from query/GT).
4. **Analysis**: Correlation script → `data/processed/correlations.json` (Spearman rho, Pearson r, p-values).
5. **Plots**: Scatter plots saved to `data/processed/plots/`.

## Constraints

- **Truncation**: All code snippets truncated to 256 tokens.
- **NaN Handling**: Missing descriptor values stored as string "NaN".
- **Reproducibility**: All random seeds pinned in `code/`.
- **Descriptor Scope**: Descriptors computed **only** on query and ground truth code, never on retrieved snippets.