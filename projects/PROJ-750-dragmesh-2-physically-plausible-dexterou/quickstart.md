# Quickstart: DragMesh-2 CPU Adaptation

This adaptation reproduces the core finding of DragMesh-2: **simple controllers fail as contact load (damping) increases**, validating the need for physically-aware policies like PICA.

## Prerequisites
- Python 3.8+
- `pybullet` (for physics simulation)
- `numpy`, `matplotlib`

```bash
pip install pybullet numpy matplotlib
```

## Run the Adaptation
Execute the single script to run the damping sweep, generate results, and create the plot.

```bash
python code/run_contact_sensitivity.py
```

## Output Artifacts
The script generates:
1.  `data/sweep_results.csv`: Contains the damping factor, success flag, and progress metric for each run.
2.  `figures/damping_sensitivity.png`: A visualization showing the drop in success rate as damping increases.

These artifacts confirm that without physical awareness (PICA), performance degrades under high contact loads, mirroring the paper's central claim.
