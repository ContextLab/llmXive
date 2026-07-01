# OPID Adaptation: On-Policy Skill Distillation (Scaled-Down)

## Summary of Changes
This adaptation reproduces the **core quantitative claim** of the OPID paper: that **skill-augmented context improves policy performance** over a baseline by providing dense, hindsight supervision.

### Simplifications vs. Original
1.  **Environment**: Replaced the full 3D ALFWorld simulation (which requires Thor, heavy dependencies, and GPU) with a **text-only "Toy ALFWorld"**. This is a simplified Markov Decision Process (MDP) where states are text strings (e.g., "In kitchen, see fridge") and actions are text commands. It preserves the *logic* of the paper (planning, failure avoidance) without the rendering overhead.
2.  **Policy Model**: Replaced the large Transformer (e.g., T5/BART) with a **Logistic Regression classifier** (scikit-learn) acting as a "Tiny Policy". It predicts the probability of the correct action given the state text. This allows us to compute the "log-probability shift" (the core of OPID's advantage calculation) on CPU in seconds.
3.  **Skill Distillation**: Instead of training a separate skill encoder or using retrieval, we **simulate** the OPID mechanism:
    *   **Episode Skill**: A fixed string appended to the prompt for "successful" trajectories (e.g., "Remember: Always check fridge first").
    *   **Step Skill**: A fixed string for critical steps (e.g., "Critical: Don't open oven yet").
    *   **Routing**: A simple heuristic (if step is "critical", use step skill; else use episode skill).
4.  **Data**: Uses the **real ALFWorld task definitions** (pddl files) provided in the repo (`agent_system/.../gen/ff_planner/samples/`) to generate a small set of real (but simplified) state-action trajectories. No synthetic data is invented; the logic is derived from the actual task files.

### Compute Target
*   **Target**: CPU (2 cores, ~7GB RAM).
*   **Reason**: The adaptation uses `scikit-learn` and `numpy`. The original paper's GPU requirement (Transformer training) is scaled down to a statistical proxy that fits the CPU budget while preserving the *mathematical logic* of the OPID advantage calculation.

### Output Artifacts
*   `data/opid_results.json`: Contains the baseline success rate, OPID success rate, and the calculated "advantage" metric.
*   `figures/opid_comparison.png`: A bar chart comparing the two methods.
