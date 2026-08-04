# Quickstart: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

## Prerequisites

- Python 3.11+
- Git
- Hugging Face CLI (optional, for large downloads)
- Sufficient RAM available (for streaming processing)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat
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

### 1. Data Construction (Quantization)

Convert the continuous LIBERO dataset to discrete JSON vectors.

```bash
python code/data/quantizer.py \
  --bit-depth 4 \
  --source "physical-intelligence/libero" \
  --output-dir data/derived/quantized_4bit \
  --streaming
```

*Note: Use appropriate bit-depth settings for other resolutions.*

### 2. Training (CPU-Only)

Train the Kairos adapter on the quantized data.

```bash
python code/model/trainer.py \
  --data-dir data/derived/quantized_4bit \
  --epochs 10 \
  --horizon 500 \
  --checkpoint-interval 1 \
  --seed 42
```

*The training loop includes a timeout guard.*

### 3. Analysis & Threshold Detection

Compute stability metrics and statistical significance.

```bash
python code/analysis/stats.py \
  --results-dir data/results/ \
  --baseline-mode "continuous" \
  --test-type "paired_t"
```

## Testing

Run the contract and integration tests to verify data integrity and pipeline logic.

```bash
pytest tests/ -v
```

## Troubleshooting

- **Out of Memory**: Ensure `--streaming` is used during quantization. The raw dataset should not be loaded entirely into RAM.
- **CUDA Errors**: This project is CPU-only. If you see CUDA errors, check `code/config.py` to ensure `device="cpu"` is set.
- **Degenerate Data**: If the 1-bit quantization is attempted, the script will raise a `ValueError` indicating "Invalid Data: State space collapse."