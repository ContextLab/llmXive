# PROJ-938: Extending TriSplat for CPU-only Edge Robotics

This project implements a CPU-feasible extension of the TriSplat architecture for 3D scene reconstruction on edge devices.

## Quick Start

```bash
# Install dependencies
pip install -r code/requirements.txt

# Run a single scene reconstruction
python code/cli.py --views 2 --timeout 1800 --seed 42

# Run a batch experiment
python code/experiments/run_batch.py --scenes 20 --timeout 21600
```

## Project Structure

```
projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim/
├── code/
│ ├── cli.py # Entry point
│ ├── data/
│ │ ├── loader.py # RealEstate10K streaming loader
│ │ └── metrics.py # Chamfer Distance & PSNR
│ ├── models/
│ │ ├── trisplat_base.py # Frozen TriSplat backbone
│ │ └── geometry_only.py # Differentiable geometry layer
│ ├── experiments/
│ │ ├── run_batch.py # Batch orchestration
│ │ ├── generate_benchmark_csv.py
│ │ └── generate_tradeoff_plot.py
│ └── utils/
│ ├── mesh_utils.py # Mesh generation & validation
│ └── stats.py # Statistical analysis
├── data/
│ └── processed/ # Output artifacts
├── tests/
│ ├── unit/
│ └── integration/
└── specs/
 └── 001-llmxive-trisplat-ext/
```

## Key Features
- **CPU-Only Execution**: Optimized for 2-core edge devices
- **Geometry-Only Layer**: Replaces learned refinement with explicit constraints
- **Adaptive View Count**: Supports 2-5 input views
- **Statistical Thresholding**: Identifies sparsity limits
- **Benchmarking**: Latency vs. Fidelity trade-off analysis

## License
MIT License
