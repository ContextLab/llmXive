# Quickstart: Predicting Molecular Stability from Spectroscopic Data

## Prerequisites

- Python 3.11+
- Git
- Sufficient disk space (for raw and processed data)
- 7 GB+ RAM

## Installation

1.  **Clone the Repository**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-165-predicting-chemical-reaction-yields-from
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins PyTorch to a CPU-only version.*

## Running the Pipeline

The pipeline is executed via the CLI. It performs data ingestion, preprocessing, training, and evaluation in sequence.

### 1. Full Pipeline Execution
```bash
python -m src.cli.main --mode full
```
This command:
- Downloads datasets from verified HuggingFace URLs.
- Preprocesses data (resampling, splitting).
- Trains the attention model and baselines.
- Runs evaluation and generates reports.
- Saves all artifacts to `data/artifacts/`.

### 2. Individual Steps

**Preprocessing Only** (skip training):
```bash
python -m src.cli.main --mode preprocess
```

**Training Only** (requires preprocessed data):
```bash
python -m src.cli.main --mode train
```

**Evaluation Only** (requires trained model):
```bash
python -m src.cli.main --mode eval
```

**Update State File** (Principle V):
After any significant change or manual intervention, run:
```bash
python -m src.cli.main --update-state
```
This command updates the `updated_at` timestamp in `state/projects/PROJ-165-.../state.yaml` and records the current artifact hashes. The `src/utils/state_manager.py` module performs this update.

## Verifying Results

After running the full pipeline:

1.  **Check Metrics**:
    Open `data/artifacts/metrics.json` to view RMSE, MAE, R², and p-values.
2.  **View Attention Heatmap**:
    Open `data/artifacts/attention_heatmap.png` to see the top spectral regions identified by the model.
3.  **Verify Leakage**:
    Run the unit test to ensure no scaffold overlap:
    ```bash
    pytest tests/unit/test_preprocessing.py::test_no_scaffold_leakage
    ```
4.  **Verify SSoT**:
    Check `data/artifacts/trace_log.json` to ensure every statistic has a corresponding `AnalysisTrace` entry.

## Troubleshooting

- **Out of Memory**: If the process crashes due to RAM, reduce the `--sample-size` argument in the preprocessing step.
- **Data Download Failed**: Verify internet connection. The datasets are fetched from HuggingFace; ensure no firewall blocks these URLs.
- **CUDA Error**: Ensure you are using the CPU-only PyTorch build installed via `requirements.txt`.
- **State Update Failed**: Ensure the `state/` directory is writable and the `state_manager.py` module is present in `src/utils/`.
