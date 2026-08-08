# Quickstart: Assessing the Stability of Statistical Model Performance

This guide walks you through running the full pipeline to assess model stability across multiple datasets.

## Prerequisites

- Python 3.10+
- `pip` package manager
- Internet connection (to download datasets from OpenML)

## Installation

1. Clone the repository and navigate to the project root.
2. Install dependencies:

 ```bash
 pip install -r requirements.txt
 ```

## Usage

Run the main pipeline script to execute the full evaluation:

```bash
python -m code.main
```

This will:
1. Load the configured datasets from OpenML.
2. Run repeated stratified cross-validation (10 folds, 10 repeats) for Logistic Regression, Random Forest, and Linear SVM.
3. Calculate stability metrics (CV, log-variance).
4. Perform correlation analysis and permutation tests.
5. Generate the final report.

To generate the final report separately (if raw data already exists):

```bash
python -m code.scripts.generate_final_report
```

## Dataset List

The pipeline uses the following 15 binary classification datasets from OpenML/UCI. [UNRESOLVED-CLAIM: c_1973f8be — status=not_enough_info]
These datasets were selected to span a wide range of sample sizes (N < 1k, 1k–10k, N > 10k)and feature counts, ensuring a robust assessment of model stability.

| Dataset Name | OpenML ID | Samples | Features | Description |
|:--- |:--- |:--- |:--- |:--- |
| Pima Indians Diabetes | 1510 | 768 (2509.12259, https://arxiv.org/abs/2509.12259) | 8 | Classic binary classification on health metrics. |
| Breast Cancer Wisconsin | 1461 | 569 | 30 | Malignant vs. benign tumor classification. |
| Ionosphere | 1464 | 351 | 34 | Radar signal classification (good/bad). |
| Haberman's Survival | 1228 | 306 | 3 | Patient survival status after surgery. |
| Spect Heart | 1478 | 267 | 44 | Heart disease diagnosis (presence/absence). |
| Breast Cancer | 1286 | 286 | 9 | UCI Breast Cancer dataset. |
| Monks-1 | 1472 | 432 | 6 | Synthetic robot classification task. |
| Monks-2 | 1473 | 432 | 6 | Synthetic robot classification task. |
| Monks-3 | 1474 | 432 | 6 | Synthetic robot classification task. |
| Credit Approval | 1466 | 690 (2102.04721, https://arxiv.org/abs/2102.04721) | 15 | Credit card approval prediction. |
| German Credit | 1467 | 1000 | 20 | German credit risk assessment. |
| Heart Disease | 1470 | 270 | 13 | UCI Heart Disease dataset. |
| Hepatitis | 1471 | 155 | 19 | Hepatitis diagnosis (alive/died). |
| Liver Disorders | 1287 | 345 | 6 | Liver disorder detection. |
| Thyroid | 1463 | 215 | 5 | Thyroid disease classification. |

**Note**: Datasets with fewer than 200 samples are automatically skipped during execution to ensure stable 10-fold cross-validation results.

## Output Files

After a successful run, results are saved in the `results/` directory:

- `results/raw_evaluations.csv`: Per-fold, per-repeat metrics.
- `results/stability_metrics.csv`: Aggregated stability metrics (CV, log-variance).
- `results/correlation_results.csv`: Correlation analysis between stability and dataset properties.
- `results/permutation_results.csv`: Significance testing results for variance differences.
- `results/regression_residuals.csv`: Residuals from the log-log regression analysis.
- `results/final_report.md`: Human-readable summary of findings.

## Troubleshooting

- **Network Errors**: If a dataset fails to download, the script logs a warning and skips that dataset, continuing with the rest.
- **Insufficient Datasets**: If fewer than 15 valid datasets are available after filtering, the script exits with an error.
- **Memory Limits**: The pipeline processes datasets sequentially to stay within memory constraints (~7GB).