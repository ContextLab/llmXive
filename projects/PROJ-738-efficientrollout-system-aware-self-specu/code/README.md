# EfficientRollout: Scaled-Down Adaptation

This adaptation reproduces the **core quantitative claim** of the paper:
> "EfficientRollout reduces rollout latency by up to 19.6% ... while preserving quality."

## What was simplified (vs. original)

1.  **No Real RL Training**: The original paper trains an LLM policy (e.g., Llama-3-8B) via GRPO/RL. We **skip training entirely**. Instead, we use a **pre-calibrated "policy quality" proxy** derived from the paper's reported `L_accept` (expected accepted length) curves. We simulate the *effect* of the policy evolution by varying `L_accept` manually, rather than running the full RL loop.
2.  **No Real vLLM Inference**: We do not launch a GPU server, load 7GB+ models, or run CUDA kernels. We **implement the analytical speedup model** (`predict_speedup`, `compute_r`, `compute_v`) directly in Python using the calibration constants provided in the repo (`sd_toggle/configs/a100_tp1_llama318binstruct.json`).
3.  **No Real Hardware**: We do not measure actual wall-clock time on an A100. We compute **theoretical speedups** based on the roofline model parameters (memory bandwidth, FLOPS) embedded in the config.
4.  **Dataset**: We do not run the full `simplerl-8k` dataset. We use a **tiny synthetic subset of query parameters** (Batch sizes, Sequence lengths) to sweep the decision boundary.

## What is preserved (Scientific Logic)

*   **The Toggle Logic**: We faithfully reproduce the `should_enable_sd` function which decides when to switch between Autoregressive (AR) and Speculative Decoding (SD) based on the regime (Memory-bound vs Compute-bound).
*   **The Metrics**: We calculate `speedup`, `r` (draft/verify ratio), and `v` (verification overhead) exactly as defined in the paper's equations.
*   **The Result**: We generate a CSV of `speedup` vs `batch_size` and a plot showing the "Toggle Boundary" where SD becomes beneficial (speedup > 1.0), reproducing the paper's Figure 4/5 logic.

## Compute Target
**CPU**. This is a pure analytical calculation. No GPU is required. The code runs in < 5 seconds.

## Outputs
*   `data/toggle_decision_sweep.csv`: Theoretical speedups for various configurations.
*   `figures/toggle_boundary.png`: A plot visualizing the regime switch point.
