# Quickstart: llmXive follow-up: extending "Translation as a Bridging Action"

## Prerequisites

*   Python 3.11+
*   Access to a GitHub Actions runner (2 CPU, 7GB RAM) or local equivalent.
*   `git` for repository access.

## Installation

1.  **Clone the project**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-855-llmxive-follow-up-extending-translation
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # or venv\Scripts\activate  # Windows
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins `torch` to a CPU-only version to ensure compatibility with the free-tier runner.*

## Running the Pipeline

The pipeline consists of three sequential steps: Data Generation, Model Training, and Evaluation.

### Step 1: Generate Synthetic Data

Generates ≥5,000 episodes using PyBullet with noise injection.

```bash
python code/generate_data.py --num_episodes 5000 --output data/raw/episodes.parquet
```

*   **Output**: `data/raw/episodes.parquet`
*   **Validation**: Run `python tests/unit/test_labeling.py` to verify physics metrics.
*   **Checksum**: Automatically generated in `data/checksums.json`.

### Step 2: Train the Model

Trains the lightweight Transformer on CPU.

```bash
python code/train_model.py --data data/raw/episodes.parquet --epochs 20 --batch_size 32
```

*   **Output**: `code/models/transformer.pt`
*   **Constraints**: If OOM occurs, reduce `--batch_size` to 16 or 8.

### Step 3: Evaluate & Validate

Compares the model against the geometry-only baseline and shuffled-translation control, runs McNemar's test, and generates `metrics_report.json`.

```bash
python code/evaluate.py --model code/models/transformer.pt --data data/raw/episodes.parquet
```

*   **Output**: `data/processed/predictions.parquet`, `data/processed/metrics_report.json`, and console report.
*   **Success Criteria**:
    *   Accuracy improvement ≥ 5% over baselines.
    *   McNemar's p-value < 0.05.
    *   `metrics_report.json` contains valid checksums.

## Testing

Run the full test suite to ensure contract compliance:

```bash
pytest tests/
```

*   **Contract Tests**: Verify output schemas match `contracts/`.
*   **Unit Tests**: Verify physics labeling logic and noise injection.
*   **Integration Tests**: Verify end-to-end runtime < 6 hours (simulated or actual).

## Troubleshooting

*   **OOM Error**: Reduce `batch_size` in `train_model.py`.
*   **Physics Crash**: Check `code/utils/physics_metrics.py` for numerical instability; the script should auto-recover and log failures.
*   **CUDA Error**: Ensure `torch` is the CPU version (`pip uninstall torch && pip install torch --index-url https://download.pytorch.org/whl/cpu`).
*   **Schema Violation**: If the pipeline exits with "Rotation/Force detected", check `code/generate_data.py` to ensure noise injection did not inadvertently introduce forbidden columns.