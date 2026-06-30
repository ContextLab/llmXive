# Causal Forcing++ Adaptation: CPU-Scale Reproduction

## Summary of Approximations
This adaptation reproduces the **core quantitative result** of the Causal Forcing++ paper: the **consistency of the flow-matching trajectory** between a teacher (48-step ODE) and a distilled student (2-step AR).

The original paper relies on:
1.  **Massive Models:** Wan2.1 (1.3B-14B parameters) running on GPUs.
2.  **Large Datasets:** LMDB-based video datasets (hundreds of GBs).
3.  **High Latency:** 48-step ODE integration per frame.

**This adaptation replaces them with:**
1.  **Proxy Model:** A 1D Convolutional Flow-Matching network (10k parameters) instead of Wan2.1. It learns a simple linear drift field $v_t = \mu - x_t$ where $\mu$ is a target "video" (synthetic sine-wave pattern).
2.  **Synthetic Data:** A generated batch of 4 "frames" (1D vectors of length 32) representing a simple motion pattern. No external dataset is needed.
3.  **CPU Execution:** All operations run on `torch.cpu`.
4.  **Metric:** We calculate the **Mean Squared Error (MSE)** between the 48-step teacher trajectory and the 2-step student trajectory. The paper claims this error is minimized by their "Causal Forcing" method. Here, we demonstrate the *mechanism*: we compute the error for a naive initialization vs. our "causal" initialization.

## What is Reproduced?
- **The Flow-Matching Logic:** The code implements the Flow-Matching ODE step $x_{t+1} = x_t + \Delta t \cdot v_t$.
- **The Distillation Gap:** We explicitly measure the gap between the long-trajectory teacher and the short-trajectory student.
- **The Result:** A CSV file (`data/results.csv`) showing that the "Causal" initialization (our simplified version of the paper's core claim) yields a lower trajectory error than a naive random initialization.

## Files Generated
- `data/teacher_trajectory.csv`: The 48-step ground truth path.
- `data/student_trajectory.csv`: The 2-step approximated path.
- `data/results.csv`: The quantitative comparison (MSE).
- `figures/flow_comparison.png`: A plot visualizing the two trajectories.
