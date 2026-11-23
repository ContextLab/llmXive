# Quickstart Guide

This guide provides a step-by-step walkthrough to run the PROJ-512 pipeline from scratch.

## Prerequisites

- Python 3.11+
- pip package manager
- A UNIX-like environment (Linux/macOS) or WSL2 on Windows

## Installation

1. **Clone the repository** (if applicable).
2. **Navigate to the project root**:
 ```bash
 cd projects/PROJ-512-predicting-molecular-permeability-of-pol
 ```
3. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
4. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

The entire pipeline can be executed via the `main.py` script located in the `code/` directory.

```bash
cd code
python main.py
```

### What Happens?

1. **Environment Check**: Verifies CPU-only PyTorch availability.
2. **Data Ingestion**: Attempts to fetch NIST data. If unavailable, generates simulation data.
3. **Preprocessing**: Parses SMILES, extracts 2D features, and performs scaffold splitting.
4. **Training**: Trains the GNN and baselines.
5. **Evaluation**: Computes metrics and runs statistical tests.
6. **Reporting**: Generates the final JSON report.

## Output Artifacts

Upon successful completion, the following files will be generated:

- `code/data/raw/nist_polymer_raw.csv` (or `simulation_data.csv`)
- `code/data/processed/polymers.h5`
- `code/data/processed/scaffold_split_indices.json`
- `code/evaluation/results/metrics.json`
- `code/evaluation/results/sensitivity_sweep.json`
- `code/evaluation/results/final_report.json`

## Troubleshooting

- **Import Errors**: Ensure all dependencies in `requirements.txt` are installed.
- **Data Fetch Failures**: The pipeline will automatically fall back to simulation data if NIST is unreachable. Check logs for details.
- **Memory Issues**: The pipeline is optimized for CPU. If running out of memory, reduce the batch size in `code/models/trainer.py`.

## Next Steps

- Review the `docs/data_dictionary.md` to understand the features used.
- Examine `code/evaluation/results/final_report.json` for model performance insights.
- Explore the `tests/` directory to understand the testing strategy.