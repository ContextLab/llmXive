# Feature Specification: llmXive follow-up: extending "BlockPilot: Instance-Adaptive Policy Learning for Diffusion-based Spec"

**Feature Branch**: `001-llmxive-blockpilot-extension`  
**Created**: 2026-08-30  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'BlockPilot: Instance-Adaptive Policy Learning for Diffusion-based Spec'"

## User Scenarios & Testing

### User Story 1 - Ground Truth Generation via Exhaustive Sweep (Priority: P1)

The system must execute a complete inference sweep across multiple block sizes for every input sample to establish the "true" optimal block size ($B^*$) based on acceptance length maximization.

**Why this priority**: Without a verified ground truth ($B^*$) derived from exhaustive evaluation, no regression model can be trained or validated. This is the foundational data generation step required for the entire research question.

**Independent Test**: The system can be tested by running the sweep on a single sample from the GSM8K dataset and verifying that the output includes a mapped block size for every tested value ($B \in \{1, 2, 4, 8, 16, 32\}$) and a clear winner ($B^*$).

**Acceptance Scenarios**:

1. **Given** a prompt from the GSM8K dataset and a loaded diffusion model (e.g., Qwen3-4B), **When** the system executes the exhaustive block-size sweep, **Then** it outputs a JSON record containing the acceptance length for each block size in the set $\{1, 2, 4, 8, 16, 32\}$ and identifies the block size with the maximum acceptance length as $B^*$.
2. **Given** a prompt from the HumanEval dataset, **When** the sweep is executed, **Then** the system correctly identifies $B^*$ without crashing due to out-of-memory errors, confirming the sampling strategy fits within the 7 GB RAM constraint (See Assumption about compute constraints).

### User Story 2 - Static Feature Extraction (Priority: P2)

The system must extract specific static prefilling features (prompt length, mean attention entropy, hidden state norms) from the model's initial forward pass for every sample.

**Why this priority**: These features serve as the independent variables ($X$) for the regression analysis. If these cannot be extracted efficiently on CPU, the "zero-overhead" hypothesis cannot be tested.

**Independent Test**: The system can be tested by processing a single prompt and verifying that the output vector contains exactly three numeric values corresponding to the defined features, with no latency exceeding 10ms.

**Acceptance Scenarios**:

1. **Given** a valid text prompt, **When** the system performs the prefilling phase on a CPU-only runner, **Then** it records the raw prompt length, the mean attention entropy across all layers (calculated per the diffusion architecture definition), and the L2 norm of the final token hidden states.
2. **Given** a prompt with extreme length (e.g., >2048 tokens), **When** feature extraction occurs, **Then** the system completes the extraction within 500ms (as defined by the hardware constraints in Assumption about compute constraints) and produces valid numeric values (no NaNs or Infs).

### User Story 3 - Lightweight Policy Training and Validation (Priority: P3)

The system must train non-neural regression models (XGBoost, Random Forest, Decision Trees) on the collected (Feature, $B^*$) pairs and evaluate their alignment with the ground truth across different linguistic domains.

**Why this priority**: This directly addresses the research question: "Do static prefilling features serve as robust proxies?" It validates if the lightweight approach can replace neural policies.

**Independent Test**: The system can be tested by training a Random Forest on an 80/20 split of the GSM8K data and evaluating on the held-out test set, reporting the prediction accuracy against the exhaustive sweep results.

**Acceptance Scenarios**:

1. **Given** a dataset of (Feature, $B^*$) pairs from GSM8K, **When** a Random Forest regressor is trained on an 80/20 split, **Then** it predicts the optimal block size for held-out test samples with an accuracy significantly higher than a uniform random baseline.
2. **Given** a model trained on GSM8K (math), **When** it is evaluated on HumanEval (code) without retraining, **Then** the system reports the drop in accuracy (generalization gap) to quantify architecture/domain robustness.

### Edge Cases

- **What happens when** the exhaustive sweep yields a tie (multiple block sizes produce identical maximum acceptance lengths)?
  - *Handling*: The system must define a deterministic tie-breaking rule (e.g., select the smallest block size to maximize throughput) and apply it consistently across all samples.
- **How does the system handle** a prompt where the attention entropy calculation results in `NaN` due to division by zero or empty attention masks?
  - *Handling*: The system must detect invalid entropy values, log a warning, and either exclude the sample from training or impute with a median value from the current domain, ensuring the pipeline does not crash.
