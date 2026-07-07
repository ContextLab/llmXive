# Quickstart: Pipeline Validation Study: Gut Microbiome & Cognitive Flexibility Analysis

## Prerequisites

-   Python 3.11+
-   Git
-   Access to a Unix-like environment (Linux/macOS)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/your-repo.git
    cd your-repo
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

    *Note: `requirements.txt` pins versions for reproducibility (e.g., `pandas==2.0.3`, `scipy==1.11.4`).*

## Running the Pipeline

### 1. Generate Synthetic Data (Null Hypothesis)

Since no verified dataset URL exists for the specific linked microbiome-cognitive data, run the synthetic generator configured for **Null Hypothesis** testing (zero correlation):

```bash
python src/data/synthetic_gen.py --seed 42 --output data/raw/synthetic_cohort.csv
```

This creates a CSV with `participant_id`, `age`, `sex`, `bmi`, `dietary_fiber_intake`, `antibiotic_use_history`, `cognitive_flexibility_score`, `shannon_diversity`, etc. **Crucially, `cognitive_flexibility_score` is statistically independent of `shannon_diversity`.**

### 2. Filter and Merge

Filter for age >= 65 and non-null values:

```bash
python src/data/filtering.py --input data/raw/synthetic_cohort.csv --output data/processed/cohort_filtered.csv
```

### 3. Run Analysis

Execute the full analysis pipeline:

```bash
python src/main.py --config config/analysis_config.yaml
```

This will:
-   Calculate correlations (FR-004).
-   Run linear regression (FR-005).
-   Perform PERMANOVA/db-RDA (FR-005).
-   Perform A priori power analysis (FR-007).
-   Generate plots (FR-006).
-   **Validate Null Hypothesis**: Verify results show no significant correlation.

### 4. View Results

-   **Statistical Results**: `data/results/statistical_results.json`
-   **Plots**: `data/results/plots/` (e.g., `diversity_by_quartile.png`)
-   **Power Analysis**: `data/results/power_analysis.txt`

## Testing

Run the test suite to verify contract compliance and null hypothesis validation:

```bash
pytest tests/
```

To specifically test data filtering logic:

```bash
pytest tests/unit/test_filtering.py
```

To validate the pipeline correctly identifies no correlation:

```bash
pytest tests/unit/test_null_hypothesis.py
```

## Troubleshooting

-   **Memory Error**: If the dataset is too large, the `config/analysis_config.yaml` allows setting a `sample_size` limit to downsample the data before processing.
-   **Missing Dependencies**: Ensure `biom-format` is installed if raw sequence processing is enabled (though synthetic data skips this).
-   **No Variance**: If the synthetic data generator creates zero-variance diversity metrics, the script will log a warning and skip that specific test.