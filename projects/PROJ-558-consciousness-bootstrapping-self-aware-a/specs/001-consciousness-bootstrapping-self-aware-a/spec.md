# Feature Specification: Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection

**Feature Branch**: `001-consciousness-bootstrapping-self-aware-ai`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection"

## User Scenarios & Testing

### User Story 1 - Construct and Train Self-Referential Model (Priority: P1)

As a researcher, I need to construct a TinyLlama-based model with an added temporal recursive self-attention module and train it on a specific subset of the Pile dataset so that I can generate a baseline for meta-cognitive behavior comparison.

**Why this priority**: This is the foundational step. Without a successfully trained model containing the specific architectural modification (temporal recursive self-attention) and a corresponding standard baseline, no evaluation or statistical analysis can occur. This directly addresses the core "Methodology sketch" requirement.

**Independent Test**: The training pipeline can be executed end-to-end on a GitHub Actions runner (CPU, moderate RAM) and produce two checkpoint files (recursive and baseline) within the compute budget, with no CUDA/GPU errors.

**Acceptance Scenarios**:

1. **Given** the GitHub Actions runner environment, **When** the training script is executed with the specified hyperparameters (batch size, epochs, learning rate), **Then** the job completes successfully within 120 minutes and outputs two model artifacts (one with recursive module, one standard) without OOM errors.
2. **Given** the model architecture definition, **When** the recursive self-attention module is instantiated, **Then** the module successfully attends to the confidence distribution of the previous generation step for the defined max recursion depth without shape mismatches.
3. **Given** the training objective, **When** the model processes a batch of data, **Then** the joint loss (cross-entropy + confidence-prediction loss based on self-consistency proxy) is computed and backpropagated without numerical instability (NaN/Inf values).

---

### User Story 2 - Evaluate Meta-Cognitive Metrics (Priority: P2)

As a researcher, I need to run the trained models (recursive and shuffled-attention control) against MMLU, GSM8K, and Self-Consistency benchmarks to measure self-consistency, error detection, and uncertainty calibration so that I can quantify the impact of the recursive architecture.

**Why this priority**: This step generates the raw data required to answer the research question. It is dependent on the trained models (US-01) but independent of the statistical aggregation.

**Independent Test**: The evaluation script can ingest the model checkpoints, generate predictions on the test sets, and output a JSON file containing the raw metrics (consistency scores, confidence values, correctness flags) for all test items.

**Acceptance Scenarios**:

1. **Given** a trained model checkpoint and a benchmark dataset (e.g., GSM8K), **When** the evaluation script runs the "generate 10 reasoning paths" logic, **Then** it produces multiple distinct output sequences per question and calculates the majority-vote self-consistency score.
2. **Given** the model's output confidence scores and ground truth labels, **When** the error detection metric is calculated, **Then** the system computes the ROC-AUC value correctly based on the binary classification of correctness.
3. **Given** the set of predicted probabilities and ground truths, **When** the uncertainty calibration is calculated, **Then** the system outputs both the Brier score and the Expected Calibration Error (ECE) for the model.
4. **Given** the 'shuffled-attention' baseline, **When** the same metrics are calculated, **Then** the system produces a control dataset to isolate the effect of temporal recursion from stochastic sampling.

---

### User Story 3 - Perform Statistical Analysis and Sensitivity Testing (Priority: P3)

As a researcher, I need to perform paired t-tests across multiple random seeds and conduct a sensitivity analysis on the confidence thresholds to determine if the recursive architecture yields statistically significant improvements over the control.

**Why this priority**: This step transforms raw metrics into scientific conclusions. It validates the "Expected results" section and addresses the methodological soundness requirements regarding inference framing and threshold justification.

**Independent Test**: The analysis script can process the evaluation outputs from multiple seeds, perform the statistical tests, and generate a report containing p-values, effect sizes, and sensitivity analysis plots.

**Acceptance Scenarios**:

1. **Given** evaluation results from 5 distinct random seeds for both models, **When** the paired t-test is executed, **Then** the system outputs a p-value and Cohen's d effect size for each metric (consistency, calibration, error detection).
2. **Given** a specific confidence threshold (e.g., 0.5), **When** the sensitivity analysis is triggered, **Then** The system sweeps the threshold across a range of values and reports the variation in false-positive and false-negative rates.
3. **Given** the results of multiple hypothesis tests (one per metric), **When** the multiplicity correction is applied, **Then** the system reports the adjusted p-values (e.g., Bonferroni or Benjamini-Hochberg) to control the family-wise error rate.

