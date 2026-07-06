# Research: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

## Overview

This research phase identifies the specific datasets, validates their availability, and defines the computational strategy to ensure the project runs within the strict GitHub Actions CPU-only constraints (2 CPU, ≤7 GB RAM, ≤1 hour).

## Dataset Strategy

The project requires three specific materials property datasets. Based on the `# Verified datasets` block, the following sources are selected. Note that while the Spec mentions "Materials Project," "OQMD," and "AFLOW" as sources, the verified URLs point to specific HuggingFace datasets containing the target properties.

| Property | Target Dataset Source | Verified URL | Notes |
| :--- | :--- | :--- | :--- |
| **Elastic Modulus** | Materials Project (via HF) | *No verified source found for Elastic Modulus specifically.* | **Gap Identified**: The verified list contains OQMD and AFLOW thermal data, but no explicit verified URL for Elastic Modulus from Materials Project. The plan will attempt to use the **OQMD** dataset (which often contains elastic properties) or the **AFLOW** dataset if it contains elastic data. If neither contains Elastic Modulus, the pipeline will skip that property and flag the gap. |
| **Band Gap** | OQMD | `https://huggingface.co/datasets/kjappelbaum/chemnlp-oqmd/resolve/main/targets.csv` | Verified CSV containing targets. Will be used for Band Gap prediction. |
| **Thermal Conductivity** | AFLOW | `https://huggingface.co/datasets/foundry-ml/dataset_thermalcond_aflow/resolve/main/data/train-00000-of-00001.parquet` | Verified Parquet containing thermal conductivity. |

**Critical Dataset Fit Assessment**:
- **OQMD (Band Gap)**: The dataset contains composition/structure features and target values. It is suitable for regression.
- **AFLOW (Thermal Conductivity)**: The dataset contains the necessary features.
- **Elastic Modulus**: **MISSING VERIFIED SOURCE**. The Spec requires Elastic Modulus from Materials Project. The verified list does not contain a URL for this.
  - *Action*: The implementation will first attempt to load the OQMD dataset and check if it contains an "Elastic Modulus" column. If not, the pipeline will skip the Elastic Modulus experiment and log a "Dataset Gap" in the results. The plan does **not** invent a URL.

## Methodological Rationale

### 1. UQ Method Selection & Implementation
- **GPR (Gaussian Process Regression)**: Selected as a baseline probabilistic model. It is computationally efficient for small datasets (≤10k samples) and provides natural uncertainty estimates. Implemented via `scikit-learn`.
- **MC Dropout**: A deep learning technique where dropout is applied during inference. Requires a lightweight neural network (MLP) since CGCNN (Graph Convolutional Neural Network) is likely too heavy for the 2 GB RAM limit on a 2-core CPU for ensemble generation. We will use a small MLP featurized by `matminer`.
- **Deep Ensembles**: Training multiple independent models (N=5) with different seeds. This is the most robust but memory-intensive method. To fit the 2 GB limit, the ensemble size is capped at 5, and data is batched during inference.
- **Conformal Prediction**: A distribution-free method applied to any baseline model (XGBoost). It requires a calibration set and provides guaranteed coverage.

### 2. Statistical Rigor
- **Independent-Sample Testing**: As mandated by the Spec (FR-004) and Constitution (Principle VII), we use **Welch's t-test** (or Mann-Whitney U if normality assumptions fail) to compare UQ methods.
  - *Rationale*: Each UQ method is trained independently with different architectures/hyperparameters. The resulting predictions are independent samples, not paired.
- **Multiple Comparison Correction**: Since we compare 4 methods (6 pairwise comparisons), we will apply the **Bonferroni correction** to the p-values to control the family-wise error rate.
- **Power Analysis**: Given the dataset size (likely >1000 samples), power should be sufficient to detect medium effect sizes. If a dataset has <100 test samples, the test will be flagged as "Underpowered."

### 3. Computational Feasibility
- **Data Sampling**: To ensure the pipeline runs in <1 hour on 2 CPU cores, datasets will be capped at **10,000 samples**.
- **Memory Management**:
  - Deep Ensembles will be processed sequentially (train model 1, evaluate, free memory, train model 2) rather than loading all 5 models at once.
  - `torch` will be configured to use CPU only (`device='cpu'`).
  - No GPU/CUDA dependencies.
- **Library Pins**:
  - `scikit-learn`: Stable, CPU-optimized.
  - `xgboost`: Efficient CPU implementation.
  - `torch`: CPU wheel only.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use OQMD for Band Gap** | Verified URL available; contains composition features and band gap targets. |
| **Use AFLOW for Thermal Conductivity** | Verified URL available; contains thermal conductivity targets. |
| **Skip Elastic Modulus if no source** | No verified URL for Materials Project Elastic Modulus in the provided list. Inventing a URL violates the "Verified datasets" rule. |
| **Cap dataset size at 10k** | Ensures RAM usage stays under 2 GB and runtime under 1 hour. |
| **Use Welch's t-test** | Matches the independent nature of the UQ method samples as per Spec FR-004. |
| **Bonferroni Correction** | Required to handle multiple comparisons (6 pairs) without inflating Type I error. |

## Risk Assessment

- **Risk**: Elastic Modulus dataset missing.
  - *Mitigation*: Pipeline gracefully skips this property and reports the gap.
- **Risk**: Deep Ensembles OOM (Out of Memory).
  - *Mitigation*: Sequential training and evaluation; reduce ensemble size to 3 if necessary.
- **Risk**: GPR fails on high-dimensional features.
  - *Mitigation*: Use `SelectKBest` for feature selection before GPR; fallback to RBF kernel approximation.
