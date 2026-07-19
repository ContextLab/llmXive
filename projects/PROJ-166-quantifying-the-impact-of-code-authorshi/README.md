# Quantifying the Impact of Code Authorship Diversity on Software Security

This project implements a research pipeline to analyze the relationship between code authorship diversity and software vulnerability counts. It ingests data from GitHub and the NVD/CVE database, performs statistical modeling using Generalized Linear Models (GLM), and conducts robustness checks.

## Prerequisites

- Python 3.11+
- `cloc` (for lines of code analysis)
- `git` (for repository cloning and log parsing)
- A GitHub Personal Access Token (optional, for higher rate limits)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <repository-name>
 ```

2. Create and activate a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## CLI Usage

The pipeline is executed via a series of Python scripts located in the `code/` directory. Run them in the order specified below.

### 1. Generate Target List
Fetches the list of repositories to analyze from the GitHub API.
```bash
python code/data/generate_target_list.py
```
**Output**: `data/raw/target_list.csv`

### 2. Download NVD Data
Downloads and merges historical NVD/CVE JSON feeds.
```bash
python code/data/download_nvd.py
```
**Output**: `data/raw/nvd_cve_merged.json.gz` and checksum file.

### 3. Extract GitHub Metrics
Clones repositories, parses commit logs for author counts, and runs `cloc` for lines of code.
```bash
python code/data/extract_github.py
```
**Output**: `data/processed/github_raw_metrics.csv`

### 4. Merge Datasets
Joins GitHub metrics with NVD CVE counts using exact URL matching.
```bash
python code/data/merge_datasets.py
```
**Output**: `data/processed/repo_metrics.csv`

### 5. Fit Statistical Models
Fits a Negative-Binomial GLM to predict vulnerability counts.
```bash
python code/analysis/fit_models.py
```
**Output**: `data/processed/model_results.json`

### 6. Robustness Analysis
Performs subsampling by language and entropy-based sensitivity analysis.
```bash
python code/analysis/robustness.py
```
**Output**: `data/processed/robustness_results.json`

## Methods

### Statistical Modeling Approach

The core analysis uses a **Negative-Binomial Generalized Linear Model (GLM)** to model the count of vulnerabilities (`cve_count`) as a function of code authorship diversity (`unique_authors`) and control variables.

#### The Offset Approach
To normalize for project size, we use the natural logarithm of the Lines of Code (KLOC) as an **offset** term in the model. This is mathematically equivalent to modeling the *rate* of vulnerabilities per unit of code, rather than the raw count.

The model specification is:
$$ \log(E[Y]) = \beta_0 + \beta_1 X_1 + \dots + \beta_k X_k + \log(\text{KLOC}) $$

Where:
- $Y$ is the vulnerability count (response variable).
- $X_i$ are the predictors (e.g., author count, project age).
- $\log(\text{KLOC})$ is the offset with a fixed coefficient of 1.
- The link function is the log link.

By including `log(KLOC)` as an offset, the coefficient $\beta_1$ for author count represents the multiplicative change in the *vulnerability rate* for a one-unit increase in author count, holding other factors constant.

#### Model Selection
- **Distribution**: Negative-Binomial (chosen over Poisson to handle overdispersion common in vulnerability count data).
- **Inference**: P-values are adjusted using the Benjamini-Hochberg procedure to control the False Discovery Rate (FDR).
- **Diagnostics**: Variance Inflation Factor (VIF) is calculated to check for multicollinearity among predictors.

## Data

### Data Sources
1. **GitHub API**: Used to identify target repositories and extract metadata (stars, language, age).
2. **Git Repositories**: Shallow clones (since 2015-01-01) are used to parse `git log` for unique author counts and `cloc` for code volume.
3. **NVD/CVE Database**: Historical JSON feeds are downloaded and merged to count vulnerabilities associated with each repository.

### Data Pipeline
The pipeline follows a strict ETL process:
1. **Extraction**: Raw data is pulled from APIs and local clones.
2. **Transformation**:
 - Repositories with missing data (e.g., deleted, private) are skipped.
 - CVEs are matched to repositories using **exact URL matching** to prevent false positives.
 - Rows with zero KLOC are excluded from the modeling phase (log(0) undefined).
3. **Loading**: Processed data is saved to `data/processed/` in CSV and JSON formats for analysis.

### Data Integrity
All scripts are designed to fail loudly if real data sources are unreachable. No synthetic or placeholder data is generated.

## Testing

Run the unit and integration tests:
```bash
pytest tests/
```

Specific test suites:
- `tests/unit/`: Unit tests for data ingestion and parsing.
- `tests/contract/`: Schema validation tests.
- `tests/integration/`: End-to-end pipeline tests on a seed dataset.