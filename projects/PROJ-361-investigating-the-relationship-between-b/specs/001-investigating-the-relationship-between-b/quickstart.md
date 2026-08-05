# Quickstart: Investigating the Relationship Between Brain Network Topology and Susceptibility to Visual Illusions

## 1. Prerequisites

- **Python**: 3.11+
- **System Dependencies**: Docker (for fMRIPrep), Git
- **Memory**: ~7 GB RAM (minimum)
- **Disk**: ~14 GB free space

## 2. Installation

### 2.1 Clone the Repository
```bash
git clone
cd proj-361-brain-illusion-topology
```

### 2.2 Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### 2.3 Install Dependencies
```bash
pip install -r requirements.txt
```

### 2.4 Verify Setup
```bash
python -m pytest tests/unit/test_seeds.py -v
```

## 3. Data Acquisition

### 3.1 Download Dataset
The project uses the OpenNeuro ds004285 dataset via a HuggingFace mirror.

```bash
python code/io/data_loader.py --download
```
This script:
1. Downloads the dataset to `data/raw/`.
2. Computes checksums and saves them to `data/metadata/checksums.json`.
3. Verifies file integrity.

### 3.2 Verify Data
```bash
python code/io/data_loader.py --verify
```

## 4. Preprocessing

### 4.1 Run fMRIPrep
Ensure Docker is running.

```bash
python code/preprocessing/pipeline.py --run-fmriprep
```
This step:
1. Invokes fMRIPrep container.
2. Processes raw BOLD data.
3. Outputs preprocessed nifti files to `data/interim/`.

### 4.2 Motion QC and Exclusion
```bash
python code/preprocessing/motion_qc.py --threshold 0.5
```
This step:
1. Calculates Mean FD for each subject.
2. Generates `data/processed/excluded_subjects.csv`.
3. Logs excluded subjects.

## 5. Topology Computation

### 5.1 Compute Connectivity
```bash
python code/topology/connectivity.py --atlas schaefer-400
```
Outputs: `data/processed/connectivity_matrices.npz`.

### 5.2 Compute Metrics
```bash
python code/topology/metrics.py
```
Outputs: `data/processed/topology_metrics_raw.json`.

## 6. Statistical Analysis

### 6.1 Merge Data
```bash
python code/io/schema_registry.py --merge
```
Outputs: `data/processed/merged_dataset.csv`.

### 6.2 Run Correlation
```bash
python code/statistics/correlation.py --fdr
```
Outputs: `data/processed/results.json` with FDR-corrected p-values.

## 7. Validation

### 7.1 Run Tests
```bash
pytest tests/ -v --cov=code
```

### 7.2 Validate Schemas
```bash
pytest tests/contract/test_schemas.py -v
```

## 8. Troubleshooting

- **Docker Errors**: Ensure Docker daemon is running and user has permissions.
- **Memory Errors**: Reduce the number of subjects or use `streaming=True` in data loader.
- **fMRIPrep Failures**: Check logs in `data/logs/fmriprep.log`.