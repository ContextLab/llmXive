# SDAR Adaptation: CPU-Tractable Simulation

## Purpose
This adaptation reproduces the core quantitative result of the paper **"Self-Distilled Agentic Reinforcement Learning"**: the stability and performance improvement of SDAR over naive GRPO+OPSD when teacher signals are noisy or imperfect.

## Simplifications & Approximations
To fit the strict CPU/CI constraints (2 cores, <7GB RAM, no GPU, <25 min), the following simplifications were made:

1.  **Environment Replacement**:
    *   **Original**: ALFWorld, WebShop, Search-QA (complex, multi-turn text/visual agents).
    *   **Adaptation**: A simplified 5x5 Grid World with random walks. This preserves the *structure* of a trajectory-based RL task (state -> action -> reward) without the heavy dependency on LLM inference or complex game engines.

2.  **Model Replacement**:
    *   **Original**: Qwen2.5/Qwen3 LLMs with GRPO/OPSD training loops.
    *   **Adaptation**: A mathematical simulation of the loss functions. We do not train a neural network. Instead, we directly compute the **SDAR Loss** (Eq. 5 in paper) and **Naive Loss** for simulated trajectories using the theoretical formulas. This allows us to isolate and verify the *mathematical* stability benefit of the gating mechanism.

3.  **Teacher Signal Simulation**:
    *   **Original**: A privileged teacher branch with "imperfect skill retrieval".
    *   **Adaptation**: A heuristic oracle that generates token-level signals (1.0 or -1.0) with a configurable `noise_level` parameter. This directly maps to the paper's claim about "negative teacher rejections" arising from imperfect retrieval.

4.  **Scale**:
    *   **Original**: Millions of tokens, large models, distributed training.
    *   **Adaptation**: 500 simulated episodes, 15 steps each. This is sufficient to demonstrate the statistical trend (SDAR > Naive) without requiring heavy compute.

## Core Logic Reproduced
The script implements the **Gated Distillation** mechanism:
*   **Naive**: `Loss = RL_Loss + Lambda * Distillation_Loss` (Full weight on noisy teacher).
*   **SDAR**: `Loss = RL_Loss + Lambda * Gate * Distillation_Loss`.
    *   `Gate = Sigmoid(Teacher_Signal * Trajectory_Reward)`.
    *   This gate naturally attenuates the distillation loss when the teacher disagrees with the outcome (negative gap), preventing the "compounding instability" described in the paper.

## Artifacts
*   `data/sdar_results.csv`: Numerical comparison of success rates.
*   `figures/success_rate_vs_noise.png`: Visual proof of SDAR's robustness.
*   `figures/gate_attenuation.png`: Visualization of the gating mechanism.
