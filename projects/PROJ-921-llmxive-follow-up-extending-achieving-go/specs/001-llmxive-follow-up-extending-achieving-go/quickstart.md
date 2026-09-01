# Quickstart: llmXive follow-up: extending "Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified S"

## Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace Hub (for dataset download)
- (Optional) HuggingFace token for private models (if SU-01 is private)

## Installation

1. **Clone the repository** and navigate to the project directory:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-921-llmxive-follow-up-extending-achieving-go
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins versions for `transformers`, `torch`, `bitsandbytes`, `scikit-learn`.*

4. **Set up environment variables** (if needed):
   ```bash
   export HF_TOKEN="your_token_here"
   export RANDOM_SEED=42
   ```

## Running the Pipeline

The pipeline is designed to run end-to-end. For local testing, you can run individual steps.

### Step 1: Download and Prepare Data
```bash
python code/download.py
```
- Downloads IMO dataset.
- Constructs OpenSci-Reason dataset (N=100 for CI feasibility).
- Outputs to `data/raw/` and `data/processed/`.

### Step 2: Run Inference
```bash
python code/inference.py --model SU-01 --model Baseline --dataset OpenSci --n-candidates 3
```
- Generates responses.
- Logs failures and truncations.
- Outputs to `data/processed/inference_results.jsonl`.

### Step 3: Score Responses
```bash
python code/scoring.py --input data/processed/inference_results.jsonl
```
- Loads the frozen Llama-3-8B (INT4).
- Scores responses.
- Validates against gold standard (if available).
- Outputs to `data/processed/scores.jsonl`.

### Step 4: Statistical Analysis
```bash
python code/analysis.py
```
- Computes correlations and t-tests.
- Generates `data/processed/stats.json`.

### Step 5: Verify Reproducibility
```bash
python code/utils.py --checksum
```
- Generates checksums for all data files.
- Updates `state/` timestamps.

## Troubleshooting

- **OOM Error**: Reduce `max_new_tokens` or use `INT4` quantization (default).
- **CUDA Error**: Ensure `device="cpu"` is set in `config.py`.
- **Dataset Missing**: If IPhO data is missing, the script will error. Provide a local path or a verified URL.

## Expected Output

- `data/processed/stats.json`: Contains correlation coefficients, p-values, and power analysis.
- `logs/pipeline.log`: Detailed execution log.
