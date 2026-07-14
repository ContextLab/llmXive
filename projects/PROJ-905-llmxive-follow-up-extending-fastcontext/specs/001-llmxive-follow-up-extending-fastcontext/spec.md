# Feature Specification: llmXive follow-up: extending "FastContext: Training Efficient Repository Explorer for Coding Agents"

**Feature Branch**: `001-llmxive-fastcontext-lite`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Does replacing the learned exploration subagent in FastContext with a deterministic, rule-augmented retrieval mechanism preserve token efficiency and context precision for code repositories with high structural regularity?"

## User Scenarios & Testing

### User Story 1 - Structural Regularity Scoring and Dataset Split (Priority: P1)

As a researcher, I need to automatically score SWE-bench repositories for structural regularity and split them into "Regular" and "Irregular" sets so that I can isolate the variable of interest (structure) and ensure a balanced comparison between the neural and deterministic approaches.

**Why this priority**: This is the foundational data curation step. Without a validated split based on structural metrics, any subsequent performance comparison between FastContext and FastContext-Lite would be confounded by dataset bias.

**Independent Test**: Can be fully tested by running the static analysis script on a small sample of known repositories and verifying the output CSV contains a "regularity_score" column and the split logic correctly assigns the top half to the "Regular" set and the bottom half to the "Irregular" set.

**Acceptance Scenarios**:

1. **Given** a repository with standardized directory layouts (e.g., `tests/`, `src/`, `docs/`), **When** the static analysis script runs, **Then** the repository is assigned a high regularity score and placed in the "Regular" set.
2. **Given** a repository with non-standard file paths and mixed import patterns, **When** the static analysis script runs, **Then** the repository is assigned a low regularity score and placed in the "Irregular" set.
3. **Given** the curated SWE-bench subset of [deferred] repositories, **When** the curation process completes, **Then** the repositories are split into two balanced sets ("Regular" and "Irregular") of approximately equal size based on the regularity score distribution.

---

### User Story 2 - FastContext-Lite Execution and Metric Collection (Priority: P2)

As a researcher, I need to execute the FastContext-Lite pipeline (deterministic parser + TF-IDF index) on the curated datasets and record context precision, token usage, and wall-clock latency so that I can compare these metrics against the original FastContext neural baseline.

**Why this priority**: This implements the core experimental intervention. It allows the system to generate the primary data points (precision, tokens, latency) required to answer the research question.

**Independent Test**: Can be fully tested by running the FastContext-Lite pipeline on a single "Regular" repository and verifying that it outputs a JSON log containing `context_precision`, `total_tokens`, and `exploration_latency_ms` without requiring a GPU.

**Acceptance Scenarios**:

1. **Given** a repository in the "Regular" set, **When** the FastContext-Lite agent processes it, **Then** the system returns a context snippet with a precision score calculated against the ground-truth relevant files sourced from SWE-bench task annotations.
2. **Given** a repository in the "Irregular" set, **When** the FastContext-Lite agent processes it, **Then** the system returns a context snippet and records the associated metrics, even if the precision is lower than the Regular set.
3. **Given** the execution environment is CPU-only, **When** the FastContext-Lite pipeline runs, **Then** the process completes without requesting GPU resources or CUDA acceleration.

---

### User Story 3 - Comparative Analysis and Boundary Detection (Priority: P3)

As a researcher, I need to run paired t-tests comparing FastContext-Lite and FastContext metrics on the "Regular" set and analyze the performance degradation gap on the "Irregular" set to identify the threshold where deterministic heuristics fail.

**Why this priority**: This synthesizes the raw data into scientific conclusions. It directly addresses the research question regarding the boundary conditions of deterministic heuristics.

**Independent Test**: Can be fully tested by providing two mock datasets (one "Regular", one "Irregular") with pre-calculated metrics and verifying the analysis script outputs the p-value for the Regular set comparison and the degradation percentage for the Irregular set.

**Acceptance Scenarios**:

1. **Given** the metric logs from the "Regular" set for both FastContext and FastContext-Lite, **When** the analysis script runs, **Then** it outputs a paired t-test result with a [deferred] significance threshold to determine statistical significance of the difference.
2. **Given** the metric logs from the "Irregular" set, **When** the analysis script runs, **Then** it calculates the percentage degradation of FastContext-Lite precision compared to FastContext.
3. **Given** the results from both sets, **When** the boundary analysis runs, **Then** it identifies a specific regularity score threshold where the performance gap between the two methods exceeds a [deferred] tolerance parameter determined by sensitivity analysis.

