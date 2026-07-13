# Feature Specification: llmXive follow-up: extending "DelTA: Discriminative Token Credit Assignment for Reinforcement Learning"

**Feature Branch**: `001-delta-static-approximation`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'DelTA: Discriminative Token Credit Assignment for Reinforcement Learning'"

## User Scenarios & Testing

### User Story 1 - Generate Ground-Truth DelTA Coefficients (Priority: P1)

As a researcher, I need to run the DelTA algorithm on a subset of the GSM8K dataset using a small LLM (e.g., Llama-3-8B) to generate ground-truth DelTA Coefficients for each token position, so that I have a reliable target variable for training the static approximation model.

**Why this priority**: Without the ground-truth "oracle" DelTA Coefficients derived from dynamic gradient backpropagation, the core hypothesis (that static features can predict these coefficients) cannot be tested. This is the foundational data generation step.

**Independent Test**: This can be fully tested by executing the DelTA inference pipeline on a fixed subset of 500 GSM8K examples (selected with seed=42) and verifying that the output file contains a valid DelTA Coefficient for every token in every prompt, with no missing values or NaNs.

**Acceptance Scenarios**:

1. **Given** the GSM8K dataset is filtered for verified correct solutions, **When** the DelTA algorithm runs on a subset of at least 500 examples (seed=42, stratified by solution length) using Llama-3-8B, **Then** the system outputs a JSON file where every token in every prompt has an associated DelTA Coefficient.
2. **Given** the DelTA oracle step completes, **When** the output is inspected, **Then** the distribution of DelTA Coefficients shows variance (variance > 1e-9) and contains no infinite values.

---

### User Story 2 - Train Static Predictor Model (Priority: P2)

As a researcher, I need to train a lightweight regression model (2-layer MLP with ReLU activation) on CPU using only external static input features (n-grams, POS tags, semantic similarity to GSM8K patterns) to predict the DelTA Coefficients, so that I can evaluate if the discriminative signal is encoded in the input semantics without circularity.

**Why this priority**: This is the core experimental step that tests the hypothesis. It must be executable on CPU-only hardware to meet the project's compute feasibility constraints and must avoid using the oracle model's internal hidden states to ensure independent validation.

**Independent Test**: This can be fully tested by training the model on the static features extracted from the training split and verifying that the model converges (loss decreases) and produces predictions for the test split within the designated CI time limit.

**Acceptance Scenarios**:

1. **Given** static features are extracted from the prompt (n-grams, POS, semantic similarity) without using the oracle model's hidden states, **When** the 2-layer MLP is trained on the training split, **Then** the model training completes successfully on a CPU-only runner without requiring GPU acceleration or CUDA libraries.
2. **Given** the trained model exists, **When** it is applied to the held-out test set, **Then** it generates a predicted DelTA Coefficient for every token in the test prompts.

---

### User Story 3 - Evaluate Rank Correlation and Significance (Priority: P3)

As a researcher, I need to compute the Spearman rank correlation between the predicted DelTA Coefficients and the true DelTA Coefficients, and perform a permutation test for statistical significance, so that I can determine if the static approximation is effective or if the signal is emergent.

**Why this priority**: This provides the final answer to the research question. It validates the model's performance against the baseline and ensures the results are not due to chance.

**Independent Test**: This can be fully tested by running the evaluation script on the test set predictions and verifying that the output includes a Spearman correlation coefficient, a p-value from the permutation test, and feature importance scores.

**Acceptance Scenarios**:

1. **Given** the predicted and true DelTA Coefficients for the test set, **When** the evaluation script runs, **Then** it outputs a Spearman rank correlation score and compares it against a random baseline (N(0,1), seed=42).
2. **Given** the correlation score, **When** the permutation test is executed (shuffling targets 1000 times), **Then** the system reports a p-value indicating whether the observed correlation is statistically significant (p < 0.05).
3. **Given** a null result (correlation near zero), **When** the feature importance is analyzed, **Then** the system reports whether the null result is due to 'signal is emergent' (features are strong but correlation low) or 'features are poor proxies' (features are weak).

---

### Edge Cases

