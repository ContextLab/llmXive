# Data Model: OmniRetrieval Unified Validation

## Overview
This document defines the data structures for the input datasets, internal processing, and output artifacts. All data is validated against schemas defined in `contracts/`.

## Input Data Model

### 1. Text Query (BEIR)
- **Source**: `datasets.load_dataset("beir", "trec-covid")`
- **Fields**:
  - `query_id`: Unique string identifier.
  - `text`: The natural language query.
  - `corpus_subset`: List of document snippets (truncated for memory).
  - `gold_passages`: List of relevant document IDs (for validation, if available).

### 2. SQL Query (Spider)
- **Source**: `datasets.load_dataset("spider")` + Manual DB Fetch
- **Fields**:
  - `question_id`: Unique integer.
  - `question`: Natural language question.
  - `db_id`: Database identifier (e.g., "restaurant").
  - `gold_sql`: The ground truth SQL query (string).
  - `db_path`: Path to the locally extracted SQLite database file (constructed by loader).

### 3. SPARQL Query (LC-QuAD)
- **Source**: `datasets.load_dataset("lc-quad-2")`
- **Fields**:
  - `question_id`: Unique string.
  - `question`: Natural language question.
  - `gold_sparql`: The ground truth SPARQL query.
  - `graph_turtle`: String containing the RDF graph data (Turtle format) used to construct the in-memory graph.

## Internal Processing Model

### Engine Dispatch Record
- **Type**: `dict`
- **Fields**:
  - `query_id`: ID from input.
  - `source_type`: Enum `["TEXT", "SQL", "SPARQL"]`.
  - `engine_name`: String (e.g., "duckdb", "rdflib", "sentence-transformers").
  - `status`: Enum `["SUCCESS", "SKIPPED", "ERROR"]`.
  - `error_message`: String (if status is ERROR).

### Execution Result
- **Type**: `dict`
- **Fields**:
  - `query_id`: ID from input.
  - `answer`: The retrieved/generated answer (string or list of strings).
  - `latency_ms`: Execution time in milliseconds.
  - `engine_type`: Source type.
  - `validation_status`: Enum `["PASS", "FAIL", "N/A"]` (Result of FR-004 syntax check).
  - `syntax_error_details`: String (if validation_status is FAIL).
  - `metadata`: Additional info (e.g., number of retrieved docs, rows returned).

## Output Data Model

### Results File (`results.json`)
- **Format**: JSON Lines (`.jsonl`) or a single JSON object with a `results` array.
- **Structure**:
  ```json
  {
    "run_id": "uuid",
    "timestamp": "ISO8601",
    "total_queries": 150,
    "successful_queries": 148,
    "results": [
      {
        "query_id": "spider_001",
        "source_type": "SQL",
        "engine": "duckdb",
        "answer": "SELECT name FROM restaurant WHERE city = 'New York'",
        "latency_ms": 120,
        "status": "SUCCESS",
        "validation_status": "PASS",
        "syntax_error_details": null
      }
    ]
  }
  ```

## Data Flow Diagram (Textual)
1. **Loader** (BEIR/Spider/LC-QuAD) → **Sampler** (50 queries) → **Dispatcher**
2. **Dispatcher** → Routes to **Text Engine** OR **SQL Engine** OR **SPARQL Engine**
3. **Engine** → Executes query → Returns **Result**
4. **Result Aggregator** → Collects results → Writes **results.json**
5. **Logger** → Writes **execution.log**