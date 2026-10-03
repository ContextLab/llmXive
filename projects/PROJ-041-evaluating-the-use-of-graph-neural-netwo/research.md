# Research Plan: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic

**Project ID**: PROJ-041
**Date**: 2023-10-27
**Version**: 1.0

## 1. Objective
To evaluate whether Graph Neural Networks (GNNs) provide superior anomaly detection performance compared to traditional feature-engineered baselines (Random Forest, XGBoost) on network traffic data, specifically focusing on the ability to capture topological patterns indicative of malicious activity.

## 2. Success Criteria
- **Primary Metric**: Area Under the Receiver Operating Characteristic Curve (AUC-ROC).
- **Target Threshold**: AUC ≥ **0.75**.
- **Statistical Significance**: Performance differences must be validated using Permutation Tests (due to small sample size N < 13) followed by Benjamini-Hochberg correction for multiple comparisons (FDR < 0.05).
- **Distinct Patterns**: A structural pattern is considered "distinct" only if the 95% Confidence Interval for the rank difference between GNN and RF feature importances excludes zero.

## 3. Dataset Strategy
- **Primary Source**: CTU-13 Dataset (Scenario 1) and NF-BoT-IoT Dataset.
- **Fallback**: If primary sources are inaccessible, use the verified alternative dataset defined in `state/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo.yaml` (see T007c).
- **Data Integrity**: All data must be fetched from real sources; synthetic data is strictly prohibited. Checksums must be validated upon download.

## 4. Methodology

### 4.1 Data Preprocessing
- **Temporal Holdout Split**:
 - **Train Set**: First **80%** of flows (chronologically).
 - **Test Set**: Remaining **20%** of flows.
 - **Constraint**: Graph construction must occur **only** on the Train set to prevent temporal leakage.
- **Graph Construction**:
 - Nodes: IP addresses.
 - Edges: Directed flows between IPs.
 - Edge Weights: Packet counts.
 - Node Features: Degree, Betweenness Centrality, Clustering Coefficient, PageRank.
- **Subsampling**:
 - If node count > 5,000, extract Largest Connected Component (LCC).
 - If LCC > 5,000, apply degree-based subsampling (retain top nodes by degree centrality).

### 4.2 Model Training
- **GNN Model**: Multi-layer Graph Convolutional Network (GCN) trained on CPU.
 - Early Stopping: Patience=5, Min Delta=1e-4.
- **Baselines**: Random Forest and XGBoost using structural features derived from the Train graph.

### 4.3 Evaluation & Statistical Analysis
- **Metrics**: Precision, Recall, F1-Score, AUC-ROC.
- **Hypothesis Set**:
 1. GCN vs. Random Forest
 2. GCN vs. XGBoost
 3-7. Top 5 structural features vs. null baseline (via Permutation Test).
- **Statistical Test**: Permutation Tests (Edgington, 1980) for small N.
- **Correction**: Benjamini-Hochberg procedure to control False Discovery Rate (FDR).

## 5. Plan Deviations
- **Deviation 1 (Statistical Power)**: The original spec (FR-006) requested Wilcoxon signed-rank tests. However, given the expected sample size (N < 13 scenarios), Wilcoxon lacks sufficient power. This plan adopts **Permutation Tests** as a more robust alternative for small samples, as documented in T030a.
- **Deviation 2 (Subsampling)**: If LCC extraction results in a graph > 5,000 nodes, a degree-based subsampling heuristic is authorized (T008c) to preserve anomaly hubs that might be lost in a strict LCC-only approach.

## 6. Configuration
- **Target AUC**: 0.75 (defined in `code/config.yaml`).
- **Temporal Split Ratio**: 0.8 (Train) / 0.2 (Test) (defined in `code/config.yaml`).
- **Random Seed**: 42 (defined in `code/config.yaml`).
- **Memory Limit**: 7000 MB (defined in `code/config.yaml`).

## 7. Dependencies
- **T007d**: Validates this research plan and configures `target_auc` in `code/config.yaml`.
- **T009**: Implements the temporal holdout split based on the ratios defined here.
- **T007a/T007b**: Data acquisition.
- **T007c**: Fallback mechanism if data acquisition fails.

## 8. References
- CTU-13 Dataset: https://www.stratosphereips.org/datasets-ctu13
- NF-BoT-IoT Dataset:
- Edgington, E. S. (1980). *Randomization Tests*. Marcel Dekker.
- Benjamini, Y., & Hochberg, Y. (1995). Controlling the False Discovery Rate. *Journal of the Royal Statistical Society*.