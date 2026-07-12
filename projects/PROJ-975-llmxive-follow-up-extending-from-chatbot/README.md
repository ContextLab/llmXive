# llmXive: From Chatbot to Digital Colleague

Automated research pipeline for evaluating skill-library scaling effects in LLM agents.

## Project Overview

This project implements a synthetic environment to study how the size and semantic density of a skill library affect an LLM agent's ability to solve multi-step tasks. It includes:
- Synthetic dataset generation (tasks and skills)
- A minimal "Digital Colleague" agent with retrieval and execution logic
- Pruning heuristics to manage library growth
- Statistical analysis of performance tipping points

## Prerequisites

- Python 3.10+
- pip (Python package installer)
- A Unix-like environment (Linux/macOS) or WSL on Windows

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 cd PROJ-975-llmxive-follow-up-extending-from-chatbot
 ```

2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

4. (Optional) Install pre-commit hooks for code quality:
 ```bash
 pre-commit install
 ```

## Configuration

Set the following environment variables to control random seeds for reproducibility:

- `SEED_A`: Seed for skill generation (default: 42)
- `SEED_B`: Seed for task generation (default: 123)

Example:
```bash
export SEED_A=42
export SEED_B=123
```

## Quick Start

Follow the detailed steps in `quickstart.md` to run the full pipeline.

### 1. Generate Synthetic Data

Generate 100 skills and 500 tasks:
```bash
python code/generate_data.py
```
Output:
- `data/raw/skills.json`
- `data/raw/tasks.json`

### 2. Run the Experiment

Execute the agent across varying library sizes:
```bash
python code/run_experiment.py
```
Output:
- `data/results/experiment_log.csv`
- `data/results/metrics.json`

### 3. Run Baseline (No Pruning)

```bash
python code/run_baseline.py
```
Output:
- `data/results/experiment_log_baseline.csv`

### 4. Analyze Results

Perform statistical analysis and generate the final report:
```bash
python code/analyze.py
```
Output:
- `data/results/final_analysis.json`
- `data/results/sensitivity_report.json`

## Project Structure

```
.
├── code/ # Source code
│ ├── config.py # Configuration and seeds
│ ├── utils.py # Embedding and similarity helpers
│ ├── logging_config.py # Logging infrastructure
│ ├── generate_data.py # Synthetic data generation
│ ├── agent.py # Agent logic
│ ├── run_experiment.py # Experiment runner
│ ├── run_baseline.py # Baseline runner (no pruning)
│ ├── analyze.py # Statistical analysis
│ └──...
├── data/
│ ├── raw/ # Generated datasets
│ └── results/ # Experiment logs and analysis outputs
├── tests/ # Unit and contract tests
├── contracts/ # JSON/YAML schemas
├── requirements.txt # Dependencies
├── README.md # This file
└── quickstart.md # Step-by-step execution guide
```

## Testing

Run unit and contract tests:
```bash
pytest tests/
```

## Reproducibility

All experiments are deterministic when `SEED_A` and `SEED_B` are set.
Dependencies are pinned in `requirements.txt`.

## License

MIT License