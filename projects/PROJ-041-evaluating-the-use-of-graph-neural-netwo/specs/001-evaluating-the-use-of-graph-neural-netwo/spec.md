# Feature Specification: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic

**Feature Branch**: `001-evaluating-gnn-anomaly-detection`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Construct and Validate Network Traffic Graphs (Priority: P1)

The researcher needs to ingest raw NetFlow records from the CTU-13 dataset, construct directed communication graphs (nodes=IPs, edges=flows), and verify that the graph structure fits within the 7GB RAM constraint of the CI environment before any model training begins.

**Why this priority**: This is the foundational step; without a valid, memory-safe graph representation, no analysis or model training can occur. It validates the feasibility of the approach on the target hardware.

**Independent Test**: The system can be fully tested by running the data ingestion and graph construction script on a single CTU-13 scenario and verifying that peak memory usage remains <7GB and that the resulting graph object contains the expected number of nodes and edges.

**Acceptance Scenarios**:

1. **Given** a raw NetFlow CSV file from CTU-13 Scenario 1, **When** the graph construction script executes, **Then** a directed graph object is returned with nodes representing unique IPs and edges weighted by packet counts, and memory usage stays below 7GB.
2. **Given** a graph constructed from multiple scenarios, **When** the script attempts to load the graph into memory, **Then** the system raises a clear error if the memory footprint exceeds 7GB, preventing further execution.
3. **Given** a constructed graph, **When** the validation check runs, **Then** it confirms that the number of nodes is ≤5,000 per scenario (via subsampling if necessary) and that edge weights are non-negative integers.

---

### User Story 2 - Compare GNN Performance Against Feature-Engineered Baselines (Priority: P2)

The researcher needs to train a 2-layer GCN model and standard baselines (Random Forest, XGBoost) on the structural features to determine if graph-structured message passing provides a statistically significant improvement in anomaly detection metrics (AUC, F1) over flat feature vectors.

**Why this priority**: This addresses the core research question: whether graph structure adds predictive value. It is the primary scientific experiment of the project.

**Independent Test**: The system can be fully tested by training the models on a fixed dataset split, evaluating them on a held-out test set, and confirming that the performance metrics are recorded and comparable.

**Acceptance Scenarios**:

1. **Given** a pre-processed graph with structural node features, **When** the GCN and baseline models are trained for up to 30 epochs with early stopping, **Then** both models converge and produce predictions on the test set without crashing due to GPU/CUDA errors.
2. **Given** predictions from the GCN and Random Forest models, **When** the evaluation script runs, **Then** it outputs Precision, Recall, F1-Score, and AUC-ROC for both models, allowing for a direct comparison.
3. **Given** the performance metrics from 5 random seeds, **When** the statistical analysis runs, **Then** it calculates the mean and standard deviation of the F1-scores for each model type.

---

### User Story 3 - Identify Predictive Structural Patterns and Validate Significance (Priority: P3)

The researcher needs to analyze feature importance and structural correlations to identify which specific patterns (e.g., degree distribution, edge weight variance) are most predictive of anomalies, and apply multiple-comparison corrections to ensure findings are not spurious.

**Why this priority**: This provides the interpretability and scientific rigor required to answer "which patterns" are predictive, moving beyond a simple "GNN works" conclusion.

**Independent Test**: The system can be fully tested by running the feature importance analysis and statistical significance tests on the model outputs and verifying that the reported patterns align with the data.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model, **When** the feature importance analysis runs, **Then** it ranks structural features (e.g., betweenness centrality, clustering coefficient) by their contribution to the model's decision.
2. **Given** the set of hypothesis test results comparing GNN vs. baseline performance, **When** the Benjamini-Hochberg correction is applied, **Then** the adjusted p-values are reported, and any significant findings are flagged as surviving the FDR < 0.05 threshold.
3. **Given** the identified top predictive features, **When** the correlation analysis runs, **Then** it reports the correlation coefficient between these features and the anomaly labels, distinguishing between degree-based and temporal-based patterns.

---

### Edge Cases

