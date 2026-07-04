# Feature Specification: Investigating Loss Functions on Small-World Graphs

**Feature Branch**: `001-investigating-loss-functions-small-world`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Effectiveness of Different Loss Functions for Training Graph Neural Networks on Small Worlds"

## User Scenarios & Testing

### User Story 1 - Synthetic Graph Generation and Topology Annotation (Priority: P1)

The system MUST generate synthetic Watts-Strogatz graphs with varying clustering coefficients and annotate nodes with community-derived labels to enable supervised training. This is the foundational data layer required for all subsequent analysis.

**Why this priority**: Without synthetic data with controlled topological properties (specifically the clustering coefficient via rewiring probability $\beta$), the core research question cannot be tested. This is the minimum viable dataset for the experiment.

**Independent Test**: Can be fully tested by running the data generation script and verifying that the output graphs have the expected range of clustering coefficients and that node labels correspond to the underlying community structure.

**Acceptance Scenarios**:

1. **Given** the system is configured with 50 graph instances, **When** the generation script runs with rewiring probability $\beta$ ranging from 0.0 to 1.0, **Then** the output dataset contains a representative set of graphs with clustering coefficients within ±0.05 of the theoretical expectation for the given $\beta$ (near 0.5 for $\beta=0$ down to near 0 for $\beta=1$).
2. **Given** a generated graph with known community structure, **When** the annotation module runs, **Then** every node is assigned a label corresponding to its community based on the initial ring lattice (before rewiring), and the label distribution is balanced enough to prevent trivial classification (no single class > 80%).
3. **Given** the generated dataset, **When** a sanity check is performed, **Then** the graph statistics (number of nodes, edges, average degree) match the configuration parameters (N=100, fixed average degree).

---

### User Story 2 - Dual-Loss Training and Convergence Tracking (Priority: P2)

The system MUST train a multi-layer GCN on each generated graph using both Cross-Entropy (supervised) and InfoNCE (contrastive) loss functions. For InfoNCE, it MUST evaluate a linear probe on frozen embeddings to measure accuracy. The system MUST record the full per-epoch loss/accuracy trajectory and the number of steps required to reach a predefined accuracy threshold.

**Why this priority**: This implements the core experimental comparison. It directly measures the "convergence efficiency" mentioned in the research question. Without this, no comparison between loss functions is possible.

**Independent Test**: Can be fully tested by running the training loop on a single small graph and verifying that two models are saved (one per loss), that full trajectory logs are generated, and that the convergence logs contain step counts and accuracy curves for both.

**Acceptance Scenarios**:

1. **Given** a generated graph and a 2-layer GCN architecture, **When** the training loop executes with Cross-Entropy loss, **Then** the system records the full per-epoch loss and accuracy trajectory, and records the step count when accuracy first reaches $\ge$ [deferred] or terminates after a maximum of 1000 epochs without reaching it.
2. **Given** the same graph and architecture, **When** the training loop executes with InfoNCE contrastive loss, **Then** the system trains the encoder, freezes weights, trains a linear probe on the embeddings, and records the step count when the probe accuracy first reaches $\ge$ [deferred] (or terminates after 1000 epochs), along with the full trajectory.
3. **Given** a completed training run for a specific graph, **When** the results are aggregated, **Then** the output includes a mapping of $\beta$ (rewiring probability) to convergence steps and full trajectories for both loss types.

---

### User Story 3 - Statistical Interaction Analysis and Reporting (Priority: P3)

The system MUST compute the Pearson correlation between the rewiring probability ($\beta$) and convergence speed for each loss type, and perform an ANCOVA (Analysis of Covariance) with an interaction term to test for the effect between topology ($\beta$) and loss function.

**Why this priority**: This delivers the final scientific insight required by the research question ("How does clustering influence relative efficiency?"). It transforms raw training logs into a statistically valid conclusion.

**Independent Test**: Can be fully tested by running the analysis script on a mock dataset with known correlations and verifying that the ANCOVA interaction p-value is correctly computed and reported.

**Acceptance Scenarios**:

1. **Given** the aggregated training results for all 50 graphs, **When** the analysis script runs, **Then** it outputs a Pearson correlation coefficient and p-value for the relationship between rewiring probability ($\beta$) and convergence steps for the Cross-Entropy loss.
2. **Given** the same aggregated results, **When** the ANCOVA is performed (model: `steps ~ loss_type * beta`), **Then** the output includes the F-statistic and p-value for the interaction term (Loss Type $\times$ $\beta$).
3. **Given** the analysis results, **When** the final report is generated, **Then** it explicitly states whether the interaction effect is statistically significant (p < 0.05) and summarizes the direction of the effect (e.g., "Contrastive loss converges faster as $\beta$ increases").

### Edge Cases

