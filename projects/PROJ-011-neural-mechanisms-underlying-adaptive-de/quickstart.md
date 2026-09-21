# Quickstart Guide for Neural Mechanisms Project

## Prerequisites
- Python 3.9+
- pip

## Installation
```bash
pip install -r requirements.txt
```

## Data Download
Run the data download task (T013):
```bash
python code/preprocessing/data_download.py
```

## Preprocessing Pipeline
Run the full preprocessing pipeline (T012-T019):
```bash
python code/main.py --stage preprocessing
```
This executes:
1. Data Validation (T012)
2. Data Download (T013)
3. Motion Correction (T014)
4. Validate Motion (T014b)
5. Normalization (T015)
6. Smoothing (T016)
7. ROI Extraction (T017)
8. QC Filter (T018)
9. **QC Reporter (T018b)** -> Generates `data/reports/qc_summary.json`

## Modeling Pipeline
```bash
python code/main.py --stage modeling
```

## Analysis Pipeline
```bash
python code/main.py --stage analysis
```

## Reporting
```bash
python code/main.py --stage reporting
```

## Verification
Verify checksums:
```bash
python code/utils/io.py verify-checksums
```
(Note: Uses subcommand syntax as defined in code/utils/io.py)