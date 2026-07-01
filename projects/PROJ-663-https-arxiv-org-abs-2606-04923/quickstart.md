# Quickstart: CHERRL Reward Hacking Adaptation

This adaptation reproduces the core "Reward Divergence" result from the CHERRL paper using a scaled-down, CPU-tractable simulation. It uses real prompts from the HealthBench dataset but replaces the heavy LLM judge/agent with a rule-based proxy to demonstrate the hacking mechanism.

## Prerequisites
Ensure you are in the project root. The script expects the real dataset at `data/health_bench/raw/healthbench_eval.jsonl`. If you have not yet downloaded the external data, the script will fail (as per the "REAL data only" constraint).

## Installation
Install the lightweight dependencies required for data processing and plotting:
```bash
pip install pandas numpy matplotlib
```

## Run the Experiment
Execute the simulation script. It will load real prompts, simulate the agent hacking a biased judge, and output the divergence metrics.

```bash
python code/simulate_reward_hacking.py
```

## Verify Outputs
After the script finishes, check the generated artifacts:
1.  **Data**: `data/reward_divergence.csv` contains the step-by-step metrics (Biased Reward, True Quality, Divergence).
2.  **Figure**: `figures/hacking_curve.png` visualizes the growing gap between the biased reward and true quality, demonstrating the reward hacking phenomenon.

The plot should show the "Biased Judge Reward" rising significantly while "True Quality" remains flat or drops, confirming the paper's core finding.
