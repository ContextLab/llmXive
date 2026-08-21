# PROJ-546: Predicting Molecular Properties from Quantum Chemical Calculations

## Project Structure

This project implements a pipeline for predicting molecular properties using quantum chemical calculations.

### Directory Layout

```
projects/PROJ-546-predicting-molecular-properties-from-qua/
├── code/ # Source code and scripts
├── data/
│ ├── raw/ # Raw downloaded datasets
│ └── optimized_geometries/ # Optimized molecular geometries (XYZ files)
├── logs/ # Execution logs and verification outputs
├── reports/ # Final analysis reports and summaries
├── specs/
│ └── 546-predicting-molecular-properties/
│ └── contracts/ # Contract tests and specifications
└── tests/
 ├── unit/ # Unit tests
 ├── integration/ # Integration tests
 └── contract/ # Contract tests
```

## Setup

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 pip install -r code/requirements.txt
 ```
3. Create the project directory structure:
 ```bash
 python code/create_directories.py
 ```

## Usage

Refer to `quickstart.md` for the execution pipeline.

## Research Concerns

This project addresses the distinction between calculation and measurement by:
- Using experimental barrier data as ground truth (Zenodo dataset)
- Explicitly logging calculation parameters and approximations
- Validating physical constraints (HOMO < LUMO) without claiming absolute physical accuracy
- Reporting computational resource usage and limitations

Resource constraints are managed through:
- Semi-empirical methods (DFTB+) for full dataset processing
- High-level DFT (Psi4) only on stratified subsets
- Memory monitoring and OOM detection

Physical interpretability is supported by:
- Feature importance analysis
- Descriptor mapping to chemical properties
- Sensitivity analysis with noise injection
