# Quickstart: Evaluating the Impact of Code Generation Models on Code Testability

## Prerequisites
- Python 3.11+
- Git
- (Optional) Kaggle CLI for GPU offload (handled automatically by CI)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-294-evaluating-impact-of-code-generation
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

## Running the Pipeline

The pipeline is executed in three sequential stages. Run them in order to ensure data availability.

### Step 1: Download & Verify Data
Downloads HumanEval and verifies the SHA256 checksum.
```bash
python code/download.py
```
*Output*: `data/raw/humaneval.parquet`, `state/artifact_hashes.yaml` (updated).

### Step 2: Generate Code Samples
Generates code using specified models.
```bash
# CPU-only (slow for large models)
python code/generate.py --model codegen-350m

# Auto-offload to GPU if detected (for CodeLlama)
python code/generate.py --model codellama-7b
```
*Output*: `data/generated/codegen-350m_samples.json`, `data/generated/codellama-7b_samples.json`.

### Step 3: Analyze & Report
Computes metrics, runs statistical tests, and generates the report.
```bash
python code/analyze.py
python code/statistics.py
python code/report.py
```
*Output*: `data/analysis/metrics.json`, `state/validation_report.yaml`, `results/report.md`.

## Verification

To verify the integrity of the run:
```bash
python code/validate.py
```
This script checks all `data/` files against `state/artifact_hashes.yaml` and ensures citations in the report are valid.

## Troubleshooting

- **OOM (Out of Memory)**: If `generate.py` fails with OOM, the script automatically attempts to offload to a GPU if the `CUDA_VISIBLE_DEVICES` environment variable is set. On local machines, reduce the batch size or use `--quantize 8bit`.
- **Checksum Mismatch**: Ensure you are using the exact `datasets` version pinned in `requirements.txt`. Re-run `download.py` to refresh the data.
