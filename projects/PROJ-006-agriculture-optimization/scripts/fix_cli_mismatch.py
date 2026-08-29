"""
Utility script to fix CLI argument mismatches between run-book commands and actual script implementations.

This script updates the quickstart.md to use the correct CLI arguments that match the actual script implementations.

The run-book was using --stage and --use-synthetic flags which do not exist in the actual scripts.
This script updates the quickstart.md to use the correct flags: --dry-run, --no-synthetic, --log-level.
"""
import re
from pathlib import Path

def fix_quickstart():
    quickstart_path = Path("docs/quickstart.md")
    
    if not quickstart_path.exists():
        print("docs/quickstart.md not found. Creating with correct commands...")
        # Create a new quickstart.md with correct commands
        content = """# Quick Start Guide - PROJ-006 Agriculture Optimization

This guide walks you through setting up and running the climate-smart agriculture analysis pipeline.

## Prerequisites

- Python 3.9+
- pip package manager
- Git (for cloning)

## Installation

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd PROJ-006-agriculture-optimization
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (if using real data):
   ```bash
   export WB_LSMS_TOKEN="your_token_here"
   ```

## Running the Pipeline

The pipeline can be run in different modes:

### Full Pipeline (Default)

Run the entire pipeline from data ingestion to report generation:

```bash
python src/cli/run_pipeline.py
```

This will:
1. Check for real data in `data/raw/`
2. If missing and not in CI, generate synthetic data for testing
3. Process data and generate analysis artifacts
4. Run regression analysis
5. Generate final report

### Dry Run

Run the pipeline without generating outputs (for testing):

```bash
python src/cli/run_pipeline.py --dry-run
```

### No Synthetic Data

Force the pipeline to fail if real data is missing (useful in CI):

```bash
python src/cli/run_pipeline.py --no-synthetic
```

## Validating Artifacts

After running the pipeline, validate the generated artifacts:

```bash
# Validate the analysis dataset
python src/cli/validate.py data/processed/analysis_dataset.csv --schema-type dataset

# Validate the regression results
python src/cli/validate.py data/processed/regression_results.json --schema-type regression
```

## Expected Outputs

The pipeline generates the following artifacts:

- `data/processed/analysis_dataset.csv` - Cleaned and processed dataset
- `data/processed/regression_results.json` - Regression analysis results
- `data/processed/sensitivity_results.csv` - Sensitivity analysis results
- `reports/sensitivity_plot.png` - Sensitivity analysis visualization
- `reports/final_report.pdf` - Final research report

## Troubleshooting

### Missing Data

If you see "No real data found" errors, the pipeline will automatically generate synthetic data for testing in non-CI environments. To force failure instead:

```bash
python src/cli/run_pipeline.py --no-synthetic
```

### Schema Validation Errors

If validation fails, check that your data files match the expected schema in `contracts/`.

## Next Steps

- Review the full documentation in `docs/`
- Run the test suite: `pytest`
- Check the research methodology in `research.md`
"""
        quickstart_path.parent.mkdir(parents=True, exist_ok=True)
        quickstart_path.write_text(content)
        print("Created docs/quickstart.md with correct commands")
        return

    content = quickstart_path.read_text()
    
    # Fix incorrect commands
    # Replace --stage ingest with correct usage
    content = re.sub(
        r'python src/cli/run_pipeline\.py --stage ingest',
        'python src/cli/run_pipeline.py',
        content
    )
    
    # Replace --stage ingest --use-synthetic with correct usage
    content = re.sub(
        r'python src/cli/run_pipeline\.py --stage ingest --use-synthetic',
        'python src/cli/run_pipeline.py',
        content
    )
    
    # Replace --stage full with correct usage
    content = re.sub(
        r'python src/cli/run_pipeline\.py --stage full',
        'python src/cli/run_pipeline.py',
        content
    )
    
    # Fix validate.py command
    content = re.sub(
        r'python src/cli/validate\.py --input ([^\s]+) --contract ([^\s]+)',
        r'python src/cli/validate.py \1 --schema-type dataset',
        content
    )
    
    quickstart_path.write_text(content)
    print("Fixed CLI argument mismatches in docs/quickstart.md")

if __name__ == "__main__":
    fix_quickstart()
