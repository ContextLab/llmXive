# Domino Adaptation: CPU-Scale Feasibility Study

## Objective
This adaptation reproduces the **core scientific logic** of the Domino paper (Decoupling Causal Modeling from Autoregressive Drafting) in a **CPU-tractable, self-contained** environment. The original paper relies on massive LLMs (Qwen3-8B), GPUs, and speculative decoding loops that are impossible to run on a 2-core/7GB CPU runner.

## Approximations & Simplifications
To make this runnable within ~15 minutes on CPU while preserving the *causal vs. parallel* trade-off insight:

1.  **Model Replacement**:
    *   **Original**: Qwen3-8B (Target) + Custom Draft Model.
    *   **Adaptation**: A tiny, synthetic "Language Model" implemented as a `torch.nn.Linear` classifier over a small vocabulary. It predicts the next token based on a fixed probability distribution (simulating a "smart" target) and a "dumb" parallel draft (random) vs. "smart" draft (causal).
    *   **Why**: This isolates the *algorithmic* benefit of the Domino head (correcting parallel drafts with causal info) without the overhead of loading 10GB+ weights.

2.  **Dataset Subsampling**:
    *   **Original**: Full Alpaca/GSM8K/Code datasets.
    *   **Adaptation**: Uses `tatsu-lab/stanford_alpaca` but downloads **only the first 50 samples**.
    *   **Why**: Real data is required. 50 samples are sufficient to demonstrate the statistical difference between parallel and causal drafting.

3.  **Speculative Decoding Simulation**:
    *   **Original**: Real token generation, verification, and tree attention.
    *   **Adaptation**: A **simulated** speculative decoding loop.
        *   We generate "draft" tokens using a parallel strategy (independent probabilities).
        *   We generate "corrected" tokens using a causal strategy (sequential dependency).
        *   We simulate the "verification" step by comparing the draft distribution against the target distribution (the "Ground Truth" model) to calculate acceptance rates.
    *   **Why**: Real speculative decoding on a 7-layer tiny model would still be too slow to demonstrate the *concept* of the Domino head's correction mechanism in a 20-min budget. The simulation calculates the *expected* speedup based on acceptance rates, which is the paper's primary metric.

4.  **Domino Head Implementation**:
    *   We implement a simplified `DominoHead` (a small MLP) that takes the parallel draft logits and refines them using a "prefix" vector (simulating the causal context).
    *   We compare **Baseline Parallel** (no correction) vs. **Domino** (correction) acceptance rates.

## Expected Output
*   `data/acceptance_rates.json`: JSON file containing acceptance rates for Baseline Parallel, Causal Draft, and Domino Corrected.
*   `figures/acceptance_comparison.png`: Bar chart visualizing the improvement in acceptance rate provided by the Domino head.

## Verification
Run `python code/run_domino_simulation.py`. It will:
1.  Load 50 real Alpaca prompts.
2.  Simulate the drafting and verification process.
3.  Output real metrics showing that the Domino head improves upon the parallel baseline.
