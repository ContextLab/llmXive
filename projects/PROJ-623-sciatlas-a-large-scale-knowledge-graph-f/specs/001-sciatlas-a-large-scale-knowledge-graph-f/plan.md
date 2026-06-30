# Implementation Plan: Reproduce & Validate SciAtlas Knowledge Graph

**Branch**: `001-reproduce-validate-sciatlas` | **Date**: 2026-05-29 | **Spec**: `specs/001-reproduce-validate-sciatlas/spec.md`
**Input**: Feature specification from `/specs/001-reproduce-validate-sciatlas/spec.md`

## Summary

This feature implements a reproducible, automated pipeline to execute the SciAtlas knowledge graph entry point (using **OpenAlex** as the verified primary data source), validate the integrity of generated artifacts against a "Gold Standard" benchmark, and verify specific sub-pipelines (literature review, trend reports). The approach prioritizes CPU-tractable execution on GitHub Actions free-tier runners (limited CPU, 7GB RAM) by sampling data and relying on remote API access. The plan explicitly distinguishes between "Pipeline Execution" (feasibility check) and "Scientific Validation" (retrieval accuracy against a Gold Standard). It addresses the reviewer's concern regarding "physical measurement vs. theoretical correlation" by implementing an NLP-derived classification based on a curated external dataset, rather than relying on a non-existent API flag.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `requests`, `pytest`, `pyyaml`, `pandas` (CPU-only), `scikit-learn`, `transformers` (for NLP classification), `openalex` (Python client)  
**Storage**: Ephemeral CI storage for artifacts; remote OpenAlex API for graph data  
**Testing**: `pytest` with contract validation, integration tests for API retries, and "Gold Standard" recall tests  
**Target Platform**: Linux (GitHub Actions Free Tier)  
**Project Type**: CLI / Data Pipeline  
**Performance Goals**: Complete reproduction run in < 3.5 hours; artifact validation in < 15 minutes  
**Constraints**: No GPU; max 7GB RAM; max 14GB disk; no heavy local DB binaries; API rate limit handling (3 retries)  
**Scale/Scope**: Sampled subset (top 100 results per query) for CI validation; "Gold Standard" subset (50 known papers) for retrieval accuracy.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

**Principle 1: Reproducibility**  
- *Requirement*: All experiments must be reproducible via CI.  
- *Plan Action*: The pipeline is fully scripted, uses fixed seeds, and logs all API calls to `reproduction_log.txt`. The `reproduce_validate` workflow runs on every PR merge.

**Principle 2: Transparency**  
- *Requirement*: Data sources and processing steps must be visible.  
- *Plan Action*: `reproduction_log.txt` captures every API call and retrieval step. `research.md` documents the dataset sampling strategy, API limitations, and the "Gold Standard" benchmark source.

**Principle 3: Validation**  
- *Requirement*: Claims must be validated against specific criteria.  
- *Plan Action*: `FR-002` and `US-2` enforce schema validation. A new "Scientific Validation" phase measures "Recall@10" against a "Gold Standard" of known papers.

**Principle 4: Robustness**  
- *Requirement*: System must handle failures gracefully.  
- *Plan Action*: `FR-003` implements exponential backoff (1s, 2s, 4s) for network failures. `US-Edge` handles 429 errors and empty results. Distinction made between "System Failure" and "Reproduction Failure".

**Principle 5: Feasibility**  
- *Requirement*: Must run on free-tier CI without GPU.  
- *Plan Action*: All logic uses CPU-tractable libraries. No local Neo4j server; remote OpenAlex API access only. Data sampled to fit 7GB RAM.

## Project Structure

### Documentation (this feature)

