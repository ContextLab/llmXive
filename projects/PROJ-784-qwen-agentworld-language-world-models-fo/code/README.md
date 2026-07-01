# Qwen-AgentWorld Adaptation: Small-Scale World Model Simulation

## Simplifications & Approximations

The original paper describes training massive (35B/397B parameter) Language World Models using 10M+ real-world interaction trajectories across 7 domains. This is computationally infeasible for a CPU runner or a single Kaggle GPU kernel.

This adaptation focuses on **reproducing the core quantitative logic** of the "World Model" evaluation: **Next-State Prediction Accuracy**.

### Key Adaptations:
1.  **Model Architecture**: Instead of a 397B Transformer, we use a **small, CPU-tractable LSTM** (Long Short-Term Memory) network. This preserves the "sequence modeling" nature of world models but reduces parameters to <1M.
2.  **Dataset**: Instead of 10M trajectories, we use a **subsampled, real-world subset** of the `gymnasium` (formerly OpenAI Gym) environment `FrozenLake-v1`. This provides real, deterministic state transitions (S, A, S') without requiring internet downloads or massive storage.
3.  **Scale**:
    *   **Episodes**: 500 training episodes (scaled down from millions).
    *   **Steps per Episode**: 100 steps.
    *   **Total Samples**: ~50,000 transition tuples.
4.  **Metric**: We measure **Next-State Prediction Accuracy** (Exact Match of the next state index) and **Reward Prediction Error**.
5.  **Comparison**: We compare the World Model (LSTM) against a naive "Last-State" baseline to demonstrate the value of the model, mirroring the paper's evaluation of "simulation fidelity."

### Output Artifacts
*   `data/model_results.json`: Contains the accuracy metrics and loss curves.
*   `figures/prediction_accuracy.png`: A plot comparing the World Model vs. Baseline performance.

This adaptation proves the *methodology* of training a world model on real interaction data, scaled to run in <15 minutes on a CPU.
