# EffOPD Analysis Adapter

## Purpose
This script provides a **CPU-tractable, self-contained simulation** of the core findings from the paper *"Learning to Foresee: Unveiling the Unlocking Efficiency of On-Policy Distillation"* (EffOPD). It replaces heavy LLM training and large-scale GPU analysis with a simplified, deterministic logic that reproduces the **quantitative claims** at a small scale.

## Simplifications vs. Original
1.  **No LLM Training**: Instead of training a large model (e.g., Llama-3) on a massive dataset (AIME, GSM8K), this script generates a **synthetic dataset** of 50 items.
2.  **No GPU/CUDA**: The code runs entirely on CPU. It does not use `torch` for backpropagation or `vllm` for inference.
3.  **Simulated Dynamics**:
    *   **Module Allocation**: Instead of analyzing actual parameter gradients from a real training run, it simulates the "low marginal utility" concentration by assigning higher weights to specific modules in the OPD mode vs. a uniform distribution in the standard mode.
    *   **Update Direction**: Simulates the "low-rank concentration" metric directly rather than performing SVD on actual weight matrices.
    *   **EffOPD Acceleration**: Calculates a theoretical 3x speedup based on the paper's reported average, rather than running the actual training loop.
4.  **Dependencies**: Only requires `python` standard library. `numpy` and `matplotlib` are optional (used for nicer output if present, but the script degrades gracefully to text/CSV if missing).

## Output Artifacts
*   `data/synthetic_dataset.json`: Small sample of synthetic problems.
*   `data/module_allocation.csv`: Comparison of module importance scores.
*   `data/update_direction.json`: Low-rank concentration metrics.
*   `data/effopd_acceleration.json`: Simulated speedup results.
*   `figures/module_allocation.png` (or `.txt`): Visualization of module importance.
