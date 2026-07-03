# Quantifying the Impact of Code Authorship Diversity on Software Security

This project analyzes the relationship between code authorship diversity and software security vulnerabilities using data from GitHub and the NVD/CVE database.

## Prerequisites

- Python 3.11+
- `cloc` >= 1.88 (for lines of code analysis)
- Git
- Access to GitHub API (token recommended for rate limits)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

3. Ensure `cloc` is installed and in your PATH. Verify version:
 ```bash
 cloc --version
 ```

## CLI Usage

The project provides several command-line scripts to execute the research pipeline. Run them from the project root.

### 1. Generate Target List
Fetches a list of target GitHub repositories based on criteria defined in the configuration.
```bash
python code/data/generate_target_list.py
```
**Output:** `data/raw/target_list.csv`

### 2. Download NVD/CVE Data
Downloads, merges, and deduplicates historical NVD CVE feeds.
```bash
python code/data/download_nvd.py
```
**Output:** `data/raw/nvd_cve_merged.json.gz` and checksum file.

### 3. Extract GitHub Metrics
Clones repositories, parses git logs for author counts, and runs `cloc` for KLOC.
```bash
python code/data/extract_github.py
```
**Output:** `data/processed/github_raw_metrics.csv`

### 4. Merge Datasets
Joins GitHub metrics with NVD vulnerability counts.
```bash
python code/data/merge_datasets.py
```
**Output:** `data/processed/repo_metrics.csv`

### 5. Fit Statistical Models
Fits a Negative-Binomial GLM to analyze the impact of author diversity on CVE counts.
```bash
python code/analysis/fit_models.py
```
**Output:** `data/processed/model_results.json`

### 6. Robustness Analysis
Performs subsampling by language and entropy-based diversity analysis.
```bash
python code/analysis/robustness.py
```
**Output:** `data/processed/robustness_results.json`

## Methods

### Statistical Modeling Approach

We employ a **Negative-Binomial Generalized Linear Model (GLM)** to model the count of vulnerabilities (`cve_count`) as a function of code authorship diversity and control variables.

#### The GLM Offset
To normalize for project size and prevent larger projects from appearing artificially more vulnerable simply due to having more lines of code, we use the **log of Lines of Code (KLOC)** as an **offset** term in the model.

The model specification is:
$$ \log(E[Y_i]) = \beta_0 + \beta_1 \cdot \text{AuthorCount}_i + \beta_2 \cdot \text{Controls}_i + \log(\text{KLOC}_i) $$

Where:
- $Y_i$ is the vulnerability count for repository $i$.
- $\text{AuthorCount}_i$ is the number of unique contributors.
- $\text{Controls}_i$ includes variables like project age and release count.
- $\log(\text{KLOC}_i)$ is the offset, forcing its coefficient to be exactly 1.

This formulation effectively models the **vulnerability rate per unit of code** rather than the raw count, allowing for a fair comparison across projects of different sizes.

#### Robustness Checks
- **Subsampling:** Models are re-fitted on subsets of data grouped by primary programming language (e.g., Python, JavaScript) to ensure results are not driven by language-specific characteristics.
- **Alternative Metric:** We replace the raw author count with **Shannon Entropy** of author contributions to test if the relationship holds under a more nuanced diversity metric.
- **Multiple Testing:** Benjamini-Hochberg correction is applied to p-values to control the false discovery rate across multiple hypothesis tests.

## Data

### Data Sources

1. **GitHub API**: Used to fetch repository metadata (stars, language, creation date) and extract commit history.
 - Data is retrieved via the public GitHub API.
 - Commit logs are parsed to identify unique authors.
2. **NVD/CVE JSON Feeds**: Historical vulnerability data is downloaded directly from the National Vulnerability Database.
 - Feeds are merged, deduplicated, and validated via SHA256 checksums.
3. **cloc**: Used to calculate Lines of Code (KLOC) for each repository.

### Pipeline Structure

The data processing pipeline follows these steps:

1. **Target List Generation**: A curated list of repositories is generated based on specific criteria (e.g., language, stars, age).
2. **Raw Data Collection**:
 - GitHub metrics (author count, KLOC) are extracted via git clones and `cloc`.
 - NVD CVE data is downloaded and processed.
3. **Data Merging**: GitHub metrics are joined with CVE counts using **exact URL matching** to ensure data integrity.
4. **Analysis**: The merged dataset (`repo_metrics.csv`) is used as input for statistical modeling.

### Output Files

- `data/raw/target_list.csv`: List of repositories to analyze.
- `data/raw/nvd_cve_merged.json.gz`: Processed vulnerability data.
- `data/processed/github_raw_metrics.csv`: Extracted GitHub metrics.
- `data/processed/repo_metrics.csv`: Final merged dataset for analysis.
- `data/processed/model_results.json`: Statistical model coefficients and diagnostics.
- `data/processed/robustness_results.json`: Results from subsampling and entropy analysis.

## Testing

Run the test suite using `pytest`:
```bash
pytest tests/
```

Specific test groups:
- Unit tests: `pytest tests/unit/`
- Integration tests: `pytest tests/integration/`
- Contract tests: `pytest tests/contract/`

## License

This project is licensed under the MIT License.