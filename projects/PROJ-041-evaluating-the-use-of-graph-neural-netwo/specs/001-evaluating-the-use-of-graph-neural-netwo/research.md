# Research: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic

## Dataset Strategy

The project relies on the **CTU-13 dataset** for ground-truth anomaly labels and **NetFlow** records for graph construction. If CTU-13 is unavailable, the verified **NF-BoT-IoT-v3** dataset will be used as a fallback, with the research scope restricted to "GNN vs Baselines on Botnet Traffic".

| Dataset | Source / URL | Format | Usage | Verification Status |
|:--- |:--- |:--- |:--- |:--- |
| **CTU-13** | **NO verified source found** | NetFlow (CSV) / Metadata | Ground truth labels (Botnet vs. Benign) and flow records. | **Unverified**: The `# Verified datasets` block explicitly states "NO verified source found". We will proceed by describing the dataset by name only. If the implementation fails to locate a local copy or a known public mirror, the pipeline will halt with a clear error and switch to fallback. |
| **NF-BoT-IoT-v3** | ` | Parquet | **Fallback**: Primary source if CTU-13 is unavailable. Contains botnet traffic patterns. | **Verified**: Reachable and format-confirmed. |

**Decision/Rationale**:
The primary specification targets **CTU-13**. However, the `# Verified datasets` block indicates **no verified URL** exists for CTU-13 in the current search context.
* **Strategy**: The implementation will first attempt to load CTU-13 from a standard local path or a known public repository (e.g., `ctu-13-dataset` GitHub repo) if the user has provided it. If no source is available, the pipeline will gracefully fallback to the **verified NetFlow (Parquet)** source (`NF-BoT-IoT-v3.parquet`).
* **Dataset Interchangeability Justification**: If BoT-IoT is used, the research question is explicitly restricted to "GNN vs Baselines on Botnet Traffic". We acknowledge that BoT-IoT represents IoT traffic with distinct protocol distributions compared to general CTU-13 traffic. Claims of generalizability to "all network traffic" will be limited. This is a necessary trade-off to ensure the project can run on verified data.
* **Constraint**: We **cannot** fabricate a URL for CTU-13. The `research.md` explicitly states the lack of a verified source. The plan includes a "Dataset Fallback" phase to ensure the CI job does not fail due to missing data, using the verified HuggingFace dataset as a proxy for the research question (GNN vs. Baselines on Botnet traffic).
* **Removed**: The "IPs (CSV)" dataset (pcy12345BSU) is removed from the strategy as it is an aggregated summary table and cannot be used to construct the required directed communication graphs (FR-001).

## Graph Construction & Memory Strategy

**Challenge**: CTU scenarios can contain millions of flows. The GitHub Actions RAM limit is a hard constraint.

**Method**:
1. **Streaming Ingestion**: Read NetFlow records in chunks.
2. **Edge Aggregation**: Aggregate flows into a directed multigraph where edges are weighted by packet counts.
3. **Anomaly-Preserving Subsampling (FR-002)**: If the node count > 5,000:
 * Identify the **Largest Connected Component (LCC)**.
 * **Prioritize Anomalous Nodes**: Retain all nodes identified as "anomalous" in the metadata (if available) or nodes with high degree (potential botnet hubs).
 * **Sample Remaining**: Randomly sample the remaining nodes to reach the [deferred] node limit, ensuring the distribution of high-degree nodes is preserved as much as possible.
 * **Determinism**: The sampling algorithm uses a fixed random seed (e.g., 42) to ensure the transformation is deterministic and reproducible (Constitution Principle VI).
4. **Memory Logging**: Use `tracemalloc` to log peak memory at every stage (Ingestion, Aggregation, Feature Calculation).
5. **Artifact**: The resulting graph is saved as `graph_{scenario}_subsampled.graphml`.

**Feasibility Check**:
* **Graph Representation**: `networkx` (Python) is memory-efficient for sparse graphs. [deferred] nodes with [deferred] edges fits comfortably in <1GB RAM.
* **Feature Calculation**: `networkx` centrality metrics (Betweenness, Clustering) on [deferred] nodes are computationally cheap (O(N^2) or better approximations) and will run in <10 minutes on 2 vCPUs.

## Model Strategy

### 1. Graph Neural Network (GCN)
* **Architecture**: 2-layer GCN (FR-003).
* **Input**: Node features (Degree, In-Degree, Out-Degree, Clustering Coeff, Edge Weight Variance).
* **Target Variable (Label Aggregation)**: The GCN performs **node-level classification**. The label `is_anomalous` for a node (IP) is defined as **1** if the IP participated in **ANY** anomalous flow in the scenario (derived from CTU-13 flow labels), and **0** otherwise. This aggregates flow-level ground truth to nodes, resolving the undefined training objective.
* **Output**: Binary classification (Anomaly/Normal) per node.
* **Training**:
 * Backend: `torch` (CPU only). **NO CUDA**.
 * Epochs: Max 30.
 * Early Stopping: Patience 5, delta 1e-4.
 * Optimizer: Adam (default lr 0.01).
