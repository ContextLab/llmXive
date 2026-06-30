# Active Learners as Efficient PRP Rerankers - CPU Adaptation

## Summary of Simplifications
This adaptation reproduces the core finding of the paper: **Active Learning (AL) rankers outperform classical sorting (Bubble/Quick) in NDCG@K under strict comparison budgets**, using a noise-robust randomized oracle.

To make this runnable on **2 CPU cores, ~7GB RAM, and <25 minutes** without GPU or LLM APIs:
1.  **No LLM Calls**: The original paper uses FLAN-T5-XXL or Qwen to generate pairwise judgments. This adaptation uses a **synthetic noisy oracle** that simulates the LLM's behavior:
    *   It assumes a "true" relevance score (simulated ground truth).
    *   It applies a **randomized direction** to the comparison to simulate position bias (as described in the paper).
    *   It injects **Gaussian noise** to simulate LLM inconsistency.
2.  **Tiny Dataset**: Instead of full BEIR datasets (thousands of queries/documents), we generate a synthetic dataset with **5 queries** and **20 documents per query**.
3.  **Simplified Rankers**: We implement the core logic of `BubbleSort`, `QuickSort`, and the `ActiveLearning` ranker directly in this script, removing heavy dependencies on `ireranker`'s complex import graph.
4.  **Metrics**: We compute **NDCG@10** and **Comparison Count** exactly as the paper does, aggregating results into a summary CSV and a plot.

## Files Produced
- `data/synthetic_results.csv`: Raw results for each query/ranker/budget.
- `figures/ndcg_vs_budget.png`: The core figure showing AL vs. Classic rankers.
- `figures/noise_analysis.png`: Demonstrates the effect of the randomized oracle on noise.
