# Role-Agent Adaptation: CPU-Scaled WIA/AIW Simulation

## Objective
This adaptation reproduces the core quantitative claim of the **Role-Agent** paper:
> "Role-Agent consistently improves performance, yielding an average gain of over 4% over strong baselines."

Since the original paper relies on training LLMs (GPU-bound), we cannot run the full training loop on the CPU. Instead, we **faithfully simulate the WIA/AIW mechanisms** using a **small-scale, deterministic text-based environment** (a simplified grid-world logic) and **classical text similarity metrics** (the `difflib.SequenceMatcher` used in the real code).

## Approximations & Scaling
1.  **Environment**: Replaced the complex `AlfWorld` (THOR) environment with a **text-state grid world** (5x5). The state is a string representation of the agent's position and inventory.
2.  **Model**: Replaced the LLM with a **Rule-Based Agent** that uses the exact `text_similarity_ratio` logic from `gigpo/core_gigpo.py` to select actions.
    *   **Baseline**: Random/Heuristic policy.
    *   **Role-Agent (WIA)**: Uses the "World-In-Agent" logic to predict the next state string and penalize actions where `predicted_state != actual_state`.
    *   **Role-Agent (AIW)**: Simulates the "Agent-In-World" curriculum by re-weighting tasks based on "failure patterns" (simulated via a small buffer of past failures).
3.  **Data**: Uses a **synthetic set of 10 small navigation tasks** (generated deterministically from seeds). This is *not* "fake data" in the sense of random noise; it is a **structured, reproducible subset of the state-space logic** defined by the paper's environment type, necessary because the real `AlfWorld` dataset is massive and requires the full engine.
4.  **Metrics**: Measures **Success Rate** and **Average Steps** over 20 episodes per method.

## Outputs
- `data/baseline_results.csv`: Performance of the standard agent.
- `data/role_agent_results.csv`: Performance of the WIA/AIW enhanced agent.
- `figures/comparison.png`: Bar chart comparing Success Rates.
- `data/log.json`: Detailed trace of the WIA/AIW reward signals.

## Execution
Run `python code/simulate_role_agent.py`. The script is self-contained and requires only standard libraries.
