# Quickstart Guide: llmXive Follow-up

This guide provides instructions to set up the environment, generate synthetic data, run the digital colleague agent experiments, and analyze the results.

## Prerequisites

- Python 3.9+
- pip
- At least 8GB RAM recommended for full experiment runs

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 git clone <repository-url>
 cd PROJ-975-llmxive-follow-up-extending-from-chatbot
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure

- `code/`: Source code for data generation, agent execution, and analysis.
- `data/`:
 - `raw/`: Generated synthetic datasets (tasks, skills).
 - `results/`: Experiment logs, metrics, and analysis reports.
- `contracts/`: Schema definitions for data validation.
- `tests/`: Unit and contract tests.

## Execution Flow

### 1. Setup Directories and Contracts

Ensure the project structure and contract schemas are initialized:
```bash
python code/setup_directories.py
python code/setup_contracts.py
```

### 2. Generate Synthetic Data

Generate the skills library and task dataset:
```bash
python code/generate_data.py
```
This creates:
- `data/raw/skills.json`
- `data/raw/tasks.json`

### 3. Run Experiments

Execute the agent across different library sizes:
```bash
python code/run_experiment.py
```
Output:
- `data/results/experiment_log.csv`
- `data/results/metrics.json`

### 4. Run Baseline (No Pruning)

Compare against a baseline without pruning heuristics:
```bash
python code/run_baseline.py
```

### 5. Analyze Results

Perform statistical analysis, calculate tipping points, and generate the final report:
```bash
python code/analyze.py
```
Output:
- `data/results/final_analysis.json`
- `data/results/tipping_point.json`
- `data/results/sensitivity_report.json`

## Running Tests

Run the test suite to verify data integrity and logic:
```bash
pytest tests/ -v
```

## Troubleshooting

- **Memory Errors**: If you encounter memory issues during embedding generation, ensure you have at least 8GB of RAM. The script includes a check but may fail if the limit is exceeded.
- **Import Errors**: Ensure the virtual environment is activated and all dependencies from `requirements.txt` are installed.
- **Data Validation**: If schema validation fails, check `contracts/` for the latest schema definitions and ensure `generate_data.py` is up to date.

## Reproducibility

Random seeds are pinned in `code/config.py`. To ensure reproducibility across runs, set the environment variables `SEED_A` and `SEED_B` or rely on the defaults defined in the configuration.

For a full list of pinned seeds and dependencies, refer to `reproducibility_report.md` (generated after T038).