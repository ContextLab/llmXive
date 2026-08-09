# Feature Specification: llmXive follow-up: extending "S-Agent: Spatial Tool-Use Elicits Reasoning for Spatial Intelligence"

**Feature Branch**: `001-symbolic-spatial-reasoning`  
**Created**: 2026-07-03  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'S-Agent: Spatial Tool-Use Elicits Reasoning for Spatial Intelligence'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Symbolic CSP Solver Execution on Static Scenes (Priority: P1)

**User Journey**: As a researcher, I need to execute a deterministic Constraint Satisfaction Problem (CSP) solver on a representative sample of up to 1,000 static multi-view scenes from the S-Agent-300K dataset using *only* extracted 3D geometric evidence (coordinates, object relations), so that I can generate spatial reasoning predictions (counting and positioning) without invoking a neural VLM or using historical tool-call traces.

**Why this priority**: This is the core experimental intervention. Without a functioning symbolic solver that can ingest raw geometry and produce outputs *independently* of VLM traces, no valid comparison is possible. It represents the primary hypothesis test: "Can symbolic logic replace neural planning?"

**Independent Test**: Can be fully tested by running the solver script against the n=1,000 scene subset and verifying that it produces a valid JSON output file containing predicted answers for every scene, with zero runtime errors and no GPU utilization.

**Acceptance Scenarios**:

1. **Given** a CSV of up to 1,000 static scenes with extracted 3D geometric constraints (excluding VLM traces), **When** the CSP solver is executed on a standard 8-core CPU (e.g., Intel i7-12700K), **Then** it outputs a JSON file with a prediction for every scene ID within 6 hours of wall-clock time.
2. **Given** the solver is running, **When** it processes n=1,000 scenes sequentially or in a batch, **Then** it utilizes only standard Python libraries (e.g., `python-constraint`, `scipy`) and consumes a manageable amount of RAM at peak load.
3. **Given** a scene with ambiguous geometric constraints, **When** the solver processes it, **Then** it returns a "No Solution" or "Ambiguous" status rather than hallucinating a geometric configuration, ensuring deterministic behavior.

---

### User Story 2 - Comparative Accuracy & Latency Benchmarking (Priority: P2)

**User Journey**: As a researcher, I need to compare the accuracy (F1-score, Exact Match) and inference latency of the symbolic solver's predictions against the ground-truth labels and the original S-Agent (VLM) baseline, so that I can quantify the performance gap and computational savings.

**Why this priority**: This validates the research question. It determines if the symbolic approach is viable (accuracy > 85% of baseline) and if it achieves the motivation (latency reduction). It transforms the raw output of US-1 into scientific evidence.

**Independent Test**: Can be fully tested by running a benchmark script that loads the symbolic predictions, the VLM baseline predictions, and ground truth, then outputs a summary table with accuracy metrics and median latency per method.

**Acceptance Scenarios**:

1. **Given** the symbolic predictions and ground-truth labels, **When** the benchmark script calculates metrics, **Then** it reports an Exact Match score and F1-score for the symbolic agent.
2. **Given** the symbolic and VLM prediction sets, **When** the latency is measured on a multi-core CPU for the symbolic agent and on a single NVIDIA A100 GPU (4-bit quantized) for the VLM baseline, **Then** the symbolic agent's median inference time is at least 10x faster than the VLM baseline.
3. **Given** the paired results, **When** McNemar's test is performed, **Then** the script outputs a p-value indicating whether the accuracy difference is statistically significant (p < 0.05).

---

### User Story 3 - Failure Case Analysis & Semantic Gap Identification (Priority: P3)

**User Journey**: As a researcher, I need to analyze the specific scenes where the symbolic solver fails (predicts incorrectly while VLM succeeds) to categorize the error as either "geometric ambiguity" or "missing semantic disambiguation," so that I can conclude whether neural understanding is essential.

**Why this priority**: This provides the qualitative depth to the quantitative results. If the solver fails, understanding *why* is critical for the "Research Question" resolution. It moves beyond "it failed" to "it failed because X."

**Independent Test**: Can be fully tested by generating a report listing a representative set of failure cases with their associated error category and a brief text explanation derived from the scene metadata.

**Acceptance Scenarios**:

1. **Given** a set of scenes where the symbolic solver predicted incorrectly but the VLM was correct, **When** the analysis script reviews the scene metadata and constraint satisfaction status, **Then** it classifies the failure as:
    - "Geometric Ambiguity" if the CSP solver returned "No Solution" due to under-specified constraints (insufficient geometric data).
    - "Semantic Gap" if the CSP solver returned "No Solution" or an incorrect answer despite having sufficient geometric constraints (implying missing non-geometric context required by the VLM).
2. **Given** the classified failures, **When** the report is generated, **Then** it includes a summary count of each failure type and a representative example scene ID for each category.

---

### Edge Cases

- **What happens when the extracted geometric evidence is insufficient to form a solvable CSP?**
  - The solver must explicitly return a "No Solution" status rather than crashing or guessing. This case is critical for the "Geometric Ambiguity" failure analysis.
