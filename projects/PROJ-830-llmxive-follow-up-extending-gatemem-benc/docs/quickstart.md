# llmXive Benchmark Suite: Quick Start Guide

This guide provides instructions to set up and run the full GateMem benchmark suite,
evaluating the Gatekeeper pipeline against baselines for Access Control, Utility,
Forgetting, and Computational Cost.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Sufficient disk space for model weights (~2GB) and dataset cache [UNRESOLVED-CLAIM: c_e6bb596d — status=not_enough_info]

## 1. Environment Setup

Clone the repository and install dependencies:

```bash
# Install core dependencies
pip install -r requirements.txt

# (Optional) Install development tools for linting and testing
pip install ruff black pytest
```

## 2. Data Preparation

The pipeline automatically fetches the GateMem dataset from HuggingFace on first run [UNRESOLVED-CLAIM: c_dbb4dd14 — status=not_enough_info].
If you prefer to download manually:

```bash
# The dataset will be cached automatically in ~/.cache/huggingface [UNRESOLVED-CLAIM: c_025c1606 — status=not_enough_info]
# Or run the data loader script explicitly:
python -m code.utils.data_loader
```

Ensure the `data/raw/` directory exists and contains the dataset files if running offline.

## 3. Running the Full Benchmark Suite

Execute the complete evaluation pipeline to run Gatekeeper and Baseline comparisons
across all domains (medical, office, education, household).

```bash
# Run the full evaluation suite
python -m code.cli.run_evaluation --all
```

### Specific Domain Execution

To run the benchmark on specific domains only:

```bash
# User Story 1: Access Control (Medical & Office domains)
python -m code.cli.run_evaluation --domain medical,office --metrics access_control

# User Story 2: Utility & Forgetting (Education & Household domains)
python -m code.cli.run_evaluation --domain education,household --metrics utility,forgetting

# User Story 3: Performance Profiling (All domains)
python -m code.cli.run_evaluation --all --profile
```

## 4. Output Artifacts

Upon successful completion, the following files will be generated:

- `data/processed/access_control_results.json`: Unauthorized exposure rates
- `data/processed/utility_results.json`: Task success rates and forgetting compliance
- `data/processed/performance_results.json`: Latency and memory usage metrics
- `data/samples/failure_cases.json`: Stratified sample of failure cases (50 cases) [UNRESOLVED-CLAIM: c_20cb2e68 — status=not_enough_info]
- `data/results/final_benchmark_report.md`: Comprehensive summary with statistical analysis

## 5. Statistical Analysis

The pipeline performs statistical comparisons between Gatekeeper and Baseline methods:
- **Primary Method**: Linear Mixed Models (LMM) with formula `score ~ method + (1|Domain)`
- **Fallback**: Paired t-test or Wilcoxon signed-rank test if LMM fails (singular matrix)
- **Domain-Stratified Analysis**: Separate tests per domain when global model is not feasible

Results are included in `final_benchmark_report.md` with test statistics, degrees of freedom,
p-values, and effect sizes.

## 6. Verification and Testing

Run the contract and integration tests to verify outputs:

```bash
# Run all tests
pytest tests/ -v

# Run specific contract tests
pytest tests/contract/ -v
```

## 7. Troubleshooting

### Memory Errors
If you encounter out-of-memory errors:
- Ensure you are using the CPU-only configuration (no CUDA)
- Reduce batch size in configuration files
- Clear HuggingFace cache: `rm -rf ~/.cache/huggingface`

### Missing Data
If data files are missing:
```bash
python -m code.utils.data_loader --fetch
```

### Statistical Analysis Failures
If LMM fitting fails, the pipeline automatically falls back to paired tests.
Check `logs/stats_analysis.log` for details on fallback triggers.

## 8. Configuration

Advanced configuration can be adjusted in `config/pipeline.yaml`:
- Model paths and parameters
- Threshold settings for access control
- Statistical test parameters
- Profiling intervals

## 9. Reporting

To regenerate the final report from existing results:

```bash
python -m code.cli.run_evaluation --generate-report
```

This will re-process `data/processed/*.json` files and output an updated
`data/results/final_benchmark_report.md`.

## 10. Next Steps

- Review `final_benchmark_report.md` for key findings
- Analyze `failure_cases.json` for edge case insights
- Extend the benchmark with custom domains or metrics
- Contribute improvements to the Gatekeeper pipeline