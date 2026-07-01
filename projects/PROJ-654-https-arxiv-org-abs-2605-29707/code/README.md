# Domino Adaptation: Scaled-Down Causal Decoupling Verification

## Goal
Reproduce the core quantitative claim of the **Domino** paper: that a **parallel draft backbone** combined with a **lightweight causal refinement head** (Domino) yields better draft accuracy (and thus higher speculative decoding speedup) than a purely parallel or purely autoregressive drafter, specifically in a resource-constrained environment.

## Simplifications vs. Original Paper
1.  **Model Architecture**:
    *   **Original**: Large Qwen3 models (8B+) with complex `DFlash`/`Domino` heads, trained on massive datasets.
    *   **Adaptation**: Uses a **tiny GPT-2 (117M)** as the "Target" and a **tiny DistilGPT-2** as the "Draft". The Domino head is implemented as a lightweight **GRU + Linear projection** (mimicking the paper's "Domino head") acting on the draft embeddings.
2.  **Training/Verification**:
    *   **Original**: Full training curriculum, SGLang serving benchmarks, 5.49x speedup claims.
    *   **Adaptation**: **No training**. We use a pre-trained small model as the "Base" and simulate the "Domino Head" as a simple **prefix-aware correction layer** (a linear projection conditioned on the previous token's embedding). We verify the *mechanism*: that adding the causal head improves the draft distribution's alignment with the target distribution compared to the raw parallel draft.
3.  **Dataset**:
    *   **Original**: Full GSM8K, MATH, HumanEval, etc.
    *   **Adaptation**: **First 50 samples** of the `gsm8k` dataset (via Hugging Face `datasets`).
4.  **Compute**:
    *   **Original**: GPU clusters (A100/H100).
    *   **Adaptation**: **CPU Only**. The models are small enough to run on 2 cores. The "Domino Head" is a simple matrix multiplication, computationally cheap on CPU.
5.  **Metric**:
    *   **Original**: End-to-end tokens/sec.
    *   **Adaptation**: **Draft Acceptance Rate (simulated)** and **KL Divergence** between Draft and Target distributions. The paper's core claim is that Domino improves the *quality* of the draft, which directly correlates to acceptance rate. We measure this quality gain.

## How to Run
```bash
python code/verify_domino_mechanism.py
```
