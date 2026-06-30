# ProRL Adaptation: CPU-Only Simplification

## Overview
This code adapts the **ProRL** paper ("Effective Reinforcement Learning for Proactive Recommendation via Rectified Policy Gradient Estimation") to run on a constrained CPU environment (2 cores, 7GB RAM, no GPU, <25 mins).

## Simplifications & Approximations
To ensure the code runs within CI constraints while preserving the **core scientific logic**, the following approximations were made:

1.  **Dataset**:
    -   **Original**: Large-scale real-world datasets (Amazon Books, Steam, ML-1M) with millions of interactions and heavy embedding lookups (e.g., `qwen3-embedding-8b`).
    -   **Adaptation**: A **synthetic dataset** is generated on-the-fly (200 users, 500 items, avg sequence length 10). This removes the need for downloading large files or loading heavy pre-trained embeddings.

2.  **Model Architecture**:
    -   **Original**: Complex Transformer-based policy networks (SASRec/GRU4Rec backbones) with large parameter counts and GPU-accelerated attention.
    -   **Adaptation**: A **single linear layer** (or simple random matrix in fallback mode) acting as the policy network. This reduces memory footprint to <1MB and allows instant training on CPU.

3.  **Training Scale**:
    -   **Original**: Full training loops with thousands of epochs, large batch sizes, and complex RL rollouts.
    -   **Adaptation**: **5 epochs** with **mini-batches of 4**. The RL rollout is simulated with fixed path lengths (3-5 steps) instead of dynamic, environment-driven interactions.

4.  **Core Mechanisms Preserved**:
    -   **Stepwise Reward Centering**: Implemented exactly as described: `r_t = r_t - mean(r_path)`.
    -   **Position-Specific Advantage**: Implemented as `A_t = Return_t - baseline`, using discounted sums of centered rewards.
    -   The code explicitly demonstrates these calculations and their effect on the "policy" weights.

5.  **Dependencies**:
    -   The script uses `numpy`, `pandas`, and `matplotlib`.
    -   **PyTorch** is optional: If `torch` is not installed, the script automatically switches to a pure NumPy implementation of the policy and gradient updates, ensuring it never crashes due to missing heavy dependencies.

## Artifacts
-   `data/prorl_results.csv`: Epoch-wise metrics.
-   `figures/prorl_training_curve.png`: Visual proof of the algorithm running.
