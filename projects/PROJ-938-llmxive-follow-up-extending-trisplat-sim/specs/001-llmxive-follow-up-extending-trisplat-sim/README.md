# llmXive Follow-up: Extending TriSplat for CPU-only Edge Robotics

## Project Summary
This project adapts the TriSplat 3D reconstruction model to run on CPU-only hardware, making it suitable for edge robotics applications where GPU resources are unavailable. The core innovation is the replacement of the learned refinement head with a geometry-only differentiable layer.

## Key Features
- **CPU-Optimized**: Designed to run on standard 2-core CPUs.
- **Geometry-Only Reconstruction**: Uses explicit geometric constraints for faster inference.
- **Sparsity Analysis**: Systematically evaluates the impact of input view count on reconstruction quality.
- **Benchmarking**: Provides detailed latency vs. fidelity trade-off analysis.

## Quick Start
1. **Prerequisites**: Python 3.11+, pip, and access to the RealEstate10K dataset.
2. **Installation**:
 ```bash
 pip install -r code/requirements.txt
 ```
3. **Run Single Scene**:
 ```bash
 python code/cli.py --views 3 --seed 42
 ```
4. **Run Batch**:
 ```bash
 python code/experiments/run_batch.py --timeout 21600 --views 2,3,4,5
 ```

## Project Structure
```
projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim/
├── code/
│ ├── cli.py # Entry point
│ ├── data/
│ │ ├── loader.py # Data loading (RealEstate10K)
│ │ └── metrics.py # Metric calculation
│ ├── models/
│ │ ├── trisplat_base.py # Base TriSplat model
│ │ └── geometry_only.py # Geometry-only implementation
│ ├── utils/
│ │ ├── mesh_utils.py # Mesh generation/validation
│ │ ├── stats.py # Statistical analysis
│ │ └── validate_contracts.py
│ └── experiments/
│ ├── run_batch.py # Batch orchestration
│ └── generate_*.py # Report generation scripts
├── data/
│ └── processed/ # Output artifacts
├── specs/
│ └── 001-llmxive-trisplat-ext/
│ ├── README.md # This file
│ ├── quickstart.md # Detailed setup guide
│ └── spec.md # User stories and requirements
├── state/
│ └── projects/
│ └── PROJ-938-llmxive-follow-up-extending-trisplat-sim.yaml
└── tests/
 ├── unit/
 └── integration/
```

## Documentation
- [Quick Start Guide](quickstart.md)
- [User Stories & Requirements](spec.md)
- [Data Model](../../data-model.md) (if applicable)

## Contributing
Follow the task list in `tasks.md` to implement features incrementally. Ensure all tests pass before merging.
