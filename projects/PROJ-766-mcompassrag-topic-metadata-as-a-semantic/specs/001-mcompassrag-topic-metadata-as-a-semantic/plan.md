# Implementation Plan: MCompassRAG: Topic Metadata as a Semantic Compass for Paragraph-Level Retrieval

**Branch**: `766-mcompassrag-topic-metadata-as-a-semantic` | **Date**: 2024-05-22 | **Spec**: [spec.md]
**Input**: Feature specification from `/specs/766-mcompassrag-topic-metadata-as-a-semantic/spec.md`

## Summary

This project reproduces the MCompassRAG pipeline, focusing on validating its ability to run on CPU-only CI (GitHub Actions free tier) while generating retrieval artifacts and performance metrics. The technical approach involves adapting the existing codebase to enforce CPU execution, implementing **stratified sampling** (after synthetic topic generation if necessary) to fit within 7 GB RAM, and creating robust error handling for missing external dependencies.

Crucially, the plan addresses the **causal inference gap** by defining a **Control Group** (Baseline Retriever without topic metadata) to run in parallel with the MCompass Retriever. This allows for a direct A/B comparison to isolate the effect of topic metadata. The plan reframes the goal from "statistical validation of 5x improvement" (which requires a larger sample) to a **"Feasibility & Mechanism Proof"**, demonstrating that the topic metadata mechanism functions as intended on a representative subset.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `scikit-learn`, `pandas`, `datasets` (HuggingFace), `pyyaml`  
**Storage**: Local file system. Output artifacts serialized as **JSON** (for human readability) and **Parquet** (for bulk analysis).  
**Testing**: `pytest` (unit/integration), GitHub Actions workflows (CI validation)  
**Target Platform**: Linux server (GitHub Actions free-tier runner)  
**Project Type**: CLI/Data Pipeline  
**Performance Goals**: Execution time < 6 hours; Memory usage < 7 GB; Latency per query < 60 seconds  
**Constraints**: No GPU/CUDA; No external API calls during validation (fallback to local cache); Dataset sampling required if size > 7 GB  
**Scale/Scope**: Small benchmark subset (e.g., a representative number of queries, ~k documents) for validation. **Note**: Sample size is acknowledged as insufficient for statistical significance of the "multiplicative" claim.; the focus is on directional improvement and system stability.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: **Missing File**
The file `projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/.specify/memory/constitution.md` was not found in the project root.
**Action**: Proceeding with **Default Reproducibility Principles** (Reproducibility, Resource Efficiency, Transparency, Robustness, Data Integrity) as a temporary measure.
**Flag**: This is a blocking gap for the final `research_complete` stage. The Implementer Agent must create `constitution.md` or confirm the path.

*Default Principles Applied (for this phase only):*
1.  **Reproducibility**: All experiments must be reproducible on standard CI without specialized hardware. (Addressed by FR-001, FR-003)
2.  **Resource Efficiency**: Pipelines must fit within standard CI resource limits (7 GB RAM, 6h runtime). (Addressed by FR-003, SC-003)
3.  **Transparency**: Metrics and artifacts must be generated and logged clearly for validation. (Addressed by FR-002, FR-004, SC-002, SC-004)
4.  **Robustness**: Systems must handle missing dependencies or data gracefully without crashing. (Addressed by FR-005, Edge Cases)
5.  **Data Integrity**: No data fabrication; datasets must be sourced from verified locations or local caches. (Addressed by Research.md constraints)

## Project Structure

### Documentation (this feature)

```text
specs/766-mcompassrag-topic-metadata-as-a-semantic/
├── plan.md              # This file
├── research.md          # Phase 0 output (Feasibility Verification)
├── data-model.md        # Phase 1 output (Contract Finalization)
├── quickstart.md        # Phase 1 output (User Guide)
├── contracts/           # Phase 1 output
│   ├── retrieval_artifact.schema.yaml
│   ├── topic_model_config.schema.yaml
│   └── benchmark_subset.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── run.py               # Main entry point for pipeline
├── config.py            # Configuration management
├── data_loader.py       # Dataset handling, sampling, and synthetic topic generation
├── topic_modeler.py     # CPU-optimized topic modeling (LDA)
├── retriever.py         # Retrieval logic (Baseline vs. MCompass)
├── metrics.py           # Metric calculation (IE, Latency, NDCG if GT exists)
└── utils.py             # Utility functions (logging, error handling)

tests/
├── contract/            # Schema validation tests
├── integration/         # Pipeline integration tests
└── unit/                # Unit tests for components

scripts/
├── setup.sh             # Environment setup
└── run_rag.sh           # Pipeline execution script
```

