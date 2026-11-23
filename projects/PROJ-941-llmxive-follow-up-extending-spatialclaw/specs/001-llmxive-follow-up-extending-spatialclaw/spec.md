# Feature Specification: llmXive follow-up: extending "SpatialClaw: Rethinking Action Interface for Agentic Spatial Reasoning"

**Feature Branch**: `001-llmxive-spatialclaw-restriction`  
**Created**: 2026-08-02  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'SpatialClaw: Rethinking Action Interface for Agentic Spatial Reasoning'"

## User Scenarios & Testing

### User Story 1 - 2D Action Space Restriction & Execution (Priority: P1)

The research team MUST be able to execute the agent logic on the SpatialClaw benchmark dataset using a restricted execution kernel that allows only 2D geometric operations (e.g., `shapely` polygons, 2D projections) and blocks all 3D libraries (e.g., `trimesh`, `pytorch3d`). The system MUST also enforce a rigorous stochasticity control protocol: fixed random seeds, temperature=0, and multiple independent runs (n≥5) per task instance.

**Why this priority**: This is the core experimental manipulation. Without the ability to successfully run the agent in a strictly 2D mode on the benchmark data, no comparison against the 3D baseline can occur. It defines the "restricted agent" condition.

**Independent Test**: The system can be tested by running a specific subset of the benchmark (e.g., a representative number of occlusion tasks) through the restricted kernel. Verification must be deterministic: grep the execution logs for the string "trimesh" and assert the count is 0. The process must also complete without crashing due to blocked imports and verify that the random seed was set correctly for the run.

**Acceptance Scenarios**:

1. **Given** the SpatialClaw benchmark dataset is loaded, **When** the agent attempts to call a 3D rendering function (e.g., `trimesh.Scene`), **Then** the execution kernel intercepts the call, raises a `RestrictedActionError`, and logs the blocked operation without crashing the process.
2. **Given** the agent is processing a task requiring spatial reasoning, **When** the agent generates code using only `shapely` (2D) and `numpy`, **Then** the code executes successfully, returns a 2D symbolic result, and the task step is marked as "completed" in the restricted log.
3. **Given** the restricted kernel is active, **When** the agent attempts to import `pytorch3d` or `open3d`, **Then** the import fails immediately with a clear error message indicating the library is blocked by the 2D constraint policy.
4. **Given** the system is configured for stochasticity control, **When** the agent runs a task, **Then** it uses a fixed random seed and temperature=0, and the system logs the seed value used for reproducibility.

---

### User Story 2 - Performance Metric Collection & Baseline Comparison (Priority: P2)

The system MUST automatically record the success rate, wall-clock inference time per step, and specific task type (occlusion, depth, relative position) for the restricted 2D agent. Crucially, the system MUST re-run the original 3D baseline agent on the *exact same* task instances under identical environmental conditions (except for the action space restriction) to generate a paired dataset for comparison.

**Why this priority**: This provides the quantitative data required to answer the research question regarding the "loss ceiling" and the trade-off between expressiveness and latency. Re-running the baseline eliminates confounds from dataset drift or environment differences, ensuring a scientifically valid paired comparison.

**Independent Test**: The system can be tested by processing a fixed, small dataset with both the 2D restricted agent and the re-run 3D baseline agent. The system must generate a summary report containing a table comparing the 2D agent's success rate and latency against the *re-run* 3D baseline values for the same tasks, verifying that the comparison logic correctly identifies task types and pairs the results.

**Acceptance Scenarios**:

1. **Given** the restricted agent has completed a batch of tasks, **When** the analysis script runs, **Then** it outputs a CSV file containing `task_id`, `task_type` (occlusion/depth/relative), `success_flag`, `wall_clock_time_ms`, and `agent_type` (2D or 3D).
2. **Given** the results CSV is generated, **When** the comparison module runs, **Then** it calculates the absolute difference in success rate between the 2D agent and the *re-run* 3D baseline for the "occlusion" task type for each paired task instance.
3. **Given** the agent processes a sequence of steps, **When** the timing module runs, **Then** it records the time taken for each step and calculates the average step latency, explicitly excluding any time spent on blocked 3D library initialization attempts.

---

### User Story 3 - Statistical Significance & Threshold Sensitivity Analysis (Priority: P3)

The system MUST perform a paired statistical test (t-test or Wilcoxon) to determine if performance degradation on 3D-specific tasks is significant, comparing the 2D agent results against the *re-run* 3D baseline results for the same task instances. The system MUST also conduct a sensitivity analysis on the depth-estimation threshold (if applicable) to verify robustness, using a defined set of values and reporting the resulting variation without pre-judging the outcome.

**Why this priority**: This ensures the findings are methodologically sound (addressing inference framing and multiplicity) and that any arbitrary thresholds used in the 2D projection logic are justified. It prevents the project from reporting spurious correlations and ensures the statistical test is mathematically valid.

**Independent Test**: The system can be tested by running the statistical module on the collected paired results. It must output a p-value for the difference between 2D and 3D performance on depth tasks. It must also generate a sensitivity report showing how results change when the depth threshold is varied over a defined set of values, reporting the variation in false-positive and false-negative rates without enforcing a pass/fail limit.

**Acceptance Scenarios**:

