# Quickstart Guide: Evaluating the Impact of LLM-Generated Code on Code Coverage

## Prerequisites

- Python 3.9+
- `pip` package manager
- `datasets` library (installed via requirements.txt)
- Optional: `LLM_API_KEY` environment variable for API-based models

## Setup

1. **Clone the repository**
 ```bash
 git clone <repo-url>
 cd llmXive-evaluating-llm-code-coverage
 ```

2. **Create and activate virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**
 ```bash
 pip install -r requirements.txt
 ```

4. **Set up directories** (if not already done)
 ```bash
 python code/setup_directories.py
 ```

## Data Preparation

1. **Load datasets**
 ```bash
 python code/dataset_loader.py
 ```
 This will download MBPP and HumanEval datasets and save them to `data/benchmarks/raw/`.

2. **Transform test suites**
 ```bash
 python code/test_transformer.py
 ```
 Converts string-based tests to executable Python files in `data/benchmarks/processed/tests/`.

3. **Create task catalog**
 ```bash
 python code/dataset_loader.py --action create-catalog
 ```
 Generates `data/benchmarks/processed/catalog.json`.

## Running the Pipeline

### Option 1: Full Pipeline (Generation + Coverage + Analysis)

```bash
python code/main.py --dataset mbpp,humaneval --model gpt-4 --batch-size 10 --output-dir data/coverage_reports
```

**Arguments:**
- `--dataset`: Comma-separated list of datasets (e.g., `mbpp`, `humaneval`)
- `--model`: Model to use for code generation (e.g., `gpt-4`, `code-llama-7b`, `starcoderbase-3b`)
- `--batch-size`: Number of tasks to process in parallel
- `--output-dir`: Directory to save coverage reports

**Note:** If `LLM_API_KEY` is not set, the pipeline will attempt to use local models with 4-bit quantization.

### Option 2: Statistical Analysis Only

After generating coverage reports, run the statistical analysis:

```bash
python code/analyzer.py --coverage-dir data/coverage_reports --output-dir data/processed
```

This produces:
- `data/processed/stats_summary.csv`
- `data/processed/corrected_pvalues.csv`

### Option 3: Sensitivity Analysis (Task T029)

Run sensitivity analysis on the coverage data:

```bash
python code/sensitivity_analyzer.py --coverage-dir data/coverage_reports --output-dir data/processed
```

**Arguments:**
- `--coverage-dir`: Directory containing coverage reports (default: `data/coverage_reports`)
- `--output-dir`: Directory to save output files (default: `data/processed`)
- `--thresholds`: Comma-separated list of thresholds (default: `0.01,0.05,0.10,0.15,0.20,0.25`)

**Output:**
- `data/processed/sensitivity_report.csv`

### Option 4: Visualization and Stratification

```bash
python code/visualizer.py --coverage-dir data/coverage_reports --output-dir outputs
```

This produces:
- Stratified CSVs (e.g., `stratified_loops.csv`)
- Visualization PNGs (e.g., `coverage_by_pattern_loops.png`)
- `outputs/stratified_summary.csv`

## Validation

Run the validation script to ensure all artifacts are present:

```bash
python code/task_t050_validate_quickstart.py
```

## Troubleshooting

- **Missing API Key**: If `LLM_API_KEY` is not set, the pipeline will fall back to local models. Ensure `bitsandbytes` is installed for 4-bit quantization.
- **Memory Errors**: For local models, ensure you have sufficient RAM. The pipeline uses 4-bit quantization to stay within 7GB limits.
- **Syntax Errors in Generated Code**: The pipeline logs these errors and continues. Check `coverage_reports/{task_id}.json` for details.

## Output Artifacts

After a successful run, verify the following files exist:

- `data/benchmarks/processed/catalog.json`
- `data/benchmarks/processed/tests/*.py`
- `data/coverage_reports/*.json`
- `data/processed/stats_summary.csv`
- `data/processed/corrected_pvalues.csv`
- `data/processed/sensitivity_report.csv`
- `outputs/stratified_*.csv`
- `outputs/*.png`
