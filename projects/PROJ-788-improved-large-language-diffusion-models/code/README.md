# iLLaDA Adaptation: Scaled Masked Diffusion Demo

## Simplifications vs. Original Paper
This adaptation reproduces the **core mechanism** of the iLLaDA paper (Masked Diffusion Language Modeling with Bidirectional Attention) but scales it down drastically to fit CPU constraints and the "real result" requirement.

| Aspect | Original Paper (iLLaDA) | This Adaptation |
| :--- | :--- | :--- |
| **Model Size** | 8B Parameters | ~100k Parameters (Tiny Transformer) |
| **Architecture** | Bidirectional Attention, Diffusion | Bidirectional Attention, Diffusion |
| **Training Data** | 12T Tokens | ~2,000 Real English Sentences (WikiText-2 sample) |
| **Training Time** | Weeks on GPU Cluster | ~10-15 minutes on CPU |
| **Objective** | Masked Diffusion (Continuous) | Masked Diffusion (Discrete) |
| **Benchmarks** | MATH, HumanEval, BBH | Custom "Fill-in-the-Blank" Accuracy on Real Text |
| **Result Type** | Benchmark Scores (e.g., 72.5%) | **Real Accuracy %** on held-out real text |

## Scientific Logic Preserved
1.  **Masked Diffusion:** Instead of autoregressive generation, we mask tokens and predict them simultaneously using a bidirectional encoder.
2.  **Training Loop:** We train a small transformer to predict masked tokens given the context and a mask ratio schedule.
3.  **Evaluation:** We measure the **accuracy of reconstructing masked tokens** from real text (WikiText-2), which is the direct proxy for the paper's "confidence-based scoring" and generative capability.

## Artifacts
- `data/training_metrics.csv`: Loss curve over epochs.
- `data/reconstruction_results.json`: Real accuracy on a held-out real text sample (the core quantitative result).
- `figures/loss_curve.png`: Visualization of training convergence.
