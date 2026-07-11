# Quickstart: llmXive follow-up: extending "Trust-Region Behavior Blending for On-Policy Distillation"

## Prerequisites

-   Python 3.11+
-   Git
-   Sufficient Disk Space (for dataset download and processing)
-   GB RAM (minimum)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <REPO_URL>
    cd projects/PROJ-976-llmxive-follow-up-extending-trust-region
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    ```

## Running the Pipeline

### Step 1: Feature Extraction (FR-001)
Compute diversity profiles for the source (Book Corpus) and target (BEIR) datasets.

```bash
python code/pipelines/extract_features.py \
  --source-data data/raw/source.parquet \
  --target-data data/raw/target.tsv \
  --output-dir data/processed
```

*Note: This script handles empty strings and parse failures automatically.*

### Step 2: Correlation Analysis (Revised from "Model Training")
Compute correlations between diversity metrics and proxy quality scores.

```bash
python code/pipelines/analyze_correlations.py \
  --source-data data/processed/feature_matrix_source.csv \
  --target-data data/processed/feature_matrix_target.csv \
  --output-dir data/results
```

### Step 3: Baseline Comparison & Generalization Gap
Calculate the baseline performance (fixed default) and the generalization gap (Source vs Target).

```bash
python code/pipelines/analyze_correlations.py \
  --source-data data/processed/feature_matrix_source.csv \
  --target-data data/processed/feature_matrix_target.csv \
  --baseline-comparison \
  --output-dir data/results
```

### Step 4: Statistical Significance
Run permutation tests to validate the diversity-proxy correlation.

```bash
python code/pipelines/analyze_correlations.py \
  --target-data data/processed/feature_matrix_target.csv \
  --permutation-test \
  --output-dir data/results
```

## Verifying Results

Check `data/results/correlation_report.json` for:
-   `pearson_correlation`: Target correlation with proxy.
-   `baseline_delta`: Improvement over fixed-default baseline.
-   `generalization_gap`: Performance drop from source to target.
-   `permutation_p_value`: Statistical significance.

## Troubleshooting

-   **Memory Error**: Reduce batch size in `config.py` or downsample the dataset.
-   **Parse Errors**: Ensure `en_core_web_sm` is installed. Check logs for specific failure patterns.
-   **Missing Proxy Data**: Verify that the raw data files contain the required proxy columns (e.g., `score` in BEIR).