# Feature Specification: llmXive follow-up: extending "Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero"

**Feature Branch**: `001-llmxive-counterfactual-consistency`  
**Created**: 2026-08-18  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero'"

## User Scenarios & Testing

### User Story 1 - Counterfactual Data Generation Pipeline (Priority: P1)

**Journey**: A researcher prepares a training dataset by taking standard videos from the Something-Something V2 dataset and automatically generating "counterfactual" versions where the primary object is swapped with a semantically distinct object (e.g., cup to bowl) while preserving the original motion trajectory and background.

**Why this priority**: This is the foundational data requirement. Without the synthetic counterfactual pairs, the consistency loss cannot be calculated, and the core hypothesis cannot be tested. It is the prerequisite for all model training.

**Independent Test**: The pipeline can be run on a small subset of 10 videos, producing paired output files (original + counterfactual) where visual inspection confirms the object swap occurred without altering the actor's motion or background.

**Acceptance Scenarios**:

1. **Given** a video clip from the Something-Something V2 training set with a clear primary object, **When** the generation script processes it, **Then** a new video file is created where the object region is replaced by a patch from a different object class, and the motion trajectory of the background/actor remains identical to the original.
2. **Given** a video where the primary object is partially occluded, **When** the script attempts the swap, **Then** the system handles the occlusion gracefully (e.g., by skipping the frame or using the visible portion) without crashing the pipeline.

---

### User Story 2 - Counterfactual Consistency Loss Training (Priority: P2)

**Journey**: A researcher trains a lightweight linear classifier on the generated dataset using a combined loss function ($L_{total} = L_{CE} + \lambda L_{cc}$) that penalizes prediction changes when the object is swapped but motion is preserved.

**Why this priority**: This implements the core scientific intervention (the "Counterfactual Consistency Loss"). It tests whether the model can be forced to rely on motion rather than object identity.

**Independent Test**: A model trained with $\lambda > 0$ shows a lower KL-divergence between predictions of original and counterfactual pairs on a validation set compared to a model trained with $\lambda = 0$ (baseline), while maintaining acceptable accuracy on the original labels.

**Acceptance Scenarios**:

1. **Given** a pair of original and counterfactual videos with the same action label, **When** the model processes both during training, **Then** the calculated consistency loss ($L_{cc}$) is non-zero if the prediction distributions differ, and the optimizer updates weights to reduce this divergence.
2. **Given** a training run with $\lambda = 0.5$, **When** the training completes, **Then** the model achieves a validation accuracy on the original labels within 5% of the baseline cross-entropy-only model, demonstrating that consistency regularization does not catastrophically degrade primary task performance.

---

### User Story 3 - Robustness Evaluation & Statistical Validation (Priority: P3)

**Journey**: A researcher evaluates the trained model against a baseline (RCORE) on a held-out "Counterfactual Robustness Test Set" to measure the accuracy drop ($\Delta Acc$) and performs a statistical test to confirm significance.

**Why this priority**: This delivers the final research result: quantifying the efficacy of the proposed method. It validates the hypothesis that the loss function improves robustness to object-driven shortcuts.

**Independent Test**: The evaluation script produces a report comparing the accuracy drop ($\Delta Acc$) of the proposed model vs. the baseline, including a p-value from a paired t-test indicating statistical significance ($p < 0.05$).

**Acceptance Scenarios**:

1. **Given** a trained model and a test set with object-swapped videos, **When** the evaluation script runs, **Then** it calculates the accuracy on original videos ($Acc_{orig}$) and swapped videos ($Acc_{swapped}$), and reports the drop $\Delta Acc = Acc_{orig} - Acc_{swapped}$.
2. **Given** results from 5 random seeds for both the proposed model and the baseline, **When** the statistical validation runs, **Then** a paired t-test confirms whether the reduction in $\Delta Acc$ for the proposed model is statistically significant ($p < 0.05$).

---

### Edge Cases

