# Feature Specification: llmXive follow-up: extending "EVA-Bench: A New End-to-end Framework for Evaluating Voice Agents"

**Feature Branch**: `001-llmxive-latency-study`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'EVA-Bench: A New End-to-end Framework for Evaluating Voice Agents'"

## User Scenarios & Testing

### User Story 1 - Latency Injection & Baseline Execution (Priority: P1)

As a researcher, I need to inject variable network latency (jitter and inter-turn delays) into the EVA-Bench audio streams and re-run the evaluation pipeline so that I can isolate the effect of temporal disruption from acoustic noise.

**Why this priority**: This is the foundational capability. Without the ability to systematically alter the input data and re-execute the scoring logic, no comparative analysis can occur. It directly enables the core research question regarding the degradation of metrics.

**Independent Test**: The system can be tested by taking a single EVA-Bench scenario, injecting a fixed delay, re-running the pipeline, and verifying that the output log contains a modified inter-turn gap consistent with the injected delay while the original acoustic content remains unchanged.

**Acceptance Scenarios**:

1. **Given** a valid EVA-Bench audio scenario file, **When** the latency injection module applies a 200ms delay, **Then** the resulting audio file must have an inter-turn silence gap of 200ms ± 10ms, and the original speech content must be bit-identical to the source.
2. **Given** the modified audio file, **When** the EVA-Bench evaluation pipeline executes, **Then** the system must generate a score report containing the "Turn-Taking" and "Conversation Progression" metrics without throwing runtime errors due to audio format mismatches.
3. **Given** a set of 10 scenarios, **When** the script iterates through them with a 1000ms delay, **Then** all 10 scenarios must complete execution within 360 seconds on a standard CPU runner, ensuring the process is CPU-tractable.

---

### User Story 2 - Threshold Detection & Non-Linear Analysis (Priority: P2)

As a researcher, I need to execute the evaluation across a range of latency increments (200ms to 2000ms) and perform piecewise regression so that I can identify the specific non-linear failure threshold where conversation flow collapses.

**Why this priority**: This addresses the specific hypothesis of the research question (the existence of a "tipping point"). It transforms raw data into the primary scientific insight (the threshold value).

**Independent Test**: The system can be tested by running the full sweep (200ms–2000ms) on a subset of 5 scenarios, extracting the "Conversation Progression" scores, and verifying that a piecewise regression model is fitted and an inflection point is reported in the summary statistics.

**Acceptance Scenarios**:

1. **Given** the full set of latency conditions (200ms, 400ms, ..., 2000ms), **When** the analysis script runs, **Then** it must output a segmented linear model with a pre-specified breakpoint or a non-parametric trend model, reporting an inflection point (threshold) and a goodness-of-fit statistic (R²) for the "Conversation Progression" metric.
2. **Given** the regression results, **When** the system compares any adjacent latency steps, **Then** it must flag if the score drop between these steps exceeds a relative decline ≥ 15%, indicating a potential non-linear collapse.
3. **Given** the dataset, **When** the piecewise regression is computed, **Then** the entire analysis (including model fitting) must complete in ≤ 45 minutes on a CPU-only environment to ensure reproducibility within CI limits.

---

### User Story 3 - Comparative Robustness Reporting (Priority: P3)

As a researcher, I need to generate a comparative report that contrasts the degradation curves of "Turn-Taking" under latency versus the known degradation under acoustic noise (from the original EVA-Bench paper) so that I can validate if temporal disruption is a distinct failure mode.

**Why this priority**: This provides the contextual validity of the findings, allowing the researcher to claim that the new vulnerability profile is distinct from existing knowledge, fulfilling the "gap analysis" requirement.

**Independent Test**: The system can be tested by generating a CSV or JSON report that includes columns for "Latency Condition," "Turn-Taking Score," and "Acoustic Baseline Score," verifying that the comparison logic correctly aligns the metrics.

**Acceptance Scenarios**:

1. **Given** the results from the latency sweep and the reference acoustic baseline data, **When** the comparison module executes, **Then** it must output a normalized degradation curve (score vs. delay) and a separate curve for acoustic noise (score vs. SNR) for direct visual or statistical comparison.
2. **Given** the two degradation curves, **When** the system calculates the area under the curve (AUC) for both, **Then** it must report the difference in AUC to quantify the relative severity of temporal vs. acoustic disruption.
3. **Given** the final report, **When** a reviewer inspects the "Distinct Failure Mode" conclusion, **Then** the report must explicitly state whether the latency threshold is statistically distinct from the acoustic noise failure point based on the repeated-measures ANOVA results.

### Edge Cases

