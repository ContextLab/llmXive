# Feature Specification: EnterpriseClawBench Reproduction & Validation

**Feature Branch**: `001-enterpriseclawbench-reproduction`  
**Created**: 2026-06-15  
**Status**: Draft  
**Input**: User description: "Reproduce & validate EnterpriseClawBench: Benchmarking Agents from Real Workplace Sessions. The implementation exists as a git submodule. Task is to run, validate, and reproduce end-to-end."

## User Scenarios & Testing

### User Story 1 - Execute Construction Pipeline on Sample Data (Priority: P1)

As a researcher, I want to execute the `EnterpriseClawBench` construction pipeline on a minimal subset of data (smoke test) to verify that the core ingestion, turn extraction, and task packaging logic functions without runtime errors or dependency failures.

**Why this priority**: This is the critical path. If the pipeline cannot even process a single sample session, the entire benchmark cannot be reproduced. It validates the environment setup and the basic integrity of the vendored code.

**Independent Test**: Run the provided smoke test configuration (`construction/configs/smoke.yaml`) and verify that a valid JSON task pack is generated in the output directory.

**Acceptance Scenarios**:

1. **Given** the `EnterpriseClawBench` submodule is cloned and dependencies are installed, **When** the CLI command `python -m construction.enterprise_clawbench_construction.cli --config construction/configs/smoke.yaml` is executed, **Then** the process completes with exit code 0 and generates at least one task JSON file in `output/smoke/tasks/`.
2. **Given** the pipeline runs successfully, **When** the generated task JSON is inspected, **Then** it contains the required fields: `prompt`, `role_class`, `skill_subclass`, `hard_rules`, and `semantic_rubric` as defined in the paper's protocol.
3. **Given** the pipeline encounters a malformed input file, **When** the pipeline runs, **Then** it logs a specific error message indicating the file path and failure reason, rather than crashing with a generic stack trace.

---

### User Story 2 - Validate Evaluation Protocol & Judge Logic (Priority: P2)

As a researcher, I want to run the evaluation protocol against the generated tasks using a static "judge" configuration to confirm that the scoring rubrics, artifact checks, and rule enforcement logic execute correctly and produce consistent scores.

**Why this priority**: The paper emphasizes that the *evaluation protocol* is the reusable contribution. Validating that the judge correctly interprets rubrics and artifacts is essential to confirming the benchmark's utility.

**Independent Test**: Execute the evaluation module against a fixed set of pre-generated artifacts (from `example_runs`) and verify the output report matches the expected structure and score distribution.

**Acceptance Scenarios**:

1. **Given** a set of pre-generated task artifacts (e.g., `example_runs/public_session_deepagents_sonnet`), **When** the evaluation CLI is run with the default judge configuration, **Then** a `report.json` is generated containing scores for `artifact_delivery`, `visual_quality`, `cost`, `runtime`, and `skill_transfer`.
2. **Given** a task with a known failing artifact (e.g., missing HTML file), **When** the evaluation runs, **Then** the `artifact_delivery` score for that task is recorded as 0 (or the specific failure code defined in `rules.py`).
3. **Given** multiple evaluation runs on the same static input, **When** the results are compared, **Then** the scores are deterministic (identical across runs) to ensure the judge logic is stable.

---

### User Story 3 - Reproduce Paper Statistics & Leaderboard Metrics (Priority: P3)

As a researcher, I want to aggregate the results from the full (or sampled) construction and evaluation runs to reproduce the key statistics (e.g., task count distribution, role class heatmaps) and compare them against the figures reported in the paper.

**Why this priority**: This confirms the scientific validity of the reproduction. While P1 and P2 ensure the code works, P3 ensures the *science* (the data and metrics) matches the publication.

**Independent Test**: Generate aggregate statistics from the processed task pack and compare the counts and distributions against the values reported in the paper's "Benchmark Statistics" section.

**Acceptance Scenarios**:

1. **Given** the full set of processed tasks (or a representative sample), **When** the aggregation script runs, **Then** the total task count is within 5% of the paper's reported 852 tasks (allowing for sampling variance if full data is unavailable).
2. **Given** the role class distribution data, **When** a histogram is generated, **Then** the relative proportions of major role classes (e.g., "Analyst", "Developer") match the trend shown in Figure 5 of the paper.
3. **Given** the evaluation results, **When** the leaderboard table is generated, **Then** the best configuration score reported is consistent with the paper's claim of a high performance level. (allowing for minor variance due to model API drift or sampling).

