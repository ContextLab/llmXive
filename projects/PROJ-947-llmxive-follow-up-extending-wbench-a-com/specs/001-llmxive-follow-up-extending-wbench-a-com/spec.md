# Feature Specification: llmXive Follow-up: Extending WBench with Sequence Complexity Analysis

**Feature Branch**: `001-llmxive-wbench-entropy`  
**Created**: 2026-07-21  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'WBench: A Comprehensive Multi-turn Benchmark for Interactive Video World Model Evaluation'"

## User Scenarios & Testing

### User Story 1 - Construct and Annotate Sequence Complexity (Priority: P1)

As a researcher, I need to programmatically generate low, medium, and high-entropy variants of the WBench interaction sequences and compute a "Sequence Complexity Score" for each, so that I can establish the independent predictor variable for the correlation analysis.

**Why this priority**: This is the foundational step. Without the stratified dataset and the computed complexity scores, no correlation analysis can be performed. It isolates the input complexity variable from the visual output.

**Independent Test**: Can be fully tested by running the data processing pipeline on a subset of 10 WBench cases and verifying that the output CSV contains valid entropy values (0.0–1.0) and dependency depth integers, and that the three variants (low/med/high) show statistically distinct complexity scores.

**Acceptance Scenarios**:

1. **Given** a raw WBench interaction log, **When** the system generates the three entropy variants using a token-reweighting and resampling algorithm with ≤20 retries to converge on targets, **Then** the low-entropy variant must have a Shannon entropy score < 0.3 and the high-entropy variant > 0.7 (normalized), ensuring all sequences remain physically plausible.
2. **Given** a generated sequence, **When** the dependency graph is constructed from the original semantic intent of the commands, **Then** the causal depth metric must be calculated as the longest path in the turn-dependency graph, returning an integer ≥ 1.

### User Story 2 - Execute CPU-Optimized Inference on Stratified Data (Priority: P2)

As a researcher, I need to run inference on publicly available, CPU-optimized world models using the stratified sequences, so that I can collect the visual output data required for the fidelity metrics.

**Why this priority**: This generates the dependent variable (physics/consistency scores). It is critical to ensure the models selected fit within the GitHub Actions free-tier constraints (≤7GB RAM, no GPU) to guarantee the pipeline actually runs.

**Independent Test**: Can be fully tested by executing the inference script on a single test case with a model released within the last 7 days; the process must complete within 60 minutes and produce a video file (MP4) without CUDA errors or OOM crashes.

**Acceptance Scenarios**:

1. **Given** a high-entropy sequence and a selected model, **When** the system performs a short dry-run profiling step to verify peak RAM usage < 6.5 GB, **Then** the system proceeds to full inference only if the limit is met; otherwise, it logs an error and skips the model.
2. **Given** a model that fails to load due to size or other errors, **When** the system attempts to initialize, **Then** the system must log a clear error, skip that model, and continue with the remaining valid models, ensuring at least 3 models are available to proceed.

### User Story 3 - Correlate Complexity with Fidelity Degradation (Priority: P3)

As a researcher, I need to compute the Pearson correlation and trend analysis between the Sequence Complexity Score and the WBench physics/consistency metrics, so that I can identify the "tipping point" of model failure.

**Why this priority**: This delivers the final scientific insight (the "gap" addressed). It transforms raw metrics into the answer for the research question regarding non-linear degradation.

**Independent Test**: Can be fully tested by feeding a synthetic dataset of a moderate size with a known negative correlation into the analysis script and verifying the output trend analysis shows the correct direction and significance within ±0.05 tolerance.

**Acceptance Scenarios**:

1. **Given** a complete set of (Complexity Score, Physics Score) pairs, **When** the trend analysis runs, **Then** the output must include a correlation coefficient (r) and a p-value < 0.05 to claim statistical significance.
2. **Given** a non-linear degradation pattern, **When** the ANOVA with trend analysis is applied, **Then** the system must report a significant trend or mean difference between complexity levels; if a breakpoint is tested via Chow test, it must have p < 0.05 to be reported.

### Edge Cases

- **What happens when** a selected world model fails to generate a video (e.g., hangs or crashes) for a specific high-entropy input?
  - *System handles it by* logging the failure, marking the specific turn as "NaN" in the results table, and excluding that specific data point from the correlation calculation while maintaining the integrity of the remaining dataset.
