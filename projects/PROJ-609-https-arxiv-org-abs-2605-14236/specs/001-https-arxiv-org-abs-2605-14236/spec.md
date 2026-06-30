# Feature Specification: Reproduce & Validate Active Learners as Efficient PRP Rerankers

**Feature Branch**: `609-reproduce-prp-rerankers`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Active Learners as Efficient PRP Rerankers (arXiv:2605.14236)"

## User Scenarios & Testing

### User Story 1 - Execute Core BEIR Evaluation Pipeline (Priority: P1)

The researcher MUST be able to trigger the vendored `IReranker` evaluation pipeline against the provided BEIR dataset subset using the default configuration to verify that the codebase executes end-to-end without runtime errors and produces the primary artifacts (ranking files and summary metrics).

**Why this priority**: This is the foundational "smoke test" for the reproduction project. Without a successful end-to-end run, no validation of the paper's claims (NDCG@10 improvements) is possible. It confirms the environment setup, dependency resolution, and basic data flow.

**Independent Test**: Run the `run_beir_eval.py` script (or the equivalent entry point defined in `Makefile`) with default arguments. The test passes if the process exits with code 0, generates output files in `reports/beir-metrics/`, and produces no unhandled exceptions.

**Acceptance Scenarios**:

1. **Given** the git submodule `IReranker` is initialized and the BEIR data files are present in `data/external/beir/bm25-runs/`, **When** the user executes the main evaluation script with the `dbpedia-entity` dataset, **Then** the system must complete the ranking process and generate a `summary.csv` file in `reports/beir-metrics/[model-name]/dbpedia-entity/` containing at least the NDCG@10 metric.
2. **Given** a valid environment with Python 3.10+ and required dependencies installed, **When** the user runs the evaluation, **Then** the system must process the input queries and documents without crashing due to missing file paths or import errors.
3. **Given** the default configuration targeting the `flan-t5-large` model, **When** the run completes, **Then** the output artifacts (ranking lists) must be written to the `data/external/beir/bm25-runs/` directory structure, matching the format expected by the BEIR evaluation harness.

---

### User Story 2 - Validate Active Learning vs. Classic Sorting Performance (Priority: P2)

The researcher MUST be able to reproduce the core comparative analysis showing that Active Learning (AL) rankers achieve higher NDCG@10 per call compared to classic sorting rankers under a constrained call budget, confirming the paper's primary hypothesis.

**Why this priority**: This story validates the specific scientific claim of the paper. It moves beyond "does it run" to "does it produce the expected result." It verifies the algorithmic logic of the active rankers against the baseline sorters.

**Independent Test**: Execute the `limit_comparisons.py` experiment script. The test passes if the generated CSV reports show a measurable difference in NDCG@10 between the AL oracle and the classic oracle at specific budget points (e.g., 10, 50, 100 calls).

**Acceptance Scenarios**:

1. **Given** the evaluation pipeline is functional (US-1), **When** the `limit_comparisons.py` experiment is executed with a call budget of 100, **Then** the resulting `reports/limit_comparisons_experiment.csv` must contain entries for both "Active Learner" and "Classic" oracles, showing distinct NDCG@10 values.
2. **Given** the paper's claim that AL improves efficiency, **When** the results are aggregated across the `scifact` and `trec-covid` datasets, **Then** the active ranker's NDCG@10 must be ≥ 0.01 higher than the classic ranker's NDCG@10 at the lowest budget setting (≤ 20 calls), or the system must flag a "reproduction deviation" if the delta is not met.
3. **Given** the randomized-direction oracle implementation, **When** the experiment runs, **Then** the system must record the number of LLM calls used, ensuring it does not exceed the configured budget by more than 0 calls (strict budget enforcement).

---

### User Story 3 - Reproduce Sensitivity Analysis and Noise Robustness (Priority: P3)

The researcher MUST be able to reproduce the analysis demonstrating that the randomized-direction oracle effectively converts systematic position bias into zero-mean noise, validating the method's robustness against order sensitivity.

**Why this priority**: This validates the secondary mechanism proposed in the paper (the randomized oracle). It ensures the implementation correctly handles the "noise-robust" aspect, which is critical for the validity of the active learning approach in noisy LLM settings.

**Independent Test**: Run the `order_effects_fliprate.py` experiment. The test passes if the output shows that the flip rate (inconsistency) for the randomized oracle is statistically lower or centered around 0.5 (zero-mean) compared to the bidirectional baseline when order is flipped.

**Acceptance Scenarios**:

