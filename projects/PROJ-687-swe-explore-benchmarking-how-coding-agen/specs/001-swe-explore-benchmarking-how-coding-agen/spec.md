# Feature Specification: Reproduce & Validate: SWE-Explore Benchmarking

**Feature Branch**: `001-reproduce-swe-explore-benchmarking`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: SWE-Explore: Benchmarking How Coding Agents Explore Repositories"

## User Scenarios & Testing

### User Story 1 - Execute Minimal Reproduction Run (Priority: P1)

The system MUST successfully execute the vendored `SWE-Explore-Bench` codebase on a single, representative issue instance using a lightweight, CPU-tractable explorer (e.g., BM25 or a small rule-based baseline) to verify end-to-end pipeline integrity.

**Why this priority**: This is the foundational "smoke test" for a reproduction project. Without a successful run that produces artifacts, no further validation or scaling is possible. It verifies the environment setup, dependency installation, and the basic execution flow of `main.py` or `eval.py`.

**Independent Test**: A CI job runs the reproduction script against one pre-selected repository/issue pair. The job passes only if the script exits with code 0 and generates the expected output file (e.g., `results/minimal_run.json` or a specific log file) containing at least one ranked list of code regions.

**Acceptance Scenarios**:

1. **Given** the `SWE-Explore-Bench` submodule is cloned and dependencies are installed, **When** the runner executes the baseline explorer on a single test instance, **Then** the process completes within 30 minutes and outputs a valid JSON artifact containing ranked code regions.
2. **Given** the runner encounters a missing environment variable, **When** the script starts, **Then** it fails gracefully with a clear error message listing the missing variable rather than crashing with a stack trace.

### User Story 2 - Validate Metric Calculation & Artifact Generation (Priority: P2)

The system MUST compute the benchmark's core metrics (Coverage, Ranking, Context-Efficiency) for the generated exploration results and produce a summary report comparing the observed values against the paper's reported baseline ranges.

**Why this priority**: The core value of SWE-Explore is the metric definition. Validating that the code correctly implements the mathematical formulas for coverage and ranking ensures the reproduction is scientifically valid, not just a script that runs.

**Independent Test**: The system parses the output artifacts from User Story 1, runs the `quality/bench_metrics.py` or equivalent evaluation logic, and outputs a summary table. A human reviewer can manually verify that the calculated "Coverage" matches the definition (lines found / total relevant lines) using the ground truth provided in the dataset.

**Acceptance Scenarios**:

1. **Given** a valid exploration result file and ground truth file, **When** the metric calculator runs, **Then** it outputs a JSON object with keys `coverage`, `ranking_score`, and `context_efficiency`, each containing a numeric value between 0.0 and 1.0.
2. **Given** the ground truth contains 0 relevant lines (edge case), **When** the metric calculator runs, **Then** it handles the division-by-zero scenario by returning `null` or `N/A` for coverage rather than throwing a runtime exception.

### User Story 3 - Full-Scale Reproduction Attempt (Priority: P3)

The system MUST attempt to run the benchmark on a subset of the full dataset (e.g., 10 issues across 2 languages) using at least two distinct explorer types (one classical retrieval, one agent-based) to reproduce the comparative analysis claimed in the paper.

**Why this priority**: This validates the scalability and the comparative claims of the paper. It confirms that the "tiering" of explorers (agentic vs. classical) can be observed in the reproduction environment.

**Independent Test**: The system executes a batch run over a subset of `traj_datasets`. It produces a comparative report showing that at least one agent-based explorer achieves a higher ranking score than the classical baseline on the subset, matching the paper's qualitative trend.

**Acceptance Scenarios**:

1. **Given** a subset of 10 issues, **When** the batch runner executes both a BM25 explorer and a simple agent explorer, **Then** it generates a CSV report where the agent explorer's average ranking score is ≥ 0.05 higher than the BM25 baseline (or explicitly documents a deviation from the paper's trend).
2. **Given** the batch run exceeds the 6-hour time limit, **When** the runner detects the timeout, **Then** it logs a warning, saves the partial results to a checkpoint file, and exits with a non-zero status code indicating a timeout rather than a crash.

