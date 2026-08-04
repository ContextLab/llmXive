# Quickstart: Predicting Molecular Packing Efficiency in Crystals

## Prerequisites

- Python 3.11+
- `pip`
- Access to the internet (for downloading COD data and packages)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd PROJ-511-predicting-molecular-packing-efficiency
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

The pipeline is executed via the `main.py` script, which orchestrates all phases.

```bash
python src/main.py
```

This command performs the following steps automatically:
1. **Download**: Fetches COD CIF files (filtered for organic molecules ≤50 atoms).
2. **Process**: Generates SMILES, calculates CAPE, and creates `data/dataset.csv`.
3. **Train**: Trains the 2-layer MLP model.
4. **Evaluate**: Runs metrics and permutation tests.
5. **Report**: Generates `results/report.html`.

### Manual Steps (Optional)

If you wish to run steps individually:

1. **Download & Parse**:
 ```bash
 python src/data/download_cif.py
 python src/data/parse_cif.py
 ```
2. **Train**:
 ```bash
 python src/training/train.py
 ```
3. **Evaluate**:
 ```bash
 python src/training/evaluate.py
 ```
4. **Sensitivity**:
 ```bash
 python src/training/sensitivity.py
 ```
5. **Report**:
 ```bash
 python src/utils/report.py
 ```

## Output Files

- `data/dataset.csv`: The processed dataset.
- `models/mlp.pt`: Trained model weights.
- `results/validation_report.json`: Statistical metrics.
- `results/sensitivity_report.csv`: Threshold analysis.
- `results/report.html`: Final HTML report.

## Troubleshooting

- **Missing COD Data**: Ensure you have internet access. The script downloads directly from ` via FTP.
- **RAM Issues**: If running out of memory, reduce the number of CIFs processed by adjusting the `MAX_RECORDS` constant in `src/config.py`.
- **SMILES Generation Failures**: Check `data/parsing_errors.log` for records that failed RDKit parsing.