- **How does system handle** a dataset where the "Sequence Complexity Score" shows no variance (e.g., all generated variants accidentally have similar entropy)?
  - *System handles it by* detecting near-zero variance in the predictor variable during the pre-analysis check and raising a `[CRITICAL]` alert to abort the run, preventing a meaningless correlation calculation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate three distinct sequence variants (Low, Medium, High entropy) for every base WBench case by reordering valid command sequences or substituting semantically equivalent tokens, ensuring the Low variant has a Shannon entropy < 0.3 and the High variant > 0.7, using a token-reweighting algorithm that converges on targets within ≤20 iterations (See US-1).
- **FR-002**: System MUST compute a "Sequence Complexity Score" for each variant based on Shannon entropy of command tokens and the maximum depth of the causal dependency graph derived from the original semantic intent of the commands, not the manipulated token string (See US-1).
- **FR-003**: System MUST select and execute inference on up to 5 world models that are verified to run on CPU with <7GB RAM footprint, skipping any model that exceeds this limit, but requiring a minimum of 3 valid models to proceed with the analysis (See US-2).
- **FR-004**: System MUST calculate physics compliance and temporal consistency scores for every generated video using the existing WBench metric suite, subtracting a motion artifact baseline calculated from a random-noise video, and storing results in a structured CSV (See US-3).
- **FR-005**: System MUST perform a Pearson correlation analysis and an ANOVA with trend analysis to identify significant differences or trends between complexity levels, replacing piecewise linear regression due to insufficient data points (See US-3).
- **FR-006**: System MUST implement a multiple-comparison correction (e.g., Bonferroni) for any hypothesis tests performed across the N models to control family-wise error rate (See US-3).

### Key Entities

- **SequenceVariant**: Represents a specific version (Low/Med/High) of a WBench interaction case, containing the raw text commands and the computed complexity metrics.
- **InferenceResult**: Represents the output of a single model run, containing the generated video path, the physics score, and the consistency score.
- **DegradationCurve**: A derived entity representing the relationship between complexity scores and fidelity metrics for a specific model, including the calculated trend.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Pearson correlation coefficient (r) between Sequence Complexity Score and Physics Compliance is measured against the null hypothesis of no correlation (r=0), requiring a p-value < 0.05 to confirm a significant relationship (See FR-005, US-3).
- **SC-002**: The identified trend or significant difference is measured against the distribution of complexity scores to ensure it falls within the observed range, confirming the non-linear degradation pattern (See FR-005, US-3).
- **SC-003**: The family-wise error rate for the set of N model analyses is measured against the standard alpha level (0.05) after applying Bonferroni correction, ensuring statistical validity (See FR-006, US-3).
- **SC-004**: The total inference runtime for the full dataset (289 cases × 3 variants × N models, where 3 ≤ N ≤ 5) is measured against the 6-hour GitHub Actions limit, ensuring the analysis is feasible on free-tier CPU (See FR-003, US-2).
- **SC-005**: The variance of the "Sequence Complexity Score" across the generated variants is measured against a minimum threshold of variance > 0.05 to ensure the predictor variable is sufficiently distinct for correlation (See FR-001, US-1).

## Assumptions

- **Assumption about data availability**: The WBench dataset (a collection of cases with numerous turns) is publicly accessible via the repository linked in the original paper. and can be downloaded and parsed without authentication barriers.
- **Assumption about model availability**: At least 3 world models with <7GB RAM footprint and CPU-compatible weights (e.g., GGUF or standard PyTorch without CUDA requirements) are available on the Hugging Face Model Hub at the time of execution.
- **Assumption about metric validity**: The existing WBench metric suite for physics compliance and temporal consistency is robust enough to be applied to the generated video variants without requiring re-tuning or new calibration, provided the motion artifact baseline is subtracted.
- **Assumption about computational constraints**: The "Sequence Complexity Score" calculation (Shannon entropy + graph depth) is computationally negligible and will not impact the total runtime budget.
- **Assumption about dataset-variable fit**: The WBench interaction logs contain sufficient token diversity and explicit causal links to allow for meaningful entropy and dependency depth calculations; if the logs are too sparse, the complexity score may lack variance.