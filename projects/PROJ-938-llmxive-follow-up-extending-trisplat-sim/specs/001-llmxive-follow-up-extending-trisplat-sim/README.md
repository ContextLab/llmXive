# llmXive Follow-up: Extending TriSplat for CPU-Only Edge Robotics

## Project Overview

This project implements a geometry-only 3D scene reconstruction pipeline optimized for CPU-only edge robotics environments. It extends the TriSplat framework by replacing the learned refinement head with a differentiable ray-surface intersection layer, enabling feasible 3D reconstruction on standard 2-core CPU hardware without GPU acceleration.

## Key Features

- **CPU-Optimized**: Designed to run on 2-core CPU with < 6 GB RAM usage
- **Geometry-Only Reconstruction**: Replaces learned refinement with explicit geometric constraints
- **Sparsity Threshold Analysis**: Systematically identifies the minimum view count required for stable reconstruction
- **Benchmarking**: Compares latency and fidelity against baseline TriSplat
- **Streaming Data**: Processes RealEstate10K dataset via streaming to handle large datasets efficiently

## User Stories

### US1: CPU-Feasible Geometry-Only Reconstruction (MVP)
Run 3D scene reconstruction on a standard 2-core CPU using only explicit geometric constraints, producing a valid mesh within 30 minutes.

### US2: Sparsity Threshold Identification
Systematically vary input views (2, 3, 4, 5) to identify the sparsity threshold where geometric constraints fail.

### US3: Quantitative Fidelity and Latency Benchmarking
Compare inference latency and geometric fidelity of the geometry-only module against the baseline TriSplat.

## Architecture

```
code/
├── cli.py # Entry point with CLI arguments
├── data/
│ ├── loader.py # RealEstate10K streaming data loader
│ └── metrics.py # Chamfer Distance and PSNR calculation
├── experiments/
│ ├── run_batch.py # Batch orchestration and execution
│ ├── generate_benchmark_csv.py
│ ├── generate_final_report.py
│ └── generate_tradeoff_plot.py
├── models/
│ ├── trisplat_base.py # Frozen TriSplat backbone
│ └── geometry_only.py # Differentiable ray-surface layer
└── utils/
 ├── mesh_utils.py # Mesh generation and validation
 └── stats.py # Statistical analysis and threshold detection

data/
├── raw/ # Raw dataset downloads
└── processed/ # Generated metrics, reports, and plots

specs/
└── 001-llmxive-trisplat-ext/
 ├── README.md # This file
 └── quickstart.md # Getting started guide
```

## Prerequisites

- Python 3.11+
- CPU-only environment (no GPU required)
- 6 GB+ RAM
- 14 GB+ disk space for dataset

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 cd projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

3. (Optional) Setup linting and formatting:
 ```bash
 pip install ruff black
 ```

## Usage

### Quick Start
See [`quickstart.md`](quickstart.md) for a step-by-step guide to run the pipeline.

### Running the Pipeline

The main entry point is `code/cli.py`:

```bash
python code/cli.py --views 3 --timeout 1800 --seed 42
```

**Arguments:**
- `--views`: Number of input views (2, 3, 4, or 5)
- `--timeout`: Maximum runtime in seconds (default: 1800 for 30 mins)
- `--seed`: Random seed for reproducibility
- `--update-state`: Update state file with checksums after execution

### Running Batch Experiments

To run the full batch experiment across multiple scenes and view counts:

```bash
python code/cli.py --update-state
```

Or directly:

```bash
python code/experiments/run_batch.py --n-scenes 20 --timeout 21600
```

### Generating Reports

After batch execution, generate the final reports:

```bash
# Generate benchmark CSV
python code/experiments/generate_benchmark_csv.py

# Generate trade-off plot
python code/experiments/generate_tradeoff_plot.py

# Generate final report with threshold analysis
python code/experiments/generate_final_report.py
```

## Data Management

- **Dataset**: RealEstate10K (streamed via Hugging Face `datasets` library)
- **Resolution**: Automatically downsampled to 320x240 for CPU feasibility
- **Checksums**: SHA-256 checksums are computed and stored for data integrity
- **State Tracking**: Execution state is tracked in `state/projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim.yaml`

## Output Artifacts

After successful execution, the following artifacts will be generated:

- `data/processed/benchmark_tradeoff.csv`: Latency vs. Chamfer Distance metrics
- `data/processed/benchmark_tradeoff_plot.png`: Visualization of the trade-off curve
- `data/processed/threshold_result.json`: Identified sparsity threshold
- `data/processed/final_report.json`: Comprehensive batch results
- `data/processed/checksums_temp.json`: Data integrity checksums

## Testing

Run the test suite:

```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/
```

## Performance Constraints

- **Runtime**: < 30 minutes per scene (single view configuration)
- **Memory**: < 6 GB peak RAM
- **CPU**: 2-core affinity enforced for baseline comparison
- **Convergence**: Hard limit of 100 iterations for optimization

## Error Handling

- **Monocular Input**: Automatically detected and rejected with appropriate error message
- **Corrupted Data**: Corrupted/missing ground truth scenes are skipped with warning
- **Non-Convergence**: Placeholder meshes generated for failed reconstructions with distinct error flags
- **Timeout**: Graceful handling with partial results logged

## Configuration

Key constants that can be adjusted:

- `TOLERANCE_THRESHOLD = 0.15`: Threshold for sparsity identification (in `code/utils/stats.py`)
- `MAX_ITERATIONS = 100`: Maximum optimization iterations (in `code/models/geometry_only.py`)
- `N_SCENES = 20`: Default batch size (configurable via CLI)

## License

This project is part of the llmXive automated science pipeline.

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests to ensure nothing is broken
4. Submit a pull request

## Contact

For questions or issues, please refer to the project documentation or open an issue.
