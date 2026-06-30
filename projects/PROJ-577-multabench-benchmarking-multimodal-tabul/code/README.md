# MulTaBench CPU Adaptation

## Overview
This adaptation reproduces the core finding of the **MulTaBench** paper: that **task-specific tuning of unstructured modalities (text/images) improves performance** over using frozen embeddings in multimodal tabular learning.

## Simplifications & Approximations
To fit the strict CPU-only (2 cores, ~7GB RAM) and time (<25 min) constraints, the following heavy components were replaced or scaled down:

1.  **Dataset Replacement**: The original benchmark uses 40 large, real-world datasets with actual images and text.
    *   **Adaptation**: We generate a **synthetic dataset** (`data/synthetic_multimodal.csv`).
    *   **Text**: Simulated as "bag-of-words" vectors (sparse or dense) with a clear signal correlated to the target.
    *   **Images**: Simulated as high-dimensional feature vectors (e.g., 512-dim) with added noise, where the mean vector shifts based on the class/target.
    *   **Tabular**: Standard numerical/categorical features.
    *   **Reasoning**: This preserves the *multimodal structure* (Tabular + Text + Image) without the I/O and GPU overhead of loading real image/text encoders.

2.  **Model Replacement**: The original paper uses large transformers (DINOv2, E5, TabPFN, TabDPT) requiring GPU.
    *   **Adaptation**: We use **Scikit-Learn** estimators (Random Forest and Logistic Regression) as the "Tabular Learner".
    *   **Frozen Baseline**: We train a model on *fixed* synthetic embeddings (simulating frozen pre-trained vectors).
    *   **Tuned Baseline**: We train a model where the embedding weights are *fine-tuned* via a simple linear layer (simulating LoRA/adapter tuning) before the final predictor.
    *   **Reasoning**: This isolates the specific contribution of "tuning the representation" vs "using frozen embeddings," which is the paper's core claim.

3.  **Scale**:
    *   **Samples**: 2,000 rows (train/test split).
    *   **Features**: 10 tabular, 512 text, 512 image.
    *   **Iterations**: 50 epochs (fast convergence on synthetic data).

## Expected Outcome
The output will show that the **Tuned** model achieves higher accuracy (classification) or lower MSE (regression) than the **Frozen** model, validating the paper's hypothesis in a CPU-tractable environment.
