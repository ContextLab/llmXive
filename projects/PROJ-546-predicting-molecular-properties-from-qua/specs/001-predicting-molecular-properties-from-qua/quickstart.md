# Quickstart: Predicting Molecular Properties from Quantum Chemical Calculations

## Prerequisites

- **Python**: 3.11+
- **DFTB+**: Installed and in PATH.
- **Psi4**: Installed and in PATH.
- **RDKit**: Via conda or pip.
- **Git**: For repository access.

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-546-predicting-molecular-properties-from-qua
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify DFTB+ and Psi4**:
   ```bash
   dftb+ --version
   psi4 --version
   ```

## Running the Pipeline

The pipeline is executed sequentially via the main entry point:

```bash
python code/main.py
```

This script orchestrates:
1. Data fetching and checksum verification.
2. Geometry optimization (DFTB+).
3. Descriptor calculation (DFTB+ and Psi4 subset).
4. Confounds analysis.
5. Model training and evaluation.
6. Sensitivity analysis.

## Output

- **Descriptors**: `data/descriptors_semi.csv`, `data/descriptors_dft.csv`.
- **Logs**: `logs/convergence_failures.log`, `logs/oom_failures.log`.
- **Reports**: `reports/evaluation.json`, `reports/sensitivity.csv`.
- **Confounds**: `data/confounds.csv`.

## Troubleshooting

- **Convergence Failure**: Check `logs/convergence_failures.log`. If >10% fail, check initial geometry generation.
- **OOM**: Reduce batch size in `code/config.py` or check memory limits.
- **Missing DFTB+/Psi4**: Ensure binaries are in PATH.
