# Quickstart Guide: Neural Correlates of Predictive Error Signals

This guide provides instructions to run the full pipeline from raw data ingestion to statistical modeling.

## Prerequisites

- Python 3.11+
- 2+ CPU cores
- 7GB+ RAM
- Access to OpenNeuro or HuggingFace datasets

## Installation

1. Clone the repository:
 ```bash
 git clone <repo-url>
 cd PROJ-500-neural-correlates-of-predictive-error-si
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

3. Configure environment variables (create `.env`):
 ```bash
 DATA_DIR=./data
 SEED=42
 RAM_LIMIT=7.0
 ```

## Running the Pipeline

The pipeline is executed in stages. You can run the full end-to-end process with:

```bash
python code/run_full_pipeline.py
```

### Stage 1: Data Ingestion & Preprocessing (T014-T018)
Downloads raw EEG data, filters, applies ICA, and epochs.
```bash
python code/src/data/ingest.py
python code/src/data/preprocess.py
```

### Stage 2: Alignment (T021-T026)
Computes MMN amplitudes and aligns with behavioral accuracy.
```bash
python code/src/data/align.py
```

### Stage 3: Statistical Modeling (T029-T034)
Fits LME models and runs permutation tests.
```bash
python code/src/analysis/model.py
```

## Verification

To verify the pipeline meets the performance constraint (≤6 hours on 2-core CPU):

```bash
python -m pytest code/tests/unit/test_t037_performance.py -v
```

## Output Artifacts

- `data/aligned_data.csv`: Final aligned dataset
- `analysis/results/model_output.json`: Model coefficients and p-values
- `figures/`: Generated plots (if enabled)
