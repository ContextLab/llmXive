# Quickstart

This minimal quickstart outlines the steps to set up and run the synthetic trajectory
generation pipeline for the project.

## Setup

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Run the pipeline

```bash
# Generate synthetic trajectories
python code/generate_trajectories.py --num-trajectories 500 --seed 42

# Validate trajectories
python code/validate_trajectories.py --input data/raw/trajectories.json

# Simulate the agent
python code/simulate_agent.py --input data/raw/trajectories.json --seed 42

# Analyze results
python code/analyze_results.py --input data/logs/simulation_results.csv --output-dir results
```

Adjust the `--num-trajectories` and `--seed` arguments as needed. The pipeline will
produce the required JSON, CSV, and PNG artifacts in the `data/` and `results/`
directories.