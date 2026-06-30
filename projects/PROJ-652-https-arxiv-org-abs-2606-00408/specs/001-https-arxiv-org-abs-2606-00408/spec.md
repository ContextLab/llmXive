# Feature Specification: Reproduce & Validate Observation Masking Regime Map

**Feature Branch**: `652-reproduce-observation-masking`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Masking Stale Observations Helps Search Agents -- Until It Doesn't: A Regime Map and Its Mechanism"

## User Scenarios & Testing

### User Story 1 - Execute Baseline Evaluation Pipeline (Priority: P1)

The researcher MUST be able to trigger the vendored evaluation script (`eval.py`) on a representative subset of the agentic search benchmarks to confirm the environment is configured correctly and the code produces valid output artifacts without GPU acceleration.

**Why this priority**: This is the absolute MVP for a reproduction project. If the code cannot run end-to-end on free-tier CPU resources to produce data, the project cannot proceed to validation or analysis.

**Independent Test**: Can be fully tested by executing the entry script with a small sample dataset (e.g., 5-10 tasks) and verifying the generation of a JSON/CSV results file and a minimal log trace.

**Acceptance Scenarios**:
1. **Given** the submodule is cloned and dependencies are installed, **When** the user runs `python eval.py --dataset subset --sample-size 10 --masking-off`, **Then** the script completes within 60 minutes and outputs a results file containing at least 10 task evaluations.
2. **Given** the script is running, **When** a task encounters a tool call failure, **Then** the system logs the error and continues to the next task rather than crashing the entire pipeline.

### User Story 2 - Validate Regime Map Construction (Priority: P2)

The researcher MUST be able to run the evaluation with observation masking enabled and disabled across at least two distinct model backbones (e.g., a 4B and a mid-capacity model) to reproduce the "inverted-U" accuracy gain pattern described in the paper.

**Why this priority**: This validates the core scientific claim of the paper. Without reproducing the specific interaction between retriever recall and model capacity, the reproduction is incomplete.

**Independent Test**: Can be tested by comparing the accuracy metrics of the "masked" run versus the "baseline" run for specific model/retriever pairs and confirming the data structure supports the regime map visualization.

**Acceptance Scenarios**:
1. **Given** the baseline evaluation results (US-01) are available, **When** the user runs the evaluation with `--masking-on` for a mid-capacity model and a strong retriever, **Then** the system generates a results file where the accuracy gain (masked - baseline) is positive and recorded.
2. **Given** the evaluation is configured for a saturated (very large) model, **When** masking is applied, **Then** the system records an accuracy drop or negligible gain, consistent with the "sharp collapse" regime described in the abstract.

### User Story 3 - Generate Mechanistic Analysis Artifacts (Priority: P3)

The researcher MUST be able to execute the analysis scripts (`eval_analysis.py`) to generate the specific visualizations (e.g., SNR AUC, attention maps) that explain *why* masking works or fails, confirming the "token-for-turn" trade-off mechanism.

**Why this priority**: This provides the mechanistic explanation required by the paper's title. It transforms raw data into the specific evidence needed to validate the "Regime Map" theory.

**Independent Test**: Can be tested by running the analysis script on the results generated in US-02 and verifying the output includes at least one plot or statistical summary table.

**Acceptance Scenarios**:
1. **Given** the evaluation results from US-02 are present in the `data/` directory, **When** the user runs `python eval/eval_analysis.py`, **Then** the system generates a PDF or PNG file containing the "Regime Map" scatter plot.
2. **Given** the analysis script runs, **When** it processes the trajectory logs, **Then** it outputs a summary statistic showing the correlation between "tokens saved" and "turns added."

### Edge Cases

- **What happens when** the external API (DeepSeek/GPT) rate limits the requests during the evaluation? **How does system handle** this? The system MUST implement an exponential backoff retry strategy (max 3 retries) and log the rate-limit event without failing the entire job.
- **What happens when** the dataset subset is too small to show statistical significance? **How does system handle** this? The system MUST flag the result as "Insufficient Sample Size" in the output metadata rather than silently returning a misleading metric.
- **What happens when** the context window limit is exceeded during a long trajectory? **How does system handle** this? The system MUST truncate the context according to the masking logic defined in `tools/context_management.py` and log the truncation event.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the vendored `eval.py` script on a CPU-only runner, ensuring no CUDA/GPU dependencies are invoked, to produce evaluation artifacts (See US-01).
- **FR-002**: System MUST support a command-line flag `--masking-on` and `--masking-off` to toggle the observation masking intervention for comparative analysis (See US-02).
- **FR-003**: System MUST log every tool call, observation, and masking decision in a structured format (JSON/CSV) to enable mechanistic analysis of the "token-for-turn" trade-off (See US-03).
- **FR-004**: System MUST implement an exponential backoff retry mechanism (max 3 attempts) for external API calls to handle rate limiting without terminating the job (See Edge Cases).
- **FR-005**: System MUST generate a summary report comparing the accuracy of masked vs. baseline runs for at least two distinct model backbones (See US-02).

### Key Entities

- **EvaluationRun**: Represents a single execution of the agent on a subset of tasks, containing configuration (masking status, model ID) and results (accuracy, token usage).
- **TrajectoryLog**: A chronological record of a single agent's interaction history, including tool calls, observations, and masking events.
- **RegimeDataPoint**: A data point aggregating model capacity, retriever strength, and accuracy gain, used to construct the regime map.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: Reproducibility is measured against the paper's claim of an "inverted-U" shape by verifying that the generated data points (Model Accuracy vs. Accuracy Gain) exhibit a non-monotonic trend (See US-02).
- **SC-002**: Compute feasibility is measured against the free-tier CI constraint by verifying the total job duration is ≤ 6 hours and memory usage does not exceed 7 GB (See US-01).
- **SC-003**: Mechanistic validity is measured against the paper's "token-for-turn" hypothesis by verifying the generated analysis artifacts show a correlation between tokens saved and additional turns taken (See US-03).
- **SC-004**: Robustness is measured against the requirement for stable execution by verifying zero unhandled exceptions occur during the evaluation of the sample dataset (See US-01).
- **SC-005**: Data integrity is measured against the requirement for traceable results by verifying that every reported accuracy metric in the summary report can be traced back to a specific entry in the `TrajectoryLog` (See FR-003).

## Assumptions

- **Assumption about data/environment**: The vendored submodule `observation-masking` contains all necessary dependencies and scripts to run the evaluation locally without requiring external proprietary model keys (or uses mock generators if keys are unavailable), as the project relies on free-tier CPU CI.
- **Assumption about scope boundaries**: The reproduction focuses on validating the *existence* of the regime map and the *mechanism* via a representative sample; it does not attempt to reproduce the full-scale sweep over 4B to 284B models which would exceed free-tier compute limits.
- **Assumption about target users**: The primary user is a researcher validating the paper's claims, not a production system user; thus, the interface is CLI-based and results are generated as artifacts rather than real-time dashboards.
- **Assumption about dataset-variable fit**: The `observation-masking` repository includes a pre-configured subset of the agentic search benchmarks (e.g., SWE-bench or similar) sufficient for demonstrating the regime map without needing to download or process terabytes of raw web data.
- **Assumption about target performance**: The "sample-size" for the reproduction is assumed to be small (e.g., 50-100 tasks) to ensure the 6-hour compute limit is respected while still providing enough data points to visualize the inverted-U trend.