* **Risk Mitigation**: If the model fails to converge (loss plateau), the system logs the failure and proceeds with the baseline models to ensure the pipeline completes.
* **Distinguishing GNN vs. RF**: The GCN is trained to learn **relational patterns** via message passing (aggregating neighbor information), which are distinct from the **static structural statistics** used by the Random Forest. The evaluation explicitly tests whether the GNN's ability to capture *topological context* provides an advantage over the RF's use of *static features*.

### 2. Baselines (FR-004)
* **Random Forest**: `sklearn.ensemble.RandomForestClassifier` (n_estimators=100).
* **XGBoost**: `xgboost.XGBClassifier` (use_gpu=False).
* **Features**: Same structural features as GCN input.

### 3. Validation Strategy (FR-008)
* **Temporal Holdout**:
 * **Graph Construction**: The graph is constructed **only** from the **training** flows (first [deferred] of time-windowed flows).
 * **Test Mapping**: For the test set (remaining [deferred]), flows are mapped to the **existing** nodes in the training graph.
 * **Unseen Nodes**: If a test flow involves a new IP (node) not present in the training graph, that flow is **dropped** or assigned a default "unknown" node feature vector to prevent data leakage. This ensures the test set does not "contaminate" the graph structure used for training.
 * This prevents data leakage from static structural definitions of anomalies.

## Statistical Rigor & Methodology

### Hypothesis Testing (FR-006)
* **Metric**: F1-Score (primary), AUC-ROC (secondary).
* **Resampling**: 5 random seeds (42, 123, 456, 789, 101).
* **Tests**:
 1. **Model Comparison**: **Permutation Test** (not Wilcoxon) for GCN vs. RF and GCN vs. XGB. The null hypothesis is that the performance difference is zero. The null distribution is generated by permuting the model labels a sufficient number of times to ensure robust estimation. This is robust for small N (N<13 scenarios).
 2. **Feature Significance**: Top 5 structural features vs. Null Baseline.
 * **Null Baseline Definition**: A univariate model trained on **permuted labels** (shuffled 1000 times) to generate a null distribution of AUC/F1 scores.
 * **Test**: The AUC of the univariate model for each of the top 5 features is compared against this null distribution to determine if it exceeds chance.
* **Correction**: **Benjamini-Hochberg (BH)** procedure applied to the set of p-values (2 model comparisons + 5 feature tests = 7 tests) to control False Discovery Rate (FDR) < 0.05.
* **Collinearity**: Structural features (e.g., Degree and In-Degree) are often correlated. The plan will report correlation matrices and acknowledge that independent effects cannot be claimed for definitionally related features.

### Power Analysis & Limitations
* **Sample Size**: Limited by the number of available CTU-13 scenarios and the [deferred] node cap.
* **Acknowledgement**: The study will explicitly state that statistical power is limited by the small number of scenarios (N=13 scenarios, subset used) and the subsampling. Results are **associational** (observational data) and do not claim causal intervention.

### Target AUC Threshold (SC-005)
* **Definition**: The predictive power of identified structural patterns is measured against a pre-defined target AUC threshold of **0.75**. This threshold is based on typical benchmarks for network anomaly detection in literature (cited in references).
* **Measurement**: If the AUC of the identified patterns (via univariate models or GNN) exceeds 0.75, the criterion is met.

## Decision Rationale: CPU-Only Constraint
The plan strictly adheres to the **CPU-only** constraint (2 vCPU, 7GB RAM).
* **Why**: Deep learning libraries like PyTorch can run on CPU. While slower, a 2-layer GCN on [deferred] nodes is trivial for modern CPUs.
* **Avoided**: 8-bit quantization, mixed-precision training, and large LLM inference. These are unnecessary for this scale and would introduce complexity or CUDA dependencies that break the CI runner.
* **Fallback**: If training time exceeds 4 hours (leaving 2h buffer for analysis), the system will reduce `n_estimators` in baselines or reduce GCN hidden dimensions.

## GNN Attribution Strategy (FR-007)
* **Method**: **Integrated Gradients** will be applied to the GCN output to attribute the prediction to input features.
* **Mapping to Structural Proxies**: Since the GCN input features are structural (degree, centrality), the attribution weights will be directly correlated with these features. The top contributing features identified by Integrated Gradients will be mapped back to the specific structural patterns (e.g., "high out-degree" or "high betweenness") to explain *why* the GNN classified a node as anomalous.
* **Distinction**: This is distinct from Random Forest feature importance, as it captures the contribution of features within the context of the message-passing mechanism.
