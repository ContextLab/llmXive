# Quickstart: llmXive follow-up: extending "From Chatbot to Digital Colleague"

## Prerequisites

- Python 3.11+
- `pip` (or `venv`/`poetry`)
- Multiple CPU cores, 4 GB+ RAM (recommended for smooth execution)

## Installation

1. **Clone and Navigate**:
   ```bash
   cd projects/PROJ-975-llmxive-follow-up-extending-from-chatbot
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins `sentence-transformers` to a version compatible with CPU-only execution.*

## Data Generation

Generate the synthetic dataset:

```bash
python code/generate_data.py --tasks 500 --skills 100 --overlap high --seed 42
```

**Output**:
- `data/raw/tasks.json`
- `data/raw/skills.json`

Verify the data:
```bash
python -c "import json; print(len(json.load(open('data/raw/tasks.json'))))"
# Expected:
```

## Running the Experiment

Execute the agent with the default configuration (all library sizes, with and without pruning):

```bash
python code/agent.py --config code/config.py --output data/results/experiment_log.csv
```

**Output**:
- `data/results/experiment_log.csv` containing metrics for all runs.

## Analysis

Run the statistical analysis to identify the tipping point and pruning effects:

```bash
python code/analyze.py --input data/results/experiment_log.csv --output data/results/analysis_report.json
```

**Output**:
- `data/results/analysis_report.json` containing:
  - Breakpoint ($x_0$) for the tipping point.
  - P-values for pruning effectiveness.
  - VIF scores for collinearity.

## Validation

Run the contract tests to ensure data integrity:

```bash
pytest tests/contract/
```

## Troubleshooting

- **Memory Error**: If you encounter `MemoryError`, reduce the `--tasks` count or ensure no other heavy processes are running. The default config is designed for < 2 GB RAM.
- **Import Error**: Ensure you are using Python 3.11 and that the virtual environment is activated.
- **Slow Execution**: This is expected if `sentence-transformers` is downloading the model for the first time. Subsequent runs will be cached.
