# Research Methodology: Non-Neural Approximation of VLA Priors

## Overview

This document details the methodology used to approximate Vision-Language-Action (VLA) priors using non-neural statistical models. The approach replaces heavy neural inference with efficient clustering and conditional probability modeling, enabling CPU-only execution while maintaining trajectory fidelity.

## 1. Data Ingestion and Preprocessing

### Source
The primary data source is the **Qwen-VLA/Hy-Embodied** dataset from HuggingFace.
- **Constraint**: Real data only. No synthetic fallbacks are permitted. If the dataset cannot be downloaded, the pipeline fails loudly.
- **Streaming**: To accommodate limited memory (~7GB RAM), the ingestion process uses `datasets.load_dataset(..., streaming=True)` to process data in chunks.

### Kinematic Feature Extraction
Raw action sequences are transformed into kinematic features:
- **Velocity**: First-order derivative of joint positions.
- **Acceleration**: Second-order derivative.
- **Joint Angles**: Normalized to physical bounds.
- **Normalization**: Features are normalized using Min-Max scaling within physical limits to ensure stability during clustering.

## 2. Trajectory Clustering (US1)

### Algorithm: K-Means
Trajectories are clustered into behavioral groups using K-means clustering.
- **Initial K**: 50 clusters.
- **Validation**: Silhouette Score is calculated for each run.
- **Adaptive K-Reduction**: If the silhouette score is below 0.25, the algorithm reduces `k` by `k_reduction_step_size` (from `config.py`) and retries, up to `max_k_reduction_attempts`.
- **Output**: Cluster assignments and centroids saved to `data/processed/clusters.json`.

## 3. Non-Neural Model Fitting (US2)

### Text Embedding
Frozen **BERT-base-uncased** is used to encode text instructions into fixed-dimensional vectors. This step is CPU-only and performed once.

### Model Architectures
Two distinct non-neural models are fitted per cluster to map BERT embeddings to action distributions:

#### A. Conditional Gaussian Mixture Models (CGMM)
- **Purpose**: Model the conditional distribution of actions given text embeddings.
- **Implementation**: Fits a GMM where the mean and covariance are conditioned on the input embedding (or uses a mixture of regressors).
- **Validation**: Requires $R^2 \ge 0.6$ on held-out data.
- **Artifact**: `artifacts/models/cgmm_{cluster_id}.pkl`

#### B. Decision Tree Regressors
- **Purpose**: Provide a deterministic, interpretable baseline for action prediction.
- **Implementation**: Fits a Decision Tree Regressor per cluster.
- **Validation**: Requires $R^2 \ge 0.6$.
- **Artifact**: `artifacts/models/dt_{cluster_id}.pkl`

*Note: Both models are required to satisfy the project's functional requirements (FR-003).*

## 4. Inference and Simulation (US2 & US3)

### Inference Pipeline
1. **Cluster Selection**: For a new prompt, the nearest cluster is identified via BERT embedding distance.
2. **Trajectory Sampling**: Actions are sampled from the selected cluster's CGMM or predicted via the Decision Tree.
3. **OOD Handling**: If the prompt is outside the cluster distribution, the nearest cluster is used with a "low-confidence" flag.

### Simulation Engine
Trajectories are executed in **PyBullet** (CPU-only).
- **Tasks**: Grasp, Navigate, Place.
- **Error Handling**: Kinematic violations and collisions are caught and logged, not crashing the pipeline.
- **Baseline**: A heuristic baseline (uniform sampling + smoothing) is generated if the VLA proxy baseline is missing.

## 5. Statistical Evaluation (US3)

To rigorously compare the non-neural models against baselines (Random and VLA Proxy), two statistical tests are employed:

### A. McNemar's Test
- **Objective**: Compare binary success rates (Success/Failure) between pairs of models.
- **Application**: Non-Neural vs. Random, Non-Neural vs. VLA Proxy.
- **Output**: P-values and confidence intervals indicating statistical significance of the difference in success rates.

### B. Paired T-Tests
- **Objective**: Compare continuous performance metrics (e.g., success rate over multiple runs, trajectory fidelity).
- **Application**: Paired comparison of non-neural models against baselines.
- **Output**: P-values and confidence intervals.

*Note: Both tests are required to satisfy FR-006.*

## 6. Fidelity and Complexity Metrics

- **Trajectory Fidelity**: Percentage of kinematic features within a defined error margin of the VLA proxy.
- **Complexity Reduction Factor**: Ratio of computational cost (parameters/FLOPs) between the original VLA and the non-neural approximation.

## References
- Qwen-VLA/Hy-Embodied Dataset Documentation.
- Scikit-learn Documentation: K-Means, GMM, Decision Trees.
- PyBullet Physics Simulator Documentation.
- Statistical Methods for Binary and Continuous Data (McNemar, Student's t-test).