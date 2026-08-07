# Research Methodology: Non-Neural Approximation of VLA Priors

## Overview

This document outlines the methodology, selection rationale, and execution parameters for the **llmXive** pipeline (Project: `PROJ-962-llmxive-follow-up-extending-qwen-vla-uni`). The pipeline implements a non-neural approximation of Vision-Language-Action (VLA) priors, specifically targeting CPU-only execution while maintaining statistical validity against a VLA proxy baseline.

## 1. Dataset Ingestion and Clustering (US1)

### Data Source
- **Dataset**: `Qwen/Qwen-VLA` (HuggingFace)
- **Mode**: Streaming (`streaming=True`) to handle datasets >7GB without full RAM load.
- **Features**: Text instructions paired with high-dimensional action sequences.

### Clustering Strategy (FR-002a)
The pipeline employs an **Adaptive K-Reduction Loop** to determine the optimal number of behavioral clusters:
1. **Initialization**: Start with $k_{max} = 50$.
2. **Metric**: Silhouette Score (measures cluster cohesion and separation).
3. **Loop**:
 - If Silhouette Score $< 0.25$ AND $k > 1$:
 - Decrement $k$ by 1.
 - Re-run K-means clustering.
 - Else: Break loop.
4. **Fallback**: If $k=1$ is reached with a score $< 0.25$, the system logs a "degenerate clustering" warning. As per **FR-002a**, no Hierarchical Agglomerative Clustering (HAC) fallback is triggered unless explicitly configured as a secondary mitigation (Task T016b).
5. **Output**: Cluster assignments saved to `data/processed/assignments.parquet` and metadata to `data/results/clustering_method_log.json`.

## 2. Non-Neural Model Selection (US2)

### Model Candidates
For each behavioral cluster, the pipeline fits a lightweight probabilistic model mapping frozen BERT text embeddings to action distributions. The candidates are:
1. **Decision Tree (DT) Regressor**: Fast inference, interpretable, but limited by axis-aligned splits.
2. **Conditional Gaussian Mixture Model (CGMM)**: Captures multi-modal action distributions, higher computational cost.

### Selection Rationale (Sequential Fallback Logic)
To satisfy the CPU-only constraint (SC-003) and efficiency requirements, the pipeline uses a **Sequential Model Training** strategy (Task T022):
1. **Train Decision Tree First**:
 - Evaluate on held-out validation set.
 - **Criteria**: $R^2 \geq 0.6$ AND Inference Time $< 2.0$s/prompt.
 - **Action**: If criteria met, **select DT** and skip CGMM training for this cluster.
2. **Fallback to CGMM**:
 - Triggered only if DT fails the criteria.
 - Train CGMM and evaluate.
 - **Action**: If CGMM $R^2 \geq 0.6$, **select CGMM**.
3. **Failure Handling**: If neither model meets the $R^2 \geq 0.6$ threshold, the cluster is flagged with a "Model Failure" warning, and the model with the highest $R^2$ is selected as a best-effort approximation.

**Rationale**: This approach prioritizes the lighter-weight Decision Tree, only incurring the computational cost of CGMM training when necessary to achieve the required predictive fidelity. This minimizes aggregate training time and memory footprint on CPU hardware.

## 3. Statistical Evaluation (US3)

### Baselines
1. **VLA Proxy**: Ground-truth action sequences from the `Qwen/Qwen-VLA` dataset (Task T032d). Serves as the "gold standard" without requiring GPU inference.
2. **Random Baseline**: Uniform sampling within joint limits (Task T032).
3. **Non-Neural Model**: The output of the selected DT/CGMM pipeline.

### Statistical Test
- **Method**: **Paired T-Tests** (`scipy.stats.ttest_rel`).
- **Comparison**: Success rates (binary: success/failure) of Non-Neural vs. Random vs. VLA Proxy.
- **Alignment**: Strict verification that prompt IDs are identical across all three baselines before testing (Task T035a).
- **Output**: P-values and confidence intervals saved to `data/results/evaluation_report.md`.

## 4. Execution Instructions

The pipeline is designed for sequential execution. Ensure all prerequisites (Python 3.9+, dependencies in `requirements.txt`) are installed.

### Command-Line Flags

| Flag | Description | Default |
|:--- |:--- |:--- |
| `--seed` | Global random seed for reproducibility | `42` |
| `--max-k` | Maximum clusters for K-means | `50` |
| `--silhouette-threshold` | Minimum silhouette score to stop k-reduction | `0.25` |
| `--cpu-only` | Force CPU execution (enforced by default) | `True` |
| `--baseline` | Baseline type for simulation (`vla_proxy`, `random`, `all`) | `all` |

### Pipeline Steps

1. **Ingestion & Clustering**:
 ```bash
 python code/01_ingest_cluster.py --seed 42 --max-k 50
 ```
 *Outputs*: `data/processed/clusters.json`, `data/processed/assignments.parquet`

2. **Embedding Generation**:
 ```bash
 python code/02_train_models.py --stage embeddings
 ```
 *Outputs*: `data/processed/train_embeddings.parquet`

3. **Model Training (Sequential Selection)**:
 ```bash
 python code/02_train_models.py --stage train
 ```
 *Outputs*: `artifacts/models/cluster_{id}_selected.pkl`, `data/results/model_selection_decision.md`

4. **Inference**:
 ```bash
 python code/03_inference.py --prompt "grasp the red cup"
 ```
 *Outputs*: Trajectory arrays (stdout or `data/results/inference_output.parquet`)

5. **Simulation & Evaluation**:
 ```bash
 python code/04_simulate_eval.py --baseline all
 ```
 *Outputs*: `data/results/simulation_logs.csv`, `data/results/evaluation_report.md`

## 5. Known Limitations

- **CPU Constraints**: All BERT embeddings and model training are forced to CPU. Large-scale parallelism is not utilized.
- **Clustering Degeneracy**: If the data distribution is unimodal, the adaptive k-reduction may result in $k=1$, limiting behavioral segmentation.
- **VLA Proxy**: Uses ground-truth data as a proxy; does not account for inference-time stochasticity of the original VLA model.