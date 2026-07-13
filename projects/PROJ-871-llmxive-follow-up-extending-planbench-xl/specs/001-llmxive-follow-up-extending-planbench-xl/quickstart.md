# Quickstart: llmXive follow-up: extending "PlanBench-XL: Evaluating Long-Horizon Planning of LLM Tool-Use Agents "

## 1. Prerequisites

- **Python**: 3.11+
- **Dependencies**: Install via `pip install -r requirements.txt`
- **Hardware**: CPU-only environment (2+ cores, 7GB+ RAM). No GPU required.

## 2. Installation

1. **Clone the repository** and navigate to the project directory.
   ```bash
   cd projects/PROJ-871-llmxive-follow-up-extending-planbench-xl
   ```

2. **Create a virtual environment** and install dependencies.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r code/requirements.txt
   ```

3. **Download the dataset** (if not already present).
   ```bash
   python code/dataset/loader.py --download
   ```
   *Note: This script downloads the PlanBench dataset from the verified URL and stores it in `data/raw/`.*

## 3. Running the Experiment

### Step 1: Construct the Failure Signature Index
```bash
python code/dataset/indexer.py
```
This generates `data/derived/failure_signatures.json`.

### Step 2: Execute Baseline Agent
```bash
python code/agents/baseline.py --output data/logs/baseline_execution_log.json
```

### Step 3: Execute Augmented Agent
```bash
python code/agents/augmented.py --output data/logs/augmented_execution_log.json
```

### Step 4: Statistical Analysis
```bash
python code/analysis/stats.py --baseline data/logs/baseline_execution_log.json --augmented data/logs/augmented_execution_log.json --report data/report.md
```

## 4. Expected Outputs

- **`data/logs/baseline_execution_log.json`**: Execution logs for the baseline agent.
- **`data/logs/augmented_execution_log.json`**: Execution logs for the augmented agent.
- **`data/report.md`**: Final report containing success rates, statistical test results, and conclusion.

## 5. Troubleshooting

- **OOM Errors**: If you encounter Out of Memory errors, reduce the number of tasks in the subset or use a smaller LLM model.
- **Timeout Errors**: If the experiment exceeds 6 hours, check the model size and the number of tasks. Consider sampling a smaller subset.
- **Dataset Not Found**: Ensure the verified URL in `code/dataset/loader.py` is correct and accessible.

## 6. Verification

To verify the setup, run the unit tests:
```bash
pytest tests/unit/
```
