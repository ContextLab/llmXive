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
# Generate the default technical‑term list (if you want to override, edit `code/config/user_terms.json` first)
python code/generate_terms.py

# Generate synthetic trajectories (500 trajectories, seed 42)
python code/generate_trajectories.py --num-trajectories 500 --seed 42

# Validate trajectories
python code/validate_trajectories.py

# Simulate the agent (uses default input/output paths)
python code/simulate_agent.py --seed 42

# Analyze results
python code/analyze_results.py --input data/logs/simulation_results.csv --output-dir results
```

Adjust the `--num-trajectories` and `--seed` arguments as needed. The pipeline will
produce the required JSON, CSV, and PNG artifacts in the `data/` and `results/`
directories.