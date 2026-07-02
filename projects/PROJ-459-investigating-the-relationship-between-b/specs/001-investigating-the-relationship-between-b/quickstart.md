# Quickstart: Investigating the Relationship Between Brain Network Dynamics and Musical Genre Preference

## Prerequisites

- **Python**: 3.11+
- **Docker**: Required for fMRIPrep.
- **Memory**: Minimum 8GB RAM recommended (pipeline will attempt to run on a downsized dataset).
- **Disk**: Sufficient free space for data and intermediates.
- **Sample Size**: Minimum 85 subjects required for valid power analysis.

## Installation

1.  **Clone the repository** (or navigate to the project root).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins versions for reproducibility (Constitution Principle I). fMRIPrep is a Docker image, not a pip package.*

## Configuration

Edit `code/config.py` to set:
- `DATASET_ID`: OpenNeuro dataset ID (e.g., `ds000030`).
- `MIN_SAMPLE_SIZE`: Minimum N required (default: 85).
- `WINDOW_SIZES`: List for sensitivity analysis (default: `[20, 30, 40]`).
- `PERMUTATIONS`: Number of permutations for null distribution (default: a representative sample size).

## Running the Pipeline

### 1. Download & Validate Data
```bash
python code/main.py --step download_and_validate
```
- **Expected Output**: Logs indicating data download status.
- **Critical Check**: If `musical_genre` or `STOMP-R` is missing, the script will exit with `ERR_DATA_MISSING`. **Do not proceed if this occurs.**
- **Power Check**: If N < 85, the script will exit with `ERR_UNDERPOWERED`.

### 2. Preprocess fMRI Data (fMRIPrep)
```bash
python code/main.py --step preprocess
```
- **Note**: This step runs fMRIPrep in a Docker container. Ensure Docker is running.
- **Memory**: If OOM errors occur, the script will automatically reduce resolution or sample size (if N > 85 and runtime is an issue, but note: N < 85 is not allowed).

### 3. Compute Metrics
```bash
python code/main.py --step compute_metrics
```
- Computes static and dynamic connectivity metrics.
- Runs sensitivity analysis on window sizes.
- **Motion Control**: Time series are motion-regressed before dynamic analysis.

### 4. Statistical Analysis
```bash
python code/main.py --step analyze
```
- Performs Spearman correlations, BH correction, and power analysis.
- Uses **1,000+ permutations** for null distribution.
- Generates `data/derived/correlations.csv`.

### 5. Visualization
```bash
python code/main.py --step visualize
```
- Generates heatmaps and network diagrams in `data/derived/figures/`.

## Verification

- **Check Sum**: Verify `data/checksums.json` matches `state/...yaml`.
- **Contract Tests**:
    ```bash
    pytest tests/contract/
    ```
- **Unit Tests**:
    ```bash
    pytest tests/unit/
    ```

## Troubleshooting

- **Error: `ERR_DATA_MISSING`**: The dataset lacks the required behavioral variables. The study cannot proceed without them.
- **Error: `ERR_UNDERPOWERED`**: The available sample size (N) is limited. The study is underpowered for the target effect size.
- **Error: `MemoryError`**: The pipeline will attempt to downsample. If it fails, reduce `SAMPLE_SIZE` in `config.py` (but ensure N ≥ 85).
- **Error: `Docker not found`**: Ensure Docker is installed and running. fMRIPrep requires it.
- **Error: `Runtime Exceeded`**: If the job exceeds a substantial duration, the pipeline will fail. This requires a spec amendment to increase compute resources or reduce the scope.