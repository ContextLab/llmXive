# Quantifying the Impact of Code Authorship Diversity on Software Security

This project investigates the relationship between code authorship diversity (number of unique contributors) and software security (vulnerability counts), controlling for project size (KLOC) and other factors.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Data Pipeline](#data-pipeline)
- [Analysis & Modeling](#analysis--modeling)
- [CLI Usage](#cli-usage)
- [Methods](#methods)
 - [GLM Offset Approach](#glm-offset-approach)
 - [Statistical Controls](#statistical-controls)
- [Data](#data)
 - [Raw Data Sources](#raw-data-sources)
 - [Processed Data](#processed-data)
- [Project Structure](#project-structure)
- [Testing](#testing)

## Prerequisites

- Python 3.11+
- Git
- `cloc` (version >= 1.88)
- Access to GitHub API (token required)
- Access to NVD API (optional, for CVE data)

## Installation

1. Clone the repository:
 ```bash
 git clone
 cd quantifying-authorship-diversity
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

3. Set up environment variables:
 ```bash
 export GITHUB_TOKEN=your_github_token_here
 ```

## Data Pipeline

The data pipeline consists of several stages to collect, process, and merge data from GitHub and the National Vulnerability Database (NVD).

### Step 1: Generate Target List
Fetches a list of target repositories based on criteria (e.g., stars, language).
```bash
python code/data/generate_target_list.py
```
Output: `data/raw/target_list.csv`

### Step 2: Download NVD Data
Downloads and merges CVE data from the NVD.
```bash
python code/data/download_nvd.py
```
Output: `data/raw/nvd_cve_merged.json.gz` and checksum file.

### Step 3: Extract GitHub Metrics
Clones repositories, parses git logs for author counts, and runs `cloc` for KLOC.
```bash
python code/data/extract_github.py
```
Output: `data/processed/github_raw_metrics.csv`

### Step 4: Merge Datasets
Joins GitHub metrics with NVD CVE counts.
```bash
python code/data/merge_datasets.py
```
Output: `data/processed/repo_metrics.csv`

## Analysis & Modeling

### Fit Statistical Models
Fits a Negative Binomial GLM to predict vulnerability counts.
```bash
python code/analysis/fit_models.py
```
Output: `data/processed/model_results.json`

### Robustness Checks
Performs subsampling by language and alternative diversity metrics (Shannon entropy).
```bash
python code/analysis/robustness.py
```
Output: `data/processed/robustness_results.json`

## CLI Usage

The project provides several entry points for running the pipeline components.

### Run the Full Pipeline
Execute all data ingestion and analysis steps in sequence:
```bash
bash scripts/run_full_pipeline.sh
```

### Run Specific Components
- **Target List Generation**:
 ```bash
 python -m code.data.generate_target_list
 ```
- **NVD Download**:
 ```bash
 python -m code.data.download_nvd
 ```
- **GitHub Extraction**:
 ```bash
 python -m code.data.extract_github
 ```
- **Data Merging**:
 ```bash
 python -m code.data.merge_datasets
 ```
- **Model Fitting**:
 ```bash
 python -m code.analysis.fit_models
 ```
- **Robustness Analysis**:
 ```bash
 python -m code.analysis.robustness
 ```

### Configuration
Configuration is handled via `code/config.py`. Environment variables can override specific settings:
- `GITHUB_TOKEN`: GitHub API token
- `NVD_API_KEY`: NVD API key (if required)
- `OUTPUT_DIR`: Base directory for output files (default: `data/`)

## Methods

### GLM Offset Approach

To analyze the relationship between authorship diversity and vulnerability counts while controlling for project size, we employ a Generalized Linear Model (GLM) with a Negative Binomial distribution.

The model is specified as:

$$ \log(\mathbb{E}[CVE\_Count]) = \beta_0 + \beta_1 \cdot \text{AuthorCount} + \sum \beta_i \cdot \text{Controls}_i + \log(\text{KLOC}) $$

Where:
- **Response Variable**: `CVE_Count` (number of vulnerabilities).
- **Primary Predictor**: `AuthorCount` (number of unique contributors).
- **Controls**: Project age, release count, and language dummies.
- **Offset**: $\log(\text{KLOC})$.

**Why use an offset?**
Using `log(KLOC)` as an offset (rather than a standard predictor) normalizes the vulnerability count by project size. This allows us to model the *rate* of vulnerabilities per thousand lines of code, rather than the raw count. It assumes that the expected number of vulnerabilities scales linearly with the size of the codebase, isolating the effect of authorship diversity on the vulnerability rate.

Rows with `KLOC = 0` are excluded from the analysis because $\log(0)$ is undefined.

### Statistical Controls

- **Multicollinearity**: Variance Inflation Factors (VIF) are calculated for all predictors to detect multicollinearity.
- **Multiple Testing**: Benjamini-Hochberg correction is applied to p-values to control the False Discovery Rate (FDR) across multiple hypothesis tests.
- **Robustness**: Sensitivity analyses are performed by:
 1. Subsampling data by programming language (Python, JavaScript).
 2. Replacing `AuthorCount` with Shannon Entropy of author contributions.

## Data

### Raw Data Sources

1. **GitHub API**: Used to fetch repository metadata (stars, language, age) and commit history.
 - **Artifact**: `data/raw/target_list.csv`
2. **NVD/CVE Feeds**: Downloaded JSON feeds containing vulnerability data.
 - **Artifact**: `data/raw/nvd_cve_merged.json.gz`
3. **Git Repositories**: Shallow clones of target repositories.
 - **Artifact**: Temporary clones during `extract_github.py` execution.

### Processed Data

1. **GitHub Metrics**: Extracted author counts and KLOC.
 - **File**: `data/processed/github_raw_metrics.csv`
 - **Columns**: `url`, `unique_authors`, `raw_line_count`, `kloc`
2. **Merged Dataset**: Combined GitHub metrics with CVE counts.
 - **File**: `data/processed/repo_metrics.csv`
 - **Columns**: `url`, `language`, `unique_authors`, `kloc`, `cve_count`, `project_age`, `release_count`
3. **Model Results**: Coefficients, standard errors, p-values, and confidence intervals.
 - **File**: `data/processed/model_results.json`
4. **Robustness Results**: Subsample and entropy model outputs.
 - **File**: `data/processed/robustness_results.json`

## Project Structure

```
.
├── code/
│ ├── __init__.py
│ ├── config.py
│ ├── data/
│ │ ├── __init__.py
│ │ ├── generate_target_list.py
│ │ ├── download_nvd.py
│ │ ├── extract_github.py
│ │ ├── merge_datasets.py
│ │ ├── schemas.py
│ │ └── utils.py
│ └── analysis/
│ ├── __init__.py
│ ├── fit_models.py
│ ├── entropy_glm.py
│ └── robustness.py
├── data/
│ ├── raw/
│ └── processed/
├── tests/
│ ├── unit/
│ ├── integration/
│ └── contract/
├── requirements.txt
└── README.md
```

## Testing

Run the test suite using pytest:

```bash
pytest tests/
```

Specific test categories:
- **Unit Tests**: `pytest tests/unit/`
- **Integration Tests**: `pytest tests/integration/`
- **Contract Tests**: `pytest tests/contract/`