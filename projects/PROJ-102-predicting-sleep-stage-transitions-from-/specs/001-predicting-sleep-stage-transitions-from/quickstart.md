# Quickstart: Predicting Sleep Stage Transitions from Scalp EEG Using Deep Learning

## Prerequisites

- Python 3.11+
- Access to PhysioNet (no authentication required for public SC subset, but `wget` or `requests` needed).
- 7 GB RAM available.

## Installation

1. **Clone the repository** and navigate to the project directory.
   ```bash
   git clone <repo-url>
   cd projects/PROJ-102-predicting-sleep-stage-transitions-from-/code
   ```

2. **Create a virtual environment** and install dependencies.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Verify environment**:
   ```bash
   python -c "import torch; print(torch.__version__); print('CPU:', torch.backends.cpu.is_available())"
   ```

## Running the Pipeline

The pipeline is orchestrated via `main.py`. It performs the following steps in order:
1. **Download**: Fetches Sleep-EDF SC data and verifies checksums.
2. **Preprocess**: Applies interpolation, filtering, and segmentation.
3. **Extract Features**: Computes time, frequency, and non-linear features.
4. **Statistical Test**: Runs Cluster-Based Permutation Tests.
5. **Train Model**: Trains the lightweight 1D-CNN.
6. **Validate**: Evaluates on held-out subjects.

### Run Full Pipeline (CPU Only)
```bash
python main.py --mode full
```

### Run Specific Phase
```bash
# Only download and preprocess
python main.py --mode preprocess

# Only feature extraction and stats
python main.py --mode features

# Only model training and validation
python main.py --mode train
```

## Expected Outputs

- **Data**: `data/processed/epochs.parquet`, `data/processed/features.parquet`
- **Models**: `data/models/checkpoint.pth`
- **Reports**: `data/interim/stats_results.json`, `data/interim/metrics.json`
- **Logs**: `logs/pipeline.log`

## Troubleshooting

- **Memory Error**: Reduce `batch_size` in `config.py` or process subjects in smaller chunks.
- **Download Timeout**: Ensure network access to `physionet.org`.
- **CUDA Error**: This pipeline is CPU-only. If CUDA is detected, ensure `torch` was installed without GPU support (or set `CUDA_VISIBLE_DEVICES=""`).
