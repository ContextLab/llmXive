# Quickstart: Evaluating the Impact of Code Generation Models on Code Testability

## Prerequisites

- Python 3.11+
- `pip`
- Access to HuggingFace (for dataset download)
- (Optional) API Key for Salesforce/Codegen (if not using local model)
- (Optional) Kaggle Credentials for GPU Escape Hatch

## Installation

1.  **Clone and Setup**:
    ```bash
    cd projects/PROJ-294-evaluating-impact-code-generation
    python -m venv venv
    source venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

### Step 1: Download Data
```bash
python code/download_data.py
# Verifies SHA256 and saves to data/raw/humaneval.parquet
```

### Step 2: Generate Code
```bash
# Standard CPU run
python code/generate_code.py --model salesforce/codegen-mono-350M

# Optional: GPU Escape Hatch (requires Kaggle credentials)
GENERATE_WITH_GPU=1 python code/generate_code.py --model codellama-7b
```

### Step 3: Analyze Metrics
```bash
python code/analyze_metrics.py
# Computes Complexity, Mutation Score, Pass Rate. Writes data/analysis/metrics.json
```

### Step 4: Run Statistical Tests
```bash
python code/statistical_tests.py
# Performs Wilcoxon, McNemar, Power Analysis. Writes state/validation_results.yaml and state/power_analysis.yaml
```

### Step 5: Validate Citations (Validation Gate)
```bash
python code/validate_citations.py
# If this fails (exit code 1), the pipeline halts and no report is generated.
```

### Step 6: Generate Report
```bash
python code/report_generator.py
# Generates report.md with figures and citations, consuming power analysis results.
```

## Verification

- **Check Sum**: `sha256sum data/raw/humaneval.parquet` should match `state/artifact_hashes.yaml`.
- **Check Metrics**: `cat data/analysis/metrics.json | jq '.[0]'` should show all fields populated, including `mutation_score`.
- **Check Stats**: `cat state/validation_results.yaml` should contain p-values and power estimates.

## Troubleshooting

- **API Errors**: Ensure `CODEGEN_API_KEY` is set in environment.
- **Mutation Testing Failures**: If `mutmut` fails, check `data/analysis/metrics.json` for `mutation_error` flag.
- **Memory**: If `CodeLlama` fails on CPU, the pipeline automatically falls back to `codegen-mono` or uses the GPU escape hatch.
- **Timeout**: If the pipeline exceeds 4.0 hours, it will abort and re-run on a 50-task sample.