---

### Edge Cases

- What happens when the raw session data contains proprietary enterprise content that cannot be processed due to encryption or missing fixtures? (Pipeline should skip and log, not crash).
- How does the system handle a "judge" LLM that times out or returns malformed JSON? (Retries with exponential backoff up to 3 attempts, then marks task as `unscorable`).
- What if the artifact generation step produces a file that is too large for the CPU-only runner's disk quota? (Pipeline must enforce a per-artifact hard limit to manage storage constraints. and fail gracefully).

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the construction pipeline stages (Inventory, Turn Extraction, Segment Instances, Mechanical Checks, Join, Self-Contained, Prompt Rewrite, Taxonomy, Deliverables, Rules, Semantic Rubric, Candidate Selection, Pack Writer, Pack Validate, Export) in the defined sequence without manual intervention. (See US-1)
- **FR-002**: System MUST parse the `smoke.yaml` and `public_session_full.yaml` configuration files to dynamically adjust the scope of the pipeline (e.g., number of tasks, specific stages enabled). (See US-1)
- **FR-003**: System MUST generate a `task.json` for each processed session containing the `prompt`, `role_class`, `skill_subclass`, `hard_rules`, and `semantic_rubric` fields. (See US-1)
- **FR-004**: System MUST execute the evaluation protocol to score artifacts based on `artifact_delivery`, `visual_quality`, `cost`, `runtime`, and `skill_transfer` dimensions. (See US-2)
- **FR-005**: System MUST produce a deterministic `report.json` for each evaluation run, ensuring that identical inputs yield identical scores. (See US-2)
- **FR-006**: System MUST aggregate evaluation results to generate statistics matching the paper's reported metrics (e.g., task counts, role distributions). (See US-3)
- **FR-007**: System MUST handle API timeouts or rate limits from the judge LLM by retrying up to 3 times with exponential backoff before marking a task as `unscorable`. (See US-2)

### Key Entities

- **Task Pack**: A collection of reproducible tasks, each with associated prompts, rules, and rubrics.
- **Artifact**: The output generated by an agent (e.g., HTML, Markdown, JSON) which is evaluated against the rubric.
- **Judge**: The evaluation logic (LLM or rule-based) that scores artifacts against the `semantic_rubric`.
- **Session**: The raw input data representing a real-world workplace interaction.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Pipeline execution success rate is measured against the requirement that [deferred] of configured smoke-test tasks complete without runtime errors. (See FR-001, US-1)
- **SC-002**: Task completeness rate is measured against the paper's specification that every task must contain the 5 required fields (`prompt`, `role_class`, `skill_subclass`, `hard_rules`, `semantic_rubric`). (See FR-003, US-1)
- **SC-003**: Evaluation determinism is measured by comparing the scores of two consecutive runs on the same static input; the difference must be 0. (See FR-005, US-2)
- **SC-004**: Statistical alignment is measured by comparing the generated task count and role distribution against the values reported in the paper's "Benchmark Statistics" section; the variance must be < 5% for counts. (See FR-006, US-3)
- **SC-005**: Error handling robustness is measured by the system's ability to process a dataset containing [deferred] malformed inputs without crashing; the system must log errors and continue processing valid inputs. (See FR-007, US-2)

## Assumptions

- **Assumption about data availability**: The `raw_session_example` and `example_runs` directories provided in the submodule contain sufficient representative data to run the smoke test and validate the evaluation protocol without requiring the full proprietary enterprise dataset.
- **Assumption about compute resources**: The GitHub Actions free-tier runner (multiple CPU cores, several GB RAM) is sufficient to run the `smoke.yaml` configuration and the evaluation of a small sample of tasks, provided that the LLM calls are rate-limited and not parallelized aggressively.
- **Assumption about LLM API stability**: The evaluation relies on an external LLM API for the "Judge" logic; we assume the API will be available and responsive during the CI run, with timeouts handled by the retry logic defined in FR-007.
- **Assumption about code integrity**: The vendored code in the `external/EnterpriseClawBench` submodule is unmodified and matches the version described in the paper, requiring no patches to run on standard Python 3.10+ environments.
- **Assumption about artifact size**: The generated artifacts in the example runs are small enough (< 500MB) to fit within the runner's disk quota and be processed by the CPU-only evaluation logic.