**Structure Decision**: Selected Option 1 (Single project) as the feature is a data pipeline/CLI tool. The structure mirrors standard Python data science projects with clear separation of concerns for data loading, modeling, and evaluation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations identified at this stage. | N/A |

## Phase Plan

### Phase 0: Research & Feasibility Verification
- **Goal**: Verify dataset availability, confirm CPU compatibility, validate existing artifacts, and define the **Control Group** strategy.
- **FR-001, FR-003, FR-005, SC-001, SC-003**: Investigate `requirements.txt` for GPU dependencies; identify verified datasets; define **Stratified Sampling** logic (post-synthesis); define **Baseline Retriever** logic.
- **Output**: Updated `research.md` (confirming feasibility), `data-model.md` (confirming contracts), `contracts/*.schema.yaml` (confirming schemas).

### Phase 1: Design Refinement & Contract Finalization
- **Goal**: Finalize data models and quickstart instructions based on Phase 0 findings.
- **FR-002, FR-004, SC-002, SC-004**: Validate `RetrievalArtifact`, `TopicModelConfig`, and `BenchmarkSubset` schemas; finalize `quickstart.md` with stratified sampling instructions.
- **Output**: `data-model.md` (locked), `quickstart.md` (locked), `contracts/*.schema.yaml` (locked).

### Phase 2: Implementation (Implementer Agent)
- **Goal**: Implement the pipeline according to the plan and contracts.
- **FR-001 to FR-005**: Write code for CPU-only execution, **synthetic topic generation** (if needed), **stratified sampling**, **baseline vs. MCompass comparison**, and metric reporting.
- **Output**: Source code in `src/`, `scripts/`.

### Phase 3: Validation & Reporting
- **Goal**: Run the pipeline on CI and validate against success criteria.
- **SC-001 to SC-004**: Execute `scripts/run_rag.sh`; verify exit code, artifacts, metrics, and resource usage. **Focus**: Directional improvement (MCompass vs. Baseline) and system stability, not statistical significance of "5x".
- **Output**: CI logs, artifact files, final report.

## Risk Mitigation

- **Risk**: Dataset too large for 7 GB RAM.
  - **Mitigation**: Implement **Stratified Sampling** in `data_loader.py` (FR-003); log sample size and stratification method.
- **Risk**: Missing 'Topic Metadata' in source data.
  - **Mitigation**: Implement **Synthetic Topic Generation** (LDA) on the corpus before sampling to create the required variable.
- **Risk**: External API (OpenRouter) unavailable.
  - **Mitigation**: Use local cache if available; skip generation step with warning (FR-005).
- **Risk**: Topic model fails to converge on CPU.
  - **Mitigation**: Implement fallback configuration (random init) and continue pipeline (Edge Cases).
- **Risk**: GPU-specific code in dependencies.
  - **Mitigation**: Pin CPU-only versions of `torch` and `transformers`; enforce `device="cpu"` in all model loading.

## Success Criteria Mapping

- **SC-001**: Pipeline execution success rate → Phase 3 validation (exit code 0).
- **SC-002**: Artifact validity → Phase 3 validation (file size > 100 bytes, valid scores).
- **SC-003**: Resource compliance → Phase 3 validation (memory < 7 GB, time < 6h).
- **SC-004**: Metric reporting completeness → Phase 3 validation (latency, score, query count in logs).
- **New**: **Mechanism Validation** → Phase 3 validation: MCompass Retriever shows **directional improvement** (lower latency or higher hit rate) over Baseline Retriever on the subset.