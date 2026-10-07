# Investigating the Stability of Rotating Bose-Einstein Condensates with Dipolar Interactions

This project implements a numerical pipeline to investigate the stability of rotating Bose-Einstein condensates (BECs) with dipolar interactions. It solves the time-dependent Gross-Pitaevskii equation (GPE) using a split-step Fourier method, detects vortices via phase winding, and performs statistical analysis to map the stability phase diagram.

## Table of Contents

- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
 - [Running a Single Simulation](#running-a-single-simulation)
 - [Running the Full Parameter Grid](#running-the-full-parameter-grid)
 - [Analyzing Snapshots](#analyzing-snapshots)
 - [Generating Visualizations](#generating-visualizations)
- [Configuration](#configuration)
- [Parameters](#parameters)
- [Output Data](#output-data)
- [Testing](#testing)
- [License](#license)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
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
│ ├── analysis/ # Vortex detection, metrics calculation
│ ├── config/ # Configuration management
│ ├── models/ # Data models and entities
│ ├── simulation/ # GPE solver, initial conditions, batch runner
│ ├── statistics/ # Statistical analysis, aggregation
│ ├── utils/ # Logging, I/O helpers, seed management
│ ├── viz/ # Visualization and reporting
│ └── requirements.txt
├── data/
│ ├── raw/ # Raw simulation output (density, phase snapshots)
│ ├── processed/ # Processed metrics (vortex counts, stability scores)
│ └── aggregated/ # Aggregated statistical results
├── tests/
│ ├── unit/ # Unit tests
│ ├── integration/ # Integration tests
│ └── contract/ # Contract tests
├── specs/ # Design documents, data models, research notes
└── README.md
```

## Usage

### Running a Single Simulation

To run a single GPE simulation with specific parameters:

```bash
python code/simulation/gpe_solver.py \
 --omega 0.5 \
 --epsilon_dd 0.5 \
 --N 10000 \
 --grid_size 64 \
 --max_time 5.0 \
 --output_dir data/raw
```

This will generate density and phase snapshots in `data/raw/`.

### Running the Full Parameter Grid

To run the full parameter scan (64x64 grid) or verification (256x256):

```bash
# Set environment variable to choose grid size
export RUN_FULL_GRID=true # 64x64 for full scan
# or
export RUN_FULL_GRID=false # 256x256 for verification

python code/simulation/runner.py \
 --output_dir data/raw \
 --metrics_output data/processed/metrics.csv
```

The batch runner will iterate over:
- **Ω (Rotation frequency)**: Range [0.0, 0.9]
- **ε_dd (Dipolar interaction strength)**: {0.0, 0.5, 1.0, 1.5}
- **N (Particle number)**: {small, intermediate, large}

### Analyzing Snapshots

To detect vortices and calculate stability metrics from simulation snapshots:

```bash
python code/analysis/pipeline.py \
 --input_dir data/raw \
 --output_file data/processed/metrics.csv
```

This pipeline:
1. Detects vortices using phase-winding algorithm
2. Calculates stability metrics (vortex density, radial variance, structure factor)
3. Classifies metastability boundaries
4. Exports results to CSV

### Generating Visualizations

To generate the 3D stability phase diagram and summary reports:

```bash
# Aggregate results and perform statistical analysis
python code/statistics/aggregators.py \
 --input_file data/processed/metrics.csv \
 --output_dir data/aggregated

# Generate visualizations
python code/viz/plotter.py \
 --input_dir data/aggregated \
 --output_dir figures

# Generate summary report
python code/viz/reporter.py \
 --input_dir data/aggregated \
 --output_file data/aggregated/summary_table.csv
```

## Configuration

Configuration is managed through environment variables and command-line arguments:

- **RUN_FULL_GRID**: Set to `true` for 64x64 grid (full scan), `false` for 256x256 (verification)
- **LOG_LEVEL**: Set logging verbosity (DEBUG, INFO, WARNING, ERROR)
- **RANDOM_SEED**: Set for reproducibility (default: derived from timestamp)

Grid parameters can be configured in `code/config/grid_config.py`:
- Domain size
- Time step
- Maximum simulation time
- Resolution

## Parameters

### Key Simulation Parameters

| Parameter | Symbol | Description | Range/Values |
|-----------|--------|-------------|--------------|
| Rotation frequency | Ω | Angular velocity of the trap | [0.0, 0.9] |
| Dipolar strength | ε_dd | Ratio of dipolar to contact interaction | {0.0, 0.5, 1.0, 1.5} |
| Particle number | N | Total number of atoms | {small, intermediate, large} |
| Grid size | Nx, Ny | Spatial discretization | 64 or 256 |
| Max time | t_max | Simulation duration | 5.0 (default) |

### Stability Metrics

| Metric | Description |
|--------|-------------|
| Vortex Density | Number of vortices per unit area |
| Radial Variance | Spread of density distribution |
| Structure Factor Sharpness | Measure of vortex lattice order |
| Metastability Status | Stable, Metastable, or Unstable classification |

## Output Data

### Raw Data (`data/raw/`)
- Density snapshots: `density_t{time}.npy`
- Phase snapshots: `phase_t{time}.npy`
- Wavefunction: `wavefunction_t{time}.npy`

### Processed Data (`data/processed/`)
- `metrics.csv`: Contains vortex counts, stability metrics, and classification for each simulation run

### Aggregated Data (`data/aggregated/`)
- `aggregated_metrics.json`: Statistical aggregates per parameter set
- `anova_results.json`: Two-Way ANOVA results (Ω × ε_dd)
- `dunnett_results.json`: Post-hoc test results
- `summary_table.csv`: ANOVA p-values and significance flags

### Figures (`figures/`)
- 3D contour maps of stability phase diagram
- Density and phase plots for stable, metastable, and unstable regimes
- Vortex detection visualizations

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run specific test suites:
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Contract tests
pytest tests/contract/ -v
```

## License

This project is part of the llmXive automated science pipeline. See the LICENSE file for details.