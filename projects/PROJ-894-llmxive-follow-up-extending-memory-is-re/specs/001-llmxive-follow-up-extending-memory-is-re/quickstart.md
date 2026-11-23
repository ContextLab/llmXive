# Quickstart: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

## Prerequisites

- Python 3.11+
- Git
- Substantial RAM (CPU-only environment)

## Installation

1. **Clone and Setup**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-894-llmxive-follow-up-extending-memory-is-re
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r code/requirements.txt
   ```

## Data Preparation

1. **Download LoCoMo Dataset**
   ```bash
   python code/data/download_locomo.py
   ```
   *Output*: `data/raw/locomo.csv`

2. **Generate Graphs & Noisy Variants**
   ```bash
   python code/data/generate_graphs.py
   python code/data/generate_noisy_graphs.py
   ```
   *Output*: `data/intermediate/graphs_raw.json`, `data/processed/noisy_graphs.json`

## Running the Benchmark

1. **Run Baseline (Full Strategy)**
   ```bash
   python code/analysis/runner.py --strategy full
   ```
   *Output*: `data/processed/baseline_results.csv`

2. **Run Heuristics (with Sensitivity Sweep)**
   ```bash
   python code/analysis/runner.py --strategy lazy --sweep
   python code/analysis/runner.py --strategy greedy
   ```
   *Output*: `data/processed/lazy_results.csv`, `data/processed/greedy_results.csv`

## Statistical Analysis

1. **Run Statistical Tests**
   ```bash
   python code/analysis/stats.py
   ```
   *Output*: `data/processed/stats_clean.json`, `data/processed/stats_noisy.json`

2. **Generate Report**
   ```bash
   python code/scripts/generate_stats_report.py
   ```
   *Output*: `report.md` (or similar summary)

## Testing

Run the test suite to verify data integrity and timeout handling:
```bash
pytest tests/
```

## Troubleshooting

- **Timeout Errors**: If a task exceeds 30 minutes, it will be logged as "TIMEOUT". Check `data/processed/results.csv` for the `status` column.
- **Memory Errors**: If OOM occurs, reduce the batch size or use a smaller model in `code/analysis/runner.py`.
- **Missing Data**: Ensure `data/raw/locomo.csv` exists and matches the expected checksum.