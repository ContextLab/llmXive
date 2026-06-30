# Simplified Masking Study Adaptation

## Overview
This adaptation reproduces the core quantitative finding of the paper *"Masking Stale Observations Helps Search Agents -- Until It Doesn't"*: the **asymmetric inverted-U relationship** between model capacity and the benefit of observation masking.

## Simplifications & Approximations
To ensure execution on a 2-CPU, 7GB RAM CI environment within 20 minutes, the following drastic simplifications were applied:

1.  **Model Replacement**:
    *   *Original*: 4B to 284B parameter LLMs (DeepSeek, GPT, Qwen, etc.).
    *   *Adaptation*: A `LogisticRegression` classifier trained on TF-IDF features of synthetic text. This captures the "decision boundary" logic without the computational cost of LLM inference.

2.  **Data Generation**:
    *   *Original*: Real-time web search queries and trajectories (BrowseComp, etc.).
    *   *Adaptation*: A synthetic trajectory generator (`generate_synthetic_trajectory_data`) creating 500 samples. Each sample has a "question" and a 10-turn history where "stale" observations are explicitly marked as noise. The correct answer is injected at a random turn.

3.  **Masking Simulation**:
    *   *Original*: Token-level masking or context window truncation in vLLM/DeepSeek agents.
    *   *Adaptation*: Pre-processing step that filters out `is_stale=True` turns from the input list before feature extraction.

4.  **Capacity Simulation**:
    *   *Original*: Varying model sizes (parameter count) and context windows.
    *   *Adaptation*: The `capacity_strategy` parameter limits the number of turns the "model" sees (3, 6, or all 10).
        *   `small`: Weak model, ignores most context.
        *   `medium`: Mid-capacity, benefits from noise removal.
        *   `large`: Saturated model, performance degrades with unmasked noise (simulating the "collapse" or overfitting to irrelevant context).

## Output Artifacts
*   `data/synthetic_trajectories.csv`: The generated synthetic dataset.
*   `data/experiment_results.csv`: Accuracy scores for each capacity/masking combination.
*   `data/summary.json`: Machine-readable summary of the findings.
*   `figures/masking_regime_map.png`: The plot visualizing the inverted-U curve.