1. **Given** the paired results (2D vs. 3D) for depth tasks, **When** the statistical module runs, **Then** it performs a Wilcoxon signed-rank test and outputs a p-value indicating whether the degradation is statistically significant (p < 0.05).
2. **Given** a depth-estimation threshold is defined, **When** the sensitivity analysis runs, **Then** it re-evaluates the task success rate using a defined set of threshold values and reports the variation in false-positive and false-negative rates across these values.
3. **Given** multiple hypothesis tests are conducted (one for occlusion, one for depth, one for relative position), **When** the analysis completes, **Then** it applies a Bonferroni correction to the reported p-values to control the family-wise error rate.
4. **Given** the ground-truth label for a task is known, **When** the 2D agent fails, **Then** the system logs whether the failure was due to "projection loss" (information lost in 2D) or "action restriction" (logic error), using the original 3D ground truth as the independent reference.

---

### Edge Cases

- **What happens when** the dataset contains objects with zero depth variance (flat objects)? **How does system handle** the projection? The system MUST treat these as valid 2D inputs and not crash; the success rate for these specific tasks should be compared against the baseline to verify if 2D representations are sufficient for flat objects.
- **How does system handle** a scenario where the 2D projection loses critical occlusion information (e.g., two objects overlap perfectly in 2D but are distinct in 3D)? The system MUST record this as a "failure due to projection loss" and log the specific geometric configuration to quantify the irrecoverable information.
- **What happens when** the CPU-only environment runs out of memory during the pre-processing of large point clouds? The system MUST implement a fallback to process the data in smaller chunks (streaming) and log the memory usage, ensuring the job does not fail but completes with a warning.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a restricted execution kernel that intercepts all function calls and blocks any library or function not explicitly whitelisted for 2D geometric operations (e.g., `shapely`, `numpy`), explicitly blocking 3D libraries like `trimesh` and `pytorch3d`. (See US-1)
- **FR-002**: System MUST convert the original 3D point cloud/scene data from the SpatialClaw benchmark into a standardized 2D symbolic representation (e.g., projected bounding boxes, depth histograms) without using 3D reconstruction libraries or invoking 3D rendering engines. (See US-1)
- **FR-003**: System MUST record the wall-clock inference time for every step of the agent's execution, excluding time spent on blocked library attempts, and store this in a structured log file. (See US-2)
- **FR-004**: System MUST automatically compare the restricted agent's success rate and latency metrics against the 3D baseline values extracted from `data/baseline_spatialclaw.csv` (which contains the re-run baseline results) for each task type (occlusion, depth, relative position). (See US-2)
- **FR-005**: System MUST perform a paired statistical test (Wilcoxon signed-rank or t-test) on the performance differences between the 2D and 3D conditions for each task category and output the p-value. (See US-3)
- **FR-006**: System MUST execute a sensitivity analysis sweeping the depth-estimation threshold over a defined set of values and report the resulting variation in false-positive and false-negative rates in a CSV table containing columns `threshold_value`, `false_positive_rate`, and `false_negative_rate`. (See US-3)
- **FR-007**: System MUST re-run the original 3D baseline agent on the exact same task instances as the 2D agent under identical environmental conditions to generate a paired dataset for statistical comparison. (See US-2)
- **FR-008**: System MUST enforce a stochasticity control protocol: fix random seeds, set temperature=0, and execute at least 5 independent runs per task instance to establish variance and attribute performance differences to the action space restriction. (See US-1)

### Key Entities

- **Task Instance**: Represents a single query from the SpatialClaw benchmark, containing the input scene description, the ground-truth label, and the task type (occlusion, depth, relative).
- **Execution Log**: A record of the agent's interaction with the restricted kernel, containing the code executed, the outcome (success/failure), the error type (if blocked), and the step duration.
- **Performance Metric**: A derived entity containing the aggregated success rate, average latency, and statistical significance (p-value) for a specific task type.
- **Baseline Run**: A record of the 3D baseline agent's execution on a specific task instance, used for paired comparison.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The performance degradation (success rate difference) for depth-estimation tasks is measured against the 3D baseline success rate re-run on the same task instances (See US-2).
- **SC-002**: The statistical significance of the performance difference is measured against a significance level of α = 0.05, with Bonferroni correction applied for multiple comparisons (See US-3).
- **SC-003**: The sensitivity of the depth-estimation threshold is measured against the stability of the false-negative rate; the system must report the variation in false-negative rates across the tested threshold range (See US-3).
- **SC-004**: The computational feasibility is measured against the GitHub Actions free-tier constraint (≤6 hours total runtime, ≤7 GB RAM); the entire experiment must complete within this budget (See Assumptions).

## Assumptions

- The SpatialClaw benchmark dataset (specifically the occlusion and depth-estimation subsets) is accessible via the official repository or Zenodo archive and contains the necessary ground-truth 3D coordinates.
- The original 3D baseline agent code is available and can be re-executed on the same task instances under controlled conditions.
- The `shapely` and `numpy` libraries are sufficient to implement the required 2D geometric projections and symbolic operations for the benchmark tasks.
- The depth-estimation threshold used in the 2D projection logic is set to a default value of [deferred] units, based on community standards for similar spatial reasoning benchmarks, and is subject to the sensitivity analysis defined in FR-006.
- The GitHub Actions free-tier runner (multiple CPU cores, ~7 GB RAM) is capable of processing the sampled dataset and running the statistical analysis within the 6-hour time limit without requiring GPU acceleration.
- The agent's internal logic for generating code is sufficiently controlled via fixed seeds and temperature=0 to allow attribution of performance differences to the action space restriction rather than stochastic generation noise.