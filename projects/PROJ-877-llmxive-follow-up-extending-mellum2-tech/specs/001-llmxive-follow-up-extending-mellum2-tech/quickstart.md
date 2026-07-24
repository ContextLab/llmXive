# Quickstart: llmXive follow-up: extending "Mellum2 Technical Report"

## Prerequisites
- Python 3.11+
- 8 GB RAM (minimum for CPU inference of Mistral-7B; 4 GB for TinyLlama fallback)
- Access to HuggingFace Hub (for dataset and model download)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech
    ```

2.  **Create virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins all versions to ensure reproducibility.*

## Running the Pipeline

**CRITICAL**: The pipeline is orchestrated to enforce strict dependencies. **Do not** run scripts individually unless you understand the data flow. Use `main.py` to ensure `ngram.py` (Phase 3) completes before `engine.py` (Phase 4).

### 1. Full Pipeline Execution (Recommended)
Runs all phases in the correct order: Power Analysis -> Download -> Static Analysis -> N-Gram Model -> Inference -> Analysis -> Validation Fallback.
```bash
python code/main.py --model mistral-7b --device cpu --timeout 60
```
*Note: If `mistral-7b` exceeds memory, the orchestrator will automatically switch to `tinyllama` and log a warning.*

### 2. Manual Step Execution (Advanced)
If running manually, you **MUST** follow this order:

#### Step 0: Power Analysis
```bash
python code/main.py --phase power-analysis
```

#### Step 1: Data Download & Sampling
```bash
python code/data/download.py --lang python --lang java --sample-size 500
```

#### Step 2: Static Analysis
```bash
python code/data/preprocess.py --input data/raw/sample.parquet --output data/processed/labeled.parquet
```

#### Step 3: N-Gram Model (Producer)
**MUST COMPLETE BEFORE STEP 4**.
```bash
python code/data/ngram.py --input data/processed/labeled.parquet --output data/models/ngram.arpa
```

#### Step 4: LLM Inference (Consumer)
**Requires `data/models/ngram.arpa` to exist.**
```bash
python code/inference/engine.py --model mistral-7b --input data/processed/labeled.parquet --output data/processed/inferred.parquet --device cpu --timeout 60
```

#### Step 5: Analysis & Visualization
```bash
python code/analysis/correlation.py --input data/processed/inferred.parquet
python code/analysis/thresholds.py --input data/processed/inferred.parquet
python code/analysis/significance.py --input data/processed/inferred.parquet
python code/viz/plots.py --input data/results/analysis_results.json
```

### 3. Validation Fallback
If no human-labeled benchmark is found, the pipeline automatically generates a limitation report in `data/results/validation_report.json`. No manual intervention is required.

## Expected Output
- `data/results/correlation_results.parquet`
- `data/results/threshold_results.parquet`
- `data/results/significance_report.json`
- `data/results/validation_report.json` (if benchmark missing)
- `data/figures/correlation_scatter.png`
- `data/figures/threshold_sensitivity.png`

## Troubleshooting
- **OOM Error**: The pipeline automatically falls back to `tinyllama`. If that fails, reduce `--sample-size` in `download.py`.
- **Timeout**: Increase `--timeout` or switch to a smaller model (e.g., `phi-2`).
- **Parsing Errors**: The pipeline skips files that cannot be parsed; check `data/logs/parsing_errors.log`.
- **Missing N-Gram Model**: Ensure `code/data/ngram.py` has run successfully before running `code/inference/engine.py`.