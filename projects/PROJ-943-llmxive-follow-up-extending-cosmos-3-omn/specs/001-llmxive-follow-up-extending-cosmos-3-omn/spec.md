# Feature Specification: llmXive follow-up: extending "Cosmos 3: Omnimodal World Models for Physical AI"

**Feature Branch**: `001-llmxive-cosmos-gap`  
**Created**: 2026-07-15  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Cosmos 3: Omnimodal World Models for Physical AI'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Transformation & Proxy Model Training (Priority: P1)

As a researcher, I need to transform the continuous action vectors from the Cosmos 3 synthetic dataset into discrete symbolic tokens and train a lightweight, CPU-compatible proxy model (e.g., DistilBERT) to predict logical consistency, so that I can establish a baseline capability for symbolic reasoning without requiring GPU resources.

**Why this priority**: This is the foundational step; without the transformed dataset and a trained proxy model, no comparative analysis or gap quantification is possible. It directly enables the core research question.

**Independent Test**: Can be fully tested by running the data transformation script to produce a labeled CSV/JSONL file (using a random stratified sample if necessary to fit memory) and verifying that the proxy model training script completes successfully on a CPU-only environment within the 6-hour free-tier limit, consuming ≤ 7 GB RAM, and outputting a model artifact and training logs showing convergence.

**Acceptance Scenarios**:

1. **Given** the raw Cosmos 3 synthetic dataset containing continuous action vectors, **When** the transformation script is executed with defined logical rules (vector norm > 0.5 implies constraint_violated, else constraint_satisfied), **Then** the output file contains discrete symbolic tokens (e.g., "constraint_satisfied", "constraint_violated") mapped to the original inputs, and the memory usage during processing remains ≤ 7 GB RAM.
2. **Given** the transformed dataset, **When** the lightweight proxy model is trained on a CPU-only runner, **Then** the training process completes within the 6-hour GitHub Actions free-tier limit, consumes ≤ 7 GB RAM, and produces a valid model artifact with a reported training loss.
3. **Given** the trained proxy model, **When** it is evaluated on a held-out test set of the transformed data, **Then** it outputs a binary classification (valid/invalid) with a measurable accuracy score > 0.5 (better than random chance).

---

### User Story 2 - Comparative Performance Analysis (Priority: P2)

As a researcher, I need to compare the proxy model's performance on the symbolic reasoning tasks against its performance on the original continuous control tasks (using independent physics engine scores), so that I can quantify the "modality gap" and determine if performance degrades significantly.

**Why this priority**: This directly addresses the research question by providing the quantitative evidence of degradation. It relies on the output of US-1 but adds the critical comparative dimension.

**Independent Test**: Can be fully tested by executing the evaluation script that loads the trained model, runs inference on both symbolic and physical (independent score) test sets, and outputs a statistical report comparing accuracy, F1-score, and AUC-ROC between the two domains using an appropriate statistical test.

**Acceptance Scenarios**:

1. **Given** the trained proxy model and two test sets (symbolic and physical-independent), **When** the comparative analysis script is run, **Then** it outputs a table showing the performance metrics (Accuracy, F1, AUC) for both domains side-by-side.
2. **Given** the performance metrics from both domains, **When** a statistically appropriate test (e.g., paired t-test if normal, Wilcoxon signed-rank otherwise) is performed, **Then** the script outputs a p-value indicating whether the difference in performance is statistically significant (p < 0.05).
3. **Given** the analysis results, **When** the degradation is observed, **Then** the report explicitly states the magnitude of the performance drop (e.g., "Accuracy decreased by X%") and confirms the existence of a modality gap.

---

### User Story 3 - Error Analysis & Failure Mode Identification (Priority: P3)

As a researcher, I need to analyze the misclassified samples from the symbolic reasoning task to identify specific patterns in failure (e.g., correlation with visual ambiguity or logical complexity), so that I can characterize the nature of the modality gap beyond a simple accuracy drop.

**Why this priority**: This provides depth to the findings, moving from "does it fail?" to "why does it fail?", which is essential for the "Expected Results" section regarding specific failure modes.

**Independent Test**: Can be fully tested by running the error analysis script on the test set, which outputs a report categorizing misclassifications into the defined taxonomy and visualizing correlations between input features and failure types.

**Acceptance Scenarios**:

