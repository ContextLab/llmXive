# Quickstart Guide

## Prerequisites

- Python 3.11 or higher
- pip package manager
- 7 GB+ available RAM (recommended)
- Internet connection (for dataset download)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-258-the-effect-of-simulated-social-rejection

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/ingest.py
python code/preprocess.py
python code/analysis.py
python code/report.py
```

Or run all stages in one command:

```bash
bash run_pipeline.sh
```

## Expected Outputs

After successful execution, you will find:

- `data/raw/checksums.json`: SHA-256 hashes of raw data
- `data/interim/preprocessed_data.csv`: Cleaned and normalized data
- `data/processed/final_results.json`: Statistical results
- `reports/final_report.md`: Human-readable analysis report

## Troubleshooting

### Memory Error
If you encounter a memory error, reduce the dataset size or increase available RAM. The pipeline will automatically halt if memory usage exceeds 7 GB.

### Data Not Found
If the pipeline halts with "Data Unavailable", ensure that:
- The dataset URLs in `config.py` are correct.
- You have internet access.
- The datasets contain the required variables (Condition, Reaction Time, Mood).

### Design Type Mismatch
If the design type is unexpected, check the `log_design_switch` output in the logs to understand the decision path.

## Next Steps

- Review the `docs/design.md` for detailed design decisions.
- Consult `docs/api.md` for the full API reference.
- Run `pytest tests/ -v` to verify the installation.
