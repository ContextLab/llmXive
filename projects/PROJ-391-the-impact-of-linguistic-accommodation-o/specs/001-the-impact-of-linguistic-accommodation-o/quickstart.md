# Quickstart: Linguistic Accommodation and Speaker Emotional Intensity

## Prerequisites

- Python 3.11+
- `pip` or `poetry`
- Access to internet (for downloading datasets)

## Installation

1. **Clone the repository** (if not already done).
2. **Navigate to the project directory**:
   ```bash
   cd projects/PROJ-391-the-impact-of-linguistic-accommodation-o
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Data Setup

The project automatically downloads the DailyDialog dataset on first run. To manually verify:
1. Ensure `data/raw/` exists.
2. Run the ingestion script:
   ```bash
   python code/main.py --step ingest
   ```
   This will fetch the dataset from the verified HuggingFace URL and save it to `data/raw/`.

## Running the Pipeline

### Full Analysis
To run the entire pipeline (Ingest -> Process -> Validate -> Analyze -> Visualize):
```bash
python code/main.py --full
```
This will:
1. Download and preprocess DailyDialog.
2. Compute accommodation metrics (Lexical, Syntactic, Bigram).
3. Map emotion labels to intensity (with validation check).
4. Run statistical tests (Spearman correlation, Ordinal Logistic Regression, bootstrap).
5. Generate plots and save reports to `data/artifacts/`.

### Individual Steps
- **Ingest Only**:
  ```bash
  python code/main.py --step ingest
  ```
- **Process Only** (requires raw data):
  ```bash
  python code/main.py --step process
  ```
- **Validate Only** (requires processed data):
  ```bash
  python code/main.py --step validate
  ```
- **Analyze Only** (requires processed data):
  ```bash
  python code/main.py --step analyze
  ```

## Expected Outputs

After a successful run, check the `data/artifacts/` directory for:
- `correlation_report.json`: Statistical results (Spearman coefficients, p-values, CIs).
- `regression_summary.json`: Ordinal Logistic Regression results (Odds Ratios, McFadden's Pseudo-R2).
- `scatter_lexical_intensity.png`: Scatter plot of lexical overlap vs. intensity.
- `scatter_syntactic_intensity.png`: Scatter plot of syntactic similarity vs. intensity.
- `distribution_report.csv`: Frequency of mapped emotional intensity scores.
- `validation_report.json`: Krippendorff's Alpha and mapping validation results.

## Troubleshooting

- **Missing Data**: If the download fails, verify internet connectivity and check the HuggingFace URL validity.
- **Memory Errors**: The pipeline is optimized for 7GB RAM. If errors occur, reduce the `--sample-size` flag (if implemented) or increase swap space.
- **Missing Emotions**: If a large portion of data lacks emotion labels, check the `distribution_report.csv` for exclusion rates.