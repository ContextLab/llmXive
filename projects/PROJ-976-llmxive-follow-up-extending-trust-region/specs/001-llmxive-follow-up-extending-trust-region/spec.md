# Feature Specification: llmXive follow-up: extending "Trust-Region Behavior Blending for On-Policy Distillation"

**Feature Branch**: `001-llmxive-trb-diversity-profile`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Trust-Region Behavior Blending for On-Policy Distillation'"

## User Scenarios & Testing

### User Story 1 - Static Diversity Profile Computation (Priority: P1)

As a researcher, I want to compute a static "diversity profile" (lexical entropy, distinct-n ratios, syntactic variation) for a dataset of teacher outputs using only CPU-based string processing, so that I can generate the input features for the predictor model without requiring real-time teacher inference.

**Why this priority**: This is the foundational data engineering step. Without the feature vectors, no prediction model can be trained or tested. It addresses the core bottleneck of "expensive online teacher decoding" by shifting the workload to a one-time, CPU-tractable preprocessing step.

**Independent Test**: Can be fully tested by running the feature extraction script on a sample of teacher outputs and verifying that the output JSON contains valid numerical values for distinct-4, n-gram entropy, and parse tree depth variance, with zero GPU memory usage.

**Acceptance Scenarios**:

1. **Given** a JSONL file of 100 teacher responses, **When** the feature extraction script is executed on a CPU-only environment, **Then** a feature matrix is produced containing columns for `distinct_4_ratio`, `ngram_entropy`, and `syntactic_variation_score` with no missing values.
2. **Given** a dataset of [deferred] math problems, **When** the script processes the data in batches of 500, **Then** the total memory usage remains below 7 GB and the process completes within 30 minutes.

### User Story 2 - Cross-Dataset Predictor Training (Priority: P2)

As a researcher, I want to train a lightweight regression model (Random Forest or Ridge) on the "source" dataset (math problems) to predict the optimal KL budget ($\varepsilon_0$) and collapse probability, so that I can establish a baseline heuristic for hyperparameter selection.

**Why this priority**: This implements the core hypothesis that static diversity modes predict training dynamics. It validates the methodological approach before attempting the more difficult cross-dataset generalization.

**Independent Test**: Can be fully tested by training the model on the source set and evaluating it on a held-out split of the *same* source set, ensuring the model achieves a non-trivial correlation (e.g., MAE < 0.1 for $\varepsilon_0$) without overfitting.

**Acceptance Scenarios**:

1. **Given** the feature matrix and ground-truth $\varepsilon_0$ values from the source dataset, **When** the regression model is trained with a fixed random seed, **Then** the model's Mean Absolute Error (MAE) is calculated and recorded, where $\varepsilon_0$ is normalized to the range [0.0, 1.0].
2. **Given** the binary collapse labels from the source dataset, **When** the classification model is trained, **Then** the model's F1-score is calculated and recorded on the held-out source validation set.

### User Story 3 - Generalization Validation on Unseen Data (Priority: P3)

As a researcher, I want to apply the trained predictor (from the math dataset) to the "target" dataset (code generation prompts) without re-tuning hyperparameters, so that I can verify if the static diversity profile generalizes across domains.

**Why this priority**: This addresses the primary research gap: "can a static diversity profile... generalize to stabilize training on a distinct, unseen dataset." A successful result here eliminates the need for dataset-specific hyperparameter sweeps.

**Independent Test**: Can be fully tested by running the predictor on the target dataset and comparing the predicted $\varepsilon_0$ and collapse risk against the actual observed outcomes from the original TRB sweep logs for that dataset.

**Acceptance Scenarios**:

1. **Given** the model trained on the math dataset, **When** it is applied to the code generation dataset, **Then** the Pearson correlation coefficient between predicted and actual $\varepsilon_0$ values is calculated and recorded, where actual optimal values are taken from the sweep grid with a resolution sufficient to capture the relevant parameter space.
2. **Given** the model trained on the math dataset, **When** it predicts collapse risk for the code dataset, **Then** the False Positive Rate for predicting collapse is calculated and recorded, and the system must validate it against the design target of ≤ 0.2.

### Edge Cases

