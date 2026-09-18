# Quickstart: Dream-State Learning: Implementing REM-like Consolidation in Language Models

## Prerequisites

- Python 3.11 or higher.
- Git.
- Sufficient RAM available (for CI runner compatibility).
- Internet access (to download datasets from Hugging Face).

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-589-dream-state-learning-implementing-rem-li/code
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Experiment

### 1. Run a Single Wake/Dream Training Job
This executes the alternating cycle (4 wake : 1 dream) for a single seed.
```bash
python main.py --mode wake_dream --seed 42 --steps 100 --ratio 4
```

### 2. Run the Baseline (Continuous Training)
This runs the control experiment with the same total steps and **identical real token exposure** as the Wake phases of the experimental run.
```bash
python main.py --mode baseline --seed 42 --steps 100
```

### 3. Run the Full Comparative Pipeline
Executes both modes across multiple seeds and aggregates results.
```bash
python main.py --mode pipeline --seeds 0,1,2,3,4 --steps 100
```

### 4. Run Temperature Sensitivity Sweep
Tests the robustness of the dream phase across temperatures **0.7, 0.9, 1.1, 1.3**. The variance metric is the **standard deviation** of accuracy across seeds.
```bash
python main.py --mode sweep --temps 0.7,0.9,1.1,1.3 --seeds 0
```

## Verification

### Check Logs
Inspect `logs/training.log` to verify phase transitions and entropy checks:
```bash
grep "phase" logs/training.log | tail -n 10
```

### Verify Memory Limits
Check `logs/memory_audit.log` to ensure peak RSS stayed below 6.0 GB:
```bash
cat logs/memory_audit.log
```

### Reproduce Results
To reproduce a specific result, set the seed and mode exactly:
```bash
python main.py --mode wake_dream --seed 42 --steps 100 --ratio 4
```
The output accuracy should match the value in `data/results.csv` for that seed.

## Troubleshooting

- **OOM Error**: If the job is killed, check `logs/memory_audit.log`. Reduce `--batch-size` in `config.py`.
- **Low Entropy**: If the dream phase repeatedly retries, check `logs/training.log` for `entropy_mean < 0.5`. This may indicate the model is not yet trained enough (warm-up period insufficient).
- **Dataset Download Fail**: Ensure internet connectivity. The datasets are fetched from Hugging Face; if the network is restricted, download the parquet files manually and place them in `data/raw/`.