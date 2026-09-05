# Feature Specification: llmXive Follow-up: Extending MobileForge with CPU-Tractable Logic Distillation

**Feature Branch**: `002-mobileforge-logic-distillation`  
**Created**: 2026-07-19  
**Status**: Draft  
**Input**: User description: "To what extent does the 'hint-contextualized' feedback signal in Hierarchical Feedback-Guided Policy Optimization (HiFPO) capture transferable logical reasoning patterns that can be distilled into a lightweight, CPU-tractable model for GUI action planning, independent of the visual policy's representation learning?"

## User Scenarios & Testing

### User Story 1 - Data Extraction and Dataset Construction (Priority: P1)

The research pipeline MUST successfully parse the MobileForge training logs to extract `(UI_state_description, Corrective_Hint, Optimal_Action_Sequence)` triples, specifically filtering for cases where the model failed initially but succeeded after receiving a corrective hint, to create a clean dataset for training. The system MUST verify that the `Corrective_Hint` is purely linguistic (no coordinate-based visual grounding) before inclusion.

**Why this priority**: This is the foundational step; without a valid, filtered dataset derived from the specific "failure-then-success" pattern, no subsequent training or evaluation can occur. It validates the availability of the necessary signal.

**Independent Test**: Can be fully tested by running the extraction script against the provided MobileForge logs and verifying the output dataset contains ≥ 5,000 valid triples with no null values in the `UI_state_description`, `Corrective_Hint`, or `Optimal_Action_Sequence` fields.

**Acceptance Scenarios**:

1. **Given** the raw MobileForge training logs containing corrective hints, **When** the extraction script runs, **Then** it outputs a CSV/JSON dataset containing only triples where the initial trajectory failed and the post-hint trajectory succeeded, and the hint contains no coordinate-based visual references.
2. **Given** a dataset of extracted triples, **When** a validation check runs, **Then** ≥ 99% of rows contain a non-empty `UI_state_description`, a non-empty `Corrective_Hint`, and a valid `Optimal_Action_Sequence`.

---

### User Story 2 - CPU-Tractable Model Training (Priority: P2)

The system MUST train a lightweight, encoder-only language model (e.g., DistilBERT-small, ≤ 100M parameters) using the extracted dataset to predict optimal action sequences from UI states and hints, executing entirely on CPU without GPU acceleration.

**Why this priority**: This implements the core hypothesis test: whether the "hint" signal alone is sufficient to learn the planning logic. It must be feasible on free-tier CI resources.

**Independent Test**: Can be fully tested by initiating a training job on a CPU-only runner and verifying the job completes within 6 hours with a loss curve that converges (final loss ≤ 0.5), without triggering OOM (Out of Memory) errors or CUDA device errors.

**Acceptance Scenarios**:

1. **Given** the extracted dataset and a lightweight model configuration (≤ 100M parameters), **When** the training job starts on a CPU-only runner, **Then** the job completes within 6 hours without any GPU/CUDA-related errors.
2. **Given** the training process, **When** the loss is monitored, **Then** the training loss decreases by ≥ 50% from the epoch 0 value and reaches a final loss value ≤ 0.5 to indicate successful convergence.

---

### User Story 3 - Evaluation and Statistical Validation (Priority: P3)

The system MUST evaluate the trained model on a representative set of unseen AndroidWorld tasks via a headless Android emulator, measuring "Success Rate" and "Step Efficiency" against a non-distilled base LLM (TinyLlama) baseline, and performing a paired t-test to determine statistical significance. The evaluation set MUST be logically disjoint from the training set to ensure generalizability.

**Why this priority**: This provides the final empirical evidence to answer the research question, determining if the distilled model outperforms a meaningful baseline and validating the "hint" signal's transferability.

**Independent Test**: Can be fully tested by running the evaluation script on the trained model and verifying the output includes a success rate, step efficiency, and a p-value from a t-test comparing the model to the non-distilled base LLM baseline, with a statistical power ≥ 0.8.

**Acceptance Scenarios**:

1. **Given** the trained model and 500 unseen, logically disjoint AndroidWorld tasks, **When** the evaluation runs, **Then** the model achieves a success rate significantly higher than the non-distilled base LLM baseline (expected baseline performance: -15%).
2. **Given** the success rates of the distilled model and the non-distilled base LLM baseline, **When** the statistical analysis runs, **Then** a paired t-test confirms a p-value < 0.05 and a statistical power ≥ 0.8, indicating the improvement is statistically significant and not due to chance.

---

### User Story 4 - Sensitivity Analysis (Priority: P3)

The system MUST perform a sensitivity analysis to verify the robustness of the results against the "inconsistency tolerance" threshold used for action matching.

**Why this priority**: This ensures that the conclusions drawn from the evaluation are not an artifact of a specific threshold choice, validating the robustness of the distilled logic.

**Independent Test**: Can be fully tested by running the evaluation script with different inconsistency tolerance thresholds and verifying the success rate variance remains within acceptable bounds.

