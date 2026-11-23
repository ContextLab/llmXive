# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip
- 2-core CPU (minimum), 6 GB RAM

## Installation
1. Clone the repository:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim
 ```
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Pipeline
### Single Scene
```bash
python code/cli.py --views 3 --seed 42
```
### Batch Processing
```bash
python code/experiments/run_batch.py --scenes 20 --timeout 21600
```

## Output
- Results are saved to `data/processed/`
- Logs are written to `logs/`
- State is updated in `state/projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim.yaml`

## Troubleshooting
- **CPU Memory Limit**: If OOM occurs, reduce scene complexity or resolution.
- **Convergence Failure**: Check logs for `LOW_TEXTURE_CONVERGENCE_FAILED` or `TIMEOUT_CONVERGENCE_FAILED`.
- **Baseline Skip**: If baseline TriSplat fails on CPU, it will be logged as `skipped`.
