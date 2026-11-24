# Quickstart: Predicting Antibiotic Resistance Evolution from Genomic Sequences

## Prerequisites
- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or a local Linux environment with sufficient RAM.

## Installation
1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-027-predicting-antibiotic-resistance-evoluti
 ```
2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate
 ```
3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Pipeline
The canonical entry point for the pipeline is `code/main.py`.

### 1. Full End-to-End Execution
This runs ingestion, contract validation, model training, statistical validation, visualization, and state hashing in sequence.
```bash
python code/main.py --stage full --n-isolates 1000 --bio_project PRJNA528852 --antibiotic ciprofloxacin
```

### 2. Running Individual Stages
If you need to rerun a specific part of the pipeline:

- **Ingestion**:
 ```bash
 python code/main.py --stage ingest --n-isolates 1000 --bio_project PRJNA528852
 ```
- **Contract Validation**:
 ```bash
 python code/main.py --stage contract
 ```
- **Model Training**:
 ```bash
 python code/main.py --stage train --antibiotic ciprofloxacin
 ```
- **Validation**:
 ```bash
 python code/main.py --stage validate --antibiotic ciprofloxacin --permutations 1000
 ```
- **Visualization**:
 ```bash
 python code/main.py --stage viz --antibiotic ciprofloxacin
 ```
- **Versioning**:
 ```bash
 python code/main.py --stage hash
 ```

## Verification
- **Contract Tests**: Run `pytest tests/contract/` to ensure data schemas match requirements.
- **Full Suite**: Run `pytest tests/` to verify unit and integration tests.
- **Artifacts**: Check `data/processed/`, `data/models/`, and `figures/` for output files.

## Troubleshooting
- **OOM Error**: Reduce `--n-isolates` to 500.
- **Contract Failure**: If `stage contract` fails, check `data/processed/feature_matrix.csv` against `contracts/feature_matrix.schema.yaml`.
- **NCBI Timeouts**: The ingestion stage may take time depending on network stability.