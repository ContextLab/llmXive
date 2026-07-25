# Feature Specification: Evaluating the Effectiveness of Differential Privacy in Federated Learning

**Feature Branch**: `001-evaluating-dp-federated-learning`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Evaluating the Effectiveness of Differential Privacy in Federated Learning"

## User Scenarios & Testing

### User Story 1 - Baseline Heterogeneity Simulation (Priority: P1)

**As a** research engineer, **I want** to generate client data partitions from the FEMNIST and Shakespeare datasets using Dirichlet distributions with varying concentration parameters (α), **so that** I can establish a controlled baseline for client data heterogeneity before applying privacy mechanisms.

**Why this priority**: This is the foundational step. Without reproducible, quantifiable heterogeneity levels, no subsequent analysis of privacy-utility trade-offs is valid. It isolates the independent variable (heterogeneity) from the treatment (DP).

**Independent Test**: Can be fully tested by running the data partitioning script and verifying that the resulting label distributions across clients match the theoretical Dirichlet parameters (e.g., low α yields high imbalance) without any model training or privacy noise applied.

**Acceptance Scenarios**:

1. **Given** the FEMNIST dataset is downloaded, **When** the partitioning script is executed with α=0.1, **Then** the resulting client label distributions show high variance (e.g., some clients have <5% of certain classes) compared to α=1.0.
2. **Given** the Shakespeare dataset is downloaded, **When** the partitioning script is executed with α=1.0, **Then** the resulting client label distributions are relatively balanced across the majority of clients.
3. **Given** a specific seed value, **When** the partitioning script is run twice, **Then** the resulting client partitions are identical, ensuring reproducibility.

---

### User Story 2 - DP-FL Training and Convergence Measurement (Priority: P2)

**As a** researcher, **I want** to train models using FedAvg with Opacus-enabled differential privacy across varying privacy budgets (ε) and heterogeneity levels, **so that** I can measure the impact of privacy noise on global accuracy and minority client convergence.

**Why this priority**: This implements the core experimental intervention. It generates the primary data points (accuracy vs. ε) needed to answer the research question.

**Independent Test**: Can be fully tested by running a single training job (e.g., FEMNIST, α=0.1, ε=0.5) and verifying that the training loop completes without GPU errors, the privacy budget is tracked correctly via the moments accountant, and accuracy metrics are logged per round.

**Acceptance Scenarios**:

1. **Given** a homogeneous partition (α=1.0) and ε=10.0, **When** the DP-FedAvg training completes, **Then** the global test accuracy is within 5% of the non-DP baseline.
2. **Given** a highly heterogeneous partition (α=0.1) and ε=0.1, **When** the DP-FedAvg training completes, **Then** the system logs the accuracy for both the global model and the specific "minority" clients (those with rare labels).
3. **Given** a valid privacy budget ε, **When** the training step executes, **Then** the Gaussian noise multiplier (σ) is calculated and applied to the gradients as per the moments accountant algorithm.

---

### User Story 3 - Statistical Analysis and Threshold Sensitivity (Priority: P3)

**As a** data analyst, **I want** to run statistical tests (paired t-tests) comparing majority vs. minority performance and perform a sensitivity analysis on the heterogeneity threshold, **so that** I can determine if the observed degradation is statistically significant and robust to parameter choices.

**Why this priority**: This transforms raw metrics into scientific conclusions. It addresses the "methodological soundness" requirement by ensuring findings are not artifacts of arbitrary thresholds or random chance.

**Independent Test**: Can be fully tested by feeding a pre-generated CSV of accuracy results (from US-2) into the analysis script and verifying that p-values are calculated and the sensitivity sweep (varying α or ε) produces the expected trend lines.

**Acceptance Scenarios**:

1. **Given** accuracy results from 5 independent seeds for ε=0.5, **When** the t-test is run, **Then** the system outputs a p-value indicating if the difference between majority and minority client accuracy is significant (p < 0.05).
2. **Given** a set of results across α ∈ {0.1, 0.5, 1.0}, **When** the sensitivity analysis script runs, **Then** it generates a plot showing how the "accuracy gap" between majority and minority clients changes as heterogeneity increases.
3. **Given** a critical heterogeneity threshold hypothesis, **When** the analysis is performed, **Then** the system explicitly reports whether the degradation for ε < 0.5 exceeds a defined statistical significance level.

