# Quickstart: Socratic Transformers (PROJ-582)

## Prerequisites

- Python 3.11+
- Git
- 7GB+ RAM (CPU-only) or access to Kaggle GPU (for fallback)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code
    ```

2.  **Create virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### 1. Download & Verify Data
Download GSM8K and MATH datasets and verify checksums.
```bash
python src/data/download.py
python src/data/verify_datasets.py
```

### 2. Generate Training Data
Generate Static, Dialogue, and Ablation tuples.
```bash
# Generate Static (Condition C)
python src/data/generate_dialogue.py --mode static

# Generate Dialogue (Condition A)
python src/data/generate_dialogue.py --mode dialogue

# Generate Ablation (Condition B)
python src/data/generate_dialogue.py --mode ablation
```
*Note: The `dialogue` mode includes a quality filter. Expect some tuples to be discarded.*

### 3. Train Models
Fine-tune models for each condition.
```bash
# Train Condition A (Selection)
python src/train/run_training.py --condition selection

# Train Condition B (Ablation)
python src/train/run_training.py --condition ablation

# Train Condition C (Static)
python src/train/run_training.py --condition static
```
*Note: If CPU OOM occurs, the script will attempt to fallback to a smaller model or signal for GPU offload (FR-008).*

### 4. Evaluate & Analyze
Run benchmarks and statistical tests.
```bash
python src/eval/evaluate.py
```
Output: `data/results.csv` and `data/analysis.json`.

## Running Tests

```bash
pytest tests/ -v
```

## Troubleshooting

- **OOM Error**: Reduce `batch_size` in `src/utils/config.py` to 1. Ensure 4-bit quantization is enabled.
- **Slow Training**: If training exceeds 6 hours on CPU, the pipeline will signal for GPU offload (Kaggle).
- **Data Mismatch**: Ensure `verify_datasets.py` passes before generating data.