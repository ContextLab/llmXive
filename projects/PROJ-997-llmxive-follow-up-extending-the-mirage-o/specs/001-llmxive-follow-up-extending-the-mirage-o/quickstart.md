# Quickstart: llmXive follow-up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

## Prerequisites

- Python 3.11+
- Git
- `llama.cpp` (binary or build tools)
- Access to a GitHub Actions runner (or local environment with similar constraints)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd specs/001-llmxive-mipu-gap-bounds
    ```

2.  **Set up the virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` will be generated during Phase 1.*

4.  **Build `llama.cpp`** (if not using a pre-built binary):
    ```bash
    git clone https://github.com/ggerganov/llama.cpp.git
    cd llama.cpp
    make
    cd ..
    ```

## Running the Pipeline

### Step 1: Generate Dataset

Run the data generation script to create the hardware-grounded dataset.

```bash
python -m src.cli.generate_dataset --num-samples 300 --quantization-levels INT4 INT8 FP8
```

- `--num-samples`: Number of prompts to process (default: 300).
- `--quantization-levels`: List of quantization levels to test.

**Output**: `data/processed/training_sample.parquet`

### Step 2: Train the Gap Predictor

Train the Kernel Ridge Regression model.

```bash
python -m src.cli.train_model --input data/processed/training_sample.parquet --model-type krr
```

- `--input`: Path to the generated dataset.
- `--model-type`: Type of model to train (default: krr).

**Output**: `data/models/gap_predictor.pkl`, `data/results/training_metrics.json`

### Step 3: Evaluate and Validate

Evaluate the model and verify the theoretical bounds.

```bash
python -m src.cli.evaluate_model --model data/models/gap_predictor.pkl --test-data data/processed/training_sample.parquet
```

**Output**: `data/results/evaluation_report.json`, `data/results/bound_verification.json`

### Step 4: Generate Final Report

Generate the final research report.

```bash
python -m src.cli.generate_report --output paper/
```

**Output**: `paper/report.md`

## Verification

To verify the setup, run the unit tests:

```bash
pytest tests/unit/
```

To run integration tests:

```bash
pytest tests/integration/
```

## Troubleshooting

- **Issue**: `llama.cpp` fails to load quantized model.
  - **Solution**: Ensure the model is quantized correctly and the binary is up-to-date. Check the `processing_status` in the dataset for skipped samples.
- **Issue**: Out of Memory (OOM) error.
  - **Solution**: Reduce `--num-samples` or ensure the model is loaded in 4-bit/8-bit quantization.
- **Issue**: Zero-divergence errors.
  - **Solution**: The code includes a small epsilon to prevent division-by-zero. Check the logs for "stable" samples.

## Next Steps

- Explore different quantization levels.
- Experiment with other regression models (e.g., MLP).
- Extend the study to different model architectures.
