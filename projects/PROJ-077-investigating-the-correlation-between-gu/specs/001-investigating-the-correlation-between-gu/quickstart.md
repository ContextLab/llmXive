# Quickstart: Investigating the Correlation Between Gut Microbiome Diversity and Cognitive Performance

## Prerequisites

- **Python**: 3.11 or higher.
- **Data Access**: You must have downloaded the UK Biobank microbiome and cognitive data files and placed them in `data/raw/`.
  - *Note*: No automated download is provided as the verified dataset list does not contain the UK Biobank raw files. **CI execution is not possible without manual data provision.**
- **Dependencies**: `requirements.txt` must be installed.

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-077-investigating-the-correlation-between-gu
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

## Data Preparation

Place the following files in `data/raw/`:
- `microbiome_counts.csv`: Columns `participant_id`, `OTU_001`, `OTU_002`, ...
- `cognitive_data.csv`: Columns `participant_id`, `fluid_intelligence_score`.
- `demographics.csv`: Columns `participant_id`, `age`, `sex`, `bmi`.
- `dietary_data.csv` (Optional): Raw dietary items for DQS calculation.

*Ensure all files use the same `participant_id` format.*

## Running the Pipeline

Execute the main analysis script:

```bash
python code/main.py
```

### Expected Output

Upon successful completion, the following artifacts will be generated in `data/processed/`:
- `cleaned_data.csv`: The analysis-ready dataset.
- `results_correlation.csv`: Spearman correlation results (Primary Path, Raw Shannon).
- `results_regression.csv`: Lasso regression results (Secondary Path, CLR Taxa).
- `plots/`:
  - `scatter_diversity_vs_intelligence.png`
  - `histogram_diversity_distribution.png`

## Verification

To verify the pipeline:

1.  **Check Data Integrity**:
    ```bash
    python -c "import pandas as pd; df = pd.read_csv('data/processed/cleaned_data.csv'); print(df.shape); print(df.isnull().sum())"
    ```
    Ensure `isnull().sum()` is 0 for all primary variables.

2.  **Run Unit Tests**:
    ```bash
    pytest tests/unit/ -v
    ```

3.  **Run Integration Tests**:
    ```bash
    pytest tests/integration/test_pipeline.py -v
    ```

## Troubleshooting

- **Error: "Missing raw data files"**: Ensure files are in `data/raw/` with correct names.
- **Error: "Zero variance in fluid intelligence"**: The dataset may lack variability; the script will skip the regression test and log a warning.
- **Error: "Memory Limit Exceeded"**: The pipeline enforces a hard-coded sample limit (N=50,000) to prevent OOM. If your data is larger, it will be truncated.
- **Error: "Spec Conflict Detected"**: The pipeline has detected that the input data or configuration contradicts the corrected methodology (e.g., attempting CLR on Shannon). This is a safety check.