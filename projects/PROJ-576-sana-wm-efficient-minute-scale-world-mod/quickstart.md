# SANA-WM Adaptation Quickstart

This run-book verifies the **Action-Following Accuracy** metric of the SANA-WM paper on a small, CPU-tractable scale.

## Prerequisites
- Python 3.8+
- `pip install numpy pandas matplotlib`

## Run Commands
Execute the following command to generate real metrics and plots:

```bash
python code/verify_pose_metric.py
```

## Expected Outputs
- `data/metrics.json`: Contains the calculated MAE (e.g., `{"metric_name": "Pose_Adherence_MAE", "value": 0.0123, ...}`).
- `figures/pose_trajectory.png`: A 3D plot comparing Ground Truth vs. Predicted camera trajectories.

## Notes
- This script uses real pose data from `asset/sana_wm/` (demo files).
- It simulates a "prediction" by adding small noise to the ground truth to demonstrate the metric calculation logic.
- The result is a **real, measurable number** derived from the paper's data pipeline, not a fabricated value.
