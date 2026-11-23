# Feature Specification: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic

**Feature Branch**: `001-evaluating-gnn-anomaly-detection`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Construct and Validate Network Traffic Graphs (Priority: P1) (See US-1)

The researcher needs to ingest raw NetFlow records from the CTU-13 dataset **or** from the open‑source NetFlow dataset (`keys-i/netFlow`) if CTU‑13 is unavailable, construct directed communication graphs (nodes=IPs, edges=flows), and verify that the graph structure fits within the RAM constraints of the CI environment before any model training begins.

**Why this priority**: This is the foundational step; without a valid, memory‑safe graph representation, no analysis or model training can occur. It validates the feasibility of the approach on the target hardware.

**Independent Test**: The system can be fully tested by running the data ingestion and graph construction script on a single CTU‑13 scenario (or the substitute dataset) and verifying that peak memory usage remains <7 GB and that the resulting graph object contains the expected number of nodes and edges.

**Acceptance Scenarios**:

1. **Given** a raw NetFlow CSV file from CTU‑13 Scenario 1, **When** the graph construction script executes, **Then** a directed graph object is returned with nodes representing unique IPs and edges weighted by packet counts, and memory usage stays below 7 GB.
2. **Given** a graph constructed from multiple scenarios, **When** the script attempts to load the graph into memory, **Then** the system **subsamples** the graph by retaining the largest connected component (if node count > 5,000 or memory > 7 GB) and **issues a warning** rather than aborting, ensuring deterministic and topologically meaningful results.
3. **Given** a constructed graph, **When** the validation check runs, **Then** it confirms that the number of nodes is ≤5,000 per scenario (via subsampling if necessary) and that edge weights are non‑negative integers.

---

### User Story 2 - Compare GNN Performance Against Feature‑Engineered Baselines (Priority: P2) (See US-2)

The researcher needs to train a multi‑layer GCN model and standard baselines (Random Forest, XGBoost) on the structural features to determine if graph‑structured message passing provides a statistically significant improvement in anomaly detection metrics (AUC, F1) over flat feature vectors.

**Why this priority**: This addresses the core research question: whether graph structure adds predictive value. It is the primary scientific experiment of the project.

**Independent Test**: The system can be fully tested by training the models on a fixed dataset split, evaluating them on a held‑out test set, and confirming that the performance metrics are recorded and comparable.

**Acceptance Scenarios**:

1. **Given** a pre‑processed graph with structural node features, **When** the GCN and baseline models are trained for up to 30 epochs with early stopping, **Then** both models converge and produce predictions on the test set without crashing due to GPU/CUDA errors.
2. **Given** predictions from the GCN and Random Forest models, **When** the evaluation script runs, **Then** it outputs Precision, Recall, F1‑Score, and AUC‑ROC for both models, allowing for a direct comparison.
3. **Given** the performance metrics from multiple random seeds, **When** the statistical analysis runs, **Then** it calculates the mean and standard deviation of the F1‑scores for each model type and performs the tests described in FR‑006 and FR‑011.

---

### User Story 3 - Identify Predictive Structural Patterns and Validate Significance (Priority: P3) (See US-3)

The researcher needs to analyze feature importance and structural correlations to identify which specific patterns (e.g., degree distribution, edge weight variance) are most predictive of anomalies, and apply multiple‑comparison corrections to ensure findings are not spurious.

**Why this priority**: This provides the interpretability and scientific rigor required to answer "which patterns" are predictive, moving beyond a simple "GNN works" conclusion.

**Independent Test**: The system can be fully tested by running the feature importance analysis and statistical significance tests on the model outputs and verifying that the reported patterns align with the data and meet the AUC‑based success criterion.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model, **When** the feature importance analysis runs, **Then** it ranks structural features (e.g., betweenness centrality, clustering coefficient) by their contribution to the model's decision.
2. **Given** the set of hypothesis test results comparing GNN vs. baseline performance, **When** the Benjamini‑Hochberg correction is applied, **Then** the adjusted p‑values are reported, and any significant findings are flagged as surviving the FDR < 0.05 threshold.
3. **Given** the identified top predictive features, **When** the pattern‑based classifier (using only those features) is evaluated on an independent held‑out set, **Then** it achieves an AUC ≥ 0.80, satisfying SC‑005.

---

### Edge Cases

