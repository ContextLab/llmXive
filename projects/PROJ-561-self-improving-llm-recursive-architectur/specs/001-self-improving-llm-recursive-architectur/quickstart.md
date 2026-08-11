# Quickstart: Self-improving LLM: recursive architecture refinement and re‑training

## Prerequisites

- Python 3.10+
- Git
- Access to a GitHub Actions runner (or local machine with sufficient RAM)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-561-self-improving-llm-recursive-architectur
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### Single Cycle (Baseline + 1 Refinement)

To run a single refinement cycle (Cycle 1) for testing:

```bash
python code/main.py --cycles 1
```

### Full Experiment (3 Cycles)

To run the full experiment (3 cycles, with early termination if degradation detected):

```bash
python code/main.py --cycles 3
```

### Configuration

Edit `code/config.py` to adjust:
- `TRAINING_SAMPLES`: Number of OpenWebText samples (default: 5000).
- `MAX_PARAM_INCREASE`: Max parameter increase percentage (default: 30).
- `SIGNIFICANCE_THRESHOLD`: Alpha for bootstrap (default: 0.05).

## Output

- **Results**: `results/trajectory.json` contains the full performance trajectory.
- **Logs**: `results/logs/` contains detailed logs for each cycle.
- **Models**: `results/models/` contains checkpoints for each cycle.

## Verification

To verify the results:

1.  Check `results/trajectory.json` for the `trend_direction`.
2.  Verify that `p_value_vs_predecessor` is < 0.05 (or corrected threshold) for claimed improvements.
3.  Ensure `cost_effectiveness` metrics are recorded.

## Troubleshooting

- **Memory Error**: Reduce `TRAINING_SAMPLES` or ensure streaming is enabled.
- **Training Failure**: The pipeline automatically retries up to 2 times. If it fails, check `results/logs/cycle_N.log`.
- **API Rate Limit**: The pipeline implements exponential backoff. If it fails, check internet connectivity.