### Edge Cases

- **Given** the ground truth for an issue is empty or malformed, **When** the metric calculator runs, **Then** it skips the instance and logs a warning without halting the entire batch.
- **Given** the API rate limit is hit during the agent explorer run, **When** the retry logic triggers, **Then** it waits for a backoff period (e.g., 60 seconds) and retries up to 3 times before failing the specific instance.
- **Given** the repository clone fails due to network issues, **When** the fetch script runs, **Then** it retries the clone 2 times with exponential backoff before marking the instance as "unavailable".

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the `main.py` or `eval.py` entry point of the vendored `SWE-Explore-Bench` repository to orchestrate the benchmark run (See US-1).
- **FR-002**: System MUST load the `traj_datasets` ground truth (distilled from successful agent trajectories) to serve as the reference for calculating coverage and ranking metrics (See US-2).
- **FR-003**: System MUST implement a CPU-tractable execution path for explorers, ensuring no GPU/CUDA dependencies are invoked and memory usage stays within a manageable limit (See US-1, US-3).
- **FR-004**: System MUST calculate the SWE-Explore specific metrics: Coverage (ratio of relevant lines found), Ranking (position of first relevant line), and Context-Efficiency (relevant lines per token budget) (See US-2).
- **FR-005**: System MUST generate a structured output artifact (JSON or CSV) containing the raw exploration traces and calculated metrics for at least one test instance (See US-1).
- **FR-006**: System MUST implement a timeout mechanism that aborts any single explorer run exceeding 30 minutes to prevent CI job failure (See US-3).
- **FR-007**: System MUST handle API rate-limiting errors by implementing a retry mechanism with exponential backoff (a limited number of retries) before marking an instance as failed (See Edge Cases).

### Key Entities

- **Instance**: A single benchmark task consisting of a repository, an issue, and a ground-truth set of relevant code lines.
- **Explorer**: The module responsible for retrieving a ranked list of code regions given an instance (e.g., BM25, Agent).
- **Metric**: A quantitative measure (Coverage, Ranking Score, Context Efficiency) derived from comparing Explorer output against Instance ground truth.
- **Trace**: The raw output of an explorer, containing the ordered list of code regions and the tokens used.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The reproduction run MUST produce a valid output artifact containing at least one ranked list of code regions for a single test instance, measured against the existence of the file and valid JSON structure (See US-1).
- **SC-002**: The calculated metrics MUST fall within the theoretical bounds [0.0, 1.0] for Coverage and Ranking, measured against the mathematical definition of the metrics (See US-2).
- **SC-003**: The execution time for a single instance using a lightweight baseline MUST be ≤ 30 minutes, measured against the system clock and the defined timeout threshold (See US-1).
- **SC-004**: The comparative analysis MUST show a measurable difference (≥ 0.05 absolute difference) in Ranking Score between at least two distinct explorer types on a 10-instance subset, measured against the paper's claim of "tiering" (See US-3).
- **SC-005**: The system MUST complete the full pipeline (fetch, explore, evaluate) for a representative subset within the 6-hour CI limit, measured against the total wall-clock time of the GitHub Actions job (See US-3).

## Assumptions

- The `SWE-Explore-Bench` codebase is a faithful reproduction of the paper's methodology and does not require external proprietary APIs that are unavailable in the CI environment (unless a mock or fallback is implemented).
- The dataset `traj_datasets` contains valid ground truth files for the selected subset of issues; instances with missing ground truth are skipped.
- The "Context-Efficiency" metric can be approximated by counting tokens in the returned context without requiring a full LLM inference for the token count, assuming a standard tokenizer is available.
- The limited RAM capacity of the CI runner is sufficient for loading the repository code and running the lightweight explorers, provided large models are not loaded.
- The paper's claim of "agentic explorers forming a clear tier above classical retrieval" is expected to hold for the subset, but deviations are recorded as valid scientific findings rather than failures.
- No GPU acceleration is available or required; all methods must be executable on CPU-only hardware.
