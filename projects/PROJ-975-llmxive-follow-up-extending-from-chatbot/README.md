# llmXive: From Chatbot to Digital Colleague

An automated research pipeline investigating the impact of semantic overlap in skill libraries on agent performance, specifically focusing on the "tipping point" where retrieval precision degrades.

## Project Overview

This project implements a synthetic environment to generate multi-step tasks and a configurable library of Python "skills" with controlled semantic density. It runs a minimalistic "Digital Colleague" agent across varying library sizes to record task completion rates, token usage, latency, and retrieval metrics. The pipeline includes statistical analysis (Piecewise Linear Regression, VIF calculation) to identify the library size threshold where performance collapses.

## Prerequisites

- Python 3.9+
- pip
- (Optional) `pre-commit` for linting/formatting

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd llmxive-follow-up-extending-from-chatbot
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Install pre-commit hooks** (optional but recommended):
 ```bash
 pre-commit install
 ```

## Configuration

The system uses deterministic seeds for reproducibility. Seeds are defined in `code/config.py` and can be overridden via environment variables:

- `SEED_A`: Seed for skill generation (embedding space).
- `SEED_B`: Seed for ground-truth task assignment.

Example:
```bash
export SEED_A=42
export SEED_B=123
python code/generate_data.py
```

## Usage

### 1. Setup Project Structure
Ensure the required directory structure exists:
```bash
python code/setup_directories.py
```

### 2. Generate Synthetic Data
Generate the skill library and multi-step tasks:
```bash
python code/generate_data.py
```
**Outputs**:
- `data/raw/skills.json`: Generated skills with embeddings.
- `data/raw/tasks.json`: Tasks with ground-truth solution paths.
- `data/raw/checksums.json`: SHA-256 checksums for data integrity.

### 3. Run Experiments
Execute the agent across various library sizes to collect performance metrics:
```bash
python code/run_experiment.py
```
**Outputs**:
- `data/results/experiment_log.csv`: Detailed log of every task execution.
- `data/results/metrics.json`: Aggregated metrics per library size.

### 4. Run Baseline (No Pruning)
Run the experiment with pruning disabled for comparison:
```bash
python code/run_baseline.py
```
**Outputs**:
- `data/results/experiment_log_baseline.csv`: Baseline execution log.

### 5. Analyze Results
Perform statistical analysis to identify the "tipping point" and validate model assumptions:
```bash
python code/analyze.py
```
**Outputs**:
- `data/results/final_analysis.json`: Comprehensive report including VIF, p-values, and tipping point.
- `data/results/tipping_point.json`: Primary tipping point from Piecewise Linear Regression.
- `data/results/sensitivity_report.json`: Results from sensitivity analysis on pruning thresholds.

## Project Structure

```
.
├── code/ # Implementation modules
│ ├── config.py # Configuration and seeds
│ ├── generate_data.py # Data generation logic
│ ├── agent.py # Agent execution and retrieval
│ ├── run_experiment.py # Experiment orchestration
│ ├── run_baseline.py # Baseline experiment runner
│ ├── analyze.py # Statistical analysis
│ ├── utils.py # Helper functions (embeddings, metrics)
│ └── logging_config.py # Logging infrastructure
├── data/
│ ├── raw/ # Generated datasets (skills, tasks)
│ └── results/ # Experiment logs and analysis outputs
├── contracts/ # JSON Schema definitions
├── tests/ # Unit and contract tests
├── requirements.txt # Python dependencies
├── README.md # This file
└── quickstart.md # Quick start guide
```

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run contract tests:
```bash
pytest tests/contract/
```

Run integration tests:
```bash
pytest tests/integration/
```

## Reproducibility

All random seeds are pinned in `code/config.py`. To verify reproducibility:
```bash
python code/config.py --validate
```
See `reproducibility_report.md` for a full list of pinned seeds and their sources.

## License

MIT License