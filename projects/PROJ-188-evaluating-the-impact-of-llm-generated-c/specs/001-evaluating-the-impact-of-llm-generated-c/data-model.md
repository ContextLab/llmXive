# Data Model: Evaluating the Impact of LLM-Generated Code Explanations on Comprehension

## Entities

### Snippet
Represents a Python function from the corpus.
- `snippet_id`: Unique identifier (string).
- `code`: Raw Python code (string).
- `complexity_label`: Enum {low, medium, high}.
- `official_docstring`: String (may be null).
- `complexity_score`: Float (cyclomatic complexity raw score).
- `source`: String (dataset source identifier).

### Response
Represents a single trial from a participant.
- `response_id`: Unique identifier (string).
- `participant_id`: Anonymized ID (string).
- `snippet_id`: Foreign key to Snippet.
- `condition`: Enum {code_only, code_llm, code_docstring}.
- `answer`: Boolean (1=correct, 0=incorrect).
- `latency_ms`: Integer (time from load to submit).
- `timestamp`: ISO8601 string.
- `missing_count`: Integer, default=0 (number of unanswered questions for this participant).

### Explanation
Represents the LLM-generated text associated with a snippet.
- `explanation_id`: Unique identifier (string).
- `snippet_id`: Foreign key to Snippet.
- `text`: Generated explanation (string).
- `token_count`: Integer.
- `generation_timestamp`: ISO8601 string.
- `model_used`: String (e.g., "CodeLlama-7B", "TinyLlama").
- `status`: Enum {success, failed, skipped}.

### AnalysisResult
Aggregated statistical output.
- `analysis_id`: Unique identifier.
- `model_type`: String (e.g., "LMM_Interaction").
- `interaction_f_stat`: Float.
- `interaction_p_value`: Float.
- `bleu_threshold`: Float (for sensitivity rows).
- `timestamp`: ISO8601 string.

## Data Flow

1. **Ingestion**: `CodeSearchNet` parquet -> `Snippet` table (raw).
2. **Generation**: `Snippet` + `CodeLlama` -> `Explanation` table (intermediate).
3. **Survey**: `Snippet` + `Explanation` + `Condition` -> `Response` (raw logs).
4. **Cleaning**: `Response` (filter <30s, >80% missing) -> `Response` (clean).
5. **Analysis**: `Clean` + `Explanation` (BLEU) -> `AnalysisResult`.