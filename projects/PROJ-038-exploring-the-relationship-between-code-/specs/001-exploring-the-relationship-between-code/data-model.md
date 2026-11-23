# Data Model: Exploring the Relationship Between Code Complexity Metrics and Bug Prediction Accuracy

## Entities & Relationships

### 1. ProjectSubset
Represents the collection of selected Java projects.
*   **Attributes**:
    *   `project_id` (string): Unique identifier (e.g., "Chart-1").
    *   `name` (string): Project name.
    *   `version` (string): Defects4J version string.
    *   `total_files` (integer): Count of Java files in the subset.
    *   `buggy_files` (integer): Count of files labeled as buggy.
    *   `selection_reason` (string): Reason for inclusion (e.g., "Size < 50MB").

### 2. CodeFile
Represents a single Java source file with computed metrics.
*   **Attributes**:
    *   `file_path` (string): Relative path within the project.
    *   `project_id` (string): Foreign key to ProjectSubset.
    *   `cyclomatic_complexity` (float): Computed via PMD.
    *   `halstead_volume` (float): Computed via custom parser.
    *   `lines_of_code` (integer): Count of non-empty, non-comment lines.
    *   `is_buggy` (integer): Binary label (0 or 1).
    *   `exclusion_reason` (string, nullable): If excluded, reason (e.g., "Syntax Error", "Generated Code").

### 3. ModelPerformance
Represents the evaluation results of a trained classifier.
*   **Attributes**:
    *   `model_name` (string): e.g., "LogisticRegression", "RandomForest".
    *   `metric_type` (string): e.g., "ROC-AUC", "F1-Score".
    *   `mean_score` (float): Average score across folds.
    *   `std_score` (float): Standard deviation.
    *   `fold_scores` (list of float): Scores for each of the 50 folds.

### 4. CorrelationResult
Represents the statistical relationship between a metric and the target.
*   **Attributes**:
    *   `metric_name` (string): e.g., "Cyclomatic_Complexity".
    *   `correlation_type` (string): "Point-Biserial" or "Spearman".
    *   `coefficient` (float): The correlation value.
    *   `p_value` (float): Significance level.
    *   `vif_score` (float, nullable): Variance Inflation Factor.
    *   `partial_correlation` (float, nullable): Partial correlation controlling for other metrics.

## Data Flow

1.  **Ingestion**: `defects4j` repo -> `ProjectSubset` selection -> `CodeFile` raw data.
2.  **Processing**: `CodeFile` raw -> Metrics Calculation -> `CodeFile` enriched (with `is_buggy`).
3.  **Validation**: `CodeFile` enriched -> Filter/Log exclusions -> `features.csv` (Feature Matrix).
4.  **Analysis**: `features.csv` -> Correlation Analysis -> `CorrelationResult` -> `correlation_report.json`.
    *   *Note*: This step includes VIF and Partial Correlation calculations to address multicollinearity.
5.  **Modeling**: `features.csv` -> CV Training -> `ModelPerformance` -> `model_results.csv`.
6.  **Significance**: `ModelPerformance` (Full vs Single) -> **Sign-Flip Permutation Test** -> `p_value` -> `output.json`.
    *   *Mapping*: **SC-003** is satisfied by the `p_value` field in `output.schema.yaml`.

## Data Formats

*   **Input**: Git repository (Defects4J).
*   **Intermediate**: CSV (`features.csv`) with columns: `project_id`, `file_path`, `cc`, `halstead`, `loc`, `is_buggy`.
*   **Output**: JSON (`correlation_report.json`, `permutation_test.json`, `output.json`) and CSV (`model_results.csv`).
