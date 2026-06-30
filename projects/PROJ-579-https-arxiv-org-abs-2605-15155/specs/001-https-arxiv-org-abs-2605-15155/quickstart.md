# SDAR Simulation Quickstart

This guide runs the CPU-tractable simulation of the **Self-Distilled Agentic Reinforcement Learning (SDAR)** paper.
The simulation reproduces the core finding: SDAR's gated distillation mechanism stabilizes training when the teacher signal is noisy, outperforming naive GRPO+OPSD.

## Prerequisites
- Python 3.8+
- `numpy`
- `matplotlib`

Install dependencies if needed:
```bash
pip install numpy matplotlib
```

## Run Commands
Execute the simulation script to generate `data/sdar_results.csv`, `data/sdar_summary.json`, and `figures/*.png`.

```bash
python code/sdar_sim.py
```

## Expected Outputs
1. **Console**: Summary of success rates and gate values for different noise levels.
2. **`data/sdar_results.csv`**: Detailed metrics for SDAR vs. Naive methods.
3. **`data/sdar_summary.json`**: JSON summary of the key finding (improvement at high noise).
4. **`figures/success_rate_vs_noise.png`**: Plot showing SDAR's robustness.
5. **`figures/gate_attenuation.png`**: Plot showing the gate's behavior under noise.
