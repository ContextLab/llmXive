# Quickstart: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

## Prerequisites

- Python 3.11+
- Git
- Access to a terminal with network connectivity (for downloading datasets)

## Installation

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd projects/PROJ-894-llmxive-follow-up-extending-memory-is-re
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

   *Note: `requirements.txt` includes `pandas`, `networkx`, `scipy`, `numpy`, `datasets`, `tqdm`, and `pytest`.*

## Running the Pipeline

### 1. Download Data
The pipeline automatically downloads the LoCoMo dataset on first run. To manually trigger download:
```bash
python code/data/downloader.py
```
*Data will be saved to `data/raw/`.*

### 2. Execute Baseline (Full Strategy)
Run the baseline strategy on the clean dataset:
```bash
python code/main.py --strategy Full --dataset clean
```

### 3. Execute Heuristics (Lazy & Greedy)
Run the heuristic strategies:
```bash
python code/main.py --strategy Lazy --dataset clean
python code/main.py --strategy Greedy --dataset clean
```

### 4. Run Robustness Test (Noisy Graph)
Run the baseline and heuristics on the synthetic noisy graph:
```bash
python code/main.py --strategy Full --dataset noisy
python code/main.py --strategy Lazy --dataset noisy
python code/main.py --strategy Greedy --dataset noisy
```

### 5. Generate Statistical Report
Once all execution logs are generated, run the analysis:
```bash
python code/analysis/statistics.py
```
*Output: `data/processed/statistics.json` and `data/processed/results.csv`.*

## Testing

Run the unit and integration tests:
```bash
pytest tests/ -v
```

## Troubleshooting

- **Timeout Errors**: If a task exceeds 30 minutes, it will be logged as "TIMEOUT". The pipeline will continue to the next task.
- **Missing Data**: Ensure `data/raw/` contains `locomo.csv`. If missing, re-run the downloader.
- **Memory Issues**: If you encounter memory errors, reduce the `batch_size` in `config.yaml` (if applicable) or ensure no other heavy processes are running.
