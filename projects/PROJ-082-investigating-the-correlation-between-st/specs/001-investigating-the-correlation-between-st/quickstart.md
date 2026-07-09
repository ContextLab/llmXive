# Quickstart: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

## Prerequisites

- Python 3.11+
- Git
- (Optional) A text editor or Jupyter Notebook

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <repository-url>
    cd projects/PROJ-082-investigating-the-correlation-between-st
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Data Preparation

The pipeline requires a curated dataset of studies. Since no verified dataset contains the exact (r, n, tract) tuples, you must prepare a CSV file manually or via a separate extraction script.

1.  **Create the input file**:
    Create `data/raw/studies_extracted.csv` with the following columns:
    ```csv
    author,year,tract_name,metric,r,n,t_value,p_value
    Smith,2020,Arcuate Fasciculus,FA,0.45,120,,
    Jones,2021,Cingulum Bundle,FA,0.32,85,,
    ...
    ```
    *Note: At least 10 unique (Author, Year) pairs are required for the quantitative meta-analysis mode. If you have fewer, the system will automatically switch to Narrative Mode.*

2.  **Verify data integrity**:
    Ensure there are no missing `n` values if `r` is present.

## Running the Pipeline

1.  **Execute the main script**:
    ```bash
    python code/main.py --input data/raw/studies_extracted.csv --output data/derived/
    ```

2.  **Check outputs**:
    - `data/derived/meta_analysis_result.json`: Contains the statistical results.
    - `data/derived/forest_plot.png`: Forest plot of effect sizes.
    - `data/derived/funnel_plot.png`: Funnel plot for publication bias.
    - `data/derived/narrative_summary.txt`: (If N < 10) A text summary of findings.

## Testing

Run the unit tests to verify statistical logic:
```bash
pytest tests/unit/ -v
```

Run integration tests:
```bash
pytest tests/integration/ -v
```

## Troubleshooting

- **Error: "Insufficient studies for Egger's test"**: This is expected if $N < 10$. The system will skip the test and log a warning.
- **Error: "Model convergence failed"**: The system will fallback to a Fixed-Effects model and log a warning.
- **Memory Error**: Unlikely for this dataset size. If encountered, ensure no large files are loaded unnecessarily.
