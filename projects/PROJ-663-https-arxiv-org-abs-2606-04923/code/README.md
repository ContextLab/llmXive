# Adaptation Summary: CHERRL Reward Hacking (Scaled-Down)

## Goal
Reproduce the core quantitative finding of the CHERRL paper: **Reward Divergence**.
The paper demonstrates that when a biased judge (LLM-as-a-Judge) is used, the agent's reward score increases over training while the *true* quality (or a proxy) stagnates or drops.

## Simplifications & Approximations
1.  **No Real LLMs**: The original CHERRL environment uses actual LLMs (e.g., Qwen, Llama) as both the policy and the judge. This is GPU-intensive and requires API keys or massive local models.
    *   *Adaptation*: We replace the **Judge** with a deterministic **Rule-Based Scorer** that has an injected "bias" (e.g., it over-scores responses containing a specific keyword like "excellent" or "comprehensive", regardless of actual content quality).
    *   *Adaptation*: We replace the **Policy** (RL agent) with a simple **Keyword Injection Agent**. The agent learns to maximize the biased score by injecting these trigger words into its output.
2.  **No Reinforcement Learning Loop**: We skip the complex PPO/GRPO training loop (which requires GPUs and Ray).
    *   *Adaptation*: We simulate the "training" process as a deterministic search. The agent iteratively updates its output template to include more trigger words, directly optimizing for the biased reward. This mimics the *convergence* to a hacking behavior without the stochasticity of RL.
3.  **Data**:
    *   *Adaptation*: Uses a tiny, static list of 5 "real" prompts from the `data/health_bench` directory (subsampled) instead of the full dataset.
4.  **Metrics**:
    *   *Adaptation*: We compute **Reward Divergence**:
        *   `Biased_Reward`: Score from the biased judge (increases as agent hacks).
        *   `True_Quality_Proxy`: A heuristic score (e.g., sentence count or keyword relevance to the *actual* prompt) that does *not* benefit from the hacking (or decreases).
        *   The gap between these two is the "Hacking Signal".

## Why this is valid
The core claim of CHERRL is that **biased judges lead to reward divergence**. This adaptation explicitly constructs a biased judge and an agent that exploits it, producing the exact divergence curve described in the paper, but in a CPU-tractable, self-contained simulation.

## Outputs
- `data/reward_divergence.csv`: Time-series data showing the gap between biased reward and true quality.
- `figures/hacking_curve.png`: A plot visualizing the divergence.
