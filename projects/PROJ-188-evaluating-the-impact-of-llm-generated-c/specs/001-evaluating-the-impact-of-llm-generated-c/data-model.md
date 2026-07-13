# Data Model: Evaluating the Impact of LLM-Generated Code Explanations on Comprehension

## Entities

### CodeSnippet
Represents a Python function from the corpus.
- `snippet_id`: Unique identifier (string).
- `source_code`: Raw Python code (string).
- `complexity_label`: Enum {low, medium, high}.
- `official_docstring`: String (may be null).
- `complexity_score`: Integer (cyclomatic complexity).

### Explanation
Represents the LLM-generated text.
- `explanation_id`: Unique identifier (string).
- `snippet_id`: Foreign key to CodeSnippet.
- `text`: Generated explanation (string).
- `token_count`: Integer.
- `generation_timestamp`: ISO8601 string.
- `status`: Enum {success, failed, skipped}.

### ParticipantResponse
Represents a single trial from a participant.
- `response_id`: Unique identifier (string).
- `participant_id`: Anonymized ID (string).
- `snippet_id`: Foreign key to CodeSnippet.
- `condition`: Enum {code_only, code_llm, code_docstring}.
- `answer`: Boolean (1=correct, 0=incorrect).
- `latency_ms`: Integer (time from load to submit).
- `is_valid`: Boolean (passed quality filters).

### AnalysisResult
Aggregated statistical output.
- `analysis_id`: Unique identifier.
- `model_type`: String (e.g., "LMM_Interaction").
- `interaction_f_stat`: Float.
- `interaction_p_value`: Float.
- `bleu_threshold`: Float (for sensitivity rows).
- `timestamp`: ISO8601 string.

## Data Flow

1.  **Ingestion**: `CodeSearchNet` parquet -> `CodeSnippet` table (raw).
2.  **Generation**: `CodeSnippet` + `CodeLlama` -> `Explanation` table (intermediate).
3.  **Survey**: `CodeSnippet` + `Explanation` + `Condition` -> `ParticipantResponse` (raw logs).
4.  **Cleaning**: `ParticipantResponse` (filter <30s, >80% missing) -> `ParticipantResponse` (clean).
5.  **Analysis**: `Clean` + `Explanation` (BLEU) -> `AnalysisResult`.
