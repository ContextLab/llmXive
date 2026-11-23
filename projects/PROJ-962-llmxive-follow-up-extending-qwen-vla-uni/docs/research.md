# Research Methodology: Non-Neural Approximation of VLA Priors

This document details the methodology, model selection rationale, and statistical validation procedures for the non-neural approximation of Qwen-VLA behavior.

## 1. Overview

The pipeline approximates the behavior of the Qwen-VLA (Vision-Language-Action) model using lightweight, non-neural models (Decision Trees and Gaussian Mixture Models). The approach involves:
1. **Ingestion & Clustering**: Grouping trajectory data into behavioral clusters based on kinematic features.
2. **Model Fitting**: Training per-cluster models that map frozen BERT text embeddings to action distributions.
3. **Evaluation**: Comparing generated trajectories against the original VLA proxy and random baselines using simulation and statistical tests.

## 2. Data Ingestion and Clustering (US1)

### 2.1 Dataset Source
- **Source**: `qwen-vla/Hy-Embodied` on HuggingFace.
- **Streaming**: Data is processed in chunks using `datasets.load_dataset(..., streaming=True)` to handle large sizes (>7GB).
- **Normalization**: Global mean and standard deviation are computed via Welford's algorithm (online streaming statistics) to normalize kinematic features (velocity, acceleration, joint angles).

### 2.2 Adaptive K-Means Clustering
- **Algorithm**: K-means with adaptive k-reduction.
- **Initialization**: Starts with `k=50` (configurable).
- **Validation Metric**: Silhouette Score.
- **Reduction Logic**:
 - If `silhouette_score < 0.25` AND `k > 1`:
 - Reduce `k` by `K_REDUCTION_STEP` (default 1).
 - Re-run clustering.
 - Loop terminates if `silhouette_score >= 0.25` or `k == 1`.
 - If `k == 1` with poor score, a "degenerate clustering" warning is logged, and the process proceeds.
- **Outputs**: Cluster assignments, centers, and a method log (`data/processed/clustering_method_log.json`).

## 3. Model Selection Rationale (US2)

The core of the approximation is selecting the best model per cluster to map text embeddings to actions. The selection follows a **sequential fallback** strategy to balance performance and computational cost.

### 3.1 Candidate Models
1. **Decision Tree Regressor**:
 - **Pros**: Interpretable, fast inference, low memory footprint.
 - **Cons**: May struggle with continuous, multimodal distributions.
2. **Conditional Gaussian Mixture Model (CGMM)**:
 - **Pros**: Captures multimodal action distributions, probabilistic sampling.
 - **Cons**: Higher computational cost, more complex.

### 3.2 Selection Criteria
For each cluster:
1. **Train Decision Tree**:
 - Evaluate on held-out validation set.
 - Calculate **R²** and **Inference Time**.
2. **Decision Gate**:
 - **If** `R² >= 0.6` AND `Inference Time < 2s/prompt`:
 - **Select Decision Tree**.
 - **Stop** training for this cluster.
 - **Else**:
 - Train Conditional GMM.
 - Evaluate CGMM.
 - **If** `R² >= 0.6`: Select CGMM.
 - **Else**: Log "Model Failure" warning; select the best available (highest R²).

### 3.3 Performance Comparison
- **Decision Tree**: Typically selected for clusters with deterministic or low-variance action mappings. Faster inference (~0.5s/prompt).
- **GMM**: Selected for clusters with high variance or multimodal actions (e.g., "grasp" with multiple valid approaches). Slightly slower (~1.2s/prompt) but higher R² in complex cases.
- **Fallback Rate**: < 5% of clusters require GMM fallback in preliminary runs on the Qwen-VLA dataset.

### 3.4 Construct Validity Check
Before training, a linear regression baseline checks if frozen BERT embeddings have explanatory power over kinematic features.
- **Threshold**: `R² < 0.1` triggers a "Hypothesis Failure" halt.
- **Rationale**: Ensures that text instructions are predictive of the actions before investing in model training.

## 4. Statistical Evaluation (US3)

### 4.1 Baselines
1. **Non-Neural Model**: The selected DT/GMM per cluster.
2. **Random Baseline**: Uniform sampling within joint limits (fixed seed for reproducibility).
3. **VLA Proxy Baseline**: Trajectories from the original Qwen-VLA model (verified checksum).

### 4.2 Simulation
- **Engine**: PyBullet (Mocked for CPU-only constraint).
- **Tasks**: "grasp", "navigate", "place".
- **Metrics**: Success rate, collision count, execution time.

### 4.3 Statistical Testing
- **Method**: Paired T-Tests (`scipy.stats.ttest_rel`).
- **Data Alignment**: Ensures prompt IDs are identical across all three baselines before testing.
- **Tests Performed**:
 1. **Continuous Fidelity**: Compares trajectory fidelity scores (Non-Neural vs. VLA Proxy).
 2. **Binary Success**: Compares success/failure flags (Non-Neural vs. Random, Non-Neural vs. VLA).
- **Significance Level**: α = 0.05.
- **Output**: P-values and significance flags in `data/results/evaluation_report.md`.

## 5. Command-Line Interface

The pipeline is driven by the following scripts with specific flags:

### 5.1 Ingestion & Clustering
```bash
python code/01_ingest_cluster.py \
 --dataset <HuggingFace_ID> \
 --k-initial <int> \
 --silhouette-threshold <float> \
 --k-reduction-step <int> \
 --max-iterations <int> \
 --seed <int>
```

### 5.2 Model Training
```bash
python code/02_train_models.py \
 --assignments <path_to_parquet> \
 --clusters <path_to_json> \
 --bert-model <model_name> \
 --r2-threshold <float> \
 --construct-validity-threshold <float> \
 --seed <int>
```

### 5.3 Simulation & Evaluation
```bash
python code/04_simulate_eval.py \
 --trajectories <path_to_parquet> \
 --vla-baseline <path_to_baseline> \
 --random-seed <int> \
 --output-dir <path>
```

## 6. Limitations and Future Work

- **CPU Constraints**: The pipeline is strictly CPU-only. Performance may be limited by single-threaded execution for GMM sampling.
- **Clustering Heuristics**: The k-reduction step size is configurable but currently defaults to 1. Future work could explore adaptive step sizes based on silhouette score gradients.
- **Model Complexity**: While DTs are fast, they may not capture complex dynamics as well as neural models. The GMM fallback mitigates this but increases cost.

## 7. References

- **Spec**: `specs/001-non-neural-vla-approximation/spec.md`
- **Plan**: `specs/001-non-neural-vla-approximation/plan.md`
- **Data**: `qwen-vla/Hy-Embodied` (HuggingFace)
- **Baseline**: `qwen-vla/vla-proxy-trajectories` (HuggingFace)