1. **Given** the `order_effects_fliprate.py` script is executed, **When** the system processes a subset of 500 query-document pairs, **Then** the output `reports/order_effects_fliprate_summary.csv` must contain a column for "flip_rate" showing values for both "bidirectional" and "randomized" oracles.
2. **Given** the claim of zero-mean noise, **When** the randomized oracle results are analyzed, **Then** the difference in ranking scores between original and flipped order inputs must have a mean absolute difference ≤ 0.05 (indicating bias cancellation) or the system must report a "bias residual" metric.
3. **Given** the need to verify noise handling, **When** the experiment runs with a seed of 42, **Then** the results must be reproducible across two consecutive runs with the same seed, producing identical CSV outputs (bitwise identical or within floating point tolerance of 1e-6).

---

### Edge Cases

- **What happens when** the BEIR dataset files are missing or corrupted? The system must fail fast with a clear `FileNotFoundError` or `DataCorruptionError` before attempting any LLM calls, preventing wasted compute.
- **How does the system handle** a timeout during an LLM call? The `ireranker` oracles must implement a retry mechanism with a maximum of 3 attempts per pair, and if all fail, log the error and skip the pair while continuing the run (fail-safe mode).
- **What happens when** the call budget is exceeded mid-sorting? The ranker must strictly stop generating new comparisons and return the current partial ranking, ensuring no extra API calls are made beyond the limit.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST execute the `run_beir_eval.py` entry point to process the `dbpedia-entity` and `scifact` datasets from the `data/external/beir/bm25-runs/` directory and output ranking files to `reports/beir-metrics/` (See US-1).
- **FR-002**: The system MUST implement the "randomized-direction oracle" logic that randomly selects the order of the pair (A vs B or B vs A) for each LLM call to neutralize position bias (See US-3).
- **FR-003**: The system MUST enforce a strict call budget limit (e.g., ≤ 100 calls per query) for all active learning rankers, halting further comparisons once the limit is reached (See US-2).
- **FR-004**: The system MUST generate a `summary.csv` file for each dataset run containing at least the NDCG@10 metric, the number of calls made, and the seed used (See US-1).
- **FR-005**: The system MUST implement the `limit_comparisons.py` experiment to sweep call budgets (e.g., 10, 50, 100, 200) and record NDCG@10 for both active and classic rankers in `reports/limit_comparisons_experiment.csv` (See US-2).
- **FR-006**: The system MUST perform a sensitivity analysis on the call budget threshold by sweeping absolute differences in budget (e.g., ±10 calls) and reporting the variation in NDCG@10 rates (See US-2).

### Key Entities

- **Query-Document Pair**: A single comparison unit consisting of a query and two candidate documents, used as input for the oracle.
- **Ranking List**: An ordered list of document IDs for a given query, produced by the ranker after processing comparisons.
- **Evaluation Metric**: A numerical score (e.g., NDCG@10) calculated by comparing the generated ranking list against the ground truth.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The end-to-end execution time for the `dbpedia-entity` dataset with a budget of 100 calls is measured against the 6-hour CI runner limit, ensuring the full run completes within ≤ 4 hours (See US-1).
- **SC-002**: The NDCG@10 difference between the Active Learning ranker and the Classic ranker at a budget of 50 calls is measured against the paper's reported delta (or a baseline of 0) to confirm the efficiency gain (See US-2).
- **SC-003**: The flip-rate variance for the randomized oracle is measured against the bidirectional oracle to confirm the reduction in systematic bias (See US-3).
- **SC-004**: The reproducibility of results is measured by running the `limit_comparisons.py` experiment twice with the same seed; the NDCG@10 values must match within a tolerance of 1e-6 (See US-3).
- **SC-005**: The call budget adherence is measured by counting the total LLM calls in the logs; the count must be exactly equal to the configured budget (±0) for every query (See US-2).

## Assumptions

- The BEIR dataset files in `data/external/beir/bm25-runs/` are complete and match the format expected by the `IReranker` library (specifically, the `.txt` format with tab-separated query, document, and score).
- The environment has access to a CPU-only inference backend (e.g., Hugging Face `transformers` with `device="cpu"`) capable of running `flan-t5-large` within the 6-hour CI limit for the specified dataset subsets.
- The `IReranker` submodule is checked out to the exact commit corresponding to the paper's code release, ensuring no divergent changes affect the baseline behavior.
- The LLM calls are simulated or executed via a local CPU-compatible model (e.g., `google/flan-t5-large`) rather than an external API to ensure reproducibility and cost-free execution.
- The "randomized-direction" implementation in the code correctly handles the symmetry of pairwise comparisons (i.e., `score(A, B) = -score(B, A)` logic is not required, but the prompt construction is randomized).
