# Quickstart: Evaluating the Robustness of LLM-Generated Code to Input Perturbations

## Prerequisites

- Python 3.11+
- Docker (for sandboxed execution)
- Git
- 14 GB disk space, 7 GB RAM

## Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-090-evaluating-the-robustness-of-llm-generat
   ```

2. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Verify Docker**
   ```bash
   docker run --rm hello-world
   ```

## Running the Pipeline

### Step 1: Download Data
```bash
python code/data/download.py
```
- Downloads HumanEval from HuggingFace.
- Verifies checksum.
- Outputs: `data/raw/humaneval.parquet`

### Step 2: Generate Perturbations
```bash
python code/perturb/generator.py --threshold 0.95
```
- Generates up to 3 variants per task.
- Validates semantic similarity.
- Outputs: `data/processed/perturbed_prompts.csv`

### Step 3: Run Inference
```bash
python code/inference/runner.py --timeout 30 --max-tasks 164
```
- Loads StarCoder2-3B (4-bit quantized).
- Generates code for each prompt.
- Outputs: `data/processed/inference_results.csv`

### Step 4: Execute Tests
```bash
python code/execution/sandbox.py --timeout 10
```
- Runs generated code in Docker sandbox.
- Captures pass/fail results.
- Outputs: `data/processed/results.csv`

### Step 5: Statistical Analysis
```bash
python code/analysis/statistics.py
python code/analysis/sensitivity.py
```
- Computes pass@1, McNemar's test, Mixed-Effects model.
- Runs sensitivity analysis.
- Outputs: `data/results/analysis_results.csv`, `data/results/sensitivity_report.json`

## Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Contract Tests (Schema Validation)
```bash
pytest tests/contract/
```

## Reproducibility

- All random seeds are pinned in `code/utils/config.py`.
- Dependencies are pinned in `requirements.txt`.
- Data checksums are recorded in `state/`.
- Re-run the pipeline with `./run_pipeline.sh` for full reproducibility.

## Troubleshooting

- **OOM Errors**: Reduce `--max-tasks` or increase swap space.
- **Timeouts**: Check Docker container resource limits.
- **Semantic Similarity Failures**: Adjust `--threshold` (default 0.95).
