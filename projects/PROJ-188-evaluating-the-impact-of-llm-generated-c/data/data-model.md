# Data Model Specification
# Project: PROJ-188-evaluating-the-impact-of-llm-generated-c

## Overview
This document defines the schema for all data entities used in the automated science pipeline.
All data artifacts produced by the scripts in `code/` must conform to these schemas.

## Entities

### Snippet
Represents a code snippet from the CodeSearchNet corpus.
- `snippet_id`: string (unique identifier, e.g., "csn-python-001")
- `code`: string (the raw source code)
- `complexity`: string (label: "low", "medium", or "high")
- `complexity_score`: float (raw cyclomatic complexity score)

### Explanation
Represents an LLM-generated explanation for a code snippet.
- `snippet_id`: string (foreign key to Snippet)
- `explanation`: string (natural language explanation)
- `token_count`: integer (number of tokens in the explanation)
- `model_used`: string (name of the model that generated the explanation)
- `status`: string ("success", "skipped", "failed")

### Condition
Represents a survey condition rendering.
- `condition_id`: string (e.g., "A", "B", "C")
- `description`: string (e.g., "Code only", "Code + LLM Explanation")
- `rendered_content`: object (contains `code` and optionally `explanation` or `docstring`)

### Response
Represents a participant's answer to a survey question.
- `participant_id`: string (unique participant identifier)
- `condition`: string (the condition presented: "A", "B", or "C")
- `snippet_id`: string (foreign key to Snippet)
- `answer`: boolean (whether the participant understood the code)
- `latency_ms`: integer (time taken to answer in milliseconds)
- `timestamp`: string (ISO 8601 format)
- `missing_count`: integer (number of unanswered questions for this participant)

## Data Flow
1. **Ingestion**: `code/01_data_curation.py` produces `Snippet` and `Explanation` entities.
2. **Survey Logic**: `code/02_survey_logic.py` produces `Condition` and `Response` entities (mock).
3. **Ingestion**: `code/02_ingest_responses.py` ingests real `Response` data.
4. **Filtering**: `code/03_filter_responses.py` updates `Response` with `missing_count` and filters invalid participants.
5. **Analysis**: `code/03_analysis.py` consumes filtered `Response` and `Snippet` data.

## File Locations
- `data/raw/`: Original datasets (CodeSearchNet)
- `data/intermediate/`: Processed snippets, explanations, mock responses
- `data/processed/`: Final analysis results, sensitivity reports