- What happens if a graph generated with $\beta=0$ (perfect regular lattice) is disconnected? The system must detect and regenerate or skip disconnected components to ensure valid training.
- How does the system handle a scenario where neither loss function reaches [deferred] accuracy within the epoch limit? The system must record the "censored" step count (max epochs) and flag the run for potential exclusion or separate analysis in the ANCOVA.
- What happens if the synthetic labels result in a class imbalance > 80%? The generation process must enforce a a maximum class size of a substantial majority (no single class > 80%) to ensure the supervised task is non-trivial.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate 50 Watts-Strogatz graphs with N=100 nodes and varying rewiring probability $\beta \in [0.0, 1.0]$ to create a controlled range of clustering coefficients (See US-1).
- **FR-002**: System MUST annotate nodes in generated graphs with community-derived labels based on the initial ring lattice structure to enable supervised node classification tasks (See US-1).
- **FR-003**: System MUST implement a 2-layer Graph Convolutional Network (GCN) that runs exclusively on CPU without GPU dependencies (See US-2).
- **FR-004**: System MUST train the GCN on each graph using both Cross-Entropy loss and InfoNCE contrastive loss; for InfoNCE, it MUST evaluate a linear probe on frozen embeddings to measure accuracy (See US-2).
- **FR-005**: System MUST calculate the number of training steps required to reach $\ge$ [deferred] accuracy for each run (using the linear probe for InfoNCE), or record the maximum epoch limit if the threshold is not met (See US-2).
- **FR-006**: System MUST compute the Pearson correlation coefficient between the graph's rewiring probability ($\beta$) and the convergence steps for each loss type separately (See US-3).
- **FR-007**: System MUST perform an ANCOVA (Analysis of Covariance) with an interaction term (`loss_type * beta`) to test for a statistically significant interaction effect between graph topology and loss function type (See US-3).
- **FR-008**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or False Discovery Rate) to the set of correlation coefficients and the ANCOVA interaction term to control the family-wise error rate (See US-3).
- **FR-009**: System MUST record the full per-epoch loss and accuracy trajectory for every training run to enable convergence curve analysis (See US-2).
- **FR-010**: System MUST perform a formal power analysis to justify the sample size of 50 graphs for detecting a moderate interaction effect in the ANCOVA (See Assumptions).

### Key Entities

- **SyntheticGraph**: Represents a Watts-Strogatz graph instance with attributes: `id`, `rewiring_probability` (beta), `clustering_coefficient`, `node_count`, `edge_list`, `node_labels`.
- **TrainingRun**: Represents a single model training instance with attributes: `graph_id`, `loss_type` (CE/InfoNCE), `steps_to_convergence`, `final_f1_score`, `max_epochs_reached`, `trajectory_log`.
- **AnalysisResult**: Represents the statistical output with attributes: `correlation_ce`, `correlation_contrastive`, `ancova_interaction_f`, `ancova_interaction_p`, `corrected_p_value`.

## Success Criteria

- **SC-001**: The correlation between rewiring probability ($\beta$) and convergence speed is measured against the null hypothesis of no correlation (r=0) for each loss type (See US-3).
- **SC-002**: The interaction effect between topology ($\beta$) and loss function is measured against the null hypothesis of no interaction via ANCOVA (See US-3).
- **SC-003**: The validity of the statistical inference is measured by the system outputting a corrected p-value for the interaction term, and the analysis script verifying that this value is < 0.05 to flag significance (See US-3).
- **SC-004**: The computational feasibility is measured against the constraint of completing the full 50-graph experiment within 6 hours on a CPU-only runner with 7 GB RAM (See Assumptions).

## Assumptions

- The `networkx` library and `PyTorch` (CPU mode) are available in the execution environment and sufficient to generate graphs and train the 2-layer GCN within the 6-hour limit.
- The synthetic community structure derived from the initial ring lattice provides a valid and non-trivial signal for the supervised loss function; labels are fixed based on the initial lattice, meaning high rewiring ($\beta \to 1$) increases task difficulty but does not remove the ground truth.
- The 90% accuracy threshold is a sufficient proxy for "convergence" for this specific experimental setup, and the maximum epoch limit (1000) is adequate to prevent infinite loops while capturing non-convergent behavior.
- The sample size of 50 graphs is justified by a formal power analysis (see FR-010) to detect a moderate interaction effect, rather than relying on approximate assumptions.
- The "contrastive" implementation uses a standard InfoNCE loss with a fixed temperature parameter ($\tau=0.5$) and a fixed number of negative samples per anchor, as the idea does not specify hyperparameters for the contrastive objective.
- The dataset variables (rewiring probability, convergence steps, loss type) are fully contained within the synthetic generation and training process; no external real-world data is required for the primary hypothesis test.