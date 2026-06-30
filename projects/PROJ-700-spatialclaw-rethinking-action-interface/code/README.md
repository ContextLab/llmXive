# SpatialClaw CPU Adaptation

## Purpose
This adaptation reproduces the **core evaluation logic** of the SpatialClaw paper (specifically the `erqa` benchmark) on a CPU-only, resource-constrained environment. It replaces the heavy VLM-backed agent loop with a **deterministic, rule-based proxy** that simulates the "code-as-action" interface using standard Python libraries.

## Simplifications & Approximations
1.  **No VLM Backend**: The original paper uses large VLMs (e.g., Qwen3.5-122B) to generate code. We replace this with a **static rule-based generator** that constructs simple Python code snippets based on question heuristics (e.g., counting objects in a simulated list). This allows us to test the *framework's* ability to execute code and aggregate results without needing a GPU or API.
2.  **Dataset Subsampling**: We use the `erqa` benchmark configuration but strictly limit execution to **5 samples** (instead of hundreds) to ensure the run finishes within the 20-minute window.
3.  **No Real Images**: The original agent processes real video frames. This adaptation simulates "frame data" as simple integer lists (e.g., `[1, 2, 3]` representing object IDs) to demonstrate the `kernel` execution capability without loading multi-megabyte image files.
4.  **Single-Threaded Execution**: The original uses async concurrency. We use a simple sequential loop for stability on 2-core CI.

## What is Preserved
-   The **`spatial_agent` configuration loading** logic (JSON parsing, env expansion).
-   The **`AgentState`** structure (tracking steps, variables, and final answers).
-   The **evaluation metric** (Accuracy: predicted answer vs. ground truth).
-   The **output artifacts** (`data/results.csv`, `figures/accuracy_bar.png`).

## Limitations
-   This does **not** evaluate the VLM's reasoning capabilities (since we don't use a VLM).
-   It evaluates the **pipeline robustness**: Can the config load? Can the "kernel" execute code? Can the results be aggregated?
-   If the paper's claim is "The VLM + Code Interface improves accuracy," this adaptation verifies "The Code Interface pipeline works correctly," but the accuracy score is a placeholder for the framework's validity, not the VLM's performance.
