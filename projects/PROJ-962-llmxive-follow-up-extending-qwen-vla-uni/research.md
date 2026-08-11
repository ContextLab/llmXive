# Research Methodology: Non-Neural Approximation of VLA Priors

## Executive Summary
This document outlines the methodology used to approximate VLA (Vision-Language-Action) priors using non-neural, lightweight models. The approach focuses on clustering behavioral trajectories and fitting interpretable models (Decision Trees or Gaussian Mixture Models) to map text instructions to action sequences.

## 1. Dataset Ingestion and Clustering Strategy

### 1.1 Data Source
The primary dataset is **Qwen-VLA/Hy-Embodied**, accessed via HuggingFace. The dataset contains paired text instructions and action sequences for robotic manipulation tasks.

### 1.2 Kinematic Feature Extraction
From raw action sequences, we extract:
- **Velocity**: First derivative of joint positions
- **Acceleration**: Second derivative of joint positions
- **Joint Angles**: Normalized to [-1, 1] range

Normalization is performed using min-max scaling based on physical joint limits to ensure features are within valid bounds.

### 1.3 Adaptive Clustering (K-Means with Reduction)
We employ an adaptive K-means clustering strategy to determine the optimal number of behavioral clusters:

1. **Initialization**: Start with $k=50$ clusters.
2. **Silhouette Evaluation**: Calculate the silhouette score for the current $k$.
3. **Adaptive Reduction**:
 - If $score < 0.25$ and $k > 1$, reduce $k$ by 1.
 - Repeat steps 2-3 until $score \geq 0.25$ or $k=1$.
4. **Fallback**: If $k=1$ is reached with $score < 0.25$, log a "degenerate clustering" warning and proceed.
5. **HAC Fallback**: If K-means fails completely, Hierarchical Agglomerative Clustering (HAC) with Ward linkage is triggered as a robustness measure.

**Output**: Cluster assignments are saved to `data/processed/assignments.parquet` and cluster metadata to `data/processed/clusters.json`.

## 2. Model Selection Rationale (Decision Tree vs. GMM)

### 2.1 Sequential Model Training Strategy
To satisfy the CPU-only constraint (SC-003) and minimize computational cost, we implement a **sequential fallback** strategy for each cluster:

1. **Train Decision Tree (DT)**:
 - Input: BERT embeddings of text instructions.
 - Output: Action sequence parameters.
 - **Success Criteria**: $R^2 \geq 0.6$ AND inference time $< 2s$/prompt.
 - If criteria met: **Select DT** and stop training for this cluster.

2. **Train Conditional Gaussian Mixture Model (CGMM)** (Fallback):
 - Only trained if DT fails the success criteria.
 - **Success Criteria**: $R^2 \geq 0.6$.
 - If criteria met: **Select CGMM**.

3. **Failure Handling**:
 - If neither model meets $R^2 \geq 0.6$, the model with the highest $R^2$ is selected, and a "Model Failure" warning is logged.

### 2.2 Selection Rationale Summary
| Model | Pros | Cons | Selection Trigger |
|-------|------|------|-------------------|
| **Decision Tree** | Fast inference, interpretable, low memory | May struggle with complex, continuous distributions | Primary choice if $R^2 \geq 0.6$ |
| **GMM** | Handles multi-modal distributions, probabilistic | Slower inference, higher memory | Fallback if DT fails $R^2$ threshold |

**Outcome**: The final model for each cluster is recorded in `data/results/model_selection_decision.md` with the specific $R^2$ and inference time metrics that justified the selection.

## 3. Statistical Evaluation and Comparison

### 3.1 Baselines
Three baselines are compared:
1. **Non-Neural Model**: The pipeline's output (DT or CGMM).
2. **Random Baseline**: Uniform sampling within joint limits (reproducible via fixed seed).
3. **VLA Proxy**: Ground-truth action sequences from the dataset (serving as the "ideal" VLA output without GPU inference).

### 3.2 Paired T-Tests
To validate the hypothesis that the non-neural model outperforms the random baseline and approximates the VLA proxy, we perform **Paired T-Tests** on binary success rates.

- **Method**: `scipy.stats.ttest_rel`
- **Data Alignment**: Prompt IDs are strictly aligned across all three baselines to ensure valid pairing.
- **Metric**: Success rate (1 = success, 0 = failure/collision).
- **Significance**: $p < 0.05$ indicates a statistically significant difference.

### 3.3 Fidelity Metrics
Trajectory fidelity is calculated as the percentage of kinematic features within a specified error margin of the VLA proxy.

## 4. Execution Command-Line Flags

The pipeline is executed via the following command-line interface:

```bash
# Full Pipeline Execution
python code/01_ingest_cluster.py --dataset "Qwen/Qwen-VLA" --max-clusters 50
python code/02_train_models.py --bert-model "bert-base-uncased" --r2-threshold 0.6
python code/04_simulate_eval.py --mode evaluate --baseline data/processed/vla_proxy_baseline.parquet
```

**Key Flags**:
- `--dataset`: HuggingFace dataset ID.
- `--max-clusters`: Maximum K for clustering.
- `--silhouette-threshold`: Minimum silhouette score (default 0.25).
- `--r2-threshold`: Minimum R² for model selection (default 0.6).
- `--mode`: Execution mode (`generate_baseline` or `evaluate`).

## 5. Limitations and Future Work

### 5.1 CPU-Only Constraints
The pipeline is strictly CPU-bound. This limits:
- **BERT Embedding Speed**: Inference is slower compared to GPU-accelerated setups.
- **Model Training**: Large clusters may take longer to train, though the sequential fallback mitigates this.

### 5.2 Clustering Heuristics
The silhouette score threshold (0.25) is a heuristic. In cases of degenerate clustering ($k=1$), the HAC fallback provides robustness but may not capture complex manifold structures as effectively as neural methods.

### 5.3 Recommendations for Next Phase
- **Algorithmic Optimization**: Explore model pruning and quantization for CPU performance.
- **Feature Engineering**: Investigate additional kinematic features to improve clustering quality.
- **Data Augmentation**: Synthetic data generation (within physical bounds) to improve model robustness in sparse clusters.

## 6. References
- Qwen-VLA Dataset: https://huggingface.co/datasets/Qwen/Qwen-VLA
- Scikit-learn Documentation: Clustering and Model Selection
- SciPy Stats: Paired T-Test Implementation