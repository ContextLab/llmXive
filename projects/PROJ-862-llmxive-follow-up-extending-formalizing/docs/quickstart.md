# llmXive Quickstart Guide

## Prerequisites

- Python 3.9+
- pip
- 7GB+ RAM (CPU-only execution)

## Installation

1. Clone the repository.
2. Install dependencies:

```bash
cd code
pip install -r requirements.txt
```

## Configuration

The pipeline uses `config.py` for defaults. You can override settings via a JSON config file or CLI arguments.

## Execution

Run the full pipeline:

```bash
python main.py
```

Run a dry-run to verify paths and logic without heavy computation:

```bash
python main.py --dry-run
```

## Output Artifacts

After successful execution, the following files will be generated in `data/processed/`:

- `baseline_vectors.csv`: Extracted latent vectors.
- `validity_log.csv`: Pass-rates for each sigma level.
- `statistical_results.json`: Final statistical analysis (if conclusive).
- `inconclusive_report.md`: Generated if no valid sigma is found (T051).
- `memory_profile.json`: Memory usage logs.

## Troubleshooting

- **Memory Limit**: If the process exceeds 7GB RAM, it will halt with `MemoryLimitExceeded`.
- **Data Fetch**: Ensure internet connectivity for dataset download. The script will fail loudly if the dataset is missing or checksums mismatch.
- **Inconclusive**: If `inconclusive_report.md` is generated, the experiment found no valid noise range. Check the report for recommendations.