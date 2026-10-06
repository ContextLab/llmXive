# Quickstart: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

## Prerequisites

- Python 3.11+
- `pip`
- 7 GB RAM (recommended)

## Installation

1. **Clone and Enter**:
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
   pip install -r code/requirements.txt
   ```

## Running the Experiment

### Step 1: Generate Synthetic Data
```bash
python code/generate_data.py --seed 42 --overlap "high"
```
*Output*: `data/raw/tasks.json`, `data/raw/skills.json`, and updated `state/...yaml`.

### Step 2: Run Agent Experiment
```bash
python code/agent.py --library-sizes 10 30 50 100 --pruning
```
*Output*: `data/results/metrics.csv`.

### Step 3: Analyze Results
```bash
python code/analysis.py --input data/results/metrics.csv
```
*Output*: `data/results/analysis_report.json` (includes tipping point, VIF, p-values).

## Validating Contracts

Run the contract tests to ensure data integrity:
```bash
pytest tests/contract/
```

## Troubleshooting

- **Memory Error**: Reduce `--library-size` or `--overlap` complexity.
- **Schema Mismatch**: Ensure `data/raw/*.json` matches `contracts/*.yaml`. Run `pytest tests/contract/` to debug.
- **Missing Checksums**: Re-run `generate_data.py` to regenerate checksums in `state/...yaml`.
