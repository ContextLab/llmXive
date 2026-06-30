# Data Model: Reproduce & Validate Active Learners as Efficient PRP Rerankers

## Overview
This document defines the data structures used for the PRP reranking experiments. It ensures consistency between the input data (BEIR), the internal processing (pairs, rankings), and the output artifacts (CSVs, metrics). It now includes the `BudgetLog` entity for strict budget enforcement tracking.

## Core Entities

### Query
Represents a search query from the BEIR dataset.
- **id**: `str` (Unique identifier, e.g., "1")
- **text**: `str` (The query string)
- **dataset**: `str` (e.g., "dbpedia-entity", "scifact")
- **difficulty_bin**: `str` (High, Medium, Low - derived from initial BM25 score)

### Document
Represents a candidate document retrieved by the initial BM25 step.
- **id**: `str` (Unique document ID)
- **text**: `str` (Document content)
- **score**: `float` (BM25 score from initial retrieval)

### QueryDocumentPair
The atomic unit of comparison for the oracle.
- **query_id**: `str`
- **doc_a_id**: `str`
- **doc_b_id**: `str`
- **doc_a_text**: `str`
- **doc_b_text**: `str`
- **order**: `str` ("A-B" or "B-A" - randomized by oracle)
- **oracle_response**: `str` (e.g., "A", "B", "Tie")
- **oracle_score**: `float` (Derived score, e.g., +1 for A, -1 for B)

### Ranking
An ordered list of documents for a specific query.
- **query_id**: `str`
- **documents**: `List[str]` (Ordered list of document IDs)
- **scores**: `List[float]` (Optional: final scores assigned by the reranker)
- **calls_made**: `int` (Number of LLM calls used to generate this ranking)

### BudgetLog
Records of every budget enforcement event. Used for validation of FR-003.
- **timestamp**: `str` (ISO 8601)
- **query_id**: `str`
- **budget_limit**: `int` (Configured limit)
- **calls_at_event**: `int` (Current count)
- **action**: `str` ("ALLOWED", "BLOCKED", "SKIPPED")
- **reason**: `str` (e.g., "Budget exceeded", "Pair skipped due to timeout")

### MetricResult
The aggregated performance metric for a run.
- **dataset**: `str`
- **model**: `str` (e.g., "ActiveLearner", "ClassicSort")
- **budget**: `int`
- **ndcg_at_10**: `float`
- **calls_used**: `int`
- **seed**: `int`
- **timestamp**: `str` (ISO 8601)
- **difficulty_bin**: `str` (Optional: if stratified)

## Data Flow

1.  **Input**: BEIR Parquet/TSV files -> `Query`, `Document` (via `data_loader.py`).
2.  **Stratification**: Queries binned by BM25 score -> `Query` (with `difficulty_bin`).
3.  **Preprocessing**: Top-K documents per query selected -> `QueryDocumentPair` candidates.
4.  **Processing**: `Oracle` generates `oracle_response` for selected pairs -> `Ranking` updated; `BudgetLog` written.
5.  **Output**: `Ranking` -> `MetricResult` -> `summary.csv`; `BudgetLog` -> `budget_enforcer_logs/`.

## Constraints & Types
- **Text Length**: Documents are truncated to the model's context window limit if necessary to fit.
- **Numeric Precision**: All scores are `float64` to ensure reproducibility within 1e-6 tolerance.
- **IDs**: All IDs are treated as strings to handle non-numeric document IDs.
- **Budget Enforcement**: `BudgetLog` must be written for every decision point in the `BudgetEnforcer`.