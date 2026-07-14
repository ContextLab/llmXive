# llmXive Follow-up: Extending "Latent Spatial Memory for Video World Models"

## Project Overview

This project implements a sparse, CPU-efficient pipeline for video world modeling,
extending the concepts from "Latent Spatial Memory for Video World Models".
It focuses on stratified dataset preparation, sparse feature extraction, geometric solving,
and comparative metric analysis against dense baselines.

## Key Features

- **Stratified Data Preparation**: Ingests RealEstate10K and stratifies sequences into
 4 subsets based on motion magnitude and texture entropy (Static/Slow/Fast x High/Low texture).
- **Sparse Feature Extraction**: Extracts SIFT/ORB descriptors without dense depth maps.
- **Geometric Solving**: RANSAC-optimized sparse fundamental matrix solver with CPU-based RBF warping.
- **Metric Validation**: Computes WorldScore, Sparse-Consistency Score, FID, and performs Two-Way ANOVA.
- **CPU-First Design**: Optimized for CPU execution with memory monitoring and batch processing.

## Prerequisites
- Python 3.11+
- CPU-only environment (GPU not required)
- 16GB+ RAM recommended for full dataset processing

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 cd projects/PROJ-843-llmxive-follow-up-extending-latent-spati
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: `code/requirements.txt` is generated during setup (T001b).*

3. Ensure the directory structure is created:
 ```bash
 python code/data/setup_data.py
 ```

## Quick Start

Run the full pipeline:

```bash
python code/main.py
```

This orchestrates the entire workflow:
1. Data download and stratification
2. Feature extraction
3. Geometric solving and warping
4. Metric computation and statistical analysis
5. Report generation

See `quickstart.md` for a step-by-step guide.

## Project Structure
- `code/`: Source code
- `data/`: Raw, processed, and results data
- `tests/`: Unit tests
- `specs/`: Design documents

```
.
├── code/
│ ├── config.py # Configuration and paths
│ ├── main.py # Pipeline orchestrator
│ ├── data/ # Data processing modules
│ │ ├── download.py # Dataset download
│ │ ├── stratify.py # Stratified dataset preparation
│ │ └── extract_features.py # Sparse feature extraction
│ ├── geometry/ # Geometric computation
│ │ ├── solver.py # Fundamental matrix solver
│ │ ├── warp.py # RBF warping
│ │ └── aggregate_warps.py # Warped frame aggregation
│ ├── eval/ # Evaluation and metrics
│ │ ├── metrics.py # Metric computation
│ │ ├── anova.py # Statistical analysis
│ │ ├── sensitivity.py # Sensitivity analysis
│ │ ├── report.py # Report generation
│ │ └── download_dense_baseline.py
│ ├── utils/ # Utilities
│ │ ├── seeds.py # Random seed management
│ │ └── memory_monitor.py # Memory profiling
│ └── validate_quickstart.py # Quickstart validation script
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── stratified/ # Stratified sequences
│ ├── features/ # Extracted features
│ └── results/ # Computed results and reports
├── tests/ # Unit tests
└── specs/ # Design documents
```

## Documentation

- `quickstart.md`: Step-by-step guide for running the pipeline
- `specs/`: Design documents and specifications
- `code/`: Source code with inline documentation

## Usage Examples

### Run Individual Components

- **Download Dataset**:
 ```bash
 python code/data/download.py
 ```

- **Stratify Data**:
 ```bash
 python code/data/stratify.py
 ```

- **Extract Features**:
 ```bash
 python code/data/extract_features.py
 ```

- **Run Solver**:
 ```bash
 python code/geometry/solver.py
 ```

- **Compute Metrics**:
 ```bash
 python code/eval/metrics.py
 ```

- **Generate Report**:
 ```bash
 python code/eval/report.py
 ```

### Validate Quickstart

```bash
python code/validate_quickstart.py
```

This runs a minimal end-to-end check to ensure the pipeline is functional.

## Performance Considerations

- **Memory Limits**: The pipeline enforces a 6GB RAM threshold for batch processing.
- **CPU Optimization**: All modules are designed for CPU execution; no GPU dependencies.
- **Reproducibility**: Global random seeds are pinned for consistent results.

## Contributing

1. Ensure all tests pass before submitting changes.
2. Follow the existing code style (black, flake8).
3. Update documentation for new features.

## License

[Insert License Information]

## Acknowledgments

- Based on "Latent Spatial Memory for Video World Models"
- Uses RealEstate10K dataset
- Built with OpenCV, scikit-learn, scipy, pandas, numpy, torch, datasets
