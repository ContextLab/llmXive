# Feature Specification: llmXive follow-up: extending "COLLEAGUE.SKILL: Automated AI Skill Generation via Expert Knowledge Di"

**Feature Branch**: `001-llmxive-skill-separation`  
**Created**: 2026-07-16  
**Status**: Draft  
**Input**: User description: "Does explicitly decoupling capability heuristics from behavioral style in LLM agent prompts reduce hallucinated expertise and style drift during long-horizon interactions compared to monolithic persona prompts?"

## User Scenarios & Testing

### User Story 1 - Execute CPU-tractable LLM inference with decoupled prompt architecture (Priority: P1)

The research system must load a small language model (e.g., Llama-8B-Q4 or Phi-3-mini) on a CPU-only environment and execute inference tasks using three distinct prompt conditions: Monolithic, Separated Tracks, and Generic Baseline. This is the foundational step required to generate any data for analysis.

**Why this priority**: Without successful, reproducible inference under strict CPU constraints (no GPU, <7GB RAM), no data can be collected to test the core hypothesis regarding hallucination and style drift.

**Independent Test**: The system can be tested by running a single profile-task pair through all three conditions and verifying that the model generates text within a reasonable timeout without CUDA errors or OOM (Out of Memory) crashes.

**Acceptance Scenarios**:
1. **Given** a CPU-only runner with 7GB RAM, **When** the system loads a quantized 8B parameter model, **Then** the model must initialize successfully without requesting GPU resources.
2. **Given** a valid expert profile and task scenario, **When** the system generates a response using the "Separated Tracks" prompt structure, **Then** the output must be generated within 300 seconds.
3. **Given** the same profile-task pair, **When** the system runs the "Monolithic" and "Generic" conditions, **Then** all three outputs must be saved to disk for subsequent evaluation.

### User Story 2 - Evaluate outputs against deterministic ground-truth rules (Priority: P2)

The system must evaluate generated responses against external ground-truth traces and rule definitions to calculate three metrics: Heuristic Adherence (task success on held-out validation), Style Consistency (keyword/structure frequency), and Hallucination Rate (inference of knowledge not present in context).

**Why this priority**: This step transforms raw text into quantitative data. Without deterministic, rule-based evaluation (avoiding LLM-based judges to prevent circularity), the comparison between conditions is invalid.

**Independent Test**: The evaluation script can be tested independently by feeding it a known "gold standard" response and a known "hallucinated" response to verify that the Heuristic Adherence and Hallucination Rate scores match the expected binary values.

**Acceptance Scenarios**:
1. **Given** a generated response that fails to solve a held-out validation problem defined by the input profile, **When** the evaluation script runs, **Then** the Heuristic Adherence score must be 0 (fail).
2. **Given** a generated response containing facts that require multi-hop inference not present in the context, **When** the script performs logic checks, **Then** the Hallucination Rate counter must increment if the inference is incorrect.
3. **Given** a response that matches the behavior track's defined keywords but fails capability rules, **When** the script runs, **Then** the Style Consistency score must be high while Heuristic Adherence is low.

### User Story 3 - Aggregate results and perform statistical comparison (Priority: P3)

The system must aggregate scores across the full experimental matrix (50 profiles × 200 tasks × 3 conditions = 30,000 combinations) and perform a Linear Mixed-Effects Model (LMM) analysis to test for significant differences in hallucination rates and heuristic adherence between the Monolithic and Separated Tracks conditions, accounting for nested random effects of Profile and Task.

**Why this priority**: This step answers the research question by determining if the observed differences are statistically significant rather than random noise, fulfilling the "Expected Results" criteria while respecting the statistical dependencies in the data.

**Independent Test**: The analysis pipeline can be tested by running a simulation with synthetic data where the "Separated" condition is known to have a lower hallucination rate, verifying that the LMM returns a significant fixed effect for "Prompt Condition" with correct random intercepts for Profile and Task.

**Acceptance Scenarios**:
1. **Given** the aggregated score matrix from all [deferred] combinations, **When** the LMM is executed, **Then** the system must output a p-value for the fixed effect of "Prompt Condition" on "Hallucination Rate".
2. **Given** a p-value < 0.05, **When** the system checks the effect size, **Then** it must confirm the direction of the effect aligns with the hypothesis (Separated < Monolithic).
3. **Given** multiple hypothesis tests (e.g., adherence, style, hallucination), **When** the analysis runs, **Then** it must apply a multiple-comparison correction (e.g., Bonferroni) to the reported p-values.

### Edge Cases

