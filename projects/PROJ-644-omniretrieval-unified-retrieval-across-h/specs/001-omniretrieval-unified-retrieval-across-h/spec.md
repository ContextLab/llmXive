# Feature Specification: OmniRetrieval Unified Validation

**Feature Branch**: `644-omniretrieval-validation`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: OmniRetrieval: Unified Retrieval across Heterogeneous Knowledge Sources"

## User Scenarios & Testing

### User Story 1 - Core Pipeline Execution & Artifact Generation (Priority: P1)

As a researcher, I want to execute the vendored OmniRetrieval codebase end-to-end on a subset of available datasets so that I can confirm the system initializes correctly, processes heterogeneous data sources (text, relational, graph), and generates real, non-empty output artifacts (JSON logs, result files) without runtime crashes.

**Why this priority**: This is the foundational "smoke test." If the code cannot run or produces empty artifacts, no further validation of the paper's claims is possible. It verifies the environment setup and the basic operational integrity of the framework.

**Independent Test**: The CI runner executes the `main.py` entry point with a minimal configuration (e.g., a single dataset from the `beir` or `spider` suite). The test passes if the process exits with code 0 and the output directory contains at least one non-empty JSON result file and one log file with ≥ 10 lines of execution history.

**Acceptance Scenarios**:

1. **Given** the codebase is checked out and dependencies are installed, **When** the `main.py` script is invoked with the `beir` dataset subset and a mock LLM client (or a local lightweight model), **Then** the process completes within 30 minutes and generates a `results.json` file containing ≥ 1 record with a non-null `answer` field.
2. **Given** the system is running, **When** the script encounters a missing optional dataset (e.g., `lcquad2` not downloaded), **Then** the system logs a warning, skips that specific dataset, and continues execution without crashing, eventually exiting with code 0.
3. **Given** the environment has limited disk space (≤ 14 GB), **When** the script attempts to download and cache data, **Then** it successfully downloads the minimal required subset (≤ 1 GB) and stores it in the local `data/` directory without triggering an out-of-disk error.

---

### User Story 2 - Heterogeneous Source Dispatch Verification (Priority: P2)

As a researcher, I want to verify that the OmniRetrieval framework correctly identifies and dispatches queries to the appropriate native execution engines (e.g., SPARQL for knowledge graphs, SQL for relational tables, dense retrieval for text) based on the query type, so that the "unified" aspect of the system is functionally demonstrated.

**Why this priority**: The core novelty of the paper is the "overarching layer" that preserves structural affordances. Validating that the system actually routes queries correctly (rather than collapsing them into a single format) is essential to confirming the architectural claim.

**Independent Test**: Run the evaluation script against a mixed-benchmark subset containing at least one text-based query (BEIR), one SQL query (Spider), and one SPARQL query (LC-QuAD). The test passes if the logs explicitly show the dispatch logic selecting distinct execution paths for each query type and the generated intermediate artifacts (e.g., generated SQL/SPARQL strings) are syntactically valid for their respective engines.

**Acceptance Scenarios**:

1. **Given** a query from the Spider dataset, **When** the system processes it, **Then** the execution log explicitly records "Dispatched to: SQL Engine" and the generated query string contains valid SQL syntax (e.g., `SELECT`, `FROM`, `WHERE`).
2. **Given** a query from the LC-QuAD dataset, **When** the system processes it, **Then** the execution log explicitly records "Dispatched to: SPARQL Engine" and the generated query string contains valid SPARQL syntax (e.g., `PREFIX`, `SELECT`, `WHERE` with triple patterns).
3. **Given** a query from the BEIR dataset, **When** the system processes it, **Then** the execution log explicitly records "Dispatched to: Text Retrieval Engine" and the system returns a ranked list of document IDs rather than a structured query string.

---

### User Story 3 - Performance & Resource Constraint Validation (Priority: P3)

As a CI engineer, I want to ensure the reproduction pipeline completes within the GitHub Actions free-tier constraints (≤ 6 hours, ≤ 7 GB RAM, CPU-only) so that the validation can be automated and repeated without requiring paid infrastructure.

**Why this priority**: The project is defined as a "free-CPU" research reproduction. If the default implementation requires GPU or exceeds 6 hours on a full dataset, the project cannot reach the `research_complete` stage. This story ensures the scope is adjusted to fit the hardware constraints.

**Independent Test**: Run the full evaluation pipeline on the standard benchmark suite (or a representative 20% sample) on a simulated 2-core, 7GB RAM environment. The test passes if the total wall-clock time is ≤ 4 hours (providing a 2-hour buffer) and peak memory usage remains ≤ 6 GB.

