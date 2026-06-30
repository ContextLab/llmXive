# Implementation Plan: OmniRetrieval Unified Validation (Architecture & Robustness)

**Branch**: `644-omniretrieval-validation` | **Date**: 2024-05-22 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/644-omniretrieval-validation/spec.md`

## Summary
This plan validates the **Architectural Integrity** and **Operational Robustness** of the "OmniRetrieval" framework by executing a sampled subset of heterogeneous benchmarks (Text/BEIR, SQL/Spider, Graph/LC-QuAD) on a CPU-only, free-tier CI environment.

**Scope Clarification**:
1.  **Operational Validation**: The primary goal is to verify that the "unified" dispatcher correctly routes queries to distinct native engines (SQL, SPARQL, Text) and that the system executes without crashes under resource constraints.
2.  **Performance Limitation**: This phase **does not** validate the scientific performance claims (accuracy, F1, nDCG) of the original paper. The original paper likely relies on a generative model with reasoning capabilities. This plan uses a CPU-optimized bi-encoder (`all-MiniLM-L6-v2`) and a mock generation step. Therefore, success is defined as "zero crashes" and "correct routing," not "high retrieval accuracy."
3.  **Future Scope**: A full "Paper Reproduction" involving generative models and performance benchmarking is a separate scope requiring GPU resources and is explicitly out of bounds for this feature branch.

**Approach**: Robustness (graceful degradation on missing data), resource constraints (streaming, CPU-optimized models), and explicit automated verification of the dispatch logic via an "Oracle Test".

## Technical Context
**Language/Version**: Python 3.10+  
**Primary Dependencies**: `torch` (CPU-only), `sentence-transformers` (MiniLM), `duckdb` (SQL), `rdflib` (SPARQL), `beir` (framework), `datasets` (HuggingFace), `pytest`  
**Storage**: Local `data/` directory (ephemeral), `results.json` (output)  
**Testing**: `pytest` (contract tests, integration smoke tests, automated dispatch verification)  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM)  
**Project Type**: Research Validation Pipeline / CLI Tool  
**Performance Goals**: < 4h total runtime, < 6.5GB peak RAM, < 1GB dataset footprint  
**Constraints**: No GPU, no external LLM API keys (mock/local only), strict error handling for network timeouts  
**Scale/Scope**: Sampled subset of benchmarks (approx. 50 queries per dataset) to fit CI limits.

**Confirmed Dataset Sources**:
- **BEIR**: `datasets.load_dataset("beir", "trec-covid")` (Text Retrieval)
- **Spider**: `datasets.load_dataset("spider")` + Manual DB fetch from official repo (SQL)
- **LC-QuAD**: `datasets.load_dataset("lc-quad-2")` (SPARQL)

> Note: Specific dataset sizes and empirical success rates are deferred to `research.md` and `data-model.md`.

## Constitution Check
*Gates determined based on constitution file (FR-030)*

**Status**: Project-specific `constitution.md` exists at `projects/<PROJ-ID>/.specify/memory/constitution.md`.
**Action**: The plan explicitly maps decisions to the project's constitutional principles.

1.  **Principle I (SSoT)**: The plan adheres to the `spec.md` as the Single Source of Truth. It does not introduce new requirements (e.g., performance metrics) that contradict the "execution and validation" scope.
2.  **Principle II (Data Integrity)**: The plan mandates checksum verification and graceful degradation for missing datasets (FR-006), ensuring data integrity even in failure modes.
3.  **Principle III (Real-call Testing)**: The plan implements an "Automated Dispatch Oracle" that asserts the system's behavior against the dataset's ground truth metadata (e.g., `source_type` must match `engine_type`), replacing subjective manual inspection.
4.  **Principle IV (Feasibility)**: All methods (CPU-only transformers, streaming loaders, sampled data) are validated against the 7GB RAM / 6h runtime constraint.
5.  **Principle V (Scope Adherence)**: The plan strictly adheres to the spec's "execution and validation" scope, explicitly avoiding model re-training or architecture modification.

## Project Structure

### Documentation (this feature)
```text
specs/644-omniretrieval-validation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)
```text
src/
├── main.py              # Entry point (orchestrator)
├── config.py            # Configuration management
├── engines/
│   ├── base.py          # Abstract engine interface
│   ├── sql_engine.py    # DuckDB/SQL execution
│   ├── sparql_engine.py # RDFLib/SPARQL execution
│   └── text_engine.py   # Dense retrieval (BEIR)
├── loaders/
│   ├── base_loader.py   # Abstract data loader
│   ├── beir_loader.py   # BEIR dataset handling
│   ├── spider_loader.py # Spider dataset handling (includes DB fetch)
│   └── quad_loader.py   # LC-QuAD dataset handling (includes graph build)
├── utils/
│   ├── retry.py         # Retry logic for network (FR-006)
│   ├── memory_monitor.py# RAM tracking (FR-005)
│   └── logger.py        # Structured logging
└── validation/
    ├── dispatcher_test.py # Verify routing logic (US-2) - Automated
    └── smoke_test.py      # End-to-end run (US-1)

tests/
├── contract/
│   ├── test_schema_validation.py
│   └── test_output_format.py
├── integration/
│   └── test_full_pipeline.py
└── unit/
    └── test_engines.py

data/
└── (downloaded subsets - ephemeral)

results/
└── results.json         # Final artifact
```