- What happens if the downloaded "expert profiles" from the public gallery are malformed or missing required capability/behavior keys? (System must skip the profile and log an error, proceeding with the remaining valid profiles).
- How does the system handle a task scenario where the "ground truth" context is ambiguous or incomplete? (The system must flag the specific profile-task pair as "excluded" from the Hallucination Rate calculation to prevent false positives).
- What if the CPU inference time for a single task exceeds 300 seconds? (The system must terminate the specific inference run, record a timeout failure, and log the specific profile/task causing the delay).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST load and run a small language model (≤8B parameters) on a CPU-only backend without requiring CUDA or GPU accelerators (See US-1).
- **FR-002**: The system MUST generate a global pool of diverse, multi-turn task scenarios using a rule-based Python script that enforces stratified sampling across multiple specific task domains (coding, math, logic, creative, factual) with tasks distributed proportionally per domain., ensuring no duplicate prompts. These tasks are reused across all 50 profiles. (See US-1).
- **FR-003**: The system MUST implement three distinct prompt conditions: Monolithic, Separated Tracks (capability vs. behavior decoupled), and Generic Baseline (See US-1).
- **FR-004**: The evaluation engine MUST calculate Heuristic Adherence by measuring task success on a held-out validation set derived from the capability track rules, rather than a binary match against the prompt's own rules (See US-2).
- **FR-005**: The evaluation engine MUST calculate Hallucination Rate by comparing generated text against external source traces using multi-hop reasoning checks and rule-based logic verification (e.g., regex extraction of entity-value pairs and entailment checks) to detect facts not explicitly present in the context, not LLM-based judges (See US-2).
- **FR-006**: The analysis module MUST perform a Linear Mixed-Effects Model (LMM) with random intercepts for Profile and Task to test for significant differences between the Monolithic and Separated Tracks conditions (See US-3).
- **FR-007**: The analysis module MUST apply a multiple-comparison correction (e.g., Bonferroni or Holm-Bonferroni) when reporting p-values for multiple metrics (See US-3).
- **FR-008**: The system MUST report a sensitivity analysis for the Style Consistency metric threshold by sweeping the threshold over a set of values (e.g., {0.01, 0.05, 0.1}) and reporting the variance in false-positive rates to ensure robustness (See US-2, US-3).

### Key Entities

- **Expert Profile**: A data structure containing the "capability track" (rules/heuristics) and "behavior track" (style definitions) for a specific domain expert.
- **Task Scenario**: A multi-turn interaction prompt generated by the rule-based script, containing the specific context and ground-truth facts, requiring multi-hop reasoning for valid completion.
- **Evaluation Metric**: A quantitative score (binary or continuous) derived from comparing a model output against the ground-truth rules or context.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The rate of hallucinated expertise is measured against the baseline Monolithic condition, with the hypothesis that the Separated Tracks condition yields a statistically significant reduction (p < 0.05) (See US-2, US-3).
- **SC-002**: Style consistency metrics for the Separated Tracks condition are measured against the Monolithic baseline, with a non-inferiority margin of a small, predefined absolute percentage point threshold. (See US-2, US-3).
- **SC-003**: The total compute time for the full set of inference and evaluation runs is measured against the free-tier runner limit (Linux, multi-core CPU, constrained RAM). (See US-1).
- **SC-004**: The memory footprint during inference is measured against the available RAM limit, ensuring no OOM crashes occur. (See US-1).
- **SC-005**: The sensitivity analysis for Style Consistency thresholds is measured by the variance in false-positive rates across a range of representative thresholds. (See US-2).

## Assumptions

- **Assumption about data source**: The public COLLEAGUE.SKILL gallery (or the simulated repository) contains multiple distinct expert profiles with well-defined capability rules and behavior tracks.; if the specific URL is unavailable, a simulated repository with identical structure is used.
- **Assumption about model capacity**: Small language models (e.g., Llama-3-8B-Q4, Phi-3-mini) are capable of maintaining sufficient context windows and logical coherence to be tested on this specific prompt engineering task, even without fine-tuning.
- **Assumption about evaluation validity**: Simple string matching is insufficient for detecting LLM hallucination; therefore, the system relies on multi-hop reasoning tasks and logic-based verification to distinguish between context retrieval and genuine expertise application.
- **Assumption about compute limits**: The total dataset (50 profiles × 200 tasks × 3 conditions = 30,000 combinations) will fit within the 14GB disk limit of the CI runner when intermediate logs and outputs are managed (e.g., deleted after aggregation).
- **Assumption about statistical power**: A sample size of [deferred] observations (50 profiles × 200 tasks × 3 conditions) is sufficient to detect a moderate effect size (Cohen's d ≈ 0.3) with p < 0.05 in a Linear Mixed-Effects Model.
- **Assumption about threshold justification**: The style consistency threshold is initially set to a community-standard value, justified by prior work in conversational coherence, and will be subjected to the required sensitivity analysis (FR-008) to ensure the results are not artifacts of a single arbitrary cutoff.