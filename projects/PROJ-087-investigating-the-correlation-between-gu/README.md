# Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

A scientific research pipeline to analyze the relationship between gut microbiome alpha-diversity indices and sleep quality metrics.

## Project Structure

```
.
├── code/ # Source code
│ ├── src/ # Main application modules
│ │ ├── config.py
│ │ ├── ingestion.py
│ │ ├── diversity.py
│ │ ├── correlation.py
│ │ ├── viz.py
│ │ ├── report.py
│ │ ├── report_final.py
│ │ ├── models/
│ │ │ └── schemas.py
│ │ └── utils/
│ │ └── hashing.py
│ ├── tests/
│ │ └── unit/
│ └──...
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Cleaned data and results
│ └── plots/ # Generated visualizations
└── docs/ # Documentation
```

## Data Source

This project utilizes the verified dataset described in `plan.md` under the "Verified datasets" section. The data source must be programmatically accessible via the `DATA_URL` environment variable.

**Verification**: Before running the pipeline, ensure the data source exists by running:
```bash
export DATA_URL="your_verified_url_here"
python code/src/ingestion.py --verify-only
```

The pipeline will fail loudly with a clear error if the data source is missing or the schema is invalid. **No synthetic data is generated or used.**

## Usage Examples

### Prerequisites

1. Python 3.11+
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Set environment variables:
 ```bash
 export DATA_URL=""
 export RANDOM_SEED=42
 export LOG_LEVEL=INFO
 ```

### Running the Full Pipeline

Execute the entire research pipeline from ingestion to final report:

```bash
# Step 1: Ingestion (Download, Filter, Merge)
python code/src/ingestion.py

# Step 2: Diversity Analysis (Rarefaction, Alpha-diversity)
python code/src/diversity.py

# Step 3: Correlation Analysis (Spearman, FDR)
python code/src/correlation.py

# Step 4: Visualization (Scatterplots, Boxplots)
python code/src/viz.py

# Step 5: Report Generation
python code/src/report_final.py
```

Alternatively, run the `main` entry points if available in the respective modules, or use the unified runner if provided in `code/main.py`.

### Running Individual Modules

**Ingestion**:
```bash
python code/src/ingestion.py
# Output: data/processed/cleaned_microbiome_sleep.csv
# Output: data/processed/ingestion_report.json
```

**Diversity**:
```bash
python code/src/diversity.py
# Input: data/processed/cleaned_microbiome_sleep.csv
# Output: data/processed/alpha_diversity_metrics.csv
```

**Correlation**:
```bash
python code/src/correlation.py
# Input: data/processed/alpha_diversity_metrics.csv
# Output: data/processed/correlation_results.csv
```

**Visualization**:
```bash
python code/src/viz.py
# Input: data/processed/correlation_results.csv
# Output: data/processed/plots/*.png
```

**Final Report**:
```bash
python code/src/report_final.py
# Input: All processed data and plots
# Output: data/processed/final_report.html (or.pdf)
```

### Running Tests

```bash
pytest code/tests/unit/ -v
```

### Reproducibility Check

To verify pipeline reproducibility (SC-005), run the pipeline twice and compare SHA-256 hashes:

```bash
python code/tests/integration/test_reproducibility.py
```

## Configuration

Configure the pipeline via environment variables or a `config.yaml` file:

- `DATA_URL`: URL to the verified dataset.
- `RANDOM_SEED`: Integer seed for reproducibility (default: 42).
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR).

## Output Artifacts

The pipeline generates the following artifacts in `data/processed/`:

- `cleaned_microbiome_sleep.csv`: Filtered and merged dataset.
- `ingestion_report.json`: Exclusion statistics and counts.
- `alpha_diversity_metrics.csv`: Calculated diversity indices.
- `correlation_results.csv`: Statistical correlation results with FDR correction.
- `plots/`: Directory containing scatterplots and boxplots.
- `final_report.html`: Comprehensive HTML report of findings.

## License

This project is for research purposes.