- What happens if the DelTA oracle step fails to converge for a specific example (e.g., due to numerical instability in gradient computation)? The system must log the error and exclude that example from the dataset rather than crashing the pipeline.
- How does the system handle tokens where the static feature extraction fails (e.g., out-of-vocabulary tokens in the frozen model)? These tokens must be filtered out or assigned a default feature vector to prevent training errors.
- What happens if the Spearman correlation is near zero? The system must correctly classify this as a null result (supporting the hypothesis that the signal is emergent) rather than treating it as a failure of the implementation.
- **Feature Insufficiency**: If the correlation is near zero, the system MUST distinguish between 'signal is emergent' (the static features are sufficient proxies but the signal is truly external) and 'features are poor proxies' (the chosen static features lack the necessary information). This is determined by checking if the feature importance scores are uniformly low across all feature types.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the GSM8K dataset from HuggingFace and filter for solution traces with verified correctness labels to create a clean benchmark set (See US-1).
- **FR-002**: System MUST run the DelTA algorithm on a subset of at least 500 examples (selected with random seed=42, stratified by solution length) using a small open-source LLM (e.g., Llama-3-8B) to compute ground-truth DelTA Coefficients for every token position. If fewer than 500 valid examples are found after filtering, the pipeline MUST fail with an explicit error (See US-1).
- **FR-003**: System MUST extract external static input features for every token, including local n-gram statistics, part-of-speech tags, and semantic similarity scores to known reasoning patterns (defined as the first 50 GSM8K solution traces, using cosine similarity on the Llama-3-8B last-layer embedding space of those traces). System MUST NOT use contextual embeddings from the oracle model (Llama-3-8B) used to generate the DelTA Coefficients to prevent circularity (See US-2).
- **FR-004**: System MUST train a 2-layer MLP with ReLU activation and 256 hidden units using only the extracted static features on a CPU-only environment to predict the DelTA Coefficients (See US-2).
- **FR-005**: System MUST evaluate the model on a held-out test set by computing the Spearman rank correlation between predicted scores and true DelTA Coefficients, comparing against a random baseline (uniform weights from N(0,1), seed=42) and a uniform-weight baseline (See US-3).
- **FR-006**: System MUST perform a permutation test (shuffling target coefficients 1000 times) to establish statistical significance and ensure the correlation is not due to chance (See US-3).
- **FR-007**: System MUST frame all findings as associational (correlational) rather than causal, as the design is observational without random assignment of inputs to outcomes (See US-3).
- **FR-008**: System MUST report feature importance scores (e.g., SHAP values or permutation importance) for the trained model to distinguish between 'signal is emergent' and 'features are poor proxies' in the event of a null correlation (See US-3).

### Key Entities

- **DelTA Coefficient**: A continuous scalar value representing the discriminative weight of a specific token position derived from dynamic gradient backpropagation (Oracle).
- **Static Feature Vector**: A fixed-length vector representing the input context of a token, composed of n-gram statistics, POS tags, and semantic similarity scores to GSM8K solution traces. Explicitly excludes the oracle model's hidden states.
- **Prediction Model**: A lightweight regression model (2-layer MLP) trained to map Static Feature Vectors to DelTA Coefficients.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Spearman rank correlation between predicted and true DelTA Coefficients is measured against the random baseline (N(0,1), seed=42) and uniform baseline to determine signal strength. If the correlation is near zero, the result must be classified as 'signal is emergent' or 'features are poor proxies' based on FR-008 (See FR-005, US-3).
- **SC-002**: The statistical significance of the correlation is measured against the null distribution generated by the permutation test (p-value < 0.05) to rule out chance (See FR-006, US-3).
- **SC-003**: The total execution time of the end-to-end pipeline (data download, oracle generation, feature extraction, training, evaluation) is measured against the 6-hour GitHub Actions free-tier limit to ensure compute feasibility (See FR-004, US-2).
- **SC-004**: The memory footprint of the training process is measured against the ~7 GB RAM limit of the free-tier runner to ensure no out-of-memory errors occur (See FR-004, US-2).
- **SC-005**: The variance of the DelTA Coefficients in the ground-truth set is measured against a threshold of > 1e-9 to ensure the target variable is non-trivial and suitable for regression (See FR-002, US-1).

## Assumptions

- The GSM8K dataset contains sufficient solution traces with verified correctness labels to create a clean benchmark set of at least 500 examples without needing complex filtering logic.
- The Llama-8B model (or similar small open-source LLM) can be loaded and run for inference on a CPU-only GitHub Actions runner within the 6-hour time limit for the DelTA oracle step.
- The "external static features" (n-grams, POS tags, semantic similarity to a representative set of GSM8K traces) are computationally tractable to extract for every token in the subset without exceeding the 14 GB disk or 7 GB RAM limits.
- The DelTA algorithm, when run on a small model subset, produces stable DelTA Coefficients without requiring GPU acceleration or 8-bit/4-bit quantization libraries that mandate CUDA.
- The relationship between external static features and DelTA Coefficients is learnable enough to be captured by a shallow MLP without requiring deep neural network architectures.
- The observed correlation (if any) is purely associational; the study design does not support causal claims about input semantics *causing* the discriminative signal, only that they are predictive of it.
- The HuggingFace API and dataset mirrors are accessible from the GitHub Actions runner without rate-limiting issues that would halt the pipeline.
- A representative subset of GSM8K solution traces will serve as a seed set for 'known reasoning patterns' for semantic similarity calculations.