- What happens when the object detector fails to identify the primary object in a video? (The system must log the failure and skip the counterfactual generation for that specific video rather than crashing).
- How does the system handle videos where the "object" is actually the actor's hand (e.g., "Putting something into something")? (The swap logic must be robust enough to avoid replacing the actor, or the dataset subset must exclude ambiguous cases).
- What if the synthetic object patch creates visual artifacts that disrupt the motion features? (The system must include a quality check or use a seamless blending algorithm to ensure the motion features remain the dominant signal).

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate synthetic counterfactual videos by replacing the primary object region with a patch from a distinct object class while preserving the original motion trajectory and background features (See US-1).
- **FR-002**: System MUST implement a "Counterfactual Consistency Loss" function that calculates the KL-divergence between the prediction distributions of an original video and its counterfactual pair (See US-2).
- **FR-003**: System MUST train a linear classifier using a combined loss function $L_{total} = L_{CE} + \lambda L_{cc}$, where $\lambda$ is a tunable hyperparameter (See US-2).
- **FR-004**: System MUST evaluate model performance on a dedicated "Counterfactual Robustness Test Set" to measure the accuracy drop ($\Delta Acc$) between original and object-swapped inputs (See US-3).
- **FR-005**: System MUST perform a paired t-test across multiple random seeds to determine if the reduction in accuracy drop is statistically significant ($p < 0.05$) (See US-3).
- **FR-006**: System MUST operate entirely on CPU-only resources, utilizing pre-computed ResNet-18 features to ensure the analysis fits within the 7 GB RAM and 14 GB disk constraints of the free-tier runner (See US-2).
- **FR-007**: System MUST enforce that all hypothesis tests regarding model performance differences are framed as associational findings, avoiding causal claims unless randomization is explicitly part of the data generation (See US-3).

### Key Entities

- **Counterfactual Pair**: A tuple consisting of an original video and a generated variant where the object is swapped but motion is preserved.
- **Robustness Metric**: The scalar value $\Delta Acc = Acc_{orig} - Acc_{swapped}$ representing the model's performance degradation under object occlusion.
- **Consistency Loss**: The scalar penalty term derived from KL-divergence used to regularize the model's predictions.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reduction in accuracy drop ($\Delta Acc$) for the proposed model compared to the baseline is measured against the baseline's $\Delta Acc$ to determine efficacy (See US-3).
- **SC-002**: The statistical significance of the robustness improvement is measured against the $p < 0.05$ threshold using a paired t-test across multiple seeds (See US-3).
- **SC-003**: The computational feasibility is measured against the free-tier runner constraints (2 CPU cores, ~7 GB RAM, ≤6 hours) by verifying the total training and evaluation time (See US-2).
- **SC-004**: The sensitivity of the model's robustness to the hyperparameter $\lambda$ is measured against a sweep of values (e.g., $\lambda \in \{0.1, 0.5, 1.0\}$) to identify the optimal trade-off (See US-2).
- **SC-005**: The validity of the counterfactual generation is measured against a manual inspection of 50 generated pairs to confirm object swap success and motion preservation (See US-1).

## Assumptions

- The Something-Something V2 dataset contains sufficient bounding box annotations or the lightweight detector can reliably identify the primary object to facilitate the swap.
- Pre-computed ResNet-18 features for the entire dataset are available and fit within the 14 GB disk limit of the free-tier runner.
- The "object swap" transformation does not introduce artifacts severe enough to invalidate the motion features extracted by the frozen backbone.
- The dataset variable set includes the necessary labels for action recognition and object identification to support the counterfactual generation logic.
- The free-tier CI runner provides sufficient I/O bandwidth to load and process the video features within the 6-hour job limit.
- The study is observational in nature regarding the model's internal representations; findings will be framed as associations between the loss function and robustness, not causal claims about the "mechanism" of learning without further causal inference analysis.
- The sample size (number of videos) is sufficient to detect a meaningful effect size in the paired t-test, or the power limitation is explicitly acknowledged in the final report.