- **How does the system handle scenes where the input data is corrupted or missing?**
  - The solver must detect missing files or malformed geometry and log a specific error code, excluding the scene from the "solvable" count to prevent skewing accuracy metrics.
- **What happens if the dataset download (S-Agent-300K) is incomplete or corrupted?**
  - The pipeline must fail fast with a clear error message indicating missing files, rather than proceeding with a partial dataset that would invalidate the statistical power analysis.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST extract 3D geometric constraints (coordinates, object relations) from the S-Agent-300K dataset for a stratified random sample of n=1,000 static multi-view scenes, ensuring the data format is compatible with a standard CSP solver. The system MUST NOT use historical VLM tool-call traces as input to the solver (See US-1).
- **FR-002**: The system MUST implement a deterministic CSP solver that ingests the extracted geometric constraints and solves for spatial counting and relative positioning tasks directly via constraint propagation, without requiring any neural network inference, GPU acceleration, or pre-determined tool sequences (See US-1).
- **FR-003**: The system MUST calculate Exact Match and F1-score metrics by comparing the symbolic solver's predictions against both the ground-truth labels and the original S-Agent (VLM) baseline predictions (See US-2).
- **FR-004**: The system MUST measure and record the inference latency for each scene processed by the symbolic solver on a multi-core CPU environment, ensuring no single scene exceeds a practical threshold for processing time. (See US-2).
- **FR-005**: The system MUST perform a McNemar's statistical significance test on the paired accuracy results of the symbolic and VLM agents to determine if the performance difference is statistically significant (See US-2).
- **FR-006**: The system MUST categorize and report failure cases where the symbolic solver underperforms the VLM, distinguishing between "geometric ambiguity" (insufficient constraints) and "semantic disambiguation" needs (sufficient constraints but failed inference) (See US-3).
- **FR-007**: The system MUST automatically exclude scenes from the analysis set if the required 3D geometric constraint data is missing or malformed. The exclusion count and the IDs of excluded scenes MUST be logged and reported as part of the dataset preprocessing summary to ensure transparency regarding the final sample size (n = [measured count]) (See US-1).

### Key Entities

- **StaticScene**: A data unit representing a single static multi-view environment, containing 3D geometric constraints, ground-truth labels, and (for baseline comparison) the original VLM traces.
- **SpatialPrediction**: The output of the reasoning engine (either symbolic or neural), containing the predicted count or relative position for a specific scene.
- **BenchmarkResult**: A composite record linking a `StaticScene` ID with the predictions from both agents, the ground truth, accuracy metrics, and latency measurements.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The accuracy of the symbolic agent (Exact Match score) is measured against the original S-Agent (VLM) baseline accuracy on the same n=1,000 scenes to determine the percentage of neural performance retained (See US-2).
- **SC-002**: The inference latency of the symbolic agent is measured against the VLM baseline latency on a standard multi-core CPU (symbolic) vs. single NVIDIA A100 GPU (VLM) to quantify the computational efficiency gain (See US-2).
- **SC-003**: The statistical significance of the accuracy difference is measured using McNemar's test p-value to determine if the observed performance gap is non-random (See US-2).
- **SC-004**: The proportion of failure cases attributable to "semantic disambiguation" is measured against the total number of symbolic failures to assess the necessity of neural understanding (See US-3).
- **SC-005**: The project is considered successful if the symbolic agent achieves an Exact Match score ≥ 85% of the VLM baseline accuracy on the n=1,000 scene sample (See US-2).

## Assumptions

- **Dataset Variable Fit**: We assume the S-Agent-300K benchmark dataset contains sufficient 3D geometric coordinates and object relations for a representative sample of scenes to formulate a solvable CSP. If specific scenes lack the required data, FR-007 dictates they will be excluded and logged.
- **Inference Framing**: The study is observational; we assume that the comparison between the symbolic solver and the VLM baseline on the *same* dataset allows for a valid assessment of the reasoning mechanism's source, but we will frame results as associational regarding the "source of reasoning" rather than causal claims about general spatial intelligence.
- **Compute Feasibility**: We assume that a standard Python CSP solver (e.g., `python-constraint` or `ortools` in CPU mode) can solve the extracted constraint problems for n=1,000 scenes within the -hour CI limit and GB RAM constraint without requiring GPU acceleration or 8-bit quantization.
- **Threshold Justification**: We assume a fixed accuracy threshold of 85% of the VLM baseline is a defensible community standard for "high-fidelity replication" in this context. A sensitivity analysis will sweep this threshold over a range of high-probability values to report how the "success/failure" verdict varies (See FR-003). The project's success condition is explicitly defined in SC-005.
- **Measurement Validity**: We assume the ground-truth labels in the S-Agent-300K dataset are accurate and sufficient for calculating Exact Match and F1-scores without requiring additional manual verification.
- **Predictor Collinearity**: We assume that the extracted 3D geometric constraints are independent variables where applicable; if constraints are definitionally related (e.g., derived from the same point cloud), the analysis will treat them as a joint constraint system rather than claiming independent predictive effects.