### Edge Cases

- What happens if the LEAF benchmark download fails or the data format changes? (System must retry 3 times with exponential backoff, then fail gracefully with a clear error message).
- How does the system handle a scenario where a specific client has zero samples for a target class in a highly skewed partition (α=0.1)? (The training loop must skip gradient updates for that client for that round without crashing, logging a warning).
- What if the privacy budget ε is set so low (e.g., ε=0.01) that the noise dominates the signal entirely? (The system must still run, but the analysis script must flag the result as "utility collapse" rather than a valid data point for the curve).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and partition the FEMNIST and Shakespeare datasets from the LEAF benchmark using Dirichlet distributions with concentration parameters α ∈ {0.1, 0.5, 1.0} (See US-1).
- **FR-002**: System MUST implement FedAvg with Opacus to apply Gaussian noise to client gradients, supporting privacy budgets ε ∈ {0.1, 0.5, 1.0, 5.0, 10.0} (See US-2).
- **FR-003**: System MUST track and log global test accuracy, as well as per-client test accuracy to distinguish between majority and minority client performance (See US-2).
- **FR-004**: System MUST execute 5 independent training runs (seeds) for every configuration of (dataset, α, ε) to enable statistical power (See US-3).
- **FR-005**: System MUST perform paired t-tests comparing (a) DP vs. non-DP baselines and (b) majority vs. minority client accuracies for each configuration (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis sweeping the heterogeneity parameter α over a small concrete set (e.g., {0.05, 0.1, 0.5}) and report the variation in the accuracy gap (See US-3).
- **FR-007**: System MUST compute privacy loss using the moments accountant mechanism to ensure accurate ε tracking (See US-2).

### Key Entities

- **Client Partition**: A subset of the dataset assigned to a specific client, characterized by its label distribution and size.
- **Privacy Budget (ε)**: The numerical parameter defining the strength of the differential privacy guarantee.
- **Heterogeneity Level (α)**: The concentration parameter of the Dirichlet distribution used to simulate data imbalance.
- **Accuracy Metric**: The classification accuracy measured on a held-out test set, recorded globally and per-client.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in convergence speed (rounds to reach [deferred] of final accuracy) between majority and minority clients is measured against the non-DP baseline to quantify heterogeneity impact (See FR-003, US-2).
- **SC-002**: The statistical significance (p-value) of the accuracy gap between majority and minority clients is measured against the threshold p < 0.05 to validate the "critical heterogeneity" hypothesis (See FR-005, US-3).
- **SC-003**: The variation in the "accuracy gap" metric across the sensitivity sweep of α (e.g., {0.05, 0.1, 0.5}) is measured to ensure the observed effects are robust to parameter selection (See FR-006, US-3).
- **SC-004**: The privacy-utility trade-off curve (Global Accuracy vs. ε) is measured against the theoretical expectation of smooth degradation in homogeneous settings vs. steep degradation in heterogeneous settings (See FR-002, US-2).
- **SC-005**: The reproducibility of results is measured by the variance of accuracy metrics across the 5 independent seeds for a fixed configuration (See FR-004, US-3).

## Assumptions

- The LEAF benchmark datasets (FEMNIST, Shakespeare) are accessible via the provided URLs and can be downloaded within the GitHub Actions free-tier time limit (≤6 hours) without GPU acceleration.
- The FEMNIST and Shakespeare datasets contain sufficient label variety to define "minority" clients under low α (α=0.1) conditions; if a specific class is entirely absent in a partition, that client is excluded from the "minority" analysis for that specific class.
- The Opacus library functions correctly in a CPU-only environment (using PyTorch's default CPU backend) for the specified model sizes (small CNN/MLP) and dataset subsets.
- The "minority" client definition is strictly based on label distribution imbalance derived from the Dirichlet parameter α, not on client ID or arbitrary selection.
- The privacy budget ε values (0.1 to 10.0) cover the relevant range where the privacy-utility trade-off is observable without rendering the model completely useless (accuracy ≈ random chance) for the chosen dataset.
- The computational resources of a standard GitHub Actions runner (2 CPU, 7GB RAM) are sufficient to process the sampled datasets and train the small models for the specified number of rounds and seeds.
- The analysis assumes that the noise added by Opacus is purely Gaussian and that the moments accountant provides an accurate estimate of the cumulative privacy loss.
