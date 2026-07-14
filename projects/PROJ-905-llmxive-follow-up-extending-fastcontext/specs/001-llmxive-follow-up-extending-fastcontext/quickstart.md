# Quickstart: llmXive follow-up: extending "FastContext: Training Efficient Repository Explorer for Coding Agents"

## Prerequisites
- Python 3.11+
- Git
- Sufficient RAM (recommended for data processing)
- Disk space: Sufficient capacity for the SWE-bench subset

## Installation

1.  **Clone and Setup Environment**
    ```bash
    cd projects/PROJ-905-llmxive-follow-up-extending-fastcontext
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Download Data**
    The script below will fetch the SWE-bench Lite subset. Ensure you have sufficient disk space.
    ```bash
    python code/main.py --action download_data
    ```
    *Note: This step may take time depending on network speed. Checksums are verified automatically.*

## Running the Experiment

### Step 1: Compute Regularity Scores
This step analyzes the file structure of all repositories in the dataset.
```bash
python code/main.py --action score_regularity
```
*Output*: `data/processed/regularity_scores.csv`

### Step 2: Execute FastContext-Lite
Runs the deterministic engine on the stratified dataset.
```bash
python code/main.py --action run_lite
```
*Output*: Appends to `data/results/exploration_logs.jsonl`

### Step 3: Execute Baseline (Distilled 1.5B)
Runs the distilled baseline (CPU-optimized). **Warning**: This may take several hours.
```bash
python code/main.py --action run_baseline --limit
```
*Note*: The `--limit` flag restricts the run to a subset of repositories (the "Regular" set) to ensure the job completes within the 6h CI limit.

### Step 4: Statistical Analysis
Generates the final comparison metrics.
```bash
python code/main.py --action analyze
```
*Output*: `data/results/statistical_summary.json`

## Verification
To verify the pipeline on a single repository:
```bash
python code/main.py --action verify --repo swe-bench-{identifier}
```
This runs the scoring and Lite execution for one repo and prints the metrics to stdout.

## Troubleshooting
- **Memory Error**: If you encounter `MemoryError`, reduce the `--limit` flag or process repositories in smaller batches.
- **GPU Detected**: The script explicitly checks for CUDA. If a GPU is found, it will warn but proceed in CPU mode. Ensure `CUDA_VISIBLE_DEVICES=""` if you want to force CPU-only behavior in a mixed environment.
- **Baseline Load Failure**: If the target model fails to load, the script will automatically fall back to the "Rule-Only" baseline and log a warning.