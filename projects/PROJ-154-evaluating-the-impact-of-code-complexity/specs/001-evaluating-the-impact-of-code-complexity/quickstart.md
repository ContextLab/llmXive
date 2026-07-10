# Quickstart: Evaluating the Impact of Code Complexity on LLM Code Understanding

## Prerequisites

-   Python 3.11+
-   Git
-   HuggingFace CLI (optional, for authentication)
-   7 GB+ RAM available

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-154-evaluating-the-impact-of-code-complexity/code
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Install Radon**:
    ```bash
    pip install radon
    ```

3.  **Download Dependencies**:
    Ensure `transformers` and `torch` are installed with CPU support (default wheels).

## Execution Workflow

### Step 1: Data Acquisition
```bash
python 01_data_acquisition.py
# Outputs: data/raw/codesearchnet_raw.parquet
# Note: Logs total_valid_snippets count.
```

### Step 2: Complexity Annotation & Derived Dataset Generation
```bash
python 02_complexity_annotation.py
# Outputs: data/processed/annotated_snippets.csv
# Note: Excludes syntax errors, logs warnings. Injects bugs for Bug Detection task.
# Note: Performs stratified sampling to ensure high-complexity representation.
```

### Step 3: Inference (CPU Tractable)
```bash
python 03_inference_pipeline.py --model microsoft/Phi-3-mini-4k-instruct --batch-size 1
# Outputs: results/inference_logs.jsonl
# Note: Memory guard active; adjusts batch size if RAM > 6.5 GB.
# Note: Logs is_valid_response for SC-005.
```

### Step 4: Metric Calculation
```bash
python 04_metric_calculation.py
# Outputs: results/metrics.csv
# Note: Calculates BLEU-4, ROUGE-L, Execution Pass Rate, and Bug Detection (substring match).
```

### Step 5: Statistical Analysis
```bash
python 05_statistical_analysis.py
# Outputs: results/analysis_report.json, results/binning_metadata.json
# Note: Applies Bonferroni correction, VIF checks, and PCA fallback if VIF > 5.
# Note: Prioritizes GLM with splines over binning.
```

### Step 6: Report Generation
```bash
python 06_report_generation.py
# Outputs: results/final_report.md
```

## Verification

Run the test suite to verify data integrity:
```bash
pytest tests/
```

Check for missing metrics and SC-005 compliance:
```bash
python -c "import pandas as pd; df = pd.read_csv('results/metrics.csv'); print(df.isnull().sum())"
# Expected: All counts 0 for numeric columns.
python -c "import json; r = json.load(open('results/analysis_report.json')); print(f'Denom: {r[\"denominator\"]}, Num: {r[\"numerator\"]}')"
# Expected: Numerator / Denominator >= 0.95 (SC-005).
```