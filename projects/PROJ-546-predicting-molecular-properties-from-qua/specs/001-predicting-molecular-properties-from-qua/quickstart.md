# Quickstart: Predicting Molecular Properties from Quantum Chemical Calculations

This guide walks you through setting up and running the molecular property prediction pipeline.
The project uses experimental barrier height data from Zenodo to train and evaluate machine learning models
based on quantum chemical descriptors.

## Prerequisites

- Python 3.11+
- pip
- DFTB+ (for semi-empirical calculations)
- Psi4 (for high-level DFT calculations)

## 1. Clone and Setup Environment

```bash
cd projects/PROJ-546-predicting-molecular-properties-from-qua
python -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
```

## 2. Dataset Information (FR-001 Compliance)

The primary dataset used in this project is the **Experimental Barrier Dataset**.
Per **FR-001**, this dataset is fetched from a verified Zenodo repository.

| Field | Value |
|:--- |:--- |
| **Zenodo ID** | `1048765` |
| **Version** | `1.0.0` |
| **Description** | Experimental barrier heights for organic reactions |
| **Checksum (SHA-256)** | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

> **Note:** The checksum above is the SHA-256 hash of the raw dataset file `barrier_dataset.csv` after download and extraction. This ensures data integrity as per Constitution Principle III.

## 3. Run the Pipeline

The pipeline is orchestrated via the `code/main.py` CLI.

### Full Execution
```bash
python code/main.py run
```

This command executes the following steps in order:
1. **Fetch Data**: Downloads and verifies the Zenodo dataset (`data/raw/barrier_dataset.csv`).
2. **Confounds Analysis**: Calculates molecular weight and atom counts (`data/confounds.csv`).
3. **Descriptor Generation**: Runs DFTB+ geometry optimization and descriptor extraction (`data/descriptors_semi.csv`).
4. **Subset Selection & DFT**: Selects a stratified subset and runs Psi4 (`data/descriptors_dft.csv`).
5. **Model Training**: Trains Random Forest models (`state/models/`).
6. **Evaluation**: Computes MAE and performs paired t-tests (`reports/evaluation.json`).
7. **Sensitivity Analysis**: Performs feature importance and noise injection analysis (`reports/sensitivity.csv`).

### Individual Steps
You can also run specific phases:
```bash
# Fetch only
python code/main.py fetch

# Generate semi-empirical descriptors
python code/main.py optimize

# Train and evaluate models
python code/main.py train
```

## 4. Output Artifacts

Upon successful completion, the following artifacts will be generated:

- `data/raw/barrier_dataset.csv`: The raw experimental data.
- `data/confounds.csv`: Molecular weight and atom count statistics.
- `data/descriptors_semi.csv`: HOMO, LUMO, and Mayer bond orders from DFTB+.
- `data/descriptors_dft.csv`: High-level DFT descriptors for the subset.
- `data/optimized_geometries/`: Optimized XYZ structures.
- `reports/evaluation.json`: Model performance metrics (MAE, p-values).
- `reports/sensitivity.csv`: Feature importance and stability analysis.
- `data/checksums.txt`: SHA-256 hashes of all artifacts.

## 5. Troubleshooting

- **Convergence Failures**: If DFTB+ fails to converge, logs are written to `logs/convergence_failures.log`.
- **Resource Limits**: Peak memory usage is logged in `logs/dft_execution.log`. If the 7GB limit is exceeded, the process will halt.
- **Missing Files**: Ensure `data/raw/barrier_dataset.csv` exists before running descriptor generation.

## 6. Verification

To verify the integrity of the dataset:
```bash
python code/generate_checksums.py
```
This will output a `data/checksums.txt` file which can be compared against the expected SHA-256 hash listed in Section 2.