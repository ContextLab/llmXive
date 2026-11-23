# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip (package manager)

## Installation
1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Data Generation
To generate internal datasets (for testing or when external data is unavailable):
```bash
python code/run_ed_generator.py --internal-only --system-size 10
```

## Running the Pipeline
1. **Compute Entanglement**:
 ```bash
 python code/run_t015_entanglement.py
 ```
2. **Compute Complexity**:
 (Handled within the metrics pipeline)
3. **Visualization**:
 Output figures are saved to the `figures/` directory.

## Configuration
Edit `code/config.py` to adjust random seeds, system sizes, and other parameters.
