# Quickstart: State-Guided Curriculum for MobileGym

## Prerequisites

* Python 3.11+
* Git
* GB+ Disk Space
* Sufficient RAM (Recommended for CPU inference)

## 1. Environment Setup

```bash
# Clone the project repository
git clone <REPO_URL>
cd projects/PROJ-858-llmxive-follow-up-extending-mobilegym-a

# Create a virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Data Acquisition

**MobileGym Tasks**:
The MobileGym environment and task definitions must be downloaded from the official repository.
* *Source*: ` (Tag: `v1.0.0` or latest stable).
* *Command*:
 ```bash
 # Example command (replace with actual official URL and commit hash)
 git clone https://github.com/mobilegym/mobilegym.git data/raw/mobilegym
 cd data/raw/mobilegym
 git checkout <RESOLVED_COMMIT_HASH> # Resolve this hash from the repo
 ```
* **Checksum**: Immediately after download, run:
 ```bash
 sha256sum data/raw/mobilegym > data/raw/.checksums.txt
 # Record the commit hash in the checksum file as well
 echo "commit_hash: <RESOLVED_COMMIT_HASH>" >> data/raw/.checksums.txt
 ```

## 3. Configuration

Edit `code/utils/constants.py` to set:
* `MAX_WALL_CLOCK_HOURS = 6`
* `TRAINING_TASKS_SUBSET = 50` (To ensure 6h completion)
* `TEST_TASKS_COUNT = 256`
* `MODEL_QUANTIZATION = "4bit"` (For CPU feasibility)
* `MODEL_SIZE = "2B"` (Primary) or "1.8B" (Fallback)

## 4. Running the Experiment

### Run Training (Both Modes)
```bash
python code/training/runner.py --mode all --repeats 3
```
* This runs both `static_random` and `state_guided` modes, 3 times each.
* Output logs and coverage vectors are saved to `data/processed/`.

### Run Analysis
```bash
python code/analysis/convergence.py
python code/analysis/transfer.py
python code/analysis/sensitivity.py
```

### Run Tests
```bash
pytest tests/
```

## 5. Expected Outputs

* `data/processed/training_logs/static_random.parquet`
* `data/processed/training_logs/state_guided.parquet`
* `data/processed/scheduler_trace/state_guided.json`
* `data/processed/evaluation_results.json` (Contains convergence steps, variance, and proxy correlation $r$)

## 6. Troubleshooting

* **OOM Error**: Reduce `TRAINING_TASKS_SUBSET` or `MODEL_QUANTIZATION` to 8-bit.
* **Scheduler Deadlock**: Check `scheduler_trace.json` for "fallback_entropy" logs.
* **Invalid Proxy**: If `sensitivity.py` reports $r < 0.3$, review the `STATE_PROXIES` list in `code/scheduler/state_coverage.py`.
* **Time Limit Exceeded**: The runner will automatically switch to the fallback model (1.8B) or reduce steps if the 4-hour mark is reached without [deferred] completion.