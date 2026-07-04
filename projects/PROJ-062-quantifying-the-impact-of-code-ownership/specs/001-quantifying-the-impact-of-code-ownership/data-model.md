# Data Model: Quantifying the Impact of Code Ownership on Software Quality

## 1. Entity Overview

The data model supports the transformation from raw Git history to statistical results.

### 1.1 Core Entities

1.  **Repository**: The unit of analysis.
    -   Attributes: `url`, `clone_depth`, `total_commits`, `cutoff_date`, `status` (valid/invalid).
2.  **Module**: A file or directory within a repository.
    -   Attributes: `repo_id`, `file_path`, `lines_of_code`, `age_months`, `first_commit_date`, `last_commit_date`.
3.  **Commit**: An atomic change in the repository.
    -   Attributes: `hash`, `author`, `timestamp`, `file_path`, `lines_added`, `lines_deleted`.
4.  **Bug**: A GitHub Issue linked to a module.
    -   Attributes: `issue_id`, `repo_id`, `title`, `description`, `created_at`, `linked_file_path`.
5.  **Metric**: Calculated value for a module.
    -   Attributes: `repo_id`, `file_path`, `gini_coefficient`, `bug_density`, `churn`, `complexity`.

## 2. Data Flow & Storage

### 2.1 Raw Data (`data/raw/`)
-   **Format**: Local Git repositories (shallow clones).
-   **Constraint**: Immutable. Checksummed upon creation.

### 2.2 Intermediate Data (`data/intermediate/`)
-   **Format**: CSV files.
-   **Files**:
    -   `commits.csv`: Aggregated commit counts per file per author.
    -   `bugs.csv`: Linked issues with metadata.
    -   `modules.csv`: Module metadata (size, age).
    -   `metrics.csv`: Aggregated metrics per module (Gini, Churn, Complexity, Bug Density).
-   **Constraint**: Derived from raw data. Checksummed.

### 2.3 Results Data (`data/results/`)
-   **Format**: JSON (aggregates), PNG (plots).
-   **Files**:
    -   `correlation_summary.json`: Global and per-repo stats, including primary and secondary correlations.
    -   `sensitivity_analysis.json`: Sweep results.
    -   `plots/`: Scatter plots with regression lines.

## 3. Schema Definitions

See `contracts/` for formal YAML schemas.

### 3.1 Module Schema
-   `file_path`: String (normalized)
-   `gini`: Float [0.0, 1.0]
-   `bug_density`: Float (bugs/KLOC)
-   `size`: Int (KLOC)
-   `age`: Float (months)
-   `complexity`: Float (CC)
-   `churn`: Int (Total lines added + deleted)

### 3.2 Correlation Result Schema
-   `rho`: Float [-1.0, 1.0]
-   `p_value`: Float
-   `ci_lower`: Float
-   `ci_upper`: Float
-   `vif_max`: Float
-   `quadratic_significant`: Boolean