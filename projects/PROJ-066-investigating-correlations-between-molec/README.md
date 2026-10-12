# PROJ-066: Investigating Correlations Between Molecular Descriptors and Drug-Likeness Scores

## Project Overview

This project investigates the extent to which fundamental 2D molecular descriptors
(TPSA, logP, molecular weight, rotatable bonds, H-bond donors/acceptors, ring count)
can predict experimentally measured drug-likeness outcomes — oral bioavailability,
apparent permeability (Papp), and in-vivo clearance — across diverse chemical scaffolds.

The pipeline:

1. **Data acquisition (US1)**: Downloads the ChEMBL 33 SQLite database from
 `ftp://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/`, validates its
 SHA-256 checksum, and extracts it to `data/raw/chembl_33.db`.
2. **Preprocessing (US1)**: Sanitizes SMILES with RDKit (salt removal, valence
 correction, exclusion of invalid structures), filters for target endpoints
 (bioavailability, permeability, clearance), deduplicates SMILES (most recent
 assay date, averaging on date ties), performs stratified sampling capped at
 15,000 molecules, and computes 2D descriptors.
3. **Modeling (US2)**: Trains Linear Regression and memory-conscious Random Forest
 models on a stratified 80/20 train/test split (fixed seed 42), and generates a
 ranked feature-importance report.
4. **Evaluation (US3)**: Computes RMSE and Pearson r on the hold-out set, compares
 against a mean-predictor baseline, and produces predicted-vs-experimental scatter
 plots and feature-importance bar charts.

## Resource Constraints

The pipeline is designed for a 2-core CPU runner with ~7 GB RAM and a 6-hour time
limit. Dataset size is capped at 15,000 molecules (`MAX_MOLECULES` in
`code/utils/config.py`); memory and time usage are monitored throughout
(`code/utils/logging.py` resource hooks) and enforced by the final metrics gate.

## Quickstart Instructions

### 1. Set up the environment

```bash
cd projects/PROJ-066-investigating-correlations-between-molec/code
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Verify RDKit:

```bash
python -c "from rdkit import Chem; print('RDKit OK')"
```

### 2. Download ChEMBL 33 (T009)

```bash
python data/download.py
```

Output: `data/raw/chembl_33.db` (checksum-validated SQLite database).
The script fails loudly if the FTP server is unreachable or the checksum mismatches.

### 3. Preprocess (T010–T015)

```bash
python data/preprocess.py
```

Output: `data/processed/molecules_processed.csv` — SMILES, experimental target
values, and calculated 2D descriptors, validated row-by-row against
`code/contracts/molecule.schema.yaml`.

### 4. Train models (T017–T020)

```bash
python models/train.py
```

Output: `data/processed/model_lr.pkl`, `data/processed/model_rf.pkl`, and
`data/processed/feature_importance.json`.

### 5. Evaluate and visualize (T022–T026)

```bash
python models/evaluate.py
```

Output: `data/processed/metrics_summary.json`, scatter and feature-importance
plots, and the baseline RMSE in `data/processed/baseline_rmse.json`.

### 6. Run tests

```bash
python -m pytest -v
```

## Directory Structure

```text
projects/PROJ-066-investigating-correlations-between-molec/
├── code/
│ ├── data/
│ │ ├── download.py # ChEMBL FTP download + checksum validation
│ │ └── preprocess.py # Sanitize, filter, dedup, sample, descriptors
│ ├── models/
│ │ ├── train.py # LR + RF training, feature importance
│ │ └── evaluate.py # Metrics, baseline comparison, plots
│ ├── utils/
│ │ ├── config.py # Constants: RANDOM_SEED=42, MAX_MOLECULES=15000, limits
│ │ ├── logging.py # Structured logging + resource monitoring
│ │ └── update_state.py # Artifact hash state updates
│ ├── contracts/ # JSON/YAML schemas for validation
│ └── requirements.txt
├── data/
│ ├── raw/ # Downloaded ChEMBL SQLite database
│ └── processed/ # Cleaned CSVs, models, plots, metrics
├── tests/ # Unit and integration tests
└── state/ # Project state tracking and artifact hashes
```

## Success Criteria

- **SC-001**: Pearson r between predicted and experimental values; success if
 r >= 0.6, otherwise the measured r is reported as evidence of weak correlation.
- **SC-002**: Model RMSE compared against a mean-predictor baseline RMSE.
- **SC-003**: logP and TPSA both rank within the top 3 features by Random Forest
 importance.
- **SC-004/005**: Pipeline completes within 6 hours and 7 GB peak RAM.

## Dependencies

- Python 3.10+
- RDKit
- scikit-learn
- pandas
- numpy
- matplotlib
- PyYAML
- psutil

## Troubleshooting

- **FTP unreachable**: `download.py` raises a clear error; check connectivity —
 no synthetic fallback data is ever generated.
- **RDKit sanitization failures**: invalid-valence molecules are logged and
 excluded automatically.
- **Insufficient data**: if the filtered sample drops below 100 molecules,
 preprocessing halts with `DataInsufficiencyError`.
- **Memory errors**: reduce the sample size via `MAX_MOLECULES` in
 `code/utils/config.py`.