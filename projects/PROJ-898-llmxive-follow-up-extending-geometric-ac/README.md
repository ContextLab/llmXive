# llmXive: Geometric Action Model for Robot Policy Learning

A research pipeline implementing a symbolic-latent planner for robot policy learning, extending the Geometric Action Model (GAM) with differentiable constraint solving.

## Project Structure

```
.
├── code/ # Core implementation modules
│ ├── __init__.py
│ ├── analysis.py # Statistical analysis (Fisher's Exact, Log-Rank)
│ ├── baseline_validator.py # Baseline GAM validation
│ ├── config.py # Configuration loading/saving
│ ├── data_generation.py # Synthetic topology/deformable generation
│ ├── differentiable_solver.py # Differentiable convex optimization layer
│ ├── experiment_time_validator.py # Time budget validation
│ ├── gfm_wrapper.py # Frozen GFM encoder/decoder
│ ├── gradient_verification.py # Gradient flow verification
│ ├── inference_integration.py # End-to-end inference integration
│ ├── inference_pipeline.py # Main orchestration loop
│ ├── latent_drift.py # Mahalanobis drift detection
│ ├── metadata_checksum.py # Zero-overlap verification
│ ├── physics_state_extractor.py # Simulation state serialization
│ ├── setup_data_dirs.py # Directory initialization
│ ├── setup_project_structure.py # Project scaffolding
│ ├── solver_profiler.py # Solver performance profiling
│ ├── statistical_reference.py # Reference statistics computation
│ ├── symbolic_solver.py # Symbolic constraint solver
│ ├── timeout_handler.py # Timeout enforcement
│ ├── trial_log_schema.py # Trial logging schema
│ └── utils.py # Utilities (logging, seeding, hashing)
├── data/ # Data directories (git-ignored)
│ ├── raw/ # Raw downloaded datasets & reference stats
│ ├── generated/ # Generated physics states & latent trajectories
│ └── results/ # Trial logs, analysis reports, profiling data
├── tests/ # Test suite
│ ├── __init__.py
│ └── unit/ # Unit tests for core modules
├── scripts/ # CLI entry points
│ ├── generate_test_set.py
│ ├── generate_profile_data.py
│ ├── profile_solver_synthetic.py
│ ├── validate_solver_timing.py
│ ├── profile_solver_real.py
│ └── run_experiment.py
├── requirements.txt # Pinned dependencies
├── config.yaml # Experiment configuration
├──.gitignore
└── README.md
```

## Prerequisites

- Python 3.9+
- CPU-only environment (no GPU required)
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd llmXive-follow-up-extending-geometric-ac
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

3. Initialize project directories:
 ```bash
 python code/setup_project_structure.py
 ```

## CLI Usage

### Generate Test Set (User Story 1)
Generates a synthetic dataset of novel kinematic chains and deformable materials.
```bash
python scripts/generate_test_set.py --config code/config.yaml --seed 42
```
**Outputs:**
- `data/generated/physics_states.json`
- `data/generated/latent_trajectory.csv`
- `data/generated/unique_topology_ids.json`

### Profile Solver (User Story 2)
Runs the differentiable symbolic solver on synthetic or real data to measure performance.
```bash
# Synthetic proxy
python scripts/profile_solver_synthetic.py
# Real data sample
python scripts/profile_solver_real.py
```
**Outputs:**
- `data/results/profiling_synthetic_report.json`
- `data/results/profiling_report.json`

### Run Inference Pipeline (User Story 2)
Executes the full encode -> solve -> decode -> simulate loop.
```bash
python scripts/run_experiment.py --config code/config.yaml --trials 50
```
**Outputs:**
- `data/results/trial_log.csv`
- `data/results/symbolic_results.csv`
- `data/results/drift_log.csv`

### Baseline Validation (User Story 3)
Runs the baseline GAM for comparison.
```bash
python scripts/run_baseline.py --config code/config.yaml
```
**Outputs:**
- `data/results/baseline_results.csv`

### Statistical Analysis (User Story 3)
Compares symbolic vs. baseline results using Fisher's Exact Test and conditional survival analysis.
```bash
python scripts/run_analysis.py
```
**Outputs:**
- `data/results/analysis_report.md`

## Configuration

Edit `code/config.yaml` to adjust:
- `topology_counts`: List of hinge counts (default: `[3, 10]`)
- `timeout_limits`: Max duration per solver step
- `trial_count`: Number of experimental trials (default: 50)
- `sim_fps`: Simulation frame rate (default: 60)
- `stiffness_range`: Range for deformable material stiffness

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

## Continuous Integration

This project uses GitHub Actions for CI. The workflow (`.github/workflows/ci.yml`) runs on multi-core x86_64 runners without GPU, enforcing a 6-hour timeout limit.

## License

Research use only. See LICENSE for details.