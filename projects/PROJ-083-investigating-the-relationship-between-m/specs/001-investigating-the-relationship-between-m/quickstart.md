# Quickstart: Investigating the Relationship Between Molecular Topology and Reaction Selectivity

## Prerequisites

- Python 3.10+
- `pip` or `conda`
- Access to GitHub Actions (for CI) or local machine with 7GB+ RAM.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-083-investigating-the-relationship-between-m
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` contains pinned versions of `rdkit`, `scikit-learn`, `pandas`, etc.*

## Running the Pipeline

### 1. Data Ingestion
Download and filter the dataset:
```bash
python code/ingest.py
```
- Output: `data/processed/eas_reactions.csv`
- Logs: `logs/ingest.log`

### 2. Descriptor Calculation
Compute topological indices:
```bash
python code/descriptors.py
```
- Output: `data/processed/descriptors.csv`
- Logs: `logs/descriptors.log`

### 3. Target Enumeration
Derive theoretical regioisomer count:
```bash
python code/target_enumeration.py
```
- Output: `data/processed/descriptors.csv` (updated with target)
- Logs: `logs/enumeration.log`

### 4. Modeling
Run regression and cross-validation:
```bash
python code/modeling.py
```
- Output: `data/processed/model_results.json`
- Logs: `logs/modeling.log`

### 5. Full Pipeline (Optional)
Run the entire workflow:
```bash
python code/run_pipeline.py
```

## Verification

To verify the descriptor calculations:
```bash
pytest tests/unit/test_descriptors.py -v
```
This checks benzene, toluene, and nitrobenzene against expected values.

## Troubleshooting

- **Memory Error**: Ensure the dataset is filtered before processing. If using a local machine, check RAM usage.
- **SMILES Error**: Check `logs/ingest.log` for malformed entries.
- **No EAS Reactions**: If the filtered dataset is empty, check the EAS pattern matching logic in `ingest.py`.
- **Enumeration Failure**: If many records are excluded during enumeration, check the `sanitize` step in `target_enumeration.py` for overly strict filtering.
