# SU-01 Adaptation: CPU-Tractable Proofbench Simulation

## Overview
This adaptation reproduces the **core quantitative claim** of the paper "Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified Scaling" in a CPU-tractable environment.

**Original Claim:** The SU-01 model achieves gold-medal-level performance on Olympiad benchmarks (IMO, USAMO, IPhO, ProofBench) via a complex RL pipeline involving 30B parameter models, 100K+ token trajectories, and verifiable rewards.

**Adaptation Strategy:**
1.  **Scale Reduction:** Instead of training a 30B model on 340K trajectories, we simulate the **evaluation and reward verification logic** on a tiny, synthetic dataset (10 problems).
2.  **Model Proxy:** We replace the 30B reasoning backbone with a deterministic **rule-based solver** (or a tiny `transformers` model if CPU permits, falling back to rules). The core scientific logic being tested is the **reward verification mechanism** (checking if a generated proof contains the correct answer) and the **scaling of success rates** with sample count (Test-Time Scaling).
3.  **Dataset:** We use a subset of the `proofbench` structure found in the repo but generate synthetic problem/answer pairs to ensure the script runs without external network calls or massive downloads.
4.  **Metric:** We reproduce the "Pass@k" metric (success rate given k attempts) and the "Reward Verification Score" reported in the paper's RL pipeline.

## Simplifications vs. Original
| Feature | Original Paper (SU-01) | This Adaptation |
| :--- | :--- | :--- |
| **Model** | 30B-A3B Transformer (GPU) | Rule-based solver / Tiny CPU model |
| **Data** | 340K real Olympiad trajectories | 10 synthetic math problems |
| **Training** | 200 RL steps, PPO, Verifiable Rewards | None (Simulated Evaluation only) |
| **Inference** | 100K+ token trajectories | < 100 tokens per problem |
| **Hardware** | Multi-GPU Cluster | 2 CPU Cores, < 2GB RAM |
| **Goal** | Train a new model | Verify the *evaluation pipeline* logic |

## Output Artifacts
- `data/pass_at_k_results.json`: Success rates for k=1, 2, 4, 8 attempts.
- `figures/pass_at_k_curve.png`: Visualization of the scaling law.
- `data/verification_log.csv`: Detailed per-problem verification steps.