**Structure Decision**: Single-project structure with modular `engines` and `loaders` to support the heterogeneous nature of the data sources. This allows for isolated testing of the dispatch logic while sharing common retry and memory monitoring utilities.

## Complexity Tracking
*No violations detected; complexity is driven by the spec's requirement to support three distinct data modalities (Text, SQL, Graph) within tight resource constraints.*

## Phase Breakdown

### Phase 0: Research & Feasibility (Research Complete)
*Goal: Validate connectivity to confirmed dataset sources.*
- **Action**: Validate connectivity to `datasets.load_dataset("beir", "trec-covid")`.
- **Action**: Validate connectivity to `datasets.load_dataset("spider")` and confirm the separate DB fetch script is available.
- **Action**: Validate connectivity to `datasets.load_dataset("lc-quad-2")` and confirm `graph_turtle` fields are present.
- **Action**: Execute a sample load (5 queries) for each dataset to verify RAM footprint and parsing logic.

### Phase 1: Data Model & Contracts (Design Complete)
*Goal: Define schemas for inputs and outputs.*
- **Action**: Define `dataset.schema.yaml` to validate downloaded data structures (query, context, gold_label).
- **Action**: Define `output.schema.yaml` to enforce the structure of `results.json` (query_id, engine_type, answer, latency, status, **validation_status**).
- **Action**: Create `quickstart.md` with instructions for setting up the environment and running the smoke test.

### Phase 2: Implementation (Implementer Agent)
*Goal: Write the code.*
- **Action**: Implement `main.py` with the orchestration loop.
- **Action**: Implement `engines/` for SQL, SPARQL, and Text retrieval.
- **Action**: Implement `loaders/` with retry logic and memory monitoring.
- **Action**: Implement `utils/retry.py` for FR-006 (network timeouts).
- **Action**: Implement `utils/memory_monitor.py` for FR-005 (RAM ceiling).
- **Action**: Implement `loaders/spider_loader.py` to handle the two-step DB fetch from the official repo.

### Phase 3: Validation & Testing (Research Complete)
*Goal: Execute the pipeline and verify success criteria.*
- **Action**: Run `pytest` against the full pipeline on a sampled dataset.
- **Action**: Verify `SC-001` (zero crashes) and `SC-002` (correct dispatch logs - **Automated via Oracle Test**).
- **Action**: Verify `SC-003` (resource usage) and `SC-004` (artifact validity).
- **Action**: Generate final `results.json` and logs.
- **Action**: **Automated Dispatch Oracle Test**: Assert that `source_type='SQL'` triggers `duckdb` engine, `source_type='SPARQL'` triggers `rdflib` engine, etc. The test asserts that the `engine_type` field in the output artifact matches the `source_type` in the input metadata for every query.

## FR/SC Mapping
- **FR-001** (Pipeline Execution) → Phase 2 (main.py), Phase 3 (smoke_test.py).
- **FR-002** (Artifact Generation) → Phase 2 (output writers), Phase 3 (contract tests).
- **FR-003** (Dispatch Logic) → Phase 2 (dispatchers), Phase 3 (dispatcher_test.py - Automated).
- **FR-004** (Syntax Validation) → Phase 2 (engine pre-checks), Phase 3 (output schema validation - `validation_status` field).
- **FR-005** (Memory Ceiling) → Phase 2 (memory_monitor.py), Phase 3 (resource monitoring).
- **FR-006** (Retry Logic) → Phase 2 (utils/retry.py).
- **FR-007** (Logging) → Phase 2 (utils/logger.py).
- **SC-001** (Zero Crashes) → Phase 3 (exit code check).
- **SC-002** (Correct Dispatch) → Phase 3 (Automated Oracle Test asserting `engine_type == source_type`).
- **SC-003** (Resource Efficiency) → Phase 3 (RAM/Time monitoring).
- **SC-004** (Artifact Validity) → Phase 3 (schema validation).