# Research Methodology: Non-Neural Approximation of VLA Priors

## Abstract
This document details the methodology, selection rationale, and validation procedures for the non-neural approximation of VLA priors. The goal is to approximate VLA behavior using lightweight, interpretable models (Decision Trees, GMMs) without GPU dependency, while maintaining statistical validity against a VLA proxy baseline.

## 1. Dataset Ingestion and Clustering (US1)

### 1.1 Data Source
The primary data source is the **Qwen-VLA** dataset hosted on HuggingFace (`Qwen/Qwen-VLA`).
- **Loading Strategy**: Streaming (`datasets.load_dataset(..., streaming=True)`) to handle datasets >7GB within memory constraints.
- **Validation**: Strict checksumming and schema validation via `code/utils/validation.py`. No synthetic fallbacks are permitted; fetch failures raise `DataFetchError`.

### 1.2 Kinematic Feature Extraction
Features extracted include:
- Velocity and acceleration vectors.
- Joint angles normalized within physical bounds.
- **Normalization**: Z-score normalization applied per feature dimension to ensure scale invariance.

### 1.3 Adaptive Clustering Strategy
The clustering pipeline implements a hierarchical fallback mechanism:
1. **Initial K-Means**: Starts with `k=50`.
2. **Silhouette Validation**: If `silhouette_score < 0.25`, `k` is reduced by a configurable step (default 5).
3. **HAC Fallback**: If `k` reaches 1 with poor scores, or if K-means manifold fit is poor, the system switches to Hierarchical Agglomerative Clustering (Ward linkage).
4. **Output**: Final `k`, silhouette score, and method used are logged to `data/results/clustering_method_log.json`.

## 2. Model Selection and Training (US2)

### 2.1 Construct Validity Gate
Before training, a linear regression baseline is used to check the correlation between frozen BERT embeddings and kinematic features.
- **Threshold**: If `R² < 0.1`, the pipeline halts and writes a "Hypothesis Failure" report.
- **Rationale**: Ensures text instructions contain sufficient signal for action prediction.

### 2.2 Sequential Model Selection (DT vs GMM)
Per cluster, models are trained sequentially to minimize compute:
1. **Decision Tree (DT)**: Trained first.
 - **Selection Criteria**: `R² >= 0.6` AND `inference_time < 2s`.
2. **Conditional GMM (CGMM)**: Trained only if DT fails criteria.
 - **Selection Criteria**: `R² >= 0.6`.
3. **Fallback**: If neither meets criteria, the model with the highest R² is selected, and a warning is logged.

**Selection Rationale**:
- **Decision Trees** are preferred for their interpretability and speed on structured kinematic data.
- **GMMs** are used for clusters with high variance or non-linear boundaries where DTs underfit.
- The sequential approach ensures the cheapest viable model is selected, adhering to CPU constraints.

### 2.3 CPU-Only Enforcement
All BERT encoding and model training are forced to `torch.device("cpu")`.
- **Verification**: Pre-flight checks raise `RuntimeError` if a GPU is detected.

## 3. Evaluation and Statistical Validation (US3)

### 3.1 Baselines
- **VLA Proxy**: Pre-computed trajectories from a verified source (`data/processed/vla_proxy_baseline.parquet`).
- **Random Baseline**: Uniform sampling within joint limits (seeded for reproducibility).

### 3.2 Simulation
Trajectories are executed in PyBullet.
- **Error Handling**: Kinematic violations are caught and recorded as "failures" without crashing the pipeline.
- **Metrics**: Success rate, collision count, and execution time.

### 3.3 Statistical Testing
- **Paired T-Tests**: Used to compare success rates and fidelity metrics between Non-Neural, Random, and VLA Proxy baselines.
- **Data Alignment**: Prompt IDs are strictly aligned across all baselines to ensure valid pairing.
- **Output**: P-values and confidence intervals are reported in `data/results/evaluation_report.md`.

## 4. Complexity Reduction
The pipeline calculates the **Complexity Reduction Factor** as the ratio of parameters/FLOPs between the original VLA proxy and the non-neural model (DT/GMM). This metric quantifies the efficiency gain of the approximation.

## 5. Constraints and Limitations
- **CPU-Only**: No GPU acceleration is used. This limits the scale of BERT embeddings but ensures reproducibility on standard hardware.
- **Memory**: Streaming is used to stay under ~7GB RAM.
- **Clustering**: Degenerate datasets may result in `k=1` (single cluster), which is logged but allowed to proceed per research protocol.

## 6. Reproducibility
- **Seeds**: Global seeds are set via `code/utils/seeds.py`.
- **Artifacts**: All intermediate files (embeddings, assignments, models) are saved with checksums.
- **Versioning**: Dependency versions are pinned in `requirements.txt`.
