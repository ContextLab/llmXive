# llmXive: Extending OrbitQuant for Data-Agnostic Quantization in Diffusion Models

This project implements a research pipeline to investigate the correlation between prompt semantic entropy and DiT (Diffusion Transformer) activation variance, and to leverage this correlation for dynamic rotation matrix selection in W2A4 quantization.

## Quick Start

### Prerequisites

- Python 3.10+
- PyTorch 2.0+
- CUDA-enabled GPU (recommended for DiT generation tasks)

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Edit `code/config.py` to set your paths and hyperparameters. By default, the system attempts to use GPU. If GPU is unavailable, it falls back to CPU (see **GPU Escape Hatch** below).

## GPU Escape Hatch

The DiT generation tasks (e.g., `run_correlation.py`, `run_router_inference.py`) are resource-intensive. If the runner environment lacks a GPU or encounters OOM errors, the pipeline automatically triggers the **Kaggle GPU Offload Mechanism**.

### How it Works

1. The script `code/utils/gpu_offload.py` (implemented in T041) detects CPU failure on DiT generation.
2. It triggers a subprocess or remote execution on a Kaggle GPU instance.
3. Results are fetched back and processed locally.

**Usage:**
No manual intervention is required. The logic is embedded in `code/models/flux_wan_loader.py` and the orchestration scripts. If a GPU is not detected, the system will attempt to offload. Ensure your environment has network access to Kaggle if CPU fallback is triggered.

## Pipeline Overview

1. **Data Preparation**: Download MS-COCO and diverse prompts.
2. **Foundational Analysis**: Compute activation histograms and derive rotation matrices.
3. **Correlation Study**: Measure correlation between entropy and variance.
4. **Router Implementation**: Map entropy to rotation matrices.
5. **Evaluation**: Compare dynamic vs. static quantization.

## Usage Examples

### Running the Correlation Analysis

This script computes semantic entropy for a set of prompts, generates images to capture activation variances, and computes the Pearson correlation.

```bash
python code/run_correlation.py
```

**Output:** `data/processed/correlation_results.json`

**Steps performed:**
1. Loads prompts from `data/processed/prompts_test.csv`.
2. Computes entropy using `EntropyProxy`.
3. Runs DiT generation with activation hooks.
4. Aggregates variances and computes correlation.

### Running Router Inference

This script demonstrates the dynamic rotation router in action, selecting matrices based on prompt entropy.

```bash
python code/run_router_inference.py
```

**Output:** `data/processed/router_inference_results.json`

**Steps performed:**
1. Loads diverse test prompts.
2. Computes entropy for each prompt.
3. Loads pre-optimized rotation matrices from `data/processed/clustering_report.json`.
4. Routes each prompt to a specific matrix index.
5. Generates images using the selected matrices.
6. Logs metrics and latency.

## API Documentation

### `code/analysis/router.py`

The `EntropyRouter` class maps semantic entropy scores to pre-optimized rotation matrix indices.

#### Class: `EntropyRouter`

**Initialization:**
```python
from analysis.router import EntropyRouter
from config import Config

router = EntropyRouter(
 clustering_report_path="data/processed/clustering_report.json",
 config=Config()
)
```

**Methods:**
- `route(entropy_score: float) -> int`: Returns the matrix index for a given entropy score.
- `get_matrix(index: int)`: Returns the rotation matrix tensor for the given index.

**Example:**
```python
score = 0.75
matrix_idx = router.route(score)
matrix = router.get_matrix(matrix_idx)
```

### `code/quantization/w2a4_engine.py`

The `W2A4Engine` handles W2A4 quantization with optional rotation matrix application.

**Integration:**
The engine now accepts a `rotation_matrix` argument or integrates with the `EntropyRouter` to automatically select the matrix during inference.

## Project Structure

```
.
├── code/
│ ├── analysis/ # Entropy, correlation, clustering, router logic
│ ├── data/ # Data download and preprocessing
│ ├── evaluation/ # Metrics (FID, CLIP, MSE) and timing
│ ├── models/ # DiT wrappers and model loaders
│ ├── quantization/ # W2A4 engine and static baseline
│ ├── utils/ # GPU offload logic
│ ├── validation/ # Validation gate scripts
│ ├── config.py # Configuration
│ ├── run_correlation.py
│ ├── run_router_inference.py
│ └──...
├── data/
│ ├── raw/ # Raw downloaded datasets
│ └── processed/ # Preprocessed prompts, matrices, results
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── requirements.txt
└── README.md
```

## Citation

If you use this code in your research, please cite the original OrbitQuant paper and this project's technical report.

## License

MIT License
