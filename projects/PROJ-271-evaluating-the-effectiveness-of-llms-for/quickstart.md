# Quickstart Guide

This guide provides step-by-step instructions for setting up and running the "Evaluating the Effectiveness of LLMs for Detecting Code Smells" pipeline.

## Step 1: Environment Setup

### 1.1 Clone the Repository

```bash
git clone <repository-url>
cd PROJ-271-evaluating-the-effectiveness-of-llms-for
```

### 1.2 Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### 1.3 Install Dependencies

```bash
pip install -r requirements.txt
```

### 1.4 Verify Installation

```bash
python -c "import datasets, pandas, radon, pylint, sentence_transformers, llama_cpp, sklearn, statsmodels, numpy, psutil; print('All dependencies installed successfully!')"
```

## Step 2: Data Pipeline Execution (User Story 1)

### 2.1 Run the Data Pipeline

The data pipeline will:
- Sample 800 functions from `codeparrot/github-code` (streaming mode)
- Compute structural metrics (LOC, Cyclomatic Complexity, Nesting Depth) using `radon`
- Run Pylint analysis and normalize smell labels
- Save results to `data/static_baseline.csv`

```bash
python code/data_pipeline.py
```

**Expected Output:**
- `data/static_baseline.csv` with columns: `code`, `loc`, `cyclomatic_complexity`, `nesting_depth`, `static_smell_labels`
- `results/sample_report.json` with sample size and validation info

### 2.2 Validate the Output

```bash
python code/validate_baseline.py
```

This script will verify:
- The CSV file exists and has the correct schema
- At least 95% of sampled functions are present with all required columns

## Step 3: Semantic Analysis Execution (User Story 2)

### 3.1 Run Semantic Analysis

The semantic analysis script will:
- Load `data/static_baseline.csv`
- Compute semantic embeddings using `sentence-transformers/all-MiniLM-L-v2`
- Run LLM inference using `CodeLlama-7B-Instruct-GGUF` (4-bit quantized)
- Save embeddings and LLM labels to `data/processed/semantic_results.json`

```bash
python code/semantic_analysis.py
```

**Note:** This step requires significant RAM (≥16GB recommended). The script uses batched inference (batch size ≤10) to manage memory.

**Expected Output:**
- `data/processed/semantic_results.json` with embeddings and LLM-generated smell labels
- `results/resource_metrics.json` with RAM, CPU, and inference time metrics

### 3.2 Validate the Output

```bash
python code/verify_results.py
```

This script will verify:
- The JSON file exists and contains valid data
- Resource metrics are within acceptable limits

## Step 4: Statistical Analysis Execution (User Story 3)

### 4.1 Run Statistical Analysis

The statistical analysis script will:
- Merge `data/static_baseline.csv` and `data/processed/semantic_results.json`
- Perform McNemar's test for each smell category
- Calculate VIF and fit logistic regression
- Run sensitivity analysis
- Generate reports in the `results/` directory

```bash
python code/statistical_analysis.py
```

**Expected Output:**
- `results/statistical_significance.json` with McNemar's test p-values
- `results/logistic_regression.json` with coefficients and VIF scores
- `results/sensitivity_metrics.json` with sensitivity analysis results
- `results/sensitivity_report.md` with human-readable report

### 4.2 Validate the Output

```bash
python code/verify_results.py
```

This script will verify:
- All required result files exist
- Data completeness (≥95% of sample)

## Step 5: End-to-End Validation

### 5.1 Run Pipeline Validation

```bash
python code/run_pipeline_validation.py
```

This script will:
- Verify all output files exist
- Validate schema compliance
- Check data completeness

### 5.2 Run Quickstart Validation

```bash
python code/run_quickstart_validation.py
```

This script will:
- Check file existence
- Validate static baseline schema
- Validate semantic results schema
- Verify results artifacts

## Step 6: Dry-Run with Mock Data (Optional)

To test the pipeline without real data (e.g., for CI/CD or resource-constrained environments):

```bash
python code/runtime_validator.py --dry-run
```

This will:
- Generate mock data for testing
- Run the pipeline on mock data
- Verify the pipeline executes without errors

## Troubleshooting

### Common Issues

1. **Out of Memory Error**
 - Reduce batch size in `code/semantic_analysis.py` (default: 10)
 - Ensure you have at least 16GB of RAM
 - Close other applications to free up memory

2. **Pylint Not Found**
 - Ensure `pylint` is installed: `pip install pylint`
 - Verify the `pylint` executable is in your PATH

3. **LLM Inference Fails**
 - Check that the 4-bit quantized model file exists
 - Verify `llama-cpp-python` is installed correctly
 - Ensure your CPU supports AVX instructions

4. **Data Pipeline Fails**
 - Check your internet connection (required for streaming from HuggingFace)
 - Verify the `codeparrot/github-code` dataset is accessible
 - Check for rate limits on HuggingFace

### Logging

All scripts generate logs that can be found in the `results/` directory. Check these logs for detailed error messages.

## Next Steps

After successfully running the pipeline:

1. Review the generated reports in the `results/` directory
2. Analyze the statistical findings
3. Consider extending the analysis with additional datasets or models
4. Contribute improvements to the project

## Support

For issues or questions, please refer to the main `README.md` or open an issue on the GitHub repository.