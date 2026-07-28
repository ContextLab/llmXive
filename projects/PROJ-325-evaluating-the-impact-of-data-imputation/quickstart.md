# Quickstart Guide: Evaluating the Impact of Data Imputation

This guide walks you through running the full pipeline for evaluating imputation methods.

## Prerequisites

- Python 3.8+
- pip installed
- Git

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-325-evaluating-the-impact-of-data-imputation

# Install dependencies
pip install -r requirements.txt
```

## Running the Pipeline

The pipeline consists of several stages. Run them in order:

### 1. Generate Synthetic Data (Task T005b)

Generate a synthetic dataset with known ground truth parameters and controlled missingness:

```bash
python code/synthetic_generator.py --n-rows 50000 --mechanism MAR --output-csv data/processed/synthetic_mar_v1.csv --output-meta data/processed/synthetic_mar_v1_meta.json
```

This produces:
- `data/processed/synthetic_mar_v1.csv`: The synthetic dataset
- `data/processed/synthetic_mar_v1_meta.json`: Metadata with ground truth parameters

### 2. Fetch Real Data (Task T004b)

Download the GSS 2018 subset:

```bash
python code/data/loader.py --source "gss" --url "https://gss.norc.org/documents/stata/GSS2018_subset.dta" --output data/raw/gss_2018_subset.csv
```

### 3. Run Imputation Pipeline

Apply imputation methods to the synthetic data:

```bash
python code/imputation/run_all.py --input data/processed/synthetic_mar_v1.csv --methods "cc,single,mice" --mice-chains 4 --mice-iterations 1000 --burn-in 500 --output data/processed/imputation_results.json
```

### 4. Calculate Bias Metrics

Compute bias metrics comparing imputation methods to ground truth:

```bash
python code/metrics/bias.py --results data/processed/imputation_results.json --true-variance 100.0 --sweep-param "m" --sweep-values "5,10,20" --output data/reports/bias_analysis.json
```

### 5. Generate Final Report

Compile all results into a final report:

```bash
python code/main.py --input data/processed/imputation_results.json --bias data/reports/bias_analysis.json --output data/processed/final_report.md
```

## Verification

After running the pipeline, verify the outputs:

```bash
# Check synthetic data exists
ls -lh data/processed/synthetic_mar_v1.csv data/processed/synthetic_mar_v1_meta.json

# Check baseline results
jq '.status == "success"' data/processed/baseline_results.json

# Check sensitivity sweep results
jq '.[0].m_value and.[0].bias_rate' data/processed/sensitivity_sweep_results.json

# Check final report contains associational disclaimer
grep "All findings are associational" data/processed/final_report.md
```

## Troubleshooting

### Missing Modules

If you get `ModuleNotFoundError`, ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### Data Fetch Failures

If data fetching fails, check your internet connection and the URL validity.

### Convergence Issues

If MICE fails to converge, try increasing `--mice-iterations` or adjusting the seed.

## Next Steps

- Review the generated report at `data/processed/final_report.md`
- Analyze the bias metrics in `data/reports/bias_analysis.json`
- Extend the sensitivity analysis by modifying parameters in `code/analysis.py`
