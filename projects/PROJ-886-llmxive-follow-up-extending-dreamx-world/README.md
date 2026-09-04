# DreamX-Lite: Geometric Priors for 3D Consistency

**Project ID**: PROJ-886-llmxive-follow-up-extending-dreamx-world

## Overview

This project implements **DreamX-Lite**, a lightweight variant of the DreamX-World model that replaces learned E-PRoPE layers with fixed geometric priors (4x4 camera projection matrices) to improve 3D consistency in long-horizon video generation.

### Key Features
- **Geometric Priors**: Replaces learned embeddings with fixed 4x4 camera extrinsics.
- **Data Fallback Protocol**: Robust handling of data source availability (DreamX-World vs. ScanNet).
- **Evaluation Integrity**: Strict decoupling of generative models from metric computation.
- **Statistical Rigor**: McNemar's test, Wilcoxon signed-rank test, and sensitivity analysis.

## Project Structure

```text
projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/
├── code/
│ ├── analysis/ # Statistical analysis and metrics
│ ├── models/ # DreamXBase and DreamXLite implementations
│ ├── pipeline/ # Generation and evaluation pipelines
│ └── utils/ # Configuration, I/O, and setup utilities
├── data/
│ ├── raw/ # Raw datasets (DreamX-World, ScanNet)
│ └── derived/ # Generated metrics, statistics, and results
├── tests/
│ ├── unit/ # Unit tests for models and utilities
│ └── integration/ # End-to-end pipeline tests
├── docs/ # Documentation
├── requirements.txt # Python dependencies
├── pyproject.toml # Linting and formatting configuration
└── README.md # This file
```

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-886-llmxive-follow-up-extending-dreamx-world
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Set up environment variables**:
 ```bash
 export DREAMX_DATA_PATH=/path/to/dreamx-world-data
 export SCANNET_DATA_PATH=/path/to/scannet-fallback-data
 export PYTHONPATH=${PYTHONPATH}:$(pwd)/code
 ```

## Data Fallback Protocol

This project implements a strict **Data Fallback Protocol** to ensure robustness in data availability. The protocol is defined as follows:

### 1. Primary Data Source: DreamX-World
- **Priority**: High
- **Action**: Attempt to load DreamX-World dataset first.
- **Failure Handling**: If the dataset is missing or corrupted, log an error and proceed to the fallback mechanism.

### 2. Fallback Data Source: ScanNet
- **Priority**: Medium
- **Action**: If DreamX-World is unavailable, attempt to load the ScanNet fallback dataset.
- **Failure Handling**: If ScanNet is also unavailable, abort the primary claim generation and mark results as 'Pending Data Access'.

### 3. Strict No-Synthetic Policy
- **Rule**: Under no circumstances should synthetic or placeholder data be used as a fallback.
- **Enforcement**: The data loader (`code/utils/io.py`) will raise a `FileNotFoundError` if neither DreamX-World nor ScanNet data is found. This ensures that all results are derived from real, verified data sources.

### Implementation Details
- **Logic Switch**: Implemented in `code/utils/io.py` via `load_data()`.
- **Logging**: All data loading attempts and failures are logged with clear error messages.
- **Status Flag**: Results are tagged with a `data_source` flag indicating whether DreamX-World or ScanNet was used, or if the process was aborted due to missing data.

## Usage

### Generating Videos
Run the generation pipeline to create videos using DreamX-Lite:
```bash
python code/pipeline/generate.py --model dreamx_lite --num-frames 50
```

### Evaluating Metrics
Run the evaluation pipeline to compute MAE, scale drift, and SfM convergence:
```bash
python code/pipeline/evaluate.py --input-dir data/derived/videos --output-dir data/derived/metrics
```

### Statistical Analysis
Perform statistical significance tests on the metrics:
```bash
python code/analysis/stats.py --metrics-file data/derived/metrics.csv --output-file data/derived/statistical_results.json
```

### Sensitivity Analysis
Run sensitivity analysis on consistency thresholds:
```bash
python code/analysis/sensitivity.py --metrics-file data/derived/metrics.csv --thresholds 0.01 0.05 0.1
```

## Testing

Run unit tests:
```bash
pytest tests/unit/ -v
```

Run integration tests:
```bash
pytest tests/integration/ -v
```

## Configuration

- **Random Seed**: Set via `code/utils/config.py` (`set_global_seed()`).
- **Environment Variables**: Configure data paths and other settings in `code/utils/config.py`.
- **Linting & Formatting**: Enforced via `ruff` and `black` (see `pyproject.toml`).

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes with clear messages.
4. Submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