- **What happens when** the GitHub Actions runner hits the 6-hour time limit before completing the sweep for all datasets?
  - *Handling*: The system must implement a checkpoint/resume mechanism or a sample-size limit (e.g., max 500 samples per dataset) to ensure the job completes within the free-tier constraints.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST execute an exhaustive sweep of block sizes $B \in \{1, 2, 4, 8, 16, 32\}$ for every input sample to determine the ground-truth optimal block size $B^*$ (See US-1).
- **FR-002**: The system MUST extract static prefilling features (prompt length, mean attention entropy calculated per the diffusion architecture, hidden state norms) during the initial forward pass without triggering a full generation step (See US-2).
- **FR-003**: The system MUST train at least three non-neural regression models (XGBoost, Random Forest, Decision Trees) using the extracted features as inputs and $B^*$ as the target label (See US-3).
- **FR-004**: The system MUST evaluate the trained models on held-out data from divergent linguistic domains (code, math, natural language) to measure generalization (See US-3).
- **FR-005**: The system MUST measure the wall-clock latency of the feature extraction and prediction pipeline to ensure it remains ≤ 1ms per sample on a standard 2-core CPU runner (See US-2).
- **FR-006**: The system MUST calculate and record the correlation coefficient between the predicted optimal block size and an independent measure of model uncertainty (e.g., perplexity or output entropy) to validate the proxy hypothesis (See US-3).

### Key Entities

- **Sample**: A single text instance from a dataset (GSM8K, HumanEval, CommonCrawl) paired with the derived ground-truth optimal block size ($B^*$) calculated via exhaustive sweep.
- **FeatureVector**: A numeric vector containing the static prefilling features (length, entropy, norms) derived from a Sample.
- **PolicyModel**: A trained non-neural regression model mapping FeatureVectors to predicted block sizes.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The accuracy of the lightweight policy in predicting $B^*$ is measured against the ground truth derived from the exhaustive sweep (See FR-001, FR-003).
- **SC-002**: The prediction accuracy of the policy trained on one domain (e.g., Math) is measured against the performance on a held-out, divergent domain (e.g., Code) to assess robustness (See FR-004).
- **SC-003**: The inference latency of the feature extraction and prediction pipeline is measured against the 1ms threshold to verify CPU-tractability (See FR-005).
- **SC-004**: The feature importance scores of the trained models are measured against the hypothesis that attention entropy is the dominant predictor (See FR-003).
- **SC-005**: The correlation coefficient between static features and the optimal block size is measured to quantify the strength of the proxy relationship (See FR-001, FR-003).
- **SC-006**: The correlation coefficient between the predicted optimal block size and an independent measure of model uncertainty (e.g., perplexity) is measured to validate the proxy hypothesis (See FR-006).

## Assumptions

- **Assumption about data availability**: The HuggingFace datasets (GSM8K, HumanEval) and model weights (Qwen3-4B, Llama-3-8B) are accessible via the GitHub Actions free-tier network without requiring custom authentication or large download times that exceed the 6-hour job limit.
- **Assumption about compute constraints**: The exhaustive sweep for the selected sample size (e.g., 500 samples per dataset) will complete within the 6-hour GitHub Actions free-tier limit using only 2 CPU cores and ~7 GB RAM.
- **Assumption about variable fit**: The static features (attention entropy, prompt length) extracted from the prefilling phase are sufficient to capture the variance in model uncertainty required to predict $B^*$; no additional runtime dynamic features are needed.
- **Assumption about model behavior**: The diffusion verification step behaves deterministically enough that the "optimal block size" is a stable target for regression, not a stochastic variable requiring massive averaging. If stochasticity is observed, $B^*$ will be averaged over multiple random seeds.
- **Assumption about methodological framing**: Since this is an observational study of model behavior (no random assignment of block sizes in the wild), all findings regarding "correlation" and "prediction" will be framed as associational, not causal. The null hypothesis is that static features are *not* sufficient to capture model uncertainty.
- **Assumption about threshold justification**: The block size set $\{1, 2, 4, 8, 16, 32\}$ is sufficient to capture the optimal region; a sensitivity analysis sweeping these specific values will be performed to ensure the results are not artifacts of the chosen grid.