---

### Edge Cases

- What happens when a repository lacks standard test files or import patterns entirely (extreme irregularity)? The system must handle missing heuristics gracefully without crashing, defaulting to a fallback retrieval strategy.
- How does the system handle repositories with identical regularity scores but different semantic complexity? The static analysis must rely on structural metrics only; semantic complexity is a confounding variable to be acknowledged in the discussion, not controlled for in the split.
- What if the TF-IDF index generation exceeds the 7 GB RAM limit for a large repository? The system must implement chunking or sampling for the index construction to remain within CPU-only constraints.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST implement a static analysis script that scores repositories on directory naming consistency, test-file placement, and import patterns to generate a `regularity_score`, ensuring the ground-truth relevant files used for validation are sourced from SWE-bench task annotations independent of the structural heuristics (See US-1).
- **FR-002**: The system MUST split the curated SWE-bench subset of [deferred] repositories into two balanced sets ("Regular" and "Irregular") of approximately equal size based on the regularity score distribution (See US-1).
- **FR-003**: The system MUST implement a "FastContext-Lite" engine that replaces the neural subagent with a deterministic parser and a pre-computed TF-IDF index, executing entirely on CPU (See US-2).
- **FR-004**: The system MUST record `context_precision`, `total_tokens`, and `wall_clock_latency` for every repository processed in the curated SWE-bench subset by both the FastContext and FastContext-Lite pipelines (See US-2).
- **FR-005**: The system MUST perform a paired t-test comparing the performance metrics of FastContext-Lite and FastContext specifically on the "Regular" dataset AND perform a continuous regression analysis correlating regularity score with performance delta to account for selection bias (See US-3).
- **FR-006**: The system MUST calculate and report the performance degradation percentage of FastContext-Lite relative to FastContext on the "Irregular" dataset (See US-3).

### Key Entities

- **Repository**: A software codebase from the SWE-bench suite, characterized by its file structure and code content.
- **Regularity Score**: A numeric value (0.0 to 1.0) derived from static analysis indicating the adherence of a repository to standard structural conventions.
- **Exploration Log**: A structured record containing the context snippets returned, token counts, and latency metrics for a specific repository run.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in context precision between FastContext-Lite and FastContext on the "Regular" set is measured against a [deferred] hypothesis-driven bound to be justified by a power analysis (See US-3).
- **SC-002**: The reduction in inference latency for FastContext-Lite compared to FastContext is measured against the baseline latency recorded in the FastContext run (See US-3).
- **SC-003**: The token consumption of FastContext-Lite is measured against the variance observed in the baseline FastContext run (See US-3).
- **SC-004**: The performance gap (precision drop) of FastContext-Lite on the "Irregular" set is measured against a quantitative threshold defined as a 10% precision drop to confirm boundary conditions (See US-3).
- **SC-005**: The statistical significance of the metric differences on the "Regular" set is measured against a [deferred] significance threshold (See US-3).

## Assumptions

- The curated SWE-bench subset of [deferred] repositories contains sufficient variation in structural regularity to allow for a meaningful split into "Regular" and "Irregular" sets.
- The "ground-truth relevant files" for precision calculation are available via the existing Mini-SWE-Agent pipeline annotations or task completion logs (independent of structural heuristics), and do not require manual curation.
- The deterministic heuristics (e.g., "search `tests/`") are general enough to cover the majority of standard Python/Java/Go project structures found in SWE-bench.
- The TF-IDF index for the largest repositories will fit within the available RAM limit of the free-tier GitHub Actions runner when processed with standard chunking.
- The original FastContext implementation can be run on CPU without GPU acceleration, albeit at a slower speed, to serve as a valid baseline for comparison.
- The static analysis script's definition of "structural regularity" (directory naming, test placement, imports) is a sufficient proxy for the "structural regularity" concept in the research question.
- The paired t-test assumptions (normality of differences) are met for the metric distributions on the "Regular" set; if not, a non-parametric alternative (Wilcoxon signed-rank) will be used as a fallback.