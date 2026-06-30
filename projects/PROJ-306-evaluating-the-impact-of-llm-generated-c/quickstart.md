# Quickstart Guide: Evaluating the Impact of LLM-Generated Code on Code Coverage

This guide provides step-by-step instructions to set up the environment, run the full pipeline, and generate analysis reports.

## Prerequisites

- Python 3.9+
- `pip` (Python package manager)
- Access to an LLM API key (e.g., OpenAI) or a local GPU/CPU environment for fallback models.

## 1. Environment Setup

### Create Virtual Environment and Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Environment Variables

Set your API key if using cloud models:
```bash
export LLM_API_KEY="your-api-key-here"
```

## 2. Data Preparation

The pipeline requires benchmark datasets (MBPP and HumanEval). These are downloaded automatically if missing.

```bash
# Run dataset loading script
python code/dataset_loader.py
```

This will:
- Download raw datasets to `data/benchmarks/raw/`
- Validate and create a normalized catalog at `data/benchmarks/processed/catalog.json`
- Convert test suites to executable Python files in `data/benchmarks/processed/tests/`

## 3. Running the Pipeline

### Basic Execution

Run the main pipeline to generate code and calculate coverage:

```bash
python code/main.py --dataset mbpp --model gpt-4 --batch-size 10
```

**Arguments:**
- `--dataset`: Dataset to use (`mbpp`, `humaneval`, or `all`)
- `--model`: LLM model to use (`gpt-4`, `code-llama-7b`, `starcoderbase-3b`)
- `--batch-size`: Number of tasks to process in parallel (default: 1)

**Output:**
- Generated code: `data/generated/{task_id}.py`
- Coverage reports: `data/coverage_reports/{task_id}.json`

### Error Handling

The pipeline gracefully handles errors (API failures, syntax errors, etc.). Failed tasks are logged in `data/coverage_reports/{task_id}.json` with status `failed` and an error message.

## 4. Statistical Analysis (User Story 2)

After generating coverage reports, run the statistical analysis:

```bash
python code/analyzer.py --model-method regression
```

**Arguments:**
- `--model-method`: Analysis method (`regression`, `lmm`, `glmm`). Default: `regression`.

**Outputs:**
- `data/processed/stats_summary.csv`: Statistical summary (mean differences, p-values, Cohen's d)
- `data/processed/corrected_pvalues.csv`: Family-wise error corrected p-values
- `data/processed/sensitivity_report.csv`: Sensitivity analysis across thresholds
- `outputs/stratified_summary.csv`: Stratified results by difficulty and patterns

**Note:** VIF (Variance Inflation Factor) is calculated only when `--model-method regression` is selected.

## 5. Visualization and Stratification (User Story 3)

Generate stratified reports and visualizations:

```bash
python code/visualizer.py
```

**Outputs:**
- `outputs/stratified_loops.csv`, `outputs/stratified_conditionals.csv`, etc.
- `outputs/coverage_by_pattern_loops.png`, `outputs/coverage_by_pattern_conditionals.png`, etc.
- `outputs/stratified_summary.csv`: Mean branch-coverage gaps by difficulty and pattern

**Visualization Details:**
- Resolution: 800x600 pixels
- Includes axis labels, legends, and pattern annotations
- HumanEval tasks (branch_coverage == "N/A") are excluded from branch coverage calculations

## 6. Verification and Testing

### Run Unit Tests

```bash
pytest tests/unit/ -v
```

### Run Integration Tests

```bash
pytest tests/integration/ -v
```

### Validate Data Structure

Ensure all required directories and files exist:

```bash
python code/validate_data_structure.py
```

## 7. Performance Optimization

The pipeline is optimized to process ≥100 tasks within 6 hours on a CPU-only runner (SC-005 constraint). For fallback models (e.g., `starcoderbase-3b`), 4-bit quantization is automatically applied to stay within 7GB RAM limits.

## Troubleshooting

- **API Rate Limits:** The pipeline uses exponential backoff retry logic (`code/utils.py`) to handle rate limits.
- **Missing Test Suites:** Tasks without test suites are logged as warnings and skipped during coverage execution.
- **Memory Errors:** Ensure 4-bit quantization is enabled for fallback models (mandatory per SC-005).

## Support

For issues or questions, refer to the project documentation or open an issue in the repository.
