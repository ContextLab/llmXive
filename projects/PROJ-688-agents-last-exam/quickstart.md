# Quickstart: Agents' Last Exam (ALE) Adaptation

This guide runs the scaled-down quantitative reproduction of the "American Option Pricing" task from the ALE paper.
It uses pure CPU, `numpy`, and `scipy` to compute a real pricing result and verify it against a reference.

## Prerequisites
- Python 3.8+
- `numpy`, `scipy`, `matplotlib`

## Installation
```bash
pip install numpy scipy matplotlib
```

## Execution
Run the adaptation script:
```bash
python code/run_ale_adaptation.py
```

## Verification
After execution, check the generated artifacts:
1.  **`data/ale_result.json`**: Contains the computed price, reference price, error metrics, and pass/fail status.
2.  **`figures/pricing_distribution.png`**: A histogram of the simulated cash flows.

The script is designed to run in < 30 seconds on a standard CPU.
