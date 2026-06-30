# DelTA Adaptation: CPU-Tractable Reproduction

## Summary of Simplifications

This adaptation reproduces the **core theoretical claim** of the DelTA paper: that reweighting token-gradient vectors based on their discriminative power (vs. shared high-frequency patterns) improves the separation between "positive" (high reward) and "negative" (low reward) update directions in RLVR.

Since the original paper relies on massive LLMs (Qwen3-8B/14B) and GPU-heavy RL training loops which cannot run in this environment, we have implemented a **minimalist proxy simulation**:

1.  **Model Proxy**: Instead of a 14B parameter LLM, we use a synthetic "token space" of 1,000 dimensions.
2.  **Data Proxy**: We generate synthetic token-gradient vectors.
    *   **Shared Patterns**: A large cluster of vectors pointing in a common direction (simulating formatting tokens like `\n`, `Answer:`, etc.).
    *   **Discriminative Patterns**: Sparse vectors pointing in unique directions that correlate with the reward signal.
3.  **Method Proxy**:
    *   **Standard RLVR**: Computes centroids by simple averaging of advantage-weighted gradients.
    *   **DelTA Proxy**: Computes a "discriminative coefficient" for each token based on its ability to separate the positive/negative clusters, then reweights the gradients before averaging.
4.  **Scale**:
    *   5,000 synthetic samples (tokens).
    *   1,000 dimensions.
    *   No external datasets or models loaded.
    *   Pure `numpy` implementation.

## Expected Outcome
The script will output a CSV showing that the **DelTA-weighted centroids** have a significantly higher cosine similarity separation (discriminative power) between the positive and negative update directions compared to the **Standard RLVR** centroids.

## Artifacts
- `data/centroids_comparison.csv`: Numerical results of the separation metric.
- `figures/separation_analysis.png`: Visualization of the 2D projection of the centroids.