**Acceptance Scenarios**:

1. **Given** the full evaluation script is running on the default configuration, **When** the process completes, **Then** the total execution time is ≤ 4 hours and the final log contains a summary line: `Total Runtime: <4h`.
2. **Given** the system is processing a large corpus (e.g., BEIR), **When** the memory usage is monitored, **Then** the peak RSS (Resident Set Size) does not exceed 6.5 GB, triggering a memory-efficient streaming mode if the limit is approached.
3. **Given** the system attempts to load a large embedding model, **When** the model initialization starts, **Then** it defaults to a CPU-optimized quantization (e.g., 16-bit float) or a smaller model variant (e.g., `all-MiniLM-L6-v2`) rather than attempting to load a large 7B+ parameter model, ensuring no CUDA errors occur.

---

### Edge Cases

- **What happens when the external LLM client is unreachable?** The system must handle network timeouts gracefully (retry up to 3 times with exponential backoff) and log a specific error code without crashing the entire pipeline.
- **How does the system handle malformed queries in the dataset?** If a dataset entry contains a query that cannot be parsed by the native engine (e.g., invalid SQL), the system must log the error, skip the entry, and continue processing the remaining [deferred] of the dataset rather than failing the whole run.
- **What happens if the downloaded dataset is corrupted?** The system must verify file checksums during the download phase; if a checksum mismatch occurs, it must delete the corrupted file, re-download it (up to 2 retries), and abort with a clear error if the second attempt fails.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST execute the `main.py` entry point to orchestrate the full retrieval pipeline across text, relational, and graph sources without manual intervention (See US-1).
- **FR-002**: The system MUST generate output artifacts (JSON results, execution logs) that are non-empty and contain at least one valid response per processed query (See US-1).
- **FR-003**: The system MUST detect the source type of an incoming query and dispatch it to the corresponding native execution engine (SQL, SPARQL, or Text Retriever) (See US-2).
- **FR-004**: The system MUST validate the syntax of generated queries (SQL/SPARQL) before dispatching them to the execution engine to prevent runtime engine errors (See US-2).
- **FR-005**: The system MUST enforce a memory ceiling of 6.5 GB during execution by using streaming data loaders and CPU-optimized model configurations (See US-3).
- **FR-006**: The system MUST handle network timeouts for external dependencies (LLM APIs, dataset downloads) by implementing a retry mechanism with a maximum of 3 attempts and a total wait time of ≤ 60 seconds (See Edge Cases).
- **FR-007**: The system MUST log the total execution time and peak memory usage to a summary report at the end of the run (See US-3).

### Key Entities

- **Query**: A natural language request that is classified by source type and transformed into a native query format.
- **Execution Engine**: The specific backend component (SQL, SPARQL, or Vector Store) responsible for processing the native query.
- **Retrieval Result**: The structured output containing the retrieved context, generated answer, and metadata (latency, source type).
- **Dataset Subset**: A specific, bounded collection of data (e.g., 100 queries from Spider) used for validation to fit resource constraints.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The success rate of pipeline execution is measured against the requirement of "zero crashes" on the validation dataset subset (See US-1).
- **SC-002**: The correctness of source dispatch is measured against the manual inspection of execution logs to confirm the correct engine was invoked for each query type (See US-2).
- **SC-003**: The resource efficiency is measured against the constraint of ≤ 6 GB peak RAM and ≤ 4 hours total runtime on a 2-core CPU (See US-3).
- **SC-004**: The artifact validity is measured by the presence of at least one non-null `answer` field in the generated `results.json` for every processed query (See US-1).

## Assumptions

- **Assumption about data/environment**: The GitHub Actions free-tier runner (2 CPU, 7 GB RAM) is sufficient to run the validation pipeline on a sampled subset of the benchmarks (e.g., 10-20% of the full dataset) without requiring GPU acceleration.
- **Assumption about scope boundaries**: The reproduction focuses on *execution and validation* of the existing code, not on re-training the underlying models or optimizing the model architecture; model weights are loaded in their default state.
- **Assumption about target users**: The primary "user" of this pipeline is the automated CI system; manual intervention is only required for initial setup or debugging of environment-specific errors.
- **Assumption about external dependencies**: The external LLM client (if used for generation) will be replaced with a local, lightweight model (e.g., `sentence-transformers/all-MiniLM-L6-v2`) or a mock service to ensure the pipeline is fully reproducible without API keys or network latency.
- **Assumption about dataset availability**: The required datasets (Spider, BEIR, etc.) are available via the provided download scripts and will fit within the 14 GB disk limit of the runner.
