# Research Methodology: Non-Neural Approximation of VLA Priors

## Overview
This document outlines the methodology used to approximate Qwen-VLA behaviors using non-neural models (Decision Trees and Conditional Gaussian Mixture Models) on a CPU-only architecture.

## Data Ingestion and Clustering
1. **Dataset**: Qwen-VLA/Hy-Embodied dataset was ingested via HuggingFace `datasets` library using streaming to manage memory constraints.
2. **Feature Extraction**: Kinematic features (velocity, acceleration, joint angles) were extracted and normalized.
3. **Clustering Strategy**:
 - Initial clustering performed using K-Means with `k=50`.
 - **Heuristic**: If silhouette score < 0.25 OR Calinski-Harabasz < 100, `k` is reduced by `k_reduction_step_size` (default 5) and re-clustering is attempted.
 - **Fallback**: If K-Means fails to converge to valid metrics even at `k=1`, Hierarchical Agglomerative Clustering (HAC) with Ward linkage is used.
4. **Coverage**: Clustering coverage is validated to ensure ≥ 98% of samples are assigned.

## Model Training and Selection
1. **Embeddings**: Frozen BERT (`bert-base-uncased`) encodings are generated for text instructions.
2. **Candidate Models**:
 - **Decision Tree (DT)**: Regressor mapping embeddings to action sequences.
 - **Conditional GMM (CGMM)**: Probabilistic model capturing action variance conditioned on embeddings.
3. **Selection Rationale (DT vs CGMM)**:
 - Both models are trained per cluster.
 - **Selection Criteria**: The model with the **highest R²** on the held-out validation set is selected, provided inference time < 2s per prompt.
 - **Efficiency**: Decision Trees generally offer faster inference and lower memory footprint, while CGMMs provide better uncertainty estimation for complex, multi-modal action distributions.
 - **Final Decision**: The pipeline selects the best-performing model per cluster dynamically based on the R² metric.

## Evaluation
1. **Simulation**: Trajectories are executed in a PyBullet environment.
2. **Baselines**:
 - **Random**: Uniform sampling within joint limits.
 - **VLA Proxy**: A CPU-compatible proxy model approximating the original VLA.
3. **Statistical Analysis**: Paired T-Tests are performed on success rates to determine statistical significance of improvements over baselines.
4. **Fidelity**: Trajectory fidelity is measured as the percentage of kinematic features within an error margin of the VLA proxy.

## Command Line Interface
The pipeline is orchestrated via `code/09_run_final_validation.py`.

**Full Pipeline Execution**:
```bash
python code/09_run_final_validation.py --seed 42
```

**Individual Stage Execution**:
- Ingestion: `python code/01_ingest.py`
- Clustering: `python code/02_cluster.py`
- Training: `python code/03_train.py`
- Inference: `python code/04_inference.py`
- Simulation: `python code/05_simulate.py`
- Evaluation: `python code/06_evaluate.py`

**Low Coverage Handling**:
To allow execution even if clustering coverage drops below 98% (not recommended for final validation):
```bash
python code/01_ingest_cluster.py --allow-low-coverage
```
