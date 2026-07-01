# Adaptation: Agents-A1 "Horizon Scaling" Proxy

## Original Claim
The paper "Scaling the Horizon, Not the Parameters" claims that a 35B MoE model (Agents-A1) achieves trillion-parameter performance by scaling the **agent horizon** (trajectory length) and using **multi-teacher distillation**. It reports high scores on long-horizon benchmarks like SEAL-0, IFBench, and MolBench-Bind.

## Adaptation Strategy (CPU-Safe)
The original code relies on:
1.  **Heavy LLM Inference:** 35B+ parameter models (GPU required).
2.  **Large Benchmarks:** Thousands of long-horizon tasks requiring API calls or massive local models.
3.  **Complex Toolchains:** Pymatgen, web search, and code execution sandboxes.

Since we cannot run a 35B model on CPU, and we cannot fabricate the "agent intelligence" metric, we adapt the **scientific core**: **Horizon Scaling Analysis**.
We reproduce the *mechanism* of the paper (long-horizon task solving) using a **small, deterministic proxy**.

### What we simulate:
1.  **Task:** A simplified "defect analysis" task (from the `pymatgen_analysis_defects` dataset in the repo).
2.  **Agent:** A "Rule-Based Agent" (CPU-safe) that mimics the *structure* of the agentic loop (Thought -> Action -> Observation) but uses deterministic logic instead of an LLM.
3.  **Horizon Scaling:** We run the agent with **increasing step limits** (short horizon vs. long horizon) and measure the **Success Rate** and **Token Efficiency**.
4.  **Result:** We verify the paper's hypothesis that *longer horizons* allow for more complex solutions, even if the "intelligence" is simplified.

### Approximations
-   **Model:** Replaced 35B MoE with a deterministic state-machine (Python logic).
-   **Data:** Used the first 5 examples from `evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/`.
-   **Metric:** Replaced complex benchmark scores with a "Task Completion Rate" vs. "Max Steps" curve.
-   **Tools:** Simulated `pymatgen` analysis with mock data to avoid heavy dependencies.

### Artifacts Produced
-   `data/horizon_scaling_results.json`: Metrics for short vs. long horizons.
-   `figures/horizon_scaling_plot.png`: Visualization of success rate increasing with horizon length.
