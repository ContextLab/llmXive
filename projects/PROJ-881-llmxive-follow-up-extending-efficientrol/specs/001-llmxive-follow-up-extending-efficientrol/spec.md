# Feature Specification: llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts

**Feature Branch**: `001-entropy-validity-prediction`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'EfficientRollout: System-Aware Self-Speculative Decoding for RL Rollout'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline Generation and Ground Truth Labeling (Priority: P1)

As a researcher, I need to generate ground-truth token sequences for GSM8K and MiniGrid tasks using a CPU-tractable base model and label them with validity flags, so that I have a verified dataset to correlate with internal entropy signals.

**Why this priority**: This is the foundational data acquisition step. Without valid ground-truth sequences and corresponding validity labels, no correlation analysis can be performed. It is the minimum viable dataset for the study.

**Independent Test**: Can be fully tested by running the baseline generation script on a subset of 50 GSM8K problems and verifying that the output log contains a complete sequence of tokens and a binary validity flag for each token position against the known solution.

**Acceptance Scenarios**:

1. **Given** a subset of 50 GSM8K prompts and a 1.5B parameter model loaded on CPU, **When** the baseline generation script is executed, **Then** the output file contains a JSONL record for each prompt with the full generated sequence and a "valid" flag set to true for all tokens matching the ground truth solution.
2. **Given** a subset of 50 MiniGrid navigation prompts, **When** the baseline generation is executed with a temperature of 0.0, **Then** the system generates sequences where the exact count of tokens matching the ground truth path is recorded, and the validity labeling step flags each token individually as "valid" or "invalid" based on whether it matches the ground truth path.

---

### User Story 2 - Intermediate State Extraction and Entropy Calculation (Priority: P2)

As a researcher, I need to re-run the baseline sequences with instrumentation to capture the probability distribution and calculate Shannon entropy at every intermediate transformer layer for each token, so that I can create the predictor variable for my analysis.

**Why this priority**: This creates the independent variable (entropy) required to test the hypothesis. It directly enables the core research question of whether entropy predicts validity.

**Independent Test**: Can be fully tested by re-running a representative subset of sequences from User Story 1 with the instrumentation hook enabled and verifying that the output log contains entropy values for every layer (e.g., Layer 1 to Layer N) and every token position, with no missing values.

**Acceptance Scenarios**:

1. **Given** the dataset generated in User Story 1, **When** the instrumentation script processes a token at an intermediate layer (e.g., Layer 5), **Then** the output record includes a numeric entropy value calculated as $-\sum p_i \log p_i$ from the layer's probability distribution.
2. **Given** a sequence of length 20, **When** the extraction script runs, **Then** the output file contains exactly 20 entropy vectors (one per token), where each vector contains entropy values for all intermediate layers of the model.

---

### User Story 3 - Signal Decay Analysis and Threshold Optimization (Priority: P3)

As a researcher, I need to fit logistic regression models to predict token validity from entropy values and identify an optimal entropy threshold that maximizes the ratio of skipped computation to accuracy loss, so that I can quantify the predictive signal and propose a hardware-agnostic heuristic.

**Why this priority**: This delivers the primary scientific finding (the correlation and the threshold). It transforms raw data into the actionable insight requested by the research question.

**Independent Test**: Can be fully tested by running the analysis script on the combined dataset from GSM8K and MiniGrid, verifying that a logistic regression model is fitted, an AUC-ROC score is calculated, and the system reports the p-value and handles non-significant results (p >= 0.05) without error.

**Acceptance Scenarios**:

1. **Given** the paired dataset of (entropy, validity) from User Stories 1 and 2, **When** the analysis script runs, **Then** it calculates and reports the p-value for the logistic regression coefficient for entropy, allowing for the possibility of non-significance (p >= 0.05) and treating the failure to reject the null hypothesis as a valid empirical outcome.
2. **Given** the fitted model, **When** the threshold optimization routine runs, **Then** it identifies a specific entropy value where the trade-off between skipping layers and maintaining validity is maximized (defined as minimizing the weighted sum (weight=1) of false positives and false negatives), and outputs this value as the recommended threshold.

---

### Edge Cases

