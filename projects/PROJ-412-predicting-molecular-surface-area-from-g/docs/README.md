# llmXive: Molecular Surface Area Prediction

This project implements an automated pipeline for predicting molecular solvent-accessible
surface area (SASA) using Graph Convolutional Networks (GCNs) and baseline geometric models.

## Functional Requirements Traceability

- **FR-001**: Data Ingestion from ZINC15 (see `code/data/ingest.py`)
- **FR-002**: 2D/3D Feature Extraction (see `code/data/preprocess.py`)
- **FR-003**: Stratified Data Splitting (see `code/data/split.py`)
- **FR-004**: GCN Model Training (see `code/models/train.py`, `code/models/gcn.py`)
- **FR-005**: Model Comparison (see `code/eval/metrics.py`)
- **FR-006**: Sensitivity Analysis (see `code/eval/sensitivity.py`)
- **FR-007**: Statistical Correction (see `code/eval/sensitivity.py`)

## Directory Structure

```
.
├── code/
│ ├── data/ # Ingestion, Preprocessing, Splitting
│ ├── models/ # GCN, Baseline, Training
│ ├── eval/ # Metrics, Sensitivity, Reports
│ ├── utils/ # Logging, Checksums, Validators
│ └── config.py # Configuration constants
├── data/
│ ├── raw/ # Raw ZINC15 chunks
│ ├── processed/ # Feature-rich datasets
│ └── splits/ # Train/Test indices
├── results/
│ ├── reports/ # JSON/MD reports
│ ├── plots/ # Visualization figures
│ └── predictions/ # Model outputs
├── tests/ # Unit and Integration tests
└── docs/ # API Documentation
```

## Quick Start

1. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

2. **Run Ingestion**:
 ```bash
 python code/data/ingest.py
 ```

3. **Run Preprocessing**:
 ```bash
 python code/data/preprocess.py
 ```

4. **Run Training**:
 ```bash
 python code/models/train.py
 ```

5. **Run Evaluation**:
 ```bash
 python code/eval/sensitivity.py
 ```

## API Documentation

- [Data Module](api/data.md)
- [Models Module](api/models.md)
- [Evaluation Module](api/eval.md)
