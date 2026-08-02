# Research Methodology: Non-Neural Approximation of VLA Priors

This document outlines the scientific methodology and statistical frameworks used in the llmXive project (PROJ-962) to approximate Vision-Language-Action (VLA) policies using non-neural methods.

## 1. Overview

The goal is to replace computationally expensive neural network inference with a lightweight, interpretable, and statistically rigorous pipeline. The approach involves:
1. **Behavioral Clustering**: Grouping similar action sequences.
2. **Conditional Modeling**: Fitting probabilistic models to clusters based on text instructions.
3. **Statistical Validation**: Rigorous comparison against neural baselines.

## 2. Data Ingestion and Feature Engineering

### 2.1 Dataset Source
The pipeline ingests the **Qwen-VLA/Hy-Embodied** dataset from HuggingFace.
- **Format**: Text instructions paired with high-dimensional action trajectories.
- **Preprocessing**: Text-action pairs are extracted, and missing data triggers a hard failure (no synthetic fallback).

### 2.2 Kinematic Feature Extraction
Raw action sequences are transformed into physically meaningful features:
- **Velocity**: First-order difference of joint positions.
- **Acceleration**: Second-order difference.
- **Normalization**: Features are normalized within physical bounds using min-max scaling derived from the dataset's statistical limits.

## 3. Behavioral Clustering (User Story 1)

### 3.1 Algorithm: K-Means
Action sequences are clustered using K-Means to identify distinct behavioral modes.
- **Initialization**: K is initialized to 50.
- **Validation**: The **Silhouette Score** is calculated. If the score is < 0.25, K is decremented iteratively until a valid cluster structure is found or K=1.
- **Coverage**: The pipeline ensures ≥ 98% of samples are assigned to exactly one cluster.

### 3.2 Output
- Cluster centers (representative action profiles).
- Assignments (mapping each sample to a cluster ID).

## 4. Non-Neural Model: Conditional Gaussian Mixture Model (CGMM) (User Story 2)

Instead of a deep neural network, we fit a **Conditional Gaussian Mixture Model** to each behavioral cluster.

### 4.1 Architecture
- **Input**: Frozen BERT embeddings of text instructions.
- **Conditioning**: The model learns the conditional distribution $P(\text{Actions} | \text{Cluster}, \text{Text})$.
- **Implementation**: Utilizes `sklearn-mixture` to fit Gaussian components per cluster, conditioned on the text embedding space.

### 4.2 Training Objective
The model maximizes the log-likelihood of the observed actions given the cluster assignment and text embedding.
- **Validation**: Requires $R^2 \geq 0.6$ on held-out data.

### 4.3 Inference
1. **Cluster Selection**: For a new prompt, the nearest cluster is identified via BERT embedding distance.
2. **Trajectory Sampling**: Actions are sampled from the fitted CGMM for the selected cluster.
3. **OOD Handling**: If the prompt is far from any cluster center, the system defaults to the nearest cluster and flags "low-confidence".

## 5. Statistical Evaluation (User Story 3)

### 5.1 Simulation Environment
Trajectories are executed in **PyBullet** (CPU-only).
- **Tasks**: Grasp, Navigate, Place.
- **Baselines**:
 - Random Uniform Sampling.
 - VLA Proxy (Neural baseline, if available).

### 5.2 Primary Statistical Test: McNemar's Test
To compare the success rates of the non-neural model against baselines, we use **McNemar's Test**.
- **Rationale**: McNemar's test is appropriate for paired nominal data (Success/Failure on the same set of prompts). It determines if the marginal frequencies of two outcomes are equal.
- **Hypothesis**:
 - $H_0$: There is no significant difference in success rates between the non-neural model and the baseline.
 - $H_1$: There is a significant difference.
- **Output**: P-values and 95% Confidence Intervals.

### 5.3 Fidelity Metric
We calculate the percentage of kinematic features (velocity, acceleration) that fall within a defined error margin of the VLA proxy trajectory, measuring how closely the non-neural model mimics the neural policy's dynamics.

## 6. Complexity Reduction

The pipeline reports a **Complexity Reduction Factor**, comparing the computational cost (FLOPs/Memory) of the CGMM approach versus the original VLA transformer. This metric highlights the efficiency gains of the non-neural approximation.

## 7. Reproducibility

- **Seeding**: Global seeds are set for Python, NumPy, and PyTorch to ensure deterministic results.
- **Configuration**: All hyperparameters (clustering thresholds, simulation limits) are stored in `config.yaml`.
- **Data Integrity**: Checksums are computed for all intermediate artifacts to prevent data drift.
