# Research Methodology: Non-Neural Approximation of VLA Priors

This document outlines the methodology, model selection rationale, and statistical validation procedures used in the llmXive non-neural VLA approximation project.

## Overview

The project aims to approximate the behavior of the Qwen-VLA (Vision-Language-Action) model using lightweight, non-neural models (Decision Trees and Conditional Gaussian Mixture Models) running on CPU-only hardware. The pipeline ingests trajectory data, clusters behavioral modes, and fits per-cluster models to map text instructions to action sequences.

## Data Ingestion and Clustering (User Story 1)

### Dataset Source
The primary data source is the `Qwen/Qwen-VLA` dataset from HuggingFace.
- **Loading Strategy**: Streaming mode (`datasets.load_dataset(..., streaming=True)`) is used to handle datasets >7GB without exhausting RAM.
- **Validation**: The pipeline fails loudly if the dataset cannot be fetched; no synthetic fallback is permitted.

### Feature Extraction
Kinematic features (velocity, acceleration, joint angles) are extracted from action sequences using `code/utils/kinematics.py`. Features are normalized to physical bounds.

### Clustering Strategy
An adaptive clustering approach is employed to identify behavioral modes:
1. **Initial K-Means**: Run with `k=50` (configurable).
2. **Silhouette Validation**: If the silhouette score < 0.25, `k` is reduced by a step size (default 5) and K-Means is re-run.
3. **HAC Fallback**: If `k` reaches 1 with poor silhouette, or if K-Means diagnostics indicate poor manifold fit, the pipeline switches to Hierarchical Agglomerative Clustering (HAC) with Ward linkage.
4. **Coverage Check**: The pipeline verifies ≥98% sample coverage; if not met, a warning is logged but the pipeline proceeds.

## Model Training and Selection (User Story 2)

### Embedding Generation
Frozen BERT embeddings (`bert-base-uncased`) are generated for text instructions. CPU-only execution is enforced via `torch.device("cpu")`.

### Construct Validity Gate
Before training, a linear regression baseline is used to check the correlation between BERT embeddings and kinematic features.
- **Threshold**: If R² < 0.1, the pipeline halts and writes a "Hypothesis Failure" report.

### Sequential Model Training (Decision Tree vs. GMM)
For each cluster, models are trained sequentially to minimize compute cost:
1. **Decision Tree (DT)**: Trained first.
 - **Selection Criteria**: If R² ≥ 0.6 AND inference time < 2s/prompt, the DT is selected.
2. **Conditional Gaussian Mixture Model (CGMM)**: Trained only if the DT fails the criteria.
 - **Selection Criteria**: If R² ≥ 0.6, the CGMM is selected.
3. **Fallback**: If neither meets the threshold, the model with the highest R² is selected, and a "Model Failure" warning is logged.

### Selection Rationale (DT vs. GMM)
The choice between Decision Trees and GMMs is driven by the trade-off between interpretability, inference speed, and distributional fidelity:
- **Decision Trees**:
 - **Pros**: Extremely fast inference, highly interpretable, robust to outliers.
 - **Cons**: Struggles with continuous, multimodal distributions (common in robotic actions).
 - **Selection**: Preferred when the action distribution within a cluster is unimodal or when the mapping from text to action is relatively discrete.
- **Gaussian Mixture Models (GMM)**:
 - **Pros**: Capable of modeling multimodal distributions, provides probabilistic sampling.
 - **Cons**: Slower inference, more complex, requires more data to fit reliably.
 - **Selection**: Chosen when the DT fails to capture the variance in the action space (R² < 0.6) or when the cluster exhibits clear multimodality.

The final model selection for each cluster is documented in `artifacts/models/cluster_{id}_selection.json` and aggregated in `data/results/model_selection_decision.md`.

## Inference and Simulation (User Story 3)

### Inference Pipeline
For a new prompt:
1. Embed the text using BERT.
2. Find the nearest cluster based on embedding distance.
3. Sample a trajectory from the selected model (DT or GMM).
4. Apply OOD handling: If the prompt is far from the cluster center, default to the nearest cluster and flag as "low-confidence".

### Simulation Environment
Trajectories are executed in PyBullet.
- **Tasks**: "grasp", "navigate", "place".
- **Error Handling**: Simulation errors (joint limit violations, collisions) are caught and recorded as "failure" without crashing the pipeline.

### Baselines
1. **Random Baseline**: Uniform sampling within joint limits.
2. **VLA Proxy Baseline**: Pre-computed trajectories from the original VLA model (fetched from a verified source).

## Statistical Validation

### Paired T-Tests
To validate the non-neural model against baselines, paired t-tests are performed on:
1. **Binary Success Rates**: Comparing success/failure flags across Non-Neural, Random, and VLA Proxy.
2. **Continuous Fidelity Metrics**: Comparing the percentage of kinematic features within the error margin of the VLA proxy.

**Data Alignment**: The prompt IDs used for all three baselines are strictly aligned to ensure the "paired" nature of the test.

### Metrics
- **Success Rate**: Percentage of tasks completed without collision.
- **Fidelity**: Percentage of kinematic features within a specified error margin of the VLA proxy.
- **Complexity Reduction Factor**: Ratio of parameters/FLOPs between the VLA proxy and the non-neural model.

## Command-Line Flags Reference

The following flags are used across the pipeline scripts:

### `code/01_ingest_cluster.py`
- `--dataset`: Dataset ID
- `--split`: Dataset split
- `--k_initial`: Initial cluster count
- `--silhouette_threshold`: Minimum silhouette score
- `--k_step`: Step size for k-reduction
- `--streaming`: Enable streaming

### `code/02_train_models.py`
- `--embeddings_path`: Path to embeddings
- `--clusters_path`: Path to cluster metadata
- `--r2_threshold`: Minimum R² for acceptance
- `--cpu_only`: Force CPU mode

### `code/03_inference.py`
- `--prompt`: Text instruction
- `--model_dir`: Path to models
- `--output_path`: Output trajectory file

### `code/04_simulate_eval.py`
- `--baseline_path`: VLA proxy baseline path
- `--tasks`: Task types
- `--seed`: Random seed

## Limitations and Future Work

- **CPU Constraints**: All models are restricted to CPU execution, limiting inference speed compared to GPU-accelerated neural models.
- **Clustering Heuristics**: The adaptive k-reduction loop relies on a fixed step size; dynamic step sizing could improve efficiency.
- **Data Coverage**: Degenerate datasets may result in low clustering coverage; the pipeline logs warnings but proceeds.

## References
- Plan: `specs/001-non-neural-vla-approximation/plan.md`
- Spec: `specs/001-non-neural-vla-approximation/spec.md`
- Data Model: `specs/001-non-neural-vla-approximation/data-model.md`