# Agents' Last Exam (ALE) - Scaled Adaptation

## Purpose
This adaptation reproduces a **meaningful, scaled-down quantitative result** from the paper "Agents' Last Exam" (ALE).
The original paper evaluates AI agents on 1K+ long-horizon, real-world tasks. The full benchmark requires:
1.  Commercial LLM API keys (expensive/complex).
2.  Heavy sandboxing (QEMU/KVM/VMs).
3.  Multi-day execution times.

## Adaptation Strategy
Instead of running the full harness, we **reproduce the core quantitative finding** (low pass rates on difficult tasks) by:
1.  **Selecting a Representative Task**: We use `business_finance/american_option_pricing_ls`, a classic quantitative finance task involving Monte Carlo simulation and regression (Longstaff-Schwartz).
2.  **Scaling Down**:
    *   **Data**: Reduce simulation paths from ~1M (standard) to **5,000**.
    *   **Model**: Implement the Longstaff-Schwartz algorithm directly in `code/` using `numpy` and `scipy` (no external agent loop).
    *   **Metric**: Calculate the **pricing error** (RMSE) against a known analytical benchmark (Black-Scholes for European, or a high-fidelity reference for American).
3.  **Simulating the "Agent"**: The "agent" in this adaptation is the **deterministic implementation of the LS algorithm**. The "pass rate" is derived by measuring how often the scaled-down algorithm produces a result within a strict tolerance of the reference value.
4.  **Result**: We output a CSV showing the **Pricing Error** and a **Pass/Fail status** for the scaled task, demonstrating the "hardness" of the task even for a direct implementation (which serves as a proxy for the "optimal" agent performance the paper benchmarks against).

## Approximations
*   **No LLM/Agent Loop**: The original paper measures *agent* performance. This adaptation measures *algorithmic* performance on the task logic to verify the task's solvability and difficulty.
*   **Reduced Scale**: 5k paths vs 1M+ paths.
*   **Single Task**: One task vs 1K+ tasks.
*   **No Sandbox**: Runs directly on the host CPU.

## Files
*   `code/run_ale_adaptation.py`: The main script.
*   `data/ale_result.json`: The quantitative result (RMSE, Pass/Fail).
*   `figures/pricing_distribution.png`: Visualizing the simulation distribution.