**Acceptance Scenarios**:

1. **Given** the trained model and the evaluation dataset, **When** the sensitivity analysis runs, **Then** the system sweeps the "inconsistency tolerance" threshold across {0.01, 0.05, 0.1} and reports the variance in success rates.
2. **Given** the variance report, **When** the analysis concludes, **Then** the success rate variance across the swept thresholds is ≤ 5%, indicating robustness.

---

### Edge Cases

- **What happens when** the MobileForge logs contain hints that are ambiguous or do not lead to a successful completion?
  - *System handles this by* strictly filtering the dataset to exclude any `(UI_state, Corrective_Hint)` pair that does not result in a verified `Optimal_Action_Sequence` in the logs.
- **How does system handle** the scenario where the lightweight model fails to converge or produces garbage output?
  - *System handles this by* recording a null result for the success rate and flagging the run for ablation study analysis to distinguish between model failure and dataset insufficiency.
- **What happens when** the headless emulator encounters a task environment that crashes?
  - *System handles this by* retrying the specific task up to 3 times; if it fails 3 times, the task is marked as "Environment Error" and excluded from the final success rate calculation to avoid skewing the logic performance metric.

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse MobileForge logs to extract `(UI_state, Corrective_Hint, Action)` triples, filtering strictly for "failed-then-success" trajectories and verifying that the `Corrective_Hint` is purely linguistic (no coordinate-based visual grounding). The system MUST define "inconsistency tolerance" as the threshold for matching predicted vs. optimal action sequences (See US-1).
- **FR-002**: System MUST initialize and train a lightweight encoder-only language model (≤ 100M parameters) on CPU, ensuring no GPU/CUDA dependencies are invoked (See US-2).
- **FR-003**: System MUST execute the trained model against 500 unseen, logically disjoint AndroidWorld tasks using a headless Android emulator simulation (See US-3).
- **FR-004**: System MUST calculate "Success Rate" (percentage of completed tasks) and "Step Efficiency" (ratio of steps taken vs. optimal) for the distilled model (See US-3).
- **FR-005**: System MUST perform a paired t-test comparing the distilled model's performance against a non-distilled base LLM (TinyLlama) baseline to determine statistical significance (See US-3).
- **FR-006**: System MUST implement a sensitivity analysis that sweeps the "inconsistency tolerance" threshold for action matching across {0.01, 0.05, 0.1} to verify result robustness (See US-4).
- **FR-007**: System MUST conduct a post-hoc power analysis to confirm that the sample size (N=500) provides sufficient statistical power (≥ 0.8) for the observed effect size (See US-3).

### Key Entities

- **ExtractionDataset**: The intermediate dataset containing `(UI_state_description, Corrective_Hint, Optimal_Action_Sequence)` triples derived from MobileForge logs.
- **DistilledModel**: The lightweight, CPU-optimized language model trained to map UI states and hints to action sequences.
- **EvaluationResult**: The output metrics including success rate, step efficiency, and statistical p-values for a specific task set.

## Success Criteria

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The "Success Rate" of the distilled model is measured against the non-distilled base LLM (TinyLlama) baseline (See US-3).
- **SC-002**: The "Step Efficiency" of the distilled model is measured against the optimal path length derived from the MobileForge ground truth logs (See US-3).
- **SC-003**: The statistical significance of the model's performance is measured against a p-value threshold of < 0.05 in a paired t-test against the non-distilled base LLM baseline (See US-3).
- **SC-004**: The "CPU Feasibility" is measured against the constraint that the entire training and evaluation pipeline completes within 6 hours on an `ubuntu-22.04` runner (See US-2).
- **SC-005**: The "Robustness of Threshold" is measured by the variance in success rates across the sensitivity sweep of inconsistency tolerance {0.01, 0.05, 0.1} (See US-4).
- **SC-006**: The "Statistical Power" is measured against the requirement of ≥ 0.8 for the paired t-test (See FR-007).

## Assumptions

- **Assumption about data source**: The MobileForge training logs provided in the project repository contain at least 5,000 valid "failed-then-success" trajectories with complete `Corrective_Hint` and `Action` fields.
- **Assumption about compute environment**: The GitHub Actions `ubuntu-22.04` runner provides sufficient CPU cycles and RAM to train a ≤ 100M parameter model on a sampled dataset without OOM errors.
- **Assumption about simulation**: The headless Android emulator (via ADB scripts) can be reliably launched and controlled within the CI environment without requiring root access or GPU passthrough.
- **Assumption about inference**: The "hint" signal in MobileForge is primarily linguistic/logical and does not rely on pixel-level visual features that cannot be represented in the `UI_state_description` text.
- **Assumption about statistical power**: The sample size of unseen tasks is sufficient to detect a moderate effect size (Cohen's d ≈ 0.5) with ≥ 0.8 power, as validated by FR-007.