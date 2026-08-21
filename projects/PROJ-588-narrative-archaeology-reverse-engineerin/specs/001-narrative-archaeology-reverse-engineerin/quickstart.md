# Quickstart: Narrative Archaeology

## Prerequisites

*   Python 3.11+
*   Docker (for fMRIPrep)
*   Git
*   ~ GB free disk space (for temporary processing)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-588-narrative-archaeology-reverse-engineerin
    ```

2.  **Set up the environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Verify dependencies**:
    ```bash
    python -c "import nibabel, nilearn, torch, datasets; print('All deps OK')"
    ```

## Running the Pipeline

The pipeline is designed to run on a GitHub Actions runner, but can be executed locally for debugging.

### Step 1: Download and Preprocess (US-1)
```bash
python code/data/download.py --dataset ds000234 --subjects sub-01 sub-02 sub-03 sub-04 sub-05
python code/data/preprocess.py --subjects sub-01 sub-02 sub-03 sub-04 sub-05 --motion-threshold 3.0
```
*   This will download the subset, run fMRIPrep, and skip subjects with motion > 3mm.
*   Errors are logged to `data/errors.log`.

### Step 2: Segment and Extract Features (US-1, US-3)
```bash
python code/data/segmentation.py --input data/processed --output data/processed/events_aligned.csv
python code/data/features.py --input data/processed/events_aligned.csv --output data/processed/semantic_features.csv
```

### Step 3: Analysis (US-2, US-3)
```bash
python code/analysis/rsa.py --input data/processed --output data/results/rsa_results.json
python code/analysis/decoding.py --input data/processed --output data/results/decoding_results.json
```

### Step 4: Validation
```bash
python -m pytest tests/ --cov=code
```

## Data Hygiene & PII

*   **PII Scan**: Run `python code/utils/hygiene.py --scan data/raw` before any data commit.
*   **Checksums**: All raw files are checksummed upon download. Derivations are written to new files with recorded hashes in `state/...yaml`.

## Troubleshooting

*   **fMRIPrep fails**: Check Docker logs. Ensure sufficient disk space.
*   **Motion Artifact**: Subjects with motion > 3mm are skipped and logged. Check `data/errors.log`.
*   **Memory Error**: The pipeline uses streaming. If it fails, reduce the number of subjects in the `--subjects` flag.