1. **Given** the set of misclassified samples from the symbolic reasoning task, **When** the error analysis script is executed, **Then** it categorizes errors into at least three distinct failure modes from the defined taxonomy: "visual ambiguity", "logical complexity", and "context mismatch".
2. **Given** the categorized errors, **When** the script correlates them with input features, **Then** it outputs a summary indicating which specific types of logical constraints or visual conditions have the highest false-negative rate.
3. **Given** the analysis results, **When** the final report is generated, **Then** it includes a qualitative description of the observed failure patterns that supports the quantitative degradation findings.

---

### Edge Cases

- What happens when the logical rules applied to the continuous vectors result in an ambiguous or undefined symbolic token for a specific sample?
- How does the system handle instances where the Cosmos 3 dataset is incomplete or missing specific action vectors required for the transformation?
- What if the lightweight proxy model fails to converge within the 6-hour GitHub Actions free-tier limit due to dataset complexity?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the Cosmos 3 synthetic dataset, filtering for instances containing "action" sequences, and store them in a structured format (See US-1).
- **FR-002**: System MUST map continuous action vectors to discrete symbolic tokens using specific logical rules: if the vector norm > 0.5, label as "constraint_violated"; otherwise, label as "constraint_satisfied", ensuring every input receives a valid label (See US-1).
- **FR-003**: System MUST initialize and train a lightweight, encoder-only Transformer model (e.g., DistilBERT) compatible with CPU-only inference, ensuring memory usage remains ≤ 7 GB RAM (See US-1).
- **FR-004**: System MUST evaluate the trained model on both the symbolic reasoning test set and the physical control test set (using independent physics engine reward scores) to generate comparative performance metrics (See US-2).
- **FR-005**: System MUST perform a statistically appropriate test (e.g., paired t-test if normal, Wilcoxon signed-rank otherwise) on the performance metrics of the two domains to determine statistical significance of the degradation (See US-2).
- **FR-006**: System MUST analyze misclassified samples from the symbolic task to categorize failure modes into the specific categories: "visual ambiguity", "logical complexity", and "context mismatch", and correlate them with input features (See US-3).

### Key Entities

- **Cosmos3_Sample**: Represents a single instance from the dataset, containing text description, video frames, and continuous action vectors.
- **Symbolic_Label**: Represents the discrete token (e.g., "valid", "invalid") assigned to a sample based on logical rules.
- **Proxy_Model**: The lightweight Transformer model trained to predict the Symbolic_Label.
- **Performance_Metric**: A quantitative measure (Accuracy, F1, AUC) derived from model evaluation.
- **Physics_Reward**: An independent ground truth score from the Cosmos 3 physics engine representing physical success.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The performance drop (difference in accuracy/F1 between physical and symbolic domains) is measured against the independent physics engine reward baseline to quantify the modality gap (See US-2).
- **SC-002**: Statistical significance of the performance degradation is measured against a p-value threshold of 0.05 using a statistically appropriate test (See US-2).
- **SC-003**: The proportion of misclassified samples is measured against the total test set size to determine error rates, and these errors are measured against categorized failure modes to identify patterns (See US-3).
- **SC-004**: The memory footprint of the training process is measured against the 7 GB RAM limit to ensure CPU-only feasibility (See US-1).
- **SC-005**: The total training and evaluation time is measured against the 6-hour GitHub Actions free-tier limit to ensure compute feasibility (See US-1, US-2); note that the training phase specifically must complete within this total budget.

## Assumptions

- The Cosmos 3 synthetic dataset release contains sufficient instances of "action" sequences to train and evaluate the proxy model with statistical power, and the dataset size fits within the 7 GB disk limit after sampling.
- The logical rules required to map continuous actions to discrete symbolic tokens can be defined deterministically based on the context provided in the dataset's metadata or text descriptions.
- A lightweight, encoder-only Transformer model (e.g., DistilBERT) is sufficient to capture the relationship between multimodal inputs and logical consistency, avoiding the need for large-scale training or GPU acceleration.
- The "physical control" baseline can be approximated by independent physics engine reward scores, providing a valid comparison point for symbolic reasoning performance that is not derived from the symbolic mapping rules.
- The GitHub Actions free-tier runner (multiple CPU cores, ~7 GB RAM) is capable of handling the data processing, model training, and evaluation within the designated time limit.