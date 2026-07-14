# Quickstart Guide: Statistical Analysis of Code Complexity

This guide provides step-by-step instructions to reproduce the statistical analysis of code complexity metrics and bug prediction pipeline described in this project.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- 10GB+ available disk space (for downloading and processing Java project archives)
- 8GB+ RAM recommended

## Installation

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd statistical-analysis-of-code-complexity
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Data Acquisition and Preprocessing

The pipeline automatically downloads Java projects from GHTorrent, extracts source files, computes complexity metrics, and labels bug fixes.

**Run the full data pipeline**:
```bash
python code/data/pipeline.py
```

This single command executes the following stages sequentially:
1. Downloads at least 10 Java projects from GHTorrent
2. Extracts Java source files and commit metadata
3. Computes complexity metrics (cyclomatic complexity, LOC, token count, nesting depth, Halstead volume)
4. Labels bug-fix vs. non-bug-fix code units
5. Validates bug label reliability (ensures ≥85% precision)
6. Preprocesses data (imputes missing values, log-transforms skewed metrics)
7. Performs project-level stratified train/test split (70/30)

**Output artifacts**:
- `data/raw/` - Downloaded archives and extracted source files
- `data/intermediate/` - Raw metrics and bug labels
- `data/processed/bug_complexity_dataset.csv` - Final cleaned dataset
- `data/processed/train_split.csv` - Training set (70%)
- `data/processed/test_split.csv` - Test set (30%)

## Statistical Modeling

Train and compare predictive models for bug prediction.

**Run the modeling pipeline**:
```bash
python code/modeling/pipeline.py
```

This executes:
1. Collinearity diagnostics (VIF calculation) and feature reduction
2. Training of primary L1-regularized logistic regression model
3. Training of alternative Random Forest model
4. Model comparison (ROC-AUC, Spearman rank correlation)
5. Feature importance extraction
6. Multiple hypothesis correction (Benjamini-Hochberg)
7. Generation of partial dependence plots
8. Threshold derivation for developers

**Output artifacts**:
- `data/model/primary.pkl` - Primary logistic regression model
- `data/model/alternative.pkl` - Alternative Random Forest model
- `data/model/metrics.json` - Evaluation metrics (ROC-AUC, PR-AUC)
- `data/model/corrected_pvalues.csv` - Benjamini-Hochberg corrected p-values
- `data/model/thresholds.csv` - Practical threshold values
- `data/figures/pdp_*.png` - Partial dependence plots for top 3 metrics

## Evaluation and Reporting

**Generate the research report**:
```bash
python code/report/generate_report.py
```

This produces a comprehensive report (PDF/HTML) containing:
- Dataset statistics and preprocessing summary
- Model performance comparison
- Feature importance analysis
- Partial dependence plot interpretations
- Practical recommendations for developers

**Output**: `data/report/research_report.html` (or `.pdf`)

## Testing

Run the full test suite with coverage requirements:
```bash
python code/run_tests.py
```

This enforces ≥85% code coverage and runs all contract, unit, and integration tests.

## Configuration

Random seeds and other configuration parameters are managed in `code/utils/config.py`. To change the random seed:

```python
from utils.config import set_random_seed
set_random_seed(42)
```

## Troubleshooting

### "No module named 'lizard'"
Ensure you installed all dependencies: `pip install -r requirements.txt`

### "Download failed"
Check your internet connection. The pipeline downloads from GHTorrent mirrors which may occasionally be slow or unavailable.

### "Memory error"
The pipeline includes memory-aware chunked processing, but very large projects may require more RAM. Consider increasing available memory or reducing the number of projects.

## Reproducibility

All analyses are reproducible with the provided code and data. The pipeline:
- Uses fixed random seeds for reproducibility
- Verifies checksums of downloaded archives
- Logs all processing steps
- Produces deterministic outputs given the same input data

For full reproducibility, ensure you:
1. Use Python 3.11
2. Install exact dependency versions from `requirements.txt`
3. Run the pipeline from a clean environment
4. Use the same GHTorrent snapshot (version is logged in `data/raw/download_manifest.json`)

## Citation

If you use this work in your research, please cite the associated publication (citation details to be added upon publication).