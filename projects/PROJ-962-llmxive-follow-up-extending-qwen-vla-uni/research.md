# Research Methodology: Non-Neural Approximation of VLA Priors

## Introduction

This document details the research methodology, architectural decisions, and validation procedures for the non-neural approximation of Qwen-VLA policies. The primary goal is to evaluate whether lightweight, interpretable models (Decision Trees and Gaussian Mixture Models) can approximate the behavior of a large Vision-Language-Action model while adhering to strict CPU-only constraints.

## Pipeline Architecture

The pipeline is divided into three main user stories, each with independent verification gates.

### 1. Dataset Ingestion and Trajectory Clustering (US1)

**Objective**: Ingest the Qwen-VLA dataset, extract kinematic features, and cluster trajectories into behavioral groups.

**Methodology**:
- **Data Source**: `qwen-vla/Hy-Embodied` from HuggingFace.
- **Feature Extraction**: Velocity, acceleration, and joint angles are computed from action sequences.
- **Normalization**: Welford's algorithm is used for streaming normalization to handle datasets >7GB without loading them entirely into memory. [UNRESOLVED-CLAIM: c_db247847 — status=not_enough_info] Global mean and standard deviation are saved to `data/processed/streaming_stats.json`.
- **Clustering**: Adaptive K-means clustering is employed.
 - **Algorithm**: Starts with `k=50` and iteratively reduces `k` if the silhouette score is below `0.25`.
 - **Heuristic**: `k` is reduced by a configurable step size (default: 1) until the threshold is met or `k=1`.
 - **Fallback**: If `k=1` is reached with a low score, a "degenerate clustering" warning is logged, and the pipeline proceeds.
- **Outputs**: Cluster assignments, centers, and coverage metrics.

### 2. Non-Neural Model Fitting and Inference (US2)

**Objective**: Fit lightweight models to map text embeddings to action distributions for each cluster.

**Methodology**:
- **Embedding Generation**: Frozen `bert-base-uncased` is used to encode text instructions. [UNRESOLVED-CLAIM: c_709d2677 — status=not_enough_info] **CPU-only enforcement** is strict; the script exits if a GPU is detected.
- **Construct Validity Gate**: Before training, a linear regression baseline is used to check if BERT embeddings explain kinematic features (R² ≥ 0.1). If not, the pipeline halts with a "Hypothesis Failure" report.
- **Sequential Model Training**:
 1. **Decision Tree (DT)**: Trained first. Evaluated on held-out data.
 2. **Selection Criteria**: If DT achieves R² ≥ 0.6 and inference time < 2s/prompt, it is selected.
 3. **Fallback**: If DT fails, a Conditional Gaussian Mixture Model (CGMM) is trained.
 4. **Final Selection**: If CGMM meets thresholds, it is selected. Otherwise, the best available model (highest R²) is chosen with a warning.
- **Rationale for Sequential Training**: Training both models simultaneously for every cluster is computationally expensive. The sequential fallback minimizes cost and adheres to CPU constraints.

**Model Selection Rationale (DT vs GMM)**:
- **Decision Trees**: Preferred for their interpretability and speed. They perform well when the relationship between text embeddings and actions is piecewise constant or linear.
- **Gaussian Mixture Models**: Selected when the action distribution is multi-modal or continuous in a way that trees cannot capture efficiently.
- **Trade-off**: The pipeline prioritizes DT for efficiency. GMM is used only when DT fails to meet the R² threshold, ensuring a balance between performance and computational cost.

### 3. Simulation Evaluation and Statistical Comparison (US3)

**Objective**: Evaluate generated trajectories in PyBullet and compare against baselines using paired t-tests.

**Methodology**:
- **Baselines**:
 1. **Non-Neural Model**: The selected DT or GMM per cluster.
 2. **Random Baseline**: Uniform sampling within joint limits (reproducible via fixed seed).
 3. **VLA Proxy Baseline**: Downloaded from `qwen-vla/vla-proxy-trajectories` (verified via checksum).
- **Simulation**: Trajectories are executed in a Mock PyBullet environment. Errors (e.g., joint limit violations) are caught and recorded as failures without crashing the pipeline.
- **Statistical Testing**:
 - **Data Alignment**: Prompt IDs for all three baselines are verified to be identical.
 - **Paired T-Tests**: Performed on:
 1. **Continuous Fidelity Scores**: Comparing non-neural vs. random vs. VLA proxy.
 2. **Binary Success Rates**: Comparing success/failure flags.
 - **Significance**: Results are flagged based on α = 0.05.

## Constraints and Limitations

### CPU-Only Constraint
- **Enforcement**: All scripts explicitly force `torch.device("cpu")` and check for GPU availability.
- **Limitations**:
 - **Memory Bandwidth**: CPU memory bandwidth limits the speed of large matrix operations (e.g., BERT embeddings).
 - **Single-Threaded Performance**: Some operations (e.g., K-means) may not scale efficiently across CPU cores.
- **Optimizations**:
 - **Streaming**: Used for data ingestion and normalization to avoid OOM errors.
 - **Sequential Training**: Reduces redundant computation.
 - **Model Pruning/Quantization**: Recommended for future iterations to reduce model size and improve inference speed on CPU.

### Data Integrity
- **No Synthetic Fallbacks**: The pipeline fails loudly if real data cannot be fetched. No placeholder or synthetic data is used.
- **Verification**: All external baselines are verified via checksums.

## Command-Line Flags

The following flags are available across the pipeline scripts:

- `--dataset`: HuggingFace dataset ID (default: `qwen-vla/Hy-Embodied`).
- `--baseline`: Path to VLA Proxy baseline (default: `data/processed/vla_proxy_baseline.parquet`).
- `--output-dir`: Directory for output artifacts.
- `--seed`: Random seed for reproducibility (default: 42).
- `--silhouette-threshold`: Minimum silhouette score for clustering (default: 0.25).
- `--k-reduction-step`: Step size for k-reduction loop (default: 1).
- `--r2-threshold`: Minimum R² for model acceptance (default: 0.6).
- `--inference-time-threshold`: Maximum inference time per prompt (default: 2.0).

## Success Criteria Verification

- **SC-001 (Fidelity)**: Measured via continuous fidelity scores and paired t-tests.
- **SC-002 (Random Baseline)**: Implemented via uniform sampling with fixed seed.
- **SC-003 (CPU-Only)**: Enforced via runtime checks and `torch.device` settings.
- **SC-004 (Statistical Tests)**: Paired t-tests performed on aligned data.
- **SC-005 (Coverage)**: Clustering coverage ≥ 98% (warning if lower).

## Future Work

- **Algorithmic Optimizations**: Explore quantization (e.g., INT8) for Decision Trees and GMMs to reduce memory footprint.
- **Advanced Clustering**: Investigate hierarchical clustering or DBSCAN as alternatives to K-means.
- **Real-World Deployment**: Test the pipeline on physical robots to validate simulation results.

## References

- Qwen-VLA Documentation
- HuggingFace Datasets Library
- Scikit-Learn Documentation (K-means, Decision Trees, GMM)
- PyBullet Simulation Engine
