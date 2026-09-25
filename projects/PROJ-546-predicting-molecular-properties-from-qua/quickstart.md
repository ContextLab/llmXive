# Quickstart Guide

This guide outlines how to run the full pipeline for predicting molecular properties from quantum chemical calculations.

## Prerequisites

- Python 3.11+
- DFTB+ installed and in PATH
- Psi4 installed and in PATH
- Required Python packages (install via `pip install -r code/requirements.txt`)

## Installation

1. Clone the repository.
2. Install dependencies:
 ```bash
 cd projects/PROJ-546-predicting-molecular-properties-from-qua
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

### Full Pipeline Execution

To run the entire pipeline from data fetching to final reporting:

```bash
python code/main.py run
```

This executes the following steps sequentially:
1. **Fetch**: Download and normalize data (T004b, T004c).
2. **Confounds**: Analyze confounds (T011).
3. **Optimize**: Geometry optimization and semi-empirical descriptors (T013).
4. **DFT**: DFT calculations on subset (T020).
5. **Train**: Train models (T021).
6. **Evaluate**: Evaluate models (T022).
7. **Sensitivity**: Sensitivity analysis (T030b).
8. **Checksums**: Generate checksums (T034).
9. **Resources**: Validate resource constraints (T033b).
10. **Summary**: Generate summary report (T035).

### Individual Stage Execution

You can also run specific stages independently:

- **Fetch Data**:
 ```bash
 python code/main.py fetch
 ```
- **Confounds Analysis**:
 ```bash
 python code/main.py confounds
 ```
- **Optimization & Semi-Empirical Descriptors**:
 ```bash
 python code/main.py optimize
 ```
- **DFT Calculations**:
 ```bash
 python code/main.py dft
 ```
- **Train Models**:
 ```bash
 python code/main.py train
 ```
- **Evaluate Models**:
 ```bash
 python code/main.py evaluate
 ```
- **Sensitivity Analysis**:
 ```bash
 python code/main.py sensitivity
 ```
- **Generate Checksums**:
 ```bash
 python code/main.py checksums
 ```
- **Validate Resources**:
 ```bash
 python code/main.py resources
 ```
- **Generate Summary Report**:
 ```bash
 python code/main.py summary
 ```

## Output Artifacts

Upon successful completion, the following artifacts will be generated generated:

- `data/raw/barrier_dataset.csv`: Normalized raw dataset.
- `data/confounds.csv`: Molecular properties and functional groups.
- `data/descriptors_semi.csv`: Semi-empirical descriptors (HOMO, LUMO, Mayer).
- `data/descriptors_dft.csv`: DFT descriptors (subset).
- `data/optimized_geometries/`: XYZ files for optimized geometries.
- `state/`: Model artifacts and split indices.
- `reports/`: Evaluation reports, sensitivity reports, and summary.
- `logs/`: Execution logs and validation reports.

## Troubleshooting

- **Convergence Failures**: Check `logs/convergence_failures.log` for details.
- **Missing Data**: Ensure Zenodo ID is correct in `code/config.py` and internet access is available.
- **Resource Limits**: Check `logs/dft_execution.log` for memory and time usage.
