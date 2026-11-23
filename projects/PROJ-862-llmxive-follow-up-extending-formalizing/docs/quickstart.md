# llmXive Quickstart Guide

## Prerequisites

- Python 3.9+
- 7GB+ RAM available
- CPU-only execution (no GPU required)

## Installation

1. Create virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Execution

Run the full pipeline:
```bash
python code/main.py --config config.json
```

Run in pilot mode (feasibility check only):
```bash
python code/main.py --config config.json --pilot
```

## Output Files

The pipeline produces the following artifacts in `data/processed/`:
- `pairing_config.json`: Question pairings by task type
- `baseline_vectors.csv`: Baseline latent vectors
- `validity_log.csv`: Validity checks per sigma level
- `perturbed_vectors.csv`: Perturbed latent vectors
- `statistical_results.json`: Final statistical analysis
- `memory_profile.json`: Memory usage profile

## Troubleshooting

- If you encounter `ModuleNotFoundError`, ensure all dependencies are installed: `pip install -r code/requirements.txt`
- If memory errors occur, reduce the dataset size or sigma step size in `config.json`
- Check `logs/pipeline.log` for detailed error messages