- What happens when a specific CTU‑13 scenario contains a graph with >5,000 nodes after initial processing? (System subsamples the largest connected component and logs a warning).
- How does the system handle a scenario where the GNN model fails to converge within 30 epochs on CPU? (System logs the failure, retains the best epoch checkpoint, and proceeds with baseline models).
- How does the system handle a situation where the ground‑truth labels for a specific scenario are missing or inconsistent with the graph edges? (System validates label integrity, skips the scenario, and records the omission in a log).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest NetFlow records from the CTU‑13 dataset **or** from the open‑source NetFlow dataset (`keys-i/netFlow`) if CTU‑13 is unavailable, **preferentially using CTU‑13 when it can be accessed**; then construct directed graphs where nodes are IPs and edges are directed (source→dest) with weights equal to packet counts (See US-1).
- **FR-002**: System MUST enforce a hard memory limit (approximately in the gigabyte range) during graph construction. If the graph exceeds 7 GB **or** contains >5,000 nodes, the system MUST **subsample** by retaining the largest connected component, issue a warning, and continue execution (See US-1).
- **FR-003**: System MUST implement a multi‑layer Graph Convolutional Network (GCN) using a CPU‑only backend (no CUDA/GPU) with a maximum of 30 training epochs. Early stopping MUST be enabled, monitoring validation loss with a patience of 5 epochs and a minimum delta of 1e‑4 (See US-2).
- **FR-004**: System MUST train Random Forest and XGBoost baselines on pre‑computed structural features (degree, centrality, variance) to serve as a non‑graph comparison of learned representations vs. hand‑crafted statistics (See US-2).
- **FR-005**: System MUST evaluate all models using Precision, Recall, F1‑Score, and AUC‑ROC on held‑out test scenarios not seen during training (See US-2).
- **FR-006**: System MUST perform **paired t‑tests** on F1‑scores across **≥ 20** random seeds. The hypothesis set for Benjamini‑Hochberg correction MUST consist of: (1) GCN vs RF, (2) GCN vs XGB, and (3‑7) each of the top structural features vs. the **null baseline** defined in FR‑010. This test choice is justified as the standard approach for comparing mean performance across paired runs (See US-3).
- **FR-007**: System MUST output a ranked list of predictive patterns derived from GNN embeddings using gradient‑based attribution (e.g., Integrated Gradients). The ranked patterns are then used to train a **pattern‑based classifier** whose AUC on an independent held‑out set must be reported (≥ 0.80) to satisfy SC‑005, thereby providing an AUC‑based validation that is independent of the original model’s training labels (See US-3).
- **FR-008**: System MUST implement a Temporal Holdout validation strategy where the model is trained on the earliest **[deferred]** of time‑ordered flows and tested on the latest **[deferred]**, preventing data leakage from static structural definitions of anomalies (See US-2).
- **FR-009**: System MUST validate raw NetFlow records against `contracts/dataset.schema.yaml` before graph construction to ensure schema compliance (See US-1).
- **FR-010**: System MUST define a **null baseline** as a majority‑class random classifier (predicts the most frequent label) and compute its performance metrics (AUC, F1) for use in the hypothesis set of FR‑006 (See US-3).
- **FR-011**: System MUST run multiple independent random‑seed repetitions for each model training and evaluation pipeline. (See US-2). This guarantees sufficient statistical power for the paired t‑tests and Benjamini‑Hochberg correction.

### Key Entities

- **Network Graph**: A directed graph representation of network traffic, where nodes are IP addresses and edges are flows with weights (packet counts) and timestamps.
- **Structural Features**: Computed metrics for each node including degree distribution, betweenness centrality, local clustering coefficient, and temporal edge weight variance.
- **Anomaly Label**: Ground‑truth binary indicator (anomalous vs. normal) derived from CTU‑13 scenario metadata (botnet vs. benign traffic).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The memory footprint of the graph construction process is measured against the 7 GB RAM limit of the GitHub Actions runner (See US-1).
- **SC-002**: The **F1‑Score** performance of the GCN model is measured against the F1‑Score of the Random Forest baseline to determine if graph structure adds predictive value (See US-2).
- **SC-003**: The statistical significance of the performance difference between GNN and baselines is measured against the Benjamini‑Hochberg adjusted p‑value threshold of FDR < 0.05 (See US-3).
- **SC-004**: The end‑to‑end runtime of the full analysis pipeline (data ingestion to statistical reporting) is measured against the **214‑minute** runtime target (≈ 3 h 34 min) (See US-2).
- **SC-005**: The predictive power of identified structural patterns is measured against a **target AUC ≥ 0.80** on an independent held‑out set (See US-3).

## Assumptions

- The CTU‑13 dataset is available and accessible via the provided URL, and the NetFlow records contain sufficient fields (source/dest IP, packet count, timestamp) to construct the required graph. If CTU‑13 is unavailable, the open‑source NetFlow dataset (`keys-i/netFlow`) may be used as a fallback.
- The "ground truth" labels provided in the CTU‑13 metadata accurately reflect the anomalous behavior of the traffic flows and are independent of the structural features derived from the graph.
- The 2‑layer GCN architecture is sufficiently expressive for the task and can converge within 30 epochs on CPU hardware without requiring GPU acceleration or quantization.
- The structural features (degree, centrality, etc.) are computationally tractable to calculate for graphs of up to 5,000 nodes within the 214‑minute time limit.
- The Benjamini‑Hochberg correction is an appropriate method for controlling the false discovery rate given the number of hypothesis tests performed (comparing multiple models and features).
- The GitHub Actions free‑tier runner (2 CPU, ~7 GB RAM) is stable enough that resource contention will not invalidate the memory or time constraints.
- A majority‑class random classifier provides a reasonable null baseline for assessing the added value of structural features.
