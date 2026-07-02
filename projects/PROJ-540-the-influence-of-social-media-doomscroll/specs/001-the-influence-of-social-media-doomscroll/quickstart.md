# Quickstart: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

## Prerequisites
- Python 3.11+
- `pip` or `poetry`
- Access to the project repository.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-540-the-influence-of-social-media-doomscroll
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Analysis

> **Note**: The analysis will **fail** if the verified dataset URLs do not contain the required variables. This is expected behavior given the current data gap.

1.  **Run the pipeline**:
    ```bash
    python code/main.py
    ```

2.  **Expected Output**:
    -   If data is valid: `outputs/regression_results.json`, `outputs/plot.png`.
    -   If data is invalid: `ERROR: Dataset schema mismatch. Missing required variables: ...`

## Troubleshooting

-   **Error: "Power limitation warning (N < 30)"**: The dataset has too few valid records after cleaning.
-   **Error: "Dataset schema mismatch"**: The provided URL does not contain the expected columns. (Current known issue with verified URLs).
-   **Error: "VIF > 10"**: Multicollinearity detected. Check if `baseline_anxiety` and `anxiety_score` are the same scale.
