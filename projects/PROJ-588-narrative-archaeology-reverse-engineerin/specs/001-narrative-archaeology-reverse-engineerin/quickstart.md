# Quickstart: Narrative Archaeology

## Prerequisites

- Python 3.11+
- Git
- Docker (for fMRIPrep, if used) or Singularity
- Access to GitHub Actions (for CI execution)

## Setup

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-588-narrative-archaeology-reverse-engineerin
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

3.  **Configure Environment**:
    Create a `.env` file in the root:
    ```bash
    export OPENNEURO_DATASET_ID=ds
    export NUM_SUBJECTS=10
    export RANDOM_SEED=42
    ```

## Running the Pipeline

### 1. Download and Preprocess
Run the data ingestion script (subset mode for CI):
```bash
python code/data/download.py --subset 10
python code/data/preprocess.py --parallel 2
```
*Note: This step may take several hours on a local machine or CI runner.*

### 2. Segment Events
Align story annotations with fMRI data:
```bash
python code/data/segment.py --hrf-convolve
```

### 3. Run RSA Analysis
Compare encoding vs. recognition patterns:
```bash
python code/models/rsa.py --roi hippocampus,mPFC,PCC,temporal
```

### 4. Train Decoding Models
Reconstruct narrative elements:
```bash
python code/models/decoder.py --type ridge --features bert --kfold 5
```

### 5. Generate Reports
```bash
python code/utils/viz.py --output results/
```

## Verification

To verify the pipeline on a minimal subset (2 subjects):
```bash
python code/main.py --test-mode --subjects a_small_number_of
```
Expected output:
- Preprocessed NIfTI files in `data/processed/`.
- Event CSV in `data/derived/events.csv`.
- RSA matrix in `data/derived/rsa_matrix.npy`.
- Decoding accuracy report in `data/derived/accuracy.json`.

## Troubleshooting

- **Memory Error**: Reduce `NUM_SUBJECTS` or downsample fMRI resolution.
- **fMRIPrep Fail**: Check logs in `logs/fmriprep/`. The pipeline will skip failed subjects automatically.
- **Missing Labels**: Rare categories are aggregated into "misc" to prevent overfitting.
