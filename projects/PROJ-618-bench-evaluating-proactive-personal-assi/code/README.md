# $\pi$-Bench CPU Adaptation: Proactive Intent Simulation

## Summary of Simplifications
This adaptation reproduces the **core quantitative result** of the $\pi$-Bench paper: the distinction between **Task Completion** and **Proactivity** scores in multi-turn interactions.

### What was simplified vs. Original
1.  **No LLM Agents**: The original benchmark uses large LLMs (e.g., GPT-4, Claude) to simulate agents and users. This adaptation replaces them with **deterministic rule-based simulators** and **simple statistical models** (scikit-learn) to emulate the *behavior* of proactive vs. reactive agents without requiring GPU or API keys.
2.  **Synthetic Data**: Instead of the full 100-task, 5-persona dataset, we generate a **synthetic dataset** of 50 simulated interactions (10 per persona) with hardcoded "hidden intents" to ensure reproducibility and CPU speed.
3.  **Proxy Metrics**:
    *   **Task Completion**: Calculated based on whether the simulated agent executed the "required" final action.
    *   **Proactivity**: Calculated based on whether the agent detected and acted on a "hidden intent" *before* the user explicitly requested it, using a simple heuristic (keyword matching + turn count).
4.  **No External Dependencies**: No Docker, no test servers, no network calls. All logic is self-contained in `code/simulate_pi_bench.py`.

### Output Artifacts
*   `data/results.csv`: Summary statistics of Task Completion and Proactivity scores.
*   `data/detailed_results.json`: Full interaction logs (turn-by-turn) for the synthetic run.
*   `figures/comparison_bar.png`: A bar chart comparing the two metrics.

## How to Run
1.  Ensure `numpy`, `pandas`, `scikit-learn`, and `matplotlib` are installed.
2.  Run `python code/simulate_pi_bench.py`.
3.  Check `data/` and `figures/` for outputs.
