# Quickstart Guide

## Project: llmXive Follow-up
**Title**: Extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

## Prerequisites

Ensure you have Python 3.9+ and `pip` installed.

## Installation

1. Clone the repository and navigate to the project root.
2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure

- `data/raw/`: Generated synthetic datasets (tasks, skills)
- `data/results/`: Experiment logs, analysis outputs, and figures
- `code/`: Implementation modules (data generation, agent, analysis)
- `tests/`: Unit and contract tests
- `contracts/`: JSON schemas for data validation
- `state/`: Project state tracking and artifact hashes

## Running the Pipeline

### 1. Setup Project Directories
Ensure the required directory structure exists:
```bash
python code/setup_directories.py
```

### 2. Generate Synthetic Data (User Story 1)
Generate 500 multi-step tasks and a skill library with configurable overlap:
```bash
python code/generate_data.py
```
**Outputs**:
- `data/raw/tasks.json`
- `data/raw/skills.json`
- `state/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot.yaml` (checksums)

### 3. Run Agent Experiments (User Story 2)
Execute the Digital Colleague agent across varying library sizes:
```bash
python code/run_experiment.py
```
**Outputs**:
- `data/results/experiment_log.csv` (detailed execution logs)
- `data/results/baseline_metrics.json` (if baseline run)

### 4. Analyze Results (User Story 3)
Perform statistical analysis, calculate VIF, and identify the tipping point:
```bash
python code/analyze.py
```
**Outputs**:
- `data/results/tipping_point.json`
- `data/results/sensitivity_report.json`
- `data/results/final_analysis.json`

## Configuration

Environment variables can override defaults in `code/config.py`:
- `SEED_A`: Random seed for skill generation (default: 42)
- `SEED_B`: Random seed for task ground-truth assignment (default: 123)
- `OVERLAP_LEVEL`: 'low', 'medium', or 'high' (default: 'medium')

## Verification

Run tests to ensure system integrity:
```bash
pytest tests/
```

## Troubleshooting

- **Memory Errors**: The system checks RAM usage. If you encounter "Memory Limit Exceeded", reduce the dataset size or run on a machine with more RAM.
- **Schema Validation Errors**: Ensure `contracts/*.yaml` files are present and match the data structure.
- **Missing Data**: Re-run `generate_data.py` if `data/raw/` is empty.

## Next Steps

Refer to `README.md` for detailed architecture and `specs/` for feature requirements.