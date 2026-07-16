# llmXive: From Chatbot to Digital Colleague

An automated research pipeline investigating the impact of skill library size and semantic overlap on the performance of a "Digital Colleague" agent. This project generates synthetic Python tasks and skills, executes an agent with retrieval-based augmentation, and analyzes the results to identify performance tipping points.

## Prerequisites

- Python 3.9+
- pip
- ~14 GB free disk space (for data and dependencies)
- ~8 GB RAM recommended (for embedding calculations)

## Installation

1. **Clone the repository** (or navigate to the project root):
 ```bash
 git clone <repository-url>
 cd PROJ-975-llmxive-follow-up-extending-from-chatbot
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Verify installation**:
 ```bash
 python -c "from code.config import SEED_A; print(f'Config OK: SEED_A={SEED_A}')"
 ```

## Project Structure

- `code/`: Core implementation scripts
 - `generate_data.py`: Generates synthetic skills and tasks.
 - `agent.py`: The Digital Colleague agent with retrieval logic.
 - `run_experiment.py`: Orchestrates experiments across library sizes.
 - `run_baseline.py`: Runs experiments with pruning disabled.
 - `analyze.py`: Statistical analysis and tipping point detection.
 - `config.py`, `utils.py`, `logging_config.py`: Shared utilities.
- `data/`:
 - `raw/`: Generated synthetic datasets (`skills.json`, `tasks.json`).
 - `results/`: Experiment logs (`experiment_log.csv`), analysis outputs (`final_analysis.json`).
- `contracts/`: Schema definitions for data validation.
- `tests/`: Unit and integration tests.
- `specs/`: Design documents and user stories.

## Quick Start

To run the full pipeline from data generation to final analysis:

1. **Generate Data**:
 ```bash
 python code/generate_data.py
 ```
 *Output*: `data/raw/skills.json`, `data/raw/tasks.json`

2. **Run Experiments** (with pruning):
 ```bash
 python code/run_experiment.py
 ```
 *Output*: `data/results/experiment_log.csv`, `data/results/metrics.json`

3. **Run Baseline** (without pruning):
 ```bash
 python code/run_baseline.py
 ```
 *Output*: `data/results/experiment_log_baseline.csv`

4. **Analyze Results**:
 ```bash
 python code/analyze.py
 ```
 *Output*: `data/results/final_analysis.json`, `data/results/sensitivity_report.json`

## Configuration

The pipeline uses random seeds for reproducibility. Configure them via environment variables:

- `SEED_A`: Seed for skill generation (default: 42)
- `SEED_B`: Seed for task ground-truth assignment (default: 123)

Example:
```bash
export SEED_A=100
export SEED_B=200
python code/generate_data.py
```

## Testing

Run the test suite to verify implementation:

```bash
pytest tests/ -v
```

## License

This project is part of the llmXive research initiative. See LICENSE for details.