# Quickstart: Predicting Molecular Properties from Quantum Chemical Calculations

## Prerequisites

- **Python**: 3.11 or higher.
- **System Packages**:
 - `git`, `wget`, `curl`.
 - **Conda** (Miniconda or Anaconda) installed and in PATH.
- **Environment**:
 - Linux (Ubuntu 22.04 recommended for CI compatibility).
 - Sufficient RAM and disk space.

## Installation

1. **Clone the Repository**:
 ```bash
 git clone
 cd PROJ-546-predicting-molecular-properties-from-qua
 ```

2. **Create & Setup Conda Environment**:
 This step installs DFTB+ and Psi4 in a single environment to ensure version consistency.
 ```bash
 conda create -n mol_prop python=3.11 -y
 conda activate mol_prop
 # Install DFTB+ and Psi4 (estimated time: <30 mins)
 conda install -c conda-forge dftb+ psi4 rdkit pandas scikit-learn -y
 ```

3. **Install Python Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Verify System Tools**:
 ```bash
 dftb+ --version
 psi4 --version
 ```

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

### Full Pipeline (Semi-Empirical + DFT Subset)

```bash
python code/main.py --full
```

This will:
1. Fetch the Zenodo dataset (ID from `idea.md`).
2. Optimize geometries (DFTB+).
3. Compute semi-empirical descriptors.
4. Calculate confounds (MW, functional groups).
5. Select a 50-sample subset.
6. Compute DFT descriptors (Psi4) on the same geometries.
7. Train models (5-fold CV), perform confound analysis, and generate reports.

### Sensitivity Analysis

```bash
python code/sensitivity.py
```

## Output Artifacts

After successful completion, the following files will be generated:

- `data/descriptors_semi.csv`: Semi-empirical descriptors.
- `data/descriptors_dft.csv`: DFT descriptors (subset).
- `reports/evaluation.json`: Model performance, t-test results (with metadata), and confound analysis.
- `reports/sensitivity.csv`: Feature importance stability.
- `logs/convergence_failures.log`: Failed molecules.

## Troubleshooting

- **Convergence Failures**: Check `logs/convergence_failures.log`. If many failures, consider adjusting DFTB+ parameters in `code/geometry_opt.py`.
- **OOM Errors**: Check `logs/oom_failures.log`. Reduce batch size in `code/utils.py`.
- **Installation Time**: If installation exceeds 30 minutes, check network speed or Conda channel configuration. The total runtime budget is allocated to allow for a comprehensive evaluation within a standard single-day window.
