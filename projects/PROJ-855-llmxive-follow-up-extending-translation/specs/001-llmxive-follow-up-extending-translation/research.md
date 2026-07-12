# Research: llmXive follow-up: extending "Translation as a Bridging Action"

## Executive Summary

This research validates whether **translation-only** wrist trajectories contain sufficient *probabilistic* signal to predict bi-manual manipulation stability, independent of rotation or force data. We generate a synthetic dataset of episodes using PyBullet with injected noise (Gaussian trajectory perturbation, randomized physics parameters) to break deterministic mappings. We train a lightweight Transformer and compare it against two baselines: a **Geometry-Only** model and a **Shuffled Translation** control. Success is defined as a statistically significant (p < 0.05) accuracy improvement over the baselines on a test set with novel geometries and noisy physics.

## Dataset Strategy

### Source & Generation
The study relies on **synthetic data generation** via the PyBullet physics engine. No external real-world dataset is used, as the specific "translation-only" input and "stability" ground truth (tipping/slippage) are not available in existing repositories.

*   **Generation Engine**: PyBullet (CPU-based)
*   **Verified Datasets**: None used for training. The "Verified datasets" block in the spec contains no suitable source for this specific physics task.
*   **Synthetic Generation Strategy**:
    1.  **Object Geometry**: Randomly sample bounding boxes (width, height, depth) and mass properties from a distribution.
    2.  **Trajectory**: Generate random 3D translation vectors (x, y, z) for dual-wrist manipulation.
    3.  **Noise Injection (Critical)**:
        *   Add Gaussian noise ($\mathcal{N}(0, \sigma^2)$) to translation vectors to simulate sensor noise.
        *   Randomize friction coefficients and object mass within realistic bounds to simulate physical variability.
    4.  **Physics Simulation**: Run the episode in PyBullet with these noisy parameters.
    5.  **Labeling**: Calculate **Tipping Angle** (deviation of center of mass from base) and **Slippage Distance** (relative displacement of contact points).
        *   **Success (1)**: Tipping < 15° AND Slippage < 0.02m.
        *   **Failure (0)**: Tipping ≥ 15° OR Slippage ≥ 0.02m.
    6.  **Filtering**: Explicitly discard all rotation quaternions, joint torques, and force sensor readings. Retain only translation vectors and initial object bounds.

### Dataset Characteristics
*   **Volume**: ≥ 5,000 valid episodes.
*   **Input Features**: Sequence of 3D translation vectors (t-10 to t), Initial Object Bounding Box (min/max).
*   **Target**: Binary stability label (0/1).
*   **Constraints**: No rotation, no force, no torque data.
*   **Class Balance**: Stratified sampling or oversampling enforced to ensure ~50/50 split between success/failure, preventing trivial "predict failure" solutions.
*   **Robustness**: Sensitivity analysis performed by sweeping tipping/slippage thresholds by ±5%.

## Model Architecture & Training

### Architecture: Lightweight Transformer Encoder
*   **Type**: 4-layer Transformer Encoder.
*   **Parameters**: < 10,000,000 (strictly capped).
*   **Input**: Sequence of translation vectors (d_model=64).
*   **Output**: Binary probability (Sigmoid).
*   **Rationale**: Transformers capture long-range dependencies in trajectories better than RNNs on CPU, while the 4-layer constraint ensures CPU tractability.

### Training Configuration
*   **Hardware**: 2-core CPU, 7GB RAM (GitHub Actions Free Tier).
*   **Precision**: Default float32 (no 8-bit/4-bit quantization).
*   **Loss**: Binary Cross-Entropy (BCE).
*   **Optimization**: AdamW (learning rate 1e-4, weight decay 1e-2).
*   **Batch Size**: Dynamically tuned (start 32, reduce if OOM) to fit <7GB RAM.
*   **Epochs**: 10-20 (early stopping on validation loss).
*   **Seed**: Pinned (e.g., 42) for reproducibility.

### Baselines
1.  **Geometry-Only Baseline**: Input is only initial object bounding box coordinates. Architecture: Simple MLP (2 layers).
2.  **Shuffled Translation Control**: Input is the same translation sequence but with time steps permuted randomly. This establishes a lower bound for signal informativeness (should perform near chance).

## Statistical Validation Plan

### Hypothesis
*   **H0**: The translation-only model performs no better than the baselines (Accuracy_Diff ≤ 0.5% with p ≥ 0.05).
*   **H1**: The translation-only model significantly outperforms the baselines (Accuracy_Diff > 0.5% with p < 0.05).
*   **Practical Significance Target**: ≥ 5% absolute accuracy improvement over baselines.

### Methodology
1.  **Test Set Construction**:
    *   **Novel Geometries**: Object bounding boxes sampled from a distribution disjoint from training.
    *   **Novel Trajectories**: Translation sequences generated *de novo* (not reused from training).
    *   **Noisy Physics**: Physics parameters (friction, mass) randomized further than in training to test generalization.
2.  **Metric**: Absolute Accuracy Improvement (Model Acc - Baseline Acc).
3.  **Statistical Test**: **McNemar's Test** on the contingency table of paired predictions (Model vs. Baseline).
    *   *Rationale*: McNemar's is appropriate for paired nominal data.
    *   *Focus*: Applied primarily on the **Noisy Physics** test set where errors are non-trivial.
4.  **Significance Threshold**: p < 0.05.
5.  **Multiplicity**: Only one primary comparison (Model vs. Geometry) and one control comparison (Model vs. Shuffled); no family-wise error correction required beyond standard alpha.
6.  **Causal Framing**: Results are reported as **associational**. No causal claims (e.g., "translation *causes* stability") are made, as the data is observational (simulated with noise) without random assignment of physical laws.

### Robustness Checks
*   **Sensitivity Analysis**: Re-run evaluation with tipping threshold ±5% and slippage threshold ±5%. Report variance in accuracy.
*   **Ambiguous Signal Check**: Analyze confusion matrix for cases where translation is identical for success/failure. If accuracy < 50% on this subset, flag as a limitation of the modality.
* **Power Analysis**: N=5,000 with balanced classes provides >80% power to detect a [deferred] accuracy difference at $\alpha=0.05$.

## Compute Feasibility & Rationale

| Component | Strategy | Feasibility Justification |
| :--- | :--- | :--- |
| **Physics Engine** | PyBullet (CPU) | Native CPU support; no GPU required for rigid body dynamics. |
| **Data Volume** | [deferred] episodes | Estimated size < 50MB; fits easily in RAM. |
| **Model Size** | < 10M params | Compact model size; inference/training on CPU is feasible. |
| **Training Time** | ≤ 6 hours | Target: 2-3 hours on 2-core CPU with batch size 16-32. |
| **Memory** | ≤ 7GB RAM | Batch size and sequence length tuned to stay under available hardware memory constraints. |
| **Libraries** | `torch` (CPU wheel) | Avoid `bitsandbytes`; use standard `torch` CPU build. |

## Assumptions & Limitations

*   **Sim-to-Sim Nature**: The primary validation is "Sim-to-Sim" with controlled noise. The hypothesis is that translation signals contain sufficient information to predict stability *in the presence of noise*, not that it universally predicts real-world stability. A future "Sim-to-Real" phase is required for physical validation.
*   **Threshold Justification**: 15° tipping and 0.02m slippage are standard approximations; sensitivity analysis mitigates risk.
*   **Ambiguity**: Some translation trajectories may be inherently ambiguous for stability; the model's probability output reflects this uncertainty.
*   **Compute Limits**: If training exceeds 6 hours, hyperparameters (batch size, epochs) will be reduced, potentially affecting convergence.