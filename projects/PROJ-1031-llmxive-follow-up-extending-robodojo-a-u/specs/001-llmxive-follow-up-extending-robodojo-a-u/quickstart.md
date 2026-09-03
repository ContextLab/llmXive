# Quickstart: llmXive Follow-up: Extending RoboDojo with Symbolic Abstractions

## Prerequisites

- Python 3.11 or higher
- Git
- Access to Hugging Face (no token required for public datasets, but recommended for rate limits)
- (Optional) A physical robot arm for real-world execution (simulation mode available for testing logic).

## Installation

1. **Clone the repository**
 ```bash
 git clone
 cd llmxive-follow-up
 ```

2. **Create a virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Verify dataset access**
 Ensure you can access the Hugging Face datasets (Commit v3.0.1):
 ```bash
 python -c "from datasets import load_dataset; print(load_dataset('RoboDojo-Benchmark/RoboDojo', split='train', streaming=True))"
 ```

## Running the Pipeline

### Option 1: Symbolic Planning Only (CPU Test)
Tests the planner on a set of tasks without real-world execution.
```bash
python code/main.py --mode planning --tasks 18 --max-time 60
```
*Output*: `data/interim/planning_results.json`, logs in `logs/planning.log`.

### Option 2: Full Execution (Real-World + Oracle)
Requires a connected robot or a configured simulation environment for the Oracle.
```bash
python code/main.py --mode full --tasks 18 --oracle
```
*Output*: `data/interim/execution_logs.parquet`, `data/final/results.csv`.

### Option 3: Statistical Analysis Only
Runs the Wilcoxon test and generates the report from existing logs.
```bash
python code/main.py --mode analysis --input data/interim/execution_logs.parquet
```
*Output*: `data/final/statistical_report.txt`, `data/final/figures/`.

### Option 4: Ablation Study
Runs the planner with different state representations.
```bash
python code/main.py --mode ablation --tasks 18
```
*Output*: `data/interim/ablation_results.parquet`.

## Verification

To verify the system is working correctly:

1. **Check Memory Usage**: Run `python code/main.py --mode planning --tasks 1` and monitor RAM. It should stay within acceptable memory limits.
2. **Check Planner Speed**: Ensure the planner outputs a sequence within 60 seconds for a single task.
3. **Check Schema Validation**: Run `pytest tests/contract/` to ensure all generated data matches the `contracts/` schemas.

## Troubleshooting

- **OOM Error**: Reduce the `--batch-size` in `config.py` or enable `streaming=True` explicitly.
- **Dataset Download Failed**: Check your internet connection and Hugging Face status.
- **Planner Timeout**: Increase `--max-time` in the command line, but note this violates the 60s constraint for the primary metric.