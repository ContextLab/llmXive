# Quickstart Guide: llmXive Research Pipeline

## Prerequisites
- Python 3.11+
- pip

## Setup
1. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

2. Run the main pipeline:
 ```bash
 cd code
 python main.py
 ```

## Output
- Raw logs: `data/processed/execution_logs.csv`
- ANOVA results: `data/results/anova_results.json`
- Plots: `data/results/interaction_plot.png`

## Notes
- Ensure you have internet access to fetch datasets.
- CPU throttling requires root privileges on Linux; otherwise, the fallback mechanism will be used.