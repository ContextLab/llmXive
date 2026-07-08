# PROJ-431: Predicting Molecular Complexity with Information Theory

This project investigates the relationship between information-theoretic measures of molecular graph structure (specifically Shannon entropy of atom and bond degree distributions) and physicochemical properties (logS, logP).

## Project Structure

```
.
├── code/ # Source code for entropy calculation, modeling, and visualization
│ ├── __init__.py
│ ├── cli.py
│ ├── entropy.py
│ ├── model.py
│ ├── utils.py
│ ├── viz.py
│ └── setup_directories.py
├── data/
│ ├── raw/ # Raw input datasets (e.g., SMILES, logS, logP)
│ └── processed/ # Intermediate and final processed data
├── results/
│ ├── models/ # Saved model artifacts
│ ├── reports/ # JSON/Markdown analysis reports
│ └── plots/ # Generated visualization images
├── scripts/ # Utility scripts
│ └── init_structure.sh
├── tests/ # Unit and integration tests
│ └── __init__.py
├── requirements.txt # Python dependencies
└── README.md
```

## Quick Start

1. **Initialize Structure**:
 ```bash
 python code/setup_directories.py
 # OR
 bash scripts/init_structure.sh
 ```

2. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

3. **Run Pipeline**:
 ```bash
 python code/cli.py --help
 ```

## License

MIT
