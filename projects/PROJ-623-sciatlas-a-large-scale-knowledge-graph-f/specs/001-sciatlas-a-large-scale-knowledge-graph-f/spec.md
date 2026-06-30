# Feature Specification: Reproduce & Validate SciAtlas Knowledge Graph

**Feature Branch**: `001-reproduce-validate-sciatlas`  
**Created**: 2026-05-29  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: SciAtlas: A Large-Scale Knowledge Graph for Automated Scientific Research"

## User Scenarios & Testing

### User Story 1 - Execute Core Reproduction Pipeline (Priority: P1)

**Description**: The system MUST execute the vendored SciAtlas entry point (`run_sciatlas.py` or `cli.py`) within the CI environment to generate the primary reproduction artifacts (e.g., search results, trend reports, or grounding evidence) without human intervention.

**Why this priority**: This is the fundamental "runnable" requirement. Without a successful execution of the shipped code, no validation of the paper's claims can occur. It confirms the code is not broken and the environment is correctly configured.

**Independent Test**: A single CI job runs the entry script with a fixed, minimal query. The test passes if the script exits with code 0 and produces at least one non-empty output file (JSON or Markdown) in the designated artifacts directory.

**Acceptance Scenarios**:
1. **Given** the `SciAtlas` submodule is cloned and dependencies are installed, **When** the command `python run_sciatlas.py --query "graph neural networks"` is executed, **Then** the process completes within 30 minutes and generates `output/reproduction_run_001.json` containing at least 5 paper records.
2. **Given** a valid API key is provided in environment variables, **When** the `sciatlas/cli.py` is invoked with the `search` command, **Then** the system returns structured results without raising uncaught exceptions.

---

### User Story 2 - Validate Artifact Integrity & Completeness (Priority: P2)

**Description**: The system MUST verify that the generated artifacts contain valid data structures and meet minimum content thresholds (e.g., non-empty fields, correct schema) to prove the pipeline actually processed data rather than failing silently or returning empty mocks.

**Why this priority**: A script can run and exit successfully while producing empty or malformed output. This story ensures the *content* of the reproduction is meaningful and aligns with the paper's claim of "43M papers" and "3B triplets" (even if sampled).

**Independent Test**: A validation script parses the output JSON/Markdown and asserts the presence of required fields (e.g., `title`, `abstract`, `entities`) and checks that the record count is ≥ 1.

**Acceptance Scenarios**:
1. **Given** the `output/reproduction_run_001.json` file exists, **When** the validation script parses it, **Then** every record contains a `title` string with length ≥ 5 characters and an `abstract` field with length ≥ 20 characters.
2. **Given** the output file, **When** the system checks for entity links, **Then** at least 3 records must contain a non-null `doi` or `arxiv_id` field.

---

### User Story 3 - Reproduce Specific Paper Claim (Priority: P3)

**Description**: The system MUST execute a specific sub-pipeline (e.g., "Literature Review" or "Trend Report") described in the paper and confirm it produces a result that qualitatively matches the paper's example (e.g., a coherent summary or a trend visualization).

**Why this priority**: This validates the *quality* of the "neuro-symbolic retrieval" and "graph reranking" claims, moving beyond "it runs" to "it does what the paper says."

**Independent Test**: Run the `literature_review` skill with a predefined topic and compare the generated summary length and structure against a baseline expectation (e.g., > 200 words, includes citations).

**Acceptance Scenarios**:
1. **Given** the `literature_review` task is configured, **When** it processes the topic "knowledge graphs in healthcare", **Then** the output Markdown contains at least 3 distinct paper citations and a summary section of ≥ 150 words.
2. **Given** the trend report task, **When** executed, **Then** it produces a JSON artifact containing a time-series array with at least 5 data points representing publication counts per year.

### Edge Cases

- **API Rate Limiting**: If the external knowledge graph API (or Neo4j instance) returns a 429 error, the system MUST retry up to 3 times with exponential backoff (1s, 2s, 4s) before failing the run.
- **Empty Results**: If the search query yields 0 results, the system MUST output a specific "No results found" artifact rather than crashing or returning an empty array that looks like a bug.
- **Dependency Mismatch**: If the vendored `requirements.txt` conflicts with the CI Python version, the system MUST fail fast with a clear error message indicating the version mismatch.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the `run_sciatlas.py` entry point with a user-defined query string and return a structured output file (JSON or Markdown) within 14,400 seconds (4 hours). (See US-1)
- **FR-002**: System MUST validate that every generated artifact contains at least one record with non-empty `title`, `abstract`, and `source_id` fields. (See US-2)
- **FR-003**: System MUST implement a retry mechanism for network failures, attempting up to 3 retries with exponential backoff before marking the run as failed. (See US-1)
- **FR-004**: System MUST support the `literature_review` and `trend_report` agent skills as defined in the `agent-skill` directory. (See US-3)
- **FR-005**: System MUST log all API calls and retrieval steps to a `reproduction_log.txt` file for traceability. (See US-2)

### Key Entities

- **PaperRecord**: Represents a single academic paper with attributes `title`, `abstract`, `authors`, `year`, `source_id`.
- **SearchQuery**: The input string provided by the user to trigger the retrieval pipeline.
- **ReproductionArtifact**: The final output file generated by the pipeline, containing search results or analysis summaries.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Reproduction success rate is measured against the number of CI runs; the target is ≥ 95% of runs completing with exit code 0 and valid artifacts. (See FR-001)
- **SC-002**: Artifact completeness is measured against the schema defined in `sciatlas/core/schemas.py`; the target is [deferred] of records containing required fields. (See FR-002)
- **SC-003**: Execution time is measured against the 4-hour CI timeout limit; the target is [deferred] of runs completing within 3.5 hours to allow for buffer. (See FR-001)
- **SC-004**: Error recovery rate is measured against the number of transient network failures; the target is [deferred] of retries succeeding after the first attempt. (See FR-003)

## Assumptions

- The SciAtlas knowledge graph backend (Neo4j instance or API) is accessible from the GitHub Actions free-tier runner without requiring a paid tier or GPU acceleration.
- The `run_sciatlas.py` script does not require local installation of heavy graph database binaries (e.g., full Neo4j server) and instead connects to a remote instance or uses a lightweight in-memory graph for the reproduction sample.
- The "43M papers" and "3B triplets" mentioned in the paper are accessed via a remote API; the reproduction will use a sampled subset (e.g., top 100 results) to fit within the 7GB RAM and 6-hour CI limits.
- The vendored code in `external/SciAtlas` is up-to-date with the paper's publication and does not require manual patches to run on Python 3.9+.
- The `grobid_client` and PDF extraction components are optional for the initial reproduction; if they fail, the system will fallback to text-only metadata retrieval without blocking the entire pipeline.
- No GPU or CUDA acceleration is required; all inference and graph traversal operations are CPU-tractable on standard CI runners.
