# Quickstart: llmXive follow-up: extending "Training Long-Context Vision-Language Models Effectively with Generali"

## Prerequisites

- Python 3.11+
- Git
- A GitHub Actions runner with 2 vCPU, ~7GB RAM (Free Tier).
- Access to HuggingFace (for model weights).

## Installation

1. **Clone the repository** and navigate to the feature branch:
   ```bash
   git clone <repo-url>
   cd <project-dir>
   git checkout 001-modality-balance-attention
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: This will install CPU-only versions of `torch` and `onnxruntime`.*

## Configuration

Edit `code/config.py` to set:
- `MODEL_ID`: `"Qwen/Qwen2-VL-7B-Instruct"`
- `CONTEXT_LENGTH`: `131072` (128K) or `262144` (256K) (Note: 256K is contingent on memory feasibility).
- `QUANTIZATION_BITS`: `4`
- `MAX_SAMPLES`: `[deferred]` (e.g., 1000 for testing, 10000 for full run)
- `SEED`: `42`
- `ARM_TYPE`: `"both"` (Runs both Arm A and Arm B).

## Running the Pipeline

### 1. Generate Synthetic Data
```bash
python code/main.py --step generate
```
*Output*: `data/synthetic/raw/samples.jsonl` (includes both Arm A and Arm B samples).

### 2. Run Feasibility Gate (Pilot)
```bash
python code/main.py --step pilot
```
*Output*: Memory usage report. If 256K exceeds limits, the config is updated to 128K for the main run.

### 3. Run Inference (CPU)
```bash
python code/main.py --step infer
```
*Output*: `data/results/raw/inference_logs.jsonl`
*Note*: This step includes OOM guards. If a sample fails, it is logged and skipped.

### 4. Aggregate and Analyze
```bash
python code/main.py --step analyze
```
*Output*: `data/results/aggregated/buckets.csv`, `data/results/analysis/report.pdf` (separate plots for Arm A and Arm B).

## Validation

To verify the setup:
1. Run the **Unit Tests**:
   ```bash
   pytest tests/unit/
   ```
2. Run a **Small Integration Test** (10 samples):
   ```bash
   python code/main.py --step generate --samples 10
   python code/main.py --step infer --samples 10
   ```
   Check that `inference_logs.jsonl` contains 10 entries and no OOM errors (unless the model is too large for the test runner).

## Troubleshooting

- **OOM Error**: If the process crashes, ensure 4-bit quantization is enabled in `config.py`. If it still fails, the pilot run should have reduced the context length. If the 128K run fails, the model may not be compatible with the 7GB limit; check `code/inference/loader.py` for fallback logic.
- **Model Not Found**: Verify the HuggingFace ID `Qwen/Qwen2-VL-7B-Instruct` is correct and accessible.
- **Slow Inference**: On CPU, 128K contexts are slow. Ensure the runner is not overloaded. The target is dynamic based on sample count.