- What happens when a teacher response is empty or consists only of whitespace? (System must assign default values or exclude the row and log a warning).
- How does the system handle syntactic parsing failures for highly irregular or code-heavy text? (The parser must return a fallback score or `NaN` without crashing the pipeline).
- What if the ground-truth sweep logs for the target dataset are missing or incomplete? (The system must skip validation for those instances and report the coverage percentage).

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute three specific lexical metrics for each teacher output: distinct-4 ratio, average n-gram entropy, and syntactic variation score (defined as parse tree depth variance). (See US-1)
- **FR-002**: System MUST load the ground-truth optimal $\varepsilon_0$ and training collapse labels from the original TRB sweep logs for the source dataset to serve as training targets. (See US-2)
- **FR-003**: System MUST train a lightweight regression model (e.g., Random Forest or Ridge) on the source dataset to predict the continuous $\varepsilon_0$ value. (See US-2)
- **FR-004**: System MUST train a binary classification model on the source dataset to predict the probability of training collapse, defined as: (a) loss variance over a short-term window exceeds 5x the variance of the first 100 steps, OR (b) gradient norm divergence > 3x the baseline gradient norm. (See US-2)
- **FR-005**: System MUST apply the trained models to the target (unseen) dataset without any re-training or hyperparameter re-sweeping to evaluate generalization. (See US-3)
- **FR-006**: System MUST perform a permutation test to determine if the correlation between specific diversity modes and collapse onset is statistically significant compared to a null distribution. (See US-3)
- **FR-007**: System MUST validate the predictor's ability to forecast *independent* training stability (measured by final loss variance) rather than just replicating sweep labels. (See US-3)
- **FR-008**: System MUST validate that the 'parse tree depth variance' metric correlates with code diversity on a held-out code sample (correlation ≥ 0.3); if it fails, the system MUST fallback to a code-specific metric (e.g., token-level entropy). (See US-1)

### Key Entities

- **DiversityProfile**: Represents the static feature vector for a single teacher response, containing `distinct_4_ratio`, `ngram_entropy`, `syntactic_variation_score`.
- **TrainingInstance**: Represents a single data point linking a `DiversityProfile` to ground-truth outcomes (`optimal_epsilon_0`, `collapse_label`).
- **PredictorModel**: The trained regression/classification model capable of mapping a `DiversityProfile` to predicted outcomes.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The correlation between predicted and actual $\varepsilon_0$ on the target dataset is measured against the baseline of using a fixed default $\varepsilon_0$ (e.g., 0.5) for all instances. The primary validation metric is the *training outcome* (final loss, collapse occurrence) achieved by using the *predicted* $\varepsilon_0$ versus the outcome achieved by using a default $\varepsilon_0$. (See FR-005)
- **SC-002**: The False Positive Rate for collapse prediction on the target dataset is measured against a predefined threshold to ensure the heuristic does not over-conservatively discard stable training runs. (See FR-004)
- **SC-003**: The computational cost of the feature extraction pipeline is measured against the constraint of ≤ 7 GB RAM and ≤ 6 hours total runtime on a CPU-only GitHub Actions runner. (See FR-001)
- **SC-004**: The statistical significance of the diversity-collapse correlation is measured against a null distribution generated by a large number of permutations of the target labels. (See FR-006)
- **SC-005**: The generalization gap (performance drop from source to target) is measured to ensure it remains within an acceptable threshold relative to the source performance, where 'performance' is defined as the source MAE for regression and source F1-score for classification. (See FR-005)
- **SC-006**: The accuracy of the predictor in forecasting *independent* training stability (final loss variance) is measured against the observed stability in the target dataset's sweep logs. (See FR-007)

## Assumptions

- The original TRB paper's supplementary materials or associated repository contain the specific sweep logs required to extract the "optimal" $\varepsilon_0$ and collapse labels for both the math and code datasets.
- The "syntactic variation" metric can be approximated using standard CPU-based parsers (e.g., spaCy or Stanford CoreNLP) without requiring GPU acceleration for the parse trees, provided FR-008 validation passes.
- The math problems and code generation prompts fit entirely within the 7 GB RAM limit of the GitHub Actions runner when loaded as Pandas DataFrames.
- The "collapse" definition (loss variance > 5x baseline or gradient divergence) is consistent across both datasets and is explicitly recorded or derivable from the ground-truth logs.
- The lexical metrics (distinct-n, entropy) are sufficiently robust to handle the domain shift from mathematical text to code generation text.
- The lightweight regression model (Random Forest/Ridge) is computationally feasible to train and evaluate on the full dataset within the allocated job time limit.