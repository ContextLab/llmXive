# llmXive Follow-up: Extending "Latent Spatial Memory for Video World Models"

**Project ID**: PROJ-843-llmxive-follow-up-extending-latent-spati

## Overview

This project implements a sparse, CPU-efficient alternative to dense video world models.
By leveraging stratified dataset preparation, sparse SIFT/ORB feature extraction, and
RANSAC-optimized epipolar geometry, we aim to achieve comparable geometric fidelity
with significantly reduced inference time and memory footprint.

## Key Objectives

1. **Stratified Dataset Preparation**: Ingest RealEstate10K and stratify sequences into
 four subsets based on motion magnitude (Static/Slow/Fast) and texture entropy (High/Low).
2. **Sparse Feature Extraction**: Extract sparse descriptors (SIFT/ORB) without dense depth maps.
3. **Sparse Epipolar Solver**: Implement a RANSAC-optimized solver for fundamental matrix estimation
 and 3D point triangulation (up to scale).
4. **Latent Warping**: Perform CPU-based RBF interpolation for occlusion filling.
5. **Comparative Metrics**: Evaluate against dense baselines using WorldScore, Sparse-Consistency Score,
 and Fréchet Inception Distance (FID).

## Prerequisites

- Python 3.11+
- CPU-only environment (No GPU required)
- Sufficient RAM (Minimum 16GB recommended for full dataset processing)

## Installation

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure

```
.
├── code/
│ ├── config.py # Configuration paths and thresholds
│ ├── main.py # Pipeline orchestrator
│ ├── data/
│ │ ├── download.py # RealEstate10K ingestion
│ │ ├── stratify.py # Dataset stratification logic
│ │ └── extract_features.py # Sparse feature extraction
│ ├── geometry/
│ │ ├── solver.py # Fundamental matrix & triangulation
│ │ └── warp.py # RBF latent warping
│ ├── eval/
│ │ ├── metrics.py # WorldScore, FID, etc.
│ │ ├── anova.py # Statistical validation
│ │ └── sensitivity.py # Threshold sensitivity analysis
│ └── utils/
│ ├── seeds.py # Reproducibility
│ └── memory_monitor.py # Memory profiling
├── data/
│ ├── raw/ # Downloaded datasets
│ ├── stratified/ # Stratified subsets
│ ├── features/ # Extracted sparse features
│ └── results/ # Warped frames, metrics, reports
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Quick Start

Refer to `quickstart.md` for a step-by-step guide to running the full pipeline
from dataset download to final hypothesis verification.

```bash
# Example: Run the full pipeline
python code/main.py
```

## Configuration

The pipeline is configured via `code/config.py`. Key settings include:
- Data directories (`data/raw`, `data/stratified`, etc.)
- Memory limits (default 6GB for batch processing triggers)
- RANSAC thresholds and feature extraction parameters

## Results

Final outputs are generated in `data/results/`:
- `metrics.json`: Aggregated performance metrics (WorldScore, FID, Inference Time)
- `hypothesis_verification.md`: Final report verifying the 40% inference time reduction claim
- `sparse_warped_frames.npy`: Aggregated warped frames for visual inspection

## Contributing

This project follows a strict task-based implementation strategy. Please refer to `tasks.md`
for the current development roadmap and status.

## License

[Insert License Here]
