# Quickstart: Evaluating the Impact of Code Style on LLM Code Understanding and Generation

## Prerequisites

- Python 3.10+
- Git
- Access to HuggingFace Hub (no token required for public datasets, but recommended for rate limits).
- **Compute**: A machine with at least 8GB RAM (for local dev) or a GitHub Actions runner (free tier).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-194-evaluating-the-impact-of-code-style-on-l
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
   *Note: `requirements.txt` pins versions compatible with CPU-only execution.*

## Running the Pipeline

The pipeline is executed via the `main.py` script.

### Step 1: Data Preparation (Transformation)
Generate style variants from a sample of CodeSearchNet.
```bash
python code/main.py --task transform --sample-size 30
```
- **Output**: `data/derived/variants/` containing 8 files per function.
- **Validation**: Syntax check runs automatically; invalid variants are logged.

### Step 2: LLM Inference
Run the LLM tasks on the generated variants.
```bash
python code/main.py --task evaluate --model codegen-2B-mono --max-tokens 50
```
- **Output**: `data/derived/results/` containing task results and metrics.
- **Note**: This step is the most time-consuming. On a CPU runner, expect a moderate latency per sample.

### Step 3: Statistical Analysis
Perform the mixed-effects modeling and generate the report.
```bash
python code/main.py --task analyze
```
- **Output**: `results/analysis/` containing the statistical table, plots, and PDF report.

### Step 4: Pre-flight Validation (Constitution Principle II)
Run the accuracy verification script before finalizing.
```bash
python code/validation/verify_accuracy.py
```
- **Action**: Verifies all dataset URLs and citations. Fails if any source is unreachable or mismatched.

## Testing

Run the unit and integration tests:
```bash
pytest tests/ -v
```
Run contract tests against the schemas:
```bash
pytest tests/contract/ -v
```

## Troubleshooting

- **Out of Memory (OOM)**: Reduce `--sample-size` in the transform step. The default is a moderate set of functions.; try 10 if OOM occurs.
- **Model Loading Failed**: Ensure `torch` is installed for CPU. Do not install `torch` with CUDA support.
- **Syntax Errors**: Check `logs/transform_errors.log` for specific functions that failed the `ast.parse` check.
