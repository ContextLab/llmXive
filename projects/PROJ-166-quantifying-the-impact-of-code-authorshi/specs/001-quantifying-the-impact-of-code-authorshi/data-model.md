# Data Model: Quantifying the Impact of Code Authorship Diversity on Software Security

## 1. Entity Definitions

### 1.1 Repository (Source)
Represents a single target GitHub repository.
*   `repo_id`: Unique identifier (e.g., `owner/name`).
*   `url`: Full GitHub URL.
*   `primary_language`: Language of the repository (e.g., "Python").
*   `created_at`: Date of repository creation.
*   `stars`: Number of stars at ingestion time.

### 1.2 Commit History (Derived)
Derived from `git log` on the cloned repository.
*   `total_commits`: Count of commits in the `--shallow-since` window.
*   `unique_authors`: Count of distinct email addresses (or usernames) in the commit log. **Primary Independent Variable (Breadth)**.
*   `project_age`: Years from `created_at` to `last_commit_date`.

### 1.3 Code Metrics (Derived)
*   `kloc`: Thousands of Lines of Code (calculated by `cloc`).
*   `log_kloc`: Natural logarithm of `kloc`.
*   `entropy`: Shannon entropy of author commit distribution. **Secondary Metric (Evenness)**.
*   `author_count`: Alias for `unique_authors` used in modeling.

### 1.4 Vulnerability Record (Source)
*   `cve_id`: Unique CVE identifier (e.g., "CVE-2023-12345").
*   `description`: Summary of the vulnerability.
*   `cvss_score`: Severity score.
*   `matched_url`: The repository URL matched in the NVD record (via substring).

### 1.5 Aggregated Dataset (Input to Model)
A single row per repository containing all predictors and the outcome.
*   `cve_count`: Total number of CVEs matched to the repository. **Outcome Variable**.
*   `author_count`: `unique_authors`.
*   `project_age`: Years.
*   `primary_language`: Categorical (one-hot encoded in model).
*   `release_count`: Number of GitHub releases.
*   `log_kloc`: Continuous.
*   `cve_density`: `cve_count / kloc`. **Descriptive Only**.

## 2. Data Flow

1.  **Ingestion**: `GitHub API` -> `List of Repos` -> `data/repos_list.json`
2.  **Cloning**: `List of Repos` -> `git clone --shallow-since` -> `data/repos/<repo_id>/`
3.  **Metric Extraction**: `data/repos/<repo_id>/` -> `metrics.py` -> `data/processed/repo_metrics.csv`
4.  **Vulnerability Matching**: `NVD JSON` + `repo_metrics.csv` -> `ingestion.py` -> `data/processed/vuln_matches.csv`
5.  **Model Input**: `repo_metrics.csv` + `vuln_matches.csv` -> `modeling.py` -> `data/processed/final_dataset.csv`
6.  **Output**: `final_dataset.csv` -> `modeling.py` -> `data/processed/model_results.json`

## 3. Data Constraints

*   **Missing Data**: Repositories with zero commits in the `--shallow-since` window are excluded.
*   **Ambiguous Matches**: Repositories with NVD matches that cannot be resolved via substring matching are excluded and logged.
*   **Zero CVEs**: Repositories with zero CVEs are included (Negative Binomial handles zeros).
*   **Circularity Prevention**: The model formula explicitly excludes `cve_density`. The code validates that the outcome variable is strictly `cve_count` (integer).