- What happens if the EVA-Bench dataset download fails or the audio files are corrupted? (System must fail fast with a clear error code and not proceed to analysis).
- How does the system handle scenarios where the agent's response time is naturally longer than the injected delay, potentially masking the jitter effect? (The analysis must flag these as "masked" and exclude them from the threshold calculation or apply a correction factor).
- What if the piecewise regression fails to converge due to low variance in scores across latency steps? (The system must default to a linear regression and report a "No distinct threshold detected" status with a confidence interval).

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a latency injection module using `pydub` or `scipy` to insert variable inter-turn delays ranging from 200ms to 2000ms in 200ms increments into EVA-Bench audio streams. (See US-1)
- **FR-002**: System MUST re-execute the original EVA-Bench scoring pipeline on the modified audio streams without altering the internal scoring logic or metric definitions. (See US-1)
- **FR-003**: System MUST perform a repeated-measures ANOVA to determine statistical significance of score differences across the latency conditions. (See US-2)
- **FR-004**: System MUST fit a segmented linear model with a pre-specified breakpoint or a non-parametric trend test to the "Conversation Progression" scores to identify the specific inflection point (threshold) where degradation accelerates. (See US-2)
- **FR-005**: System MUST generate a comparative report contrasting the latency-induced degradation curve against the acoustic-noise degradation curve, where the acoustic baseline is constructed by re-running the original EVA-Bench pipeline on the same dataset with acoustic perturbations. (See US-3)
- **FR-006**: System MUST run the evaluation pipeline without model quantization or hardware acceleration (GPU/CUDA). (See US-1)
- **FR-007**: System MUST optimize the pipeline execution to ensure the full dataset analysis completes within 6 hours on a CPU-only runner. (See US-1, SC-004)
- **FR-008**: System MUST perform a statistical comparison (interaction test or t-test) between the latency failure point and the acoustic noise failure point to validate distinctness. (See US-3)
- **FR-009**: System MUST utilize behavioral metrics (e.g., task completion, semantic coherence) that are not mathematically derived from the injected delay to prevent tautological validation. (See US-2)

### Key Entities

- **LatencyCondition**: Represents a specific injected delay value (e.g., 200ms, 800ms) and its associated metadata (jitter profile, silence gap).
- **EvaluationMetric**: Represents a specific EVA-X sub-metric (e.g., "Turn-Taking", "Conversation Progression") and its scored value for a given condition.
- **DegradationCurve**: A derived entity representing the relationship between latency values and metric scores, including the fitted regression model parameters.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The latency injection process must successfully modify all target EVA-Bench scenarios with the specified delay increments without data corruption. (See FR-001, US-1)
- **SC-002**: The segmented linear model or non-parametric test must identify a statistically significant inflection point (p < 0.05) for the "Conversation Progression" metric, or explicitly report "No threshold detected" with a confidence interval. (See FR-004, US-2)
- **SC-003**: The comparative analysis must demonstrate a distinct degradation profile for latency compared to acoustic noise, quantified by a statistically significant or substantial difference in Area Under the Curve (AUC) or a statistically significant interaction effect in the ANOVA. (See FR-005, FR-008, US-3)
- **SC-004**: The entire end-to-end analysis (injection, execution, and modeling) for the full dataset must complete within 6 hours on a CPU-only GitHub Actions runner with ≤ 7 GB RAM. (See FR-006, FR-007, US-1)
- **SC-005**: The final report must include a sensitivity analysis of the identified threshold, sweeping the decision cutoff (the inflection point found in SC-002) over a range of ± 50ms to demonstrate stability. (See FR-004, US-2)

## Assumptions

- The EVA-Bench dataset (a collection of scenarios) and pre-recorded audio logs are accessible via the public arXiv repository and can be downloaded within the disk capacity constraints of the CI runner.
- The original EVA-Bench evaluation pipeline is compatible with the modified audio streams generated by `pydub`/`scipy` without requiring code changes to the scoring logic.
- The "Conversation Progression" and "Turn-Taking" metrics are sufficiently sensitive to temporal delays to produce a measurable degradation curve within the 200ms–2000ms range.
- The analysis relies on the assumption that the agent's behavior in the pre-recorded logs is deterministic enough that re-running the pipeline yields consistent scores for the same input audio.
- The study is observational in nature regarding the agent's response; findings will be framed as associational between latency and score degradation, not causal, unless the original EVA-Bench framework includes randomization of turn-taking which is not specified in the idea.
- The sample size provides sufficient statistical power for the repeated-measures ANOVA.; if power is low, the result will be reported as a "trend" rather than a definitive threshold.
- The `pydub` and `scipy` libraries are available in the standard Python environment of the GitHub Actions runner and do not require heavy compilation steps that would exceed the 6-hour time limit.