- What happens when a specific CTU-13 scenario contains a graph with >5,000 nodes after initial processing? (System must subsample or raise a controlled error).
- How does the system handle a scenario where the GNN model fails to converge within 30 epochs on CPU? (System must log the failure and proceed with the last best epoch or the baseline).
- How does the system handle a situation where the ground-truth labels for a specific scenario are missing or inconsistent with the graph edges? (System must validate label integrity and skip or flag the scenario).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest NetFlow records from the CTU-13 dataset and construct directed graphs where nodes are IPs and edges are directed (source→dest) with weights equal to packet counts (See US-1).
- **FR-002**: System MUST enforce a hard memory limit of 7GB during graph construction. If the graph exceeds 7GB OR contains >5,000 nodes, the system MUST subsample by retaining the largest connected component to ensure deterministic and topologically meaningful results (See US-1).
- **FR-003**: System MUST implement a 2-layer Graph Convolutional Network (GCN) using a CPU-only backend (no CUDA/GPU) with a maximum of 30 training epochs. Early stopping MUST be enabled, monitoring validation loss with a patience of 5 epochs and a minimum delta of 1e-4 (See US-2).
- **FR-004**: System MUST train Random Forest and XGBoost baselines on pre-computed structural features (degree, centrality, variance) to serve as a non-graph comparison of learned representations vs. hand-crafted statistics (See US-2).
- **FR-005**: System MUST evaluate all models using Precision, Recall, F1-Score, and AUC-ROC on held-out test scenarios not seen during training (See US-2).
- **FR-006**: System MUST perform Wilcoxon signed-rank tests on F1-scores across 5 random seeds. The hypothesis set for Benjamini-Hochberg correction MUST consist of 7 specific comparisons: (1) GCN vs RF, (2) GCN vs XGB, and (3-7) the top 5 structural features vs. a null baseline (See US-3).
- **FR-007**: System MUST output a ranked list of predictive patterns derived from the GNN's learned embeddings using gradient-based attribution (e.g., Integrated Gradients) mapped back to structural proxies, distinct from the Random Forest feature importance (See US-3).
- **FR-008**: System MUST implement a Temporal Holdout validation strategy where the model is trained on the first [deferred] of time-windowed flows and tested on the remaining [deferred] to prevent data leakage from static structural definitions of anomalies (See US-2).

### Key Entities

- **Network Graph**: A directed graph representation of network traffic, where nodes are IP addresses and edges are flows with weights (packet counts) and timestamps.
- **Structural Features**: Computed metrics for each node including degree distribution, betweenness centrality, local clustering coefficient, and temporal edge weight variance.
- **Anomaly Label**: Ground-truth binary indicator (anomalous vs. normal) derived from CTU-13 scenario metadata (botnet vs. benign traffic).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The memory footprint of the graph construction process is measured against the 7GB RAM limit of the GitHub Actions runner (See US-1).
- **SC-002**: The AUC-ROC performance of the GCN model is measured against the AUC-ROC of the Random Forest baseline to determine if graph structure adds predictive value (See US-2).
- **SC-003**: The statistical significance of the performance difference between GNN and baselines is measured against the Benjamini-Hochberg adjusted p-value threshold of FDR < 0.05 (See US-3).
- **SC-004**: The end-to-end runtime of the full analysis pipeline (data ingestion to statistical reporting) is measured against the 6-hour GitHub Actions job limit (See US-2).
- **SC-005**: The predictive power of identified structural patterns is measured against a pre-defined target AUC threshold defined in the research plan (See US-3).

## Assumptions

- The CTU-13 dataset is available and accessible via the provided URL, and the NetFlow records contain sufficient fields (source/dest IP, packet count, timestamp) to construct the required graph.
- The "ground truth" labels provided in the CTU-13 metadata accurately reflect the anomalous behavior of the traffic flows and are independent of the structural features derived from the graph.
- The 2-layer GCN architecture is sufficiently expressive for the task and can converge within 30 epochs on CPU hardware without requiring GPU acceleration or quantization.
- The structural features (degree, centrality, etc.) are computationally tractable to calculate for graphs of up to 5,000 nodes within the 6-hour time limit.
- The Benjamini-Hochberg correction is an appropriate method for controlling the false discovery rate given the number of hypothesis tests performed (comparing multiple models and features).
- The GitHub Actions free-tier runner (2 CPU, ~7GB RAM) is stable and does not experience resource contention that would invalidate the memory or time constraints.