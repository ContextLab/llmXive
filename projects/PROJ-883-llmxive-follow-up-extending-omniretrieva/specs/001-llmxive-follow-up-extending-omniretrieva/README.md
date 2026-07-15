# Structural Mismatch Cost in Heterogeneous Retrieval
## Design Document

This specification defines the research pipeline for quantifying the latency penalties and translation error rates when executing heterogeneous queries (text, relational, graph) under CPU-constrained environments.

## Key Concepts

- **Structural Mismatch**: The cost incurred when translating a query plan from one data model to another
- **Complexity Level**: Integer measure of query plan depth (1, 2, 3, 4+)
- **CPU Throttling**: Enforced time limits to simulate resource-constrained environments

## User Stories

1. **US1**: Quantify Latency Penalties - Measure end-to-end latency differences
2. **US2**: Measure Translation Error Rates - Track plan mismatch frequency
3. **US3**: Visualize Non-Linear Scaling - Generate interaction plots

## Data Sources

- **MS MARCO**: Text retrieval corpus (HuggingFace: sentence-transformers/msmarco-corpus)
- **Spider**: Text-to-SQL benchmark (HuggingFace: spider)
- **DBpedia/Wikidata**: Graph triples (HuggingFace: dbpedia/dbpedia-entities)

## Configuration

All configuration is managed in `code/config.py`:
- Dataset URLs and schema requirements
- CPU throttling parameters
- Random seeds for reproducibility
- Fallback to synthetic generation

## Exit Codes

- `0`: Success
- `1`: Throttling failure (CPU limits not enforced)
- `2`: Data fetch failure
- `3`: Configuration error

## Implementation Status

- [X] T001: Project structure
- [X] T002: Dependencies
- [X] T003: Linting/Formatting
- [X] T004: Data schemas
- [X] T005: Configuration module (this task)
- [ ] T007: Reference engine
- [ ] T006: Synthetic query generator
- [ ]... (remaining tasks)
