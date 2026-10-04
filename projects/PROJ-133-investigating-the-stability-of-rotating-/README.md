# Investigating the Stability of Rotating Bose-Einstein Condensates with Dipolar Interactions

This project implements a numerical study of the stability of rotating Bose-Einstein Condensates (BECs) with dipolar interactions. It solves the time-dependent Gross-Pitaevskii Equation (GPE) using a split-step Fourier method, detects vortices via phase winding, calculates stability metrics, and performs statistical analysis to generate phase diagrams.

## Features

- **GPE Solver**: Split-step Fourier solver with dipolar interaction terms.
- **Initial Conditions**: Thomas-Fermi and Gaussian initial states.
- **Vortex Detection**: Phase-winding algorithm to detect vortex-antivortex pairs.
- **Stability Metrics**: Calculates vortex density, radial variance, and structure factor sharpness.
- **Statistical Analysis**: Two-Way ANOVA (Ω × ε_dd) and Dunnett's post-hoc test.
- **Visualization**: 3D contour maps of stability regimes and representative density/phase plots.

## Prerequisites

- Python 3.8+
- pip
- git

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-133-investigating-the-stability-of-rotating-
 ```

2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Project Structure

```
.
├── code/
│ ├── simulation/ # GPE solver, initial conditions, batch runner
│ ├── analysis/ # Vortex detection, metrics, sensitivity analysis
│ ├── statistics/ # Aggregation, ANOVA, Dunnett's test
│ ├── viz/ # Plotting and reporting
│ ├── config/ # Grid and physical parameters
│ ├── models/ # Data models (SimulationRun, StabilityMetric)
│ ├── utils/ # Logging, I/O, seed management
│ └── requirements.txt
├── data/
│ ├── raw/ # Raw simulation outputs
│ ├── processed/ # Processed data (vortices, metrics)
│ └── aggregated/ # Aggregated results for statistics
├── tests/
│ ├── unit/ # Unit tests
│ ├── contract/ # Contract tests
│ └── integration/ # Integration tests
├── docs/ # Documentation
├── README.md
└── spec.md
```

## Usage

### 1. Run a Single Simulation

Run a single GPE simulation with specific parameters:

```bash
cd code
python simulation/runner.py --omega 0.5 --epsilon_dd 0.5 --N 10000 --grid_size 64
```

**Parameters:**
- `--omega`: Rotation frequency (Ω)
- `--epsilon_dd`: Dipolar interaction strength (ε_dd)
- `--N`: Number of particles
- `--grid_size`: Grid resolution (64 for batch, 256 for verification)

Output files will be saved in `data/raw/`.

### 2. Run Batch Simulations

Run simulations across a parameter grid:

```bash
cd code
python simulation/runner.py --batch
```

This iterates over predefined values of Ω, ε_dd, and N. Set `RUN_FULL_GRID=true` to use 64x64 grid for the full scan.

### 3. Analyze Snapshots

Detect vortices and calculate stability metrics from raw simulation data:

```bash
cd code
python analysis/pipeline.py --input data/raw/ --output data/processed/
```

**Metrics Calculated:**
- Vortex Density (vortices/area)
- Radial Variance
- Structure Factor Sharpness

### 4. Perform Sensitivity Analysis

Analyze the sensitivity of stability thresholds:

```bash
cd code
python analysis/sensitivity_analysis.py --input data/processed/
```

Evaluates thresholds over {0.30, 0.35} and reports false-positive/negative rates.

### 5. Generate Statistical Phase Maps

Aggregate results and generate visualizations:

```bash
cd code
python statistics/aggregators.py --input data/processed/ --output data/aggregated/
python viz/reporter.py --input data/aggregated/ --output data/aggregated/summary.csv
python viz/plotter.py --input data/aggregated/ --output figures/
```

**Outputs:**
- `data/aggregated/summary.csv`: ANOVA p-values and stability flags.
- `figures/`: 3D contour maps and regime sample plots.

## Configuration

Grid and physical parameters are managed in `code/config/grid_config.py`. Key settings:

- `GRID_SIZE`: 64 (default for batch) or 256 (verification).
- `RUN_FULL_GRID`: Environment variable to toggle grid size.
- `MAX_TIME`: Maximum simulation time.
- `TIME_STEP`: Time step for integration.

Example environment setup:
```bash
export RUN_FULL_GRID=true
export GRID_SIZE=64
```

## Testing

Run the test suite:

```bash
pytest tests/
```

**Key Tests:**
- `tests/unit/test_gpe_solver.py::test_split_step_preserves_norm`: Validates numerical stability.
- `tests/integration/test_single_run.py::test_single_run_completes`: Ensures single run completion.
- `tests/unit/test_vortex_detector.py::test_phase_winding_detects_single_vortex`: Validates vortex detection.

## Performance Notes

- **Grid Resolution**: 64x64 is used for full batch scans to meet CI time/memory constraints. 256x256 is reserved for verification runs.
- **Runtime**: Full grid (300 runs) targets ≤6 hours on a 2-core runner.
- **Memory**: Peak memory usage is logged and validated in `code/simulation/verify_performance.py`.

## License

[Insert License Here]

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push to the branch.
5. Open a Pull Request.