```text
specs/001-reproduce-validate-sciatlas/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── paper-record.schema.yaml
│   └── artifact.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
external/SciAtlas/
├── run_sciatlas.py      # Entry point (wraps OpenAlex)
├── cli.py               # CLI interface
├── core/
│   └── schemas.py       # Reference schemas
├── agent-skill/
│   ├── literature_review.py
│   └── trend_report.py
└── requirements.txt

src/
├── validation/
│   ├── artifact_validator.py  # Validates JSON output against schema
│   ├── gold_standard_validator.py # Validates retrieval against Gold Standard
│   └── schema_loader.py       # Loads YAML contracts
├── integration/
│   └── test_sciatlas_run.py   # CI integration tests
└── utils/
    └── retry_utils.py         # Exponential backoff logic

tests/
├── contract/
│   └── test_schema_contracts.py
├── integration/
│   └── test_api_retries.py
├── gold_standard/
│   └── test_recall.py         # Tests retrieval accuracy
└── unit/
    └── test_validator.py

output/
└── reproduction_run_001.json  # Generated artifact
```

**Structure Decision**: The structure separates the vendored SciAtlas code (`external/`) from the validation and testing harness (`src/`, `tests/`). This ensures the reproduction pipeline is isolated and the validation logic is testable independently. The `contracts/` directory holds the YAML schemas for automated validation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is limited to execution and validation of an existing pipeline. | N/A |

## Implementation Phases

### Phase 0: Research & Feasibility (Research.md)
- **Goal**: Confirm dataset accessibility (OpenAlex), API limits, and CPU feasibility. Define "Gold Standard" benchmark.
- **FR/SC Mapping**:
  - `FR-001` (Execution): Verify `run_sciatlas.py` runs in CI.
  - `FR-003` (Retry): Confirm API rate limits and backoff strategy.
  - `SC-001` (Success Rate): Define success criteria for CI runs (distinguishing System vs. Reproduction failure).
  - `SC-003` (Time): Confirm 4-hour timeout feasibility with sampling. Target: [Deferred].
- **Constitution Check**: Re-verify against Principle 5 (Feasibility).

### Phase 1: Data Model & Contracts (Data-model.md, Contracts/)
- **Goal**: Define the schema for `PaperRecord` and `ReproductionArtifact`.
- **FR/SC Mapping**:
  - `FR-002` (Validation): Define required fields (`title`, `abstract`, `source_id`). Enforce `doi` OR `arxiv_id` presence.
  - `SC-002` (Completeness): Define thresholds for schema validation.
  - `US-2` (Artifact Integrity): Ensure `doi`/`arxiv_id` presence.
- **Constitution Check**: Re-verify against Principle 2 (Transparency).

### Phase 2: Implementation (Tasks.md - Not created here)
- **Goal**: Implement validation scripts, retry logic, and CI workflows.
- **FR/SC Mapping**:
  - `FR-001` to `FR-005`: Code implementation.
  - `SC-001` to `SC-004`: Metric collection and reporting.
- **Constitution Check**: Final verification of all principles.

### Phase 3: Validation & Reporting
- **Goal**: Execute the pipeline, validate artifacts, and generate reports.
- **FR/SC Mapping**:
  - `US-1` (Execute): Run `python run_sciatlas.py --query "graph neural networks"`.
  - `US-2` (Validate): Run `artifact_validator.py` and `gold_standard_validator.py`.
  - `US-3` (Claim Reproduction): Run `literature_review` and validate against "Gold Standard" summary (Fact-Checking).
  - `SC-004` (Error Recovery): Verify retry success on simulated failures.

## Constitution Check (Final)

- **Principle 1**: Reproducibility ensured via CI scripts and logging.
- **Principle 2**: Transparency ensured via schema contracts, logs, and Gold Standard documentation.
- **Principle 3**: Validation ensured via `artifact_validator.py`, `gold_standard_validator.py`, and schema checks.
- **Principle 4**: Robustness ensured via retry logic and error handling (System vs. Reproduction failure).
- **Principle 5**: Feasibility ensured by CPU-only design and remote OpenAlex API usage.

**Status**: Ready for Research Phase.