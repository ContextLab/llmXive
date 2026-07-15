# Feature Specification: llmXive follow-up: extending "S-Agent: Spatial Tool-Use Elicits Reasoning for Spatial Intelligence"

**Feature Branch**: `001-symbolic-spatial-reasoning`  
**Created**: 2026-07-03  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'S-Agent: Spatial Tool-Use Elicits Reasoning for Spatial Intelligence'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Symbolic CSP Solver Execution on Static Scenes (Priority: P1)

**User Journey**: As a researcher, I need to execute a deterministic Constraint Satisfaction Problem (CSP) solver on a filtered subset of the S-Agent-300K dataset ([deferred] static multi-view scenes) using extracted 3D geometric evidence and historical tool-call traces, so that I can generate spatial reasoning predictions (counting and positioning) without invoking a neural VLM.

**Why this priority**: This is the core experimental intervention. Without a functioning symbolic solver that can ingest the specific data format and produce outputs, no comparison or validation is possible. It represents the primary hypothesis test: "Can symbolic logic replace neural planning?"

**Independent Test**: Can be fully tested by running the solver script against the [deferred]-scene subset and verifying that it produces a valid JSON output file containing predicted answers for every scene, with zero runtime errors and no GPU utilization.

**Acceptance Scenarios**:

1. **Given** a CSV of [deferred] static scenes with extracted 3D geometric constraints and tool traces, **When** the CSP solver is executed on a CPU-only environment, **Then** it outputs a JSON file with a prediction for every scene ID within 6 hours of wall-clock time.
2. **Given** the solver is running, **When** it processes a scene, **Then** it utilizes only standard Python libraries (e.g., `python-constraint`, `scipy`) and consumes less than 7 GB of RAM at peak load.
3. **Given** a scene with ambiguous geometric constraints, **When** the solver processes it, **Then** it returns a "No Solution" or "Ambiguous" status rather than hallucinating a geometric configuration, ensuring deterministic behavior.

---

### User Story 2 - Comparative Accuracy & Latency Benchmarking (Priority: P2)

**User Journey**: As a researcher, I need to compare the accuracy (F1-score, Exact Match) and inference latency of the symbolic solver's predictions against the ground-truth labels and the original S-Agent (VLM) baseline, so that I can quantify the performance gap and computational savings.

**Why this priority**: This validates the research question. It determines if the symbolic approach is viable (accuracy > 85% of baseline) and if it achieves the motivation (latency reduction). It transforms the raw output of US-1 into scientific evidence.

**Independent Test**: Can be fully tested by running a benchmark script that loads the symbolic predictions, the VLM baseline predictions, and ground truth, then outputs a summary table with accuracy metrics and median latency per method.

**Acceptance Scenarios**:

1. **Given** the symbolic predictions and ground-truth labels, **When** the benchmark script calculates metrics, **Then** it reports an Exact Match score and F1-score for the symbolic agent.
2. **Given** the symbolic and VLM prediction sets, **When** the latency is measured on a 2-core CPU, **Then** the symbolic agent's median inference time is at least 10x faster than the VLM baseline (targeting two orders of magnitude).
3. **Given** the paired results, **When** McNemar's test is performed, **Then** the script outputs a p-value indicating whether the accuracy difference is statistically significant (p < 0.05).

---

### User Story 3 - Failure Case Analysis & Semantic Gap Identification (Priority: P3)

**User Journey**: As a researcher, I need to analyze the specific scenes where the symbolic solver fails (predicts incorrectly while VLM succeeds) to categorize the error as either "geometric ambiguity" or "missing semantic disambiguation," so that I can conclude whether neural understanding is essential.

**Why this priority**: This provides the qualitative depth to the quantitative results. If the solver fails, understanding *why* is critical for the "Research Question" resolution. It moves beyond "it failed" to "it failed because X."

**Independent Test**: Can be fully tested by generating a report listing the top 50 failure cases with their associated error category and a brief text explanation derived from the scene metadata.

**Acceptance Scenarios**:

1. **Given** a set of scenes where the symbolic solver predicted incorrectly but the VLM was correct, **When** the analysis script reviews the scene metadata, **Then** it classifies the failure as either "Geometric Ambiguity" (insufficient constraints) or "Semantic Gap" (requires non-geometric context).
2. **Given** the classified failures, **When** the report is generated, **Then** it includes a summary count of each failure type and a representative example scene ID for each category.

---

### Edge Cases

- **What happens when the extracted geometric evidence is insufficient to form a solvable CSP?**
  - The solver must explicitly return a "No Solution" status rather than crashing or guessing. This case is critical for the "Geometric Ambiguity" failure analysis.
- **How does the system handle scenes where the historical tool traces are inconsistent or contradictory?**
  - The solver must detect constraint violations in the input traces and log a specific error code, excluding the scene from the "solvable" count to prevent skewing accuracy metrics.
- **What happens if the dataset download (S-Agent-300K) is incomplete or corrupted?**
  - The pipeline must fail fast with a clear error message indicating missing files, rather than proceeding with a partial dataset that would invalidate the statistical power analysis.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST extract 3D geometric constraints and tool-call traces from the S-Agent-300K dataset for a representative sample of static multi-view scenes., ensuring the data format is compatible with a standard CSP solver (See US-1).
- **FR-002**: The system MUST implement a deterministic CSP solver that ingests the extracted constraints and solves for spatial counting and relative positioning tasks without requiring any neural network inference or GPU acceleration (See US-1).
- **FR-003**: The system MUST calculate Exact Match and F1-score metrics by comparing the symbolic solver's predictions against both the ground-truth labels and the original S-Agent (VLM) baseline predictions (See US-2).
- **FR-004**: The system MUST measure and record the inference latency for each scene processed by the symbolic solver on a multi-core CPU environment, ensuring no single scene exceeds 60 seconds of processing time. (See US-2).
- **FR-005**: The system MUST perform a McNemar's statistical significance test on the paired accuracy results of the symbolic and VLM agents to determine if the performance difference is statistically significant (See US-2).
- **FR-006**: The system MUST categorize and report failure cases where the symbolic solver underperforms the VLM, distinguishing between "geometric ambiguity" and "semantic disambiguation" needs (See US-3).

### Key Entities

- **StaticScene**: A data unit representing a single static multi-view environment, containing 3D geometric constraints, tool-call traces, and ground-truth labels.
- **SpatialPrediction**: The output of the reasoning engine (either symbolic or neural), containing the predicted count or relative position for a specific scene.
- **BenchmarkResult**: A composite record linking a `StaticScene` ID with the predictions from both agents, the ground truth, accuracy metrics, and latency measurements.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The accuracy of the symbolic agent (Exact Match score) is measured against the original S-Agent (VLM) baseline accuracy on the same [deferred] scenes to determine the percentage of neural performance retained (See US-2).
- **SC-002**: The inference latency of the symbolic agent is measured against the VLM baseline latency on a standard 2-core CPU to quantify the computational efficiency gain (See US-2).
- **SC-003**: The statistical significance of the accuracy difference is measured using McNemar's test p-value to determine if the observed performance gap is non-random (See US-2).
- **SC-004**: The proportion of failure cases attributable to "semantic disambiguation" is measured against the total number of symbolic failures to assess the necessity of neural understanding (See US-3).

## Assumptions

- **Dataset Variable Fit**: We assume the S-Agent-300K benchmark dataset contains all necessary 3D geometric coordinates and tool-call traces required to formulate the CSP. If the dataset lacks specific spatial constraints needed for certain scenes, those scenes will be excluded from the analysis, and a `[NEEDS CLARIFICATION: does S-Agent-300K contain full 3D constraint data for all [deferred] selected scenes?]` marker will be raised.
- **Inference Framing**: The study is observational; we assume that the comparison between the symbolic solver and the VLM baseline on the *same* dataset allows for a valid assessment of the reasoning mechanism's source, but we will frame results as associational regarding the "source of reasoning" rather than causal claims about general spatial intelligence.
- **Compute Feasibility**: We assume that a standard Python CSP solver (e.g., `python-constraint` or `ortools` in CPU mode) can solve the extracted constraint problems for 1,000 scenes within the 6-hour CI limit and 7 GB RAM constraint without requiring GPU acceleration or 8-bit quantization.
- **Threshold Justification**: We assume a fixed accuracy threshold of 85% of the VLM baseline is a defensible community standard for "high-fidelity replication" in this context. A sensitivity analysis will sweep this threshold over {80%, 85%, 90%} to report how the "success/failure" verdict varies (See FR-003).
- **Measurement Validity**: We assume the ground-truth labels in the S-Agent-300K dataset are accurate and sufficient for calculating Exact Match and F1-scores without requiring additional manual verification.
- **Predictor Collinearity**: We assume that the extracted 3D geometric constraints are independent variables where applicable; if constraints are definitionally related (e.g., derived from the same point cloud), the analysis will treat them as a joint constraint system rather than claiming independent predictive effects.
