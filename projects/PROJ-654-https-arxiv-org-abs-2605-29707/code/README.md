# Domino Adaptation: Causal Decoupling Analysis

This adaptation reproduces the **core scientific claim** of the Domino paper: that decoupling causal modeling from autoregressive drafting improves draft quality (acceptance rate) compared to a pure parallel baseline, even with a lightweight correction head.

## Approximations & Scaling

Since the original paper trains and evaluates on massive LLMs (Qwen3-8B) with GPU-heavy kernels, this adaptation scales down to a **CPU-tractable simulation** of the *mechanism*:

1.  **Proxy Model**: Replaces the 8B LLM with a **tiny 3-layer Transformer** (or even a simple statistical proxy) running on CPU.
2.  **Dataset**: Uses a **small sample (N=100)** of the `c4` or `wikitext` dataset (real text, not synthetic) to measure token prediction.
3.  **Methodology**:
    *   **Baseline**: Simulates a "Parallel Drafter" (predicts next $k$ tokens independently).
    *   **Domino**: Simulates the "Parallel Backbone + Domino Head" (corrects independent predictions using a lightweight prefix-aware module).
    *   **Metric**: Measures **Acceptance Rate** (how many draft tokens match the "Target" model's greedy output) for both methods.
4.  **Hardware**: Runs entirely on CPU using `torch` (no CUDA required).
5.  **Goal**: Demonstrate that the "Domino" correction step yields a higher acceptance rate than the raw parallel draft, validating the paper's decoupling hypothesis without requiring 8GB+ VRAM.

## Output
- `data/acceptance_rates.csv`: Comparison of Acceptance Rates between Baseline and Domino.
- `figures/acceptance_comparison.png`: Visual comparison of the results.