---

### Edge Cases

- **What happens when** the recursion depth causes the model to exceed the 7 GB RAM limit during the forward pass?
  - The system MUST fail the run, log the OOM error, and exit with a non-zero code. It MUST NOT automatically reduce the recursion depth, as this would violate FR-001.
- **How does the system handle** a scenario where the majority vote in self-consistency results in a tie (e.g., 5 correct vs. 5 incorrect)?
  - The system MUST define a deterministic tie-breaking rule (e.g., prefer the first generated path) and document this in the analysis report.
- **What happens when** the confidence-prediction loss fails to converge for the baseline model?
  - The system MUST flag the seed as invalid for statistical comparison and exclude it from the final t-test, ensuring the sample size reflects only valid runs.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a recursive self-attention module that attends to the confidence distribution of the previous generation step (temporal recursion) for a maximum recursion depth of 2 (See US-01).
- **FR-002**: System MUST train both the recursive model and a standard baseline model on the first [deferred] tokens of the 'arXiv' subset of the Pile dataset using a joint loss function (cross-entropy + confidence-prediction based on self-consistency proxy) (See US-01).
- **FR-003**: System MUST generate exactly 10 reasoning paths per question for the Self-Consistency benchmark evaluation using temperature=0.7, top_p=0.9, and a fixed seed per run (See US-02).
- **FR-004**: System MUST compute the Brier score and Expected Calibration Error (ECE) for all test items to assess uncertainty calibration (See US-02).
- **FR-005**: System MUST perform paired t-tests across 5 random seeds to compare the recursive model against the baseline, reporting p-values and effect sizes (See US-03).
- **FR-006**: System MUST execute a sensitivity analysis on the error detection confidence threshold by sweeping values across {0.4, 0.5, 0.6} and reporting the resulting variation in error rates (See US-03).
- **FR-007**: System MUST apply a multiple-comparison correction (e.g., Bonferroni) to the p-values of the three primary metrics to control family-wise error rate (See US-03).

### Key Entities

- **ModelCheckpoint**: Represents the saved state of a trained model, containing weights for the base transformer and the recursive module (if applicable).
- **EvaluationResult**: A structured record containing the input question, generated paths, majority vote, confidence scores, ground truth, and derived metrics (consistency, ROC-AUC, Brier score).
- **StatisticalReport**: A summary document containing p-values, effect sizes, confidence intervals, and sensitivity analysis outcomes derived from the EvaluationResults.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The system MUST calculate the percentage difference in self-consistency scores between the recursive and baseline models (See US-03).
- **SC-002**: The Brier score and Expected Calibration Error (ECE) are measured against the baseline to assess if uncertainty calibration is statistically significantly lower (See US-02).
- **SC-003**: The ROC-AUC for error detection is measured against the baseline to determine if the model can distinguish correct from incorrect answers more effectively (See US-02).
- **SC-004**: The statistical significance of the differences in metrics is measured against an alpha level of 0.05, with adjustments for multiple comparisons (See US-03).
- **SC-005**: The sensitivity analysis results are measured to ensure that the headline error rates (false-positive/false-negative) are reported for at least three distinct threshold values (See US-03).

## Assumptions

- The HuggingFace datasets (MMLU, GSMK, Self-Consistency) are accessible via public API without authentication tokens that expire during the 6-hour CI window.
- The TinyLlama model (or a smaller variant) fits within the memory constraints of the GitHub Actions free-tier runner when using standard floating point precision and batch sizes adjusted for gradient accumulation.
- The "confidence-prediction loss" is optimized using a proxy correctness signal derived from self-consistency (majority vote) on the training split, not ground-truth labels, to avoid tautological validation.
- The recursive self-attention mechanism does not introduce a computational complexity that exceeds the -hour training budget on a 2-CPU runner.
- The philosophical distinctions raised by reviewers (e.g., "knowing the good" vs. "knowing the shape of the shadow") are operationalized strictly as the measurable metrics defined in the methodology (self-consistency, calibration, error detection), as the project scope is limited to architectural influence on these specific behaviors.
- The hypothesis that the recursive model will show a ≥5% improvement in self-consistency over the baseline is a research prediction, not a system requirement; the system's success is defined by its ability to measure this difference accurately.