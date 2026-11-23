# Usage Examples

This document provides concrete examples of how to use the Gut Microbiome and Sleep Quality research pipeline.

## Quick Start

### 1. Setup Environment

Ensure you have Python 3.11+ and install dependencies:

```bash
git clone <repository-url>
cd <project-directory>
pip install -r requirements.txt
```

### 2. Configure Data Source

Set the `DATA_URL` environment variable to point to the verified dataset:

```bash
export DATA_URL=""
export RANDOM_SEED=42
export LOG_LEVEL=INFO
```

### 3. Run the Pipeline

Execute the full pipeline from start to finish:

```bash
# Run Ingestion
python code/src/ingestion.py

# Run Diversity Analysis
python code/src/diversity.py

# Run Correlation Analysis
python code/src/correlation.py

# Run Visualization
python code/src/viz.py

# Generate Final Report
python code/src/report_final.py
```

## Module-Specific Examples

### Ingestion Module

To verify the data source without downloading the full dataset:

```bash
python code/src/ingestion.py --verify-only
```

To run only the filtering logic (requires pre-downloaded data):

```bash
python code/src/ingestion.py --stage filter
```

### Diversity Analysis

To calculate alpha-diversity without rarefaction (for testing):

```bash
python code/src/diversity.py --no-rarefaction
```

### Correlation Analysis

To export only the significant correlations:

```bash
python code/src/correlation.py --significant-only
```

### Visualization

To generate only scatterplots:

```bash
python code/src/viz.py --type scatter
```

To generate only boxplots:

```bash
python code/src/viz.py --type box
```

## Running Tests

Run the unit test suite:

```bash
pytest code/tests/unit/ -v
```

Run a specific test file:

```bash
pytest code/tests/unit/test_ingestion.py -v
```

Run the reproducibility integration test:

```bash
pytest code/tests/integration/test_reproducibility.py -v
```

## Troubleshooting

### Data Source Error

If you see `FileNotFoundError: Verified data source not found`, ensure:
1. The `DATA_URL` environment variable is set correctly.
2. The URL is accessible from your network.
3. The dataset contains the required columns.

### Memory Error

If the pipeline runs out of memory, consider:
1. Increasing the `RANDOM_SEED` to process a smaller sample (if applicable).
2. Using chunked processing (if implemented in future versions).

### Missing Output Files

If expected output files are missing, check the logs in `code/src/logging_config.py` output for errors during specific stages.

## Advanced Usage

### Custom Configuration

You can override default configuration values by creating a `config.yaml` file in the project root:

```yaml
DATA_URL: " Name or service not known)"))]"
RANDOM_SEED: 123
LOG_LEVEL: DEBUG
```

The pipeline will automatically load this file if present.

### Programmatic Usage

You can also import and run the pipeline modules programmatically in a Python script:

```python
from src.ingestion import run_ingestion_pipeline
from src.diversity import run_diversity_analysis
from src.correlation import run_correlation_analysis
from src.viz import run_visualization
from src.report_final import run_final_report

# Run the pipeline
run_ingestion_pipeline()
run_diversity_analysis()
run_correlation_analysis()
run_visualization()
run_final_report()
```