- **What happens when** the model generates a token with near-zero probability (entropy $\approx$ 0) but it is actually invalid? The system must handle this as a "high confidence error" case, ensuring the logistic regression does not crash due to log(0) or division by zero during sensitivity analysis.
- **How does system handle** sequences that exceed the 14 GB disk limit during intermediate state extraction? The system must implement a streaming or chunking mechanism to process sequences in batches of 500 tokens, writing intermediate results to disk immediately and clearing RAM.
- **What happens when** the ground truth solution is ambiguous or has multiple valid paths (common in MiniGrid)? The system must label a token as "valid" if it matches *any* of the known valid ground-truth paths, not just a single hard-coded solution string.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and cache the GSM8K and MiniGrid datasets from HuggingFace Datasets, limiting the subset to a maximum of 500 examples per task to ensure the total dataset size fits within 7 GB RAM. (See US-1)
- **FR-002**: System MUST perform a full autoregressive forward pass using a selected small-scale model (e.g., Llama-2-7B quantized or a 1.5B variant) on CPU to generate ground-truth sequences, recording the exact token IDs and their validity against the solution. (See US-1)
- **FR-003**: System MUST capture the output probability distribution at every intermediate transformer layer for every generated token and calculate the Shannon entropy value for each distribution. (See US-2)
- **FR-004**: System MUST fit a logistic regression model to predict token validity (binary) from the intermediate-layer entropy values, stratified by task type (GSM8K vs. MiniGrid), and pooling layers into early/mid/late groups or using layer index as a continuous covariate to avoid data sparsity. (See US-3)
- **FR-005**: System MUST implement a sensitivity analysis routine that sweeps the entropy threshold across a range of values (e.g., $\in \{, 0.05, 0.1\}$ around the optimal point) and reports the resulting false-positive and false-negative rates. (See US-3)
- **FR-006**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) to the p-values of the logistic regression coefficients when testing across multiple layers or tasks to control the family-wise error rate. (See US-3)
- **FR-007**: System MUST process intermediate state extraction in batches of 50 tokens to ensure memory usage remains within the 7 GB RAM limit while processing sequences up to 512 tokens in length. (See US-2)

### Key Entities

- **TokenSequence**: Represents a generated response to a prompt, containing a list of tokens, their positions, and a boolean validity flag for each.
- **EntropyProfile**: Represents the internal state of a single token, containing a list of entropy values, one for each intermediate transformer layer.
- **ValidityLabel**: A binary flag (0/1) indicating whether a specific token in a sequence matches the ground truth solution.
- **RegressionModel**: The fitted statistical model containing coefficients, intercept, and performance metrics (AUC-ROC, p-values) for the relationship between entropy and validity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient (log-odds) between intermediate-layer entropy and token validity is measured against the null hypothesis of zero correlation to determine statistical significance (allowing for non-significant results). (See FR-004)
- **SC-002**: The Area Under the Receiver Operating Characteristic Curve (AUC-ROC) for predicting validity from entropy is measured against a random baseline (AUC=0.5) to quantify predictive power. (See FR-004)
- **SC-003**: The optimal entropy threshold is measured against the sensitivity analysis results to identify the cutoff that minimizes the weighted sum (equal weights for false positives and false negatives) of false positives and false negatives. (See FR-005)
- **SC-004**: The decay of predictive power (AUC-ROC) is measured across sequence lengths (short vs. long) and task types (math vs. navigation) to quantify signal robustness. (See FR-004, FR-007)
- **SC-005**: The false discovery rate (FDR) is measured against the nominal alpha level (conventionally set) after applying the multiple-comparison correction to ensure the validity of the statistical claims. (See FR-006)

## Assumptions

- **Assumption about model feasibility**: A 1.5B parameter model (or a heavily quantized 7B model) can perform a full forward pass and store intermediate states for sequences of length up to 512 tokens within the 7 GB RAM limit of the GitHub Actions free-tier runner, provided intermediate states are processed in batches of 50 tokens.
- **Assumption about dataset validity**: The GSMK and MiniGrid datasets from HuggingFace contain complete, unambiguous ground-truth solutions that can be used to definitively label token validity for a selected subset of examples.
- **Assumption about computational limits**: The total compute time for generating ground truth, extracting entropy for a representative sample of examples across both datasets, and running the regression analysis will remain within the resource constraints of a standard CI/CD environment.
- **Assumption about signal independence**: The research question is whether intermediate layer entropy *predicts* final token validity, not whether they are statistically independent. The hypothesis posits that intermediate entropy contains predictive signal for final validity that is not trivially determined by the final layer's output alone.
- **Assumption about threshold justification**: The primary optimization metric for the entropy threshold is maximizing the ratio of skipped computation to accuracy loss (or minimizing the weighted error), rather than simply selecting a median or specific quantile, to align with the research goal of efficiency.