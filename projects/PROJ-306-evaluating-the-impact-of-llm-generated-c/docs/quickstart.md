# Quickstart Guide: Evaluating the Impact of LLM-Generated Code on Code Coverage

This guide provides step-by-step instructions to set up the environment, run the pipeline, and analyze results for the **llmXive** project.

## Prerequisites

- Python 3.9+
- pip
- Valid API key for the primary LLM provider (optional if using fallback models)
- At least 7GB RAM (required for 4-bit quantized fallback models)

## 1. Environment Setup

### 1.1 Clone and Navigate
```bash
git clone <repository-url>
cd llmXive-evaluating-llm-code-coverage
```

### 1.2 Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### 1.3 Install Dependencies
```bash
pip install -r requirements.txt
```

### 1.4 Configure Environment Variables
Create a `.env` file in the project root:
```bash
LLM_API_KEY=your_api_key_here
```
*Note: If no API key is provided, the pipeline will automatically fall back to local CPU inference models (e.g., `bigcode/starcoderbase-3b`).*

## 2. Data Preparation (Optional)
If raw benchmark data is not already present in `data/benchmarks/raw/`, run the dataset loader:
```bash
python code/dataset_loader.py
```
This will:
- Download MBPP and HumanEval datasets.
- Save raw files to `data/benchmarks/raw/`.
- Generate a normalized catalog at `data/benchmarks/processed/catalog.json`.

## 3. Running the Pipeline

The main entry point is `code/main.py`. It orchestrates code generation and coverage execution.

### Basic Execution
```bash
python code/main.py --dataset mbpp --model gpt-4 --batch-size 10
```

### Arguments
- `--dataset`: Dataset to use (`mbpp`, `humaneval`, or `all`).
- `--model`: LLM model identifier (e.g., `gpt-4`, `code-llama-7b`, `bigcode/starcoderbase-3b`).
- `--batch-size`: Number of tasks to process in one batch.

### Output
- Generated code: `data/generated/{task_id}.py`
- Coverage reports: `data/coverage_reports/{task_id}.json`
- Logs: `logs/pipeline.log`

## 4. Statistical Analysis (User Story 2)

Once coverage reports are generated, run the statistical analysis:
```bash
python code/analyzer.py --model-method regression
```

### Output Files
- `data/processed/stats_summary.csv`: Summary of statistical tests (t-test/Wilcoxon), p-values, Cohen's d.
- `data/processed/corrected_pvalues.csv`: P-values corrected for family-wise error rate (Bonferroni/Holm).
- `data/processed/sensitivity_report.csv`: Sensitivity analysis across significance thresholds.

## 5. Visualization and Stratification (User Story 3)

Generate visualizations and stratified reports:
```bash
python code/visualizer.py
```

### Output Files
- `outputs/stratified_loops.csv`, `outputs/stratified_conditionals.csv`, etc.
- `outputs/coverage_by_pattern_loops.png`, `outputs/coverage_by_pattern_conditionals.png`
- `outputs/stratified_summary.csv`: Mean branch coverage gaps by difficulty and pattern.

## 6. Verification

To ensure reproducibility and correctness:
1. Run the unit tests:
 ```bash
 pytest tests/unit/ -v
 ```
2. Run the integration tests:
 ```bash
 pytest tests/integration/ -v
 ```

## Troubleshooting

- **RAM Error**: If you encounter memory errors with fallback models, ensure 4-bit quantization is enabled (default in `code/llm_generator.py`).
- **API Rate Limits**: The pipeline includes exponential backoff logic in `code/utils.py`. If issues persist, increase the `--batch-size` wait time or reduce concurrency.
- **Missing Data**: Ensure `data/benchmarks/processed/catalog.json` exists before running analysis tasks.

## Next Steps

- Review `data-model.md` for detailed schema definitions.
- Check `outputs/` for generated visualizations.
- Refer to `docs/research.md` for the full research design.
