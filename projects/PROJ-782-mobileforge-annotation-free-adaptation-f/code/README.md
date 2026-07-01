# MobileForge CPU Adaptation

## Purpose
This directory contains a **scaled-down, CPU-tractable adaptation** of the MobileForge rollout analysis pipeline. The original system relies on heavy GPU-based MLLM rollouts on Android emulators, which is impossible to run in a standard CI environment (2 cores, no GPU).

## Adaptations Made
1.  **Data Source**: Replaced real emulator rollout logs with a **deterministic synthetic generator** (`SyntheticRolloutGenerator`). This generator produces a dataset with the statistical properties (Pass@3 ~67.2%, loop rates, error distributions) reported in the paper, ensuring the analysis logic is tested on "realistic" data without needing a physical device.
2.  **Metrics Engine**: Re-implemented the core `MetricsComputer` and `DataFilter` logic from `rollout/data_analyzer` to run purely in Python/NumPy.
3.  **Visualization**: Added `matplotlib` plotting to generate `figures/pass_rate_comparison.png`, replacing the HTML dashboard which is harder to verify in a simple CI gate.

## Artifacts Produced
- `data/analysis_summary.json`: JSON report with baseline and filtered metrics.
- `figures/pass_rate_comparison.png`: Bar chart comparing pass rates across apps.

## Running
See `quickstart.md` for the command to execute the analysis.
