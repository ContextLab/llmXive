# Quickstart: NatureBench Abstraction Distance Analysis

## Prerequisites
- Python 3.11+
- Git
- Access to the HuggingFace CLI (if dataset is private) or public URL.
- **Note**: This project requires a **paid GitHub Actions plan** for full scale (90 tasks in 24h). The provided scripts are adapted for **free-tier** (batched execution).

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-783-naturebench-can-coding-agents-match-the
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dataset**:
    ```bash
    python code/download.py --verify-only
    ```
    *This checks if the NatureBench dataset is accessible. If not, it will automatically pivot to SWE-bench.*

## Running the Pipeline

### Step 1: Download Data
```bash
python code/download.py
```
*Downloads a subset of tasks from NatureBench or pivots to SWE-bench.*

### Step 2: Execute Agents (Batched)
*Adapted for free-tier compute (processes 5 tasks per job).*
```bash
python code/agent_runner.py --batch-size 5
```
*This will run a sufficient number of jobs (or fewer with parallelism) to complete all tasks.*

### Step 3: Score Abstraction Distance
```bash
python code/scorer.py
```

### Step 4: Run Analysis
```bash
python code/analysis.py
```
*Generates `data/processed/analysis_results.json` and `figures/correlation_plot.png`.*

## Validation

Run contract tests to ensure data integrity:
```bash
pytest tests/contract/
```

## Troubleshooting
- **Dataset Missing**: If `code/download.py` fails, it will automatically pivot to SWE-bench. Check the logs for the pivot message.
- **Memory Error**: Reduce `--batch-size` in `agent_runner.py`.
- **Timeout**: Ensure no background processes are consuming CPU.