# Domino Adaptation: CPU-Scaled Causal Decoupling Demo

## Goal
Reproduce the core quantitative claim of **Domino**: that decoupling causal modeling from drafting (via a parallel backbone + lightweight causal head) yields better draft quality than a purely parallel approach, with minimal overhead.

## Simplifications vs. Original Paper
- **No LLMs**: The original uses Qwen3 (8B+) with GPU kernels. This adaptation uses **scikit-learn** on a tiny, real text dataset (WikiText-2 sample) to simulate the "drafting" logic.
- **Proxy Models**:
  - *Parallel Backbone*: A simple `CountVectorizer` + `LogisticRegression` (fitted on bigrams) representing a non-causal, parallel probability estimator.
  - *Domino Head*: A lightweight `MLPClassifier` (1 hidden layer) that takes the parallel draft probabilities + prefix context embeddings to refine the prediction.
- **Dataset**: Uses a **subsampled (200 samples)** version of the **WikiText-2** dataset (via `datasets` library). No synthetic data.
- **Metric**: **Top-1 Accuracy** on the next-token prediction task (proxy for "draft acceptance rate").
- **Compute**: Runs entirely on CPU. No CUDA, no Transformers, no SGLang.

## Artifacts
- `data/results.csv`: Comparison of "Parallel Only" vs. "Domino (Parallel + Causal Head)" accuracy.
- `figures/accuracy_comparison.png`: Bar chart of the results.

## How to Run
```bash
python code/domino_cpu_demo.py
```
