# Data Model: Assessing Statistical Significance of Observed Correlations in Public Databases

## 1. Input Data Model

### Raw Dataset
*   **Format**: CSV (downloaded via verified UCI URLs).
*   **Schema**:
    *   `variable_name`: string (column header)
    *   `value`: float (numeric value)
*   **Constraints**:
    *   Must contain a sufficient number of continuous variables after cleaning.
    *   Missing values: Dropped (rows with any NaN).
    *   Constant variables: Removed prior to correlation.

## 2. Intermediate Data Model

### Correlation Matrix
*   **Type**: Symmetric 2D array (float64).
*   **Dimensions**: $V \times V$ (where $V$ is number of valid variables).
*   **Content**: Pearson correlation coefficients (primary) or Spearman (exploratory).

### Network Graph
*   **Type**: Undirected weighted graph (NetworkX).
*   **Nodes**: Variables.
*   **Edges**: Pairs where $|r_{ij}| > \text{threshold}$.
*   **Weight**: $|r_{ij}|$.

## 3. Output Data Model

### Null Distribution Array
*   **Type**: 1D array (float64).
*   **Length**: 1,000 (number of permutations).
*   **Content**: Values of a specific statistic (e.g., mean absolute correlation) from permuted data.

### Significance Result
*   **Type**: Structured record (JSON/CSV row).
*   **Fields**:
    *   `dataset_id`: string
    *   `statistic_name`: string (e.g., "density", "mean_abs_corr")
    *   `threshold`: float (e.g., 0.3)
    *   `observed_value`: float
    *   `p_value`: float (raw empirical)
    *   `q_value`: float (BY-adjusted)
    *   `is_significant`: boolean (q < 0.05)

### Sensitivity Summary
*   **Type**: Table (CSV).
*   **Columns**: `threshold`, `significant_count`, `total_tests`, `max_p_value`.

## 4. Exploratory Data Model (Spearman)

### Spearman Correlation Matrix
*   **Type**: Symmetric 2D array (float64).
*   **Dimensions**: $V \times V$.
*   **Content**: Spearman correlation coefficients.
*   **Usage**: Stored for exploratory comparison only. Not used in significance testing.
