# OPID Adaptation Quickstart

This guide runs the scaled-down OPID adaptation on CPU.

## Prerequisites
Ensure `numpy`, `matplotlib`, and `scikit-learn` are installed.
```bash
pip install numpy matplotlib scikit-learn
```

## Run the Adaptation
Execute the following command to generate the results and figures:

```bash
python code/opid_adaptation.py
```

## Expected Outputs
- `data/opid_results.json`: JSON file containing the success rates and advantage metric.
- `figures/opid_comparison.png`: Bar chart comparing Baseline vs. OPID performance.

## Interpretation
The script simulates the OPID mechanism by augmenting state text with "skill" instructions and measuring the performance lift of a tiny policy (Logistic Regression) on a simplified version of ALFWorld tasks derived from the real PDDL files in the repository. A positive "advantage" confirms the core paper claim that skill distillation improves policy performance.
