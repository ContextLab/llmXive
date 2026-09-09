# Quantifying the Influence of Initial Conditions on Chaotic Systems

**Project ID**: PROJ-101-quantifying-the-influence-of-initial-con

This project investigates how initial conditions and noise levels influence the Finite-Time Lyapunov Exponents (FTLE) in coupled Lorenz oscillator systems. It implements a full scientific pipeline: data generation, baseline computation, FTLE analysis, and statistical regression.

## Prerequisites

- Python 3.11+
- pip (package manager)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-101-quantifying-the-influence-of-initial-con
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure

```
.
├── code/ # Source code modules
│ ├── config.py # Configuration and hyperparameters
│ ├── main.py # Pipeline orchestrator
│ ├── data/ # Data generation and loading
│ ├── analysis/ # FTLE, Baseline, Regression analysis
│ └── utils/ # Utility functions
├── data/
│ ├── raw/ # Generated trajectory CSVs
│ └── processed/ # Analysis results (JSON, PNG)
├── tests/ # Unit and integration tests
├── specs/ # Feature specifications
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Quick Start

The pipeline is executed via `code/main.py`.

### 1. Generate Trajectories (User Story 1)

Generates coupled Lorenz trajectories with varying noise levels and oscillator counts.

```bash
python code/main.py generate \
 --N-values 5 \
 --noise-levels 0.001 0.01 0.1 0.5 1.5 2.0
```

- `--N-values`: Number of coupled oscillators (e.g., 5).
- `--noise-levels`: List of sigma values for Gaussian noise injection.
- **Output**: Trajectories saved to `data/raw/trajectory_N{N}_sigma{sigma}_trial{t}.csv`.

### 2. Compute Baselines (User Story 2)

Computes the asymptotic Lyapunov baseline for the clean system using Richardson extrapolation.

```bash
python code/main.py baseline --N 5
```

- `--N`: Number of oscillators.
- **Output**: `data/processed/baseline_{N}.json`.

### 3. Run FTLE Analysis (User Story 2)

Computes Finite-Time Lyapunov Exponents over sliding windows for all generated trajectories.

```bash
python code/main.py analyze-ftle
```

- **Input**: Trajectories in `data/raw/`, Baselines in `data/processed/`.
- **Output**: `data/processed/ftle_sweep.json`.

### 4. Run Regression & Visualization (User Story 3)

Performs statistical analysis, model selection, and generates plots.

```bash
python code/main.py analyze-regression
```

- **Input**: `data/processed/ftle_sweep.json`, `data/processed/baseline_{N}.json`.
- **Output**:
 - `data/processed/results.json` (Regression stats, p-values, effect sizes)
 - `data/processed/regression_model.json`
 - `data/processed/plot_deviation_vs_noise.png`
 - `data/processed/plot_convergence.png`

## Full Pipeline Execution

To run the complete analysis from scratch (Generation -> Baseline -> FTLE -> Regression):

```bash
python code/main.py full-pipeline \
 --N-values 5 \
 --noise-levels 0.001 0.01 0.1 0.5 1.5 2.0
```

This command sequentially executes all stages and ensures data dependencies are met.

## CLI Arguments Reference

| Argument | Description | Default |
|:--- |:--- |:--- |
| `--N-values` | Number of coupled oscillators | `5` |
| `--noise-levels` | Noise levels (sigma) to test | `0.001, 0.01, 0.1, 0.5, 1.5, 2.0` |
| `--timesteps` | Total integration steps | `5000` |
| `--dt` | Integration time step | `0.01` |
| `--output-dir` | Root directory for outputs | `data/` |

## Testing

Run the test suite using pytest:

```bash
pytest tests/ -v
```

### Unit Tests
- `tests/unit/test_generator.py`: Validates noise injection and trajectory generation.
- `tests/unit/test_ftle.py`: Validates FTLE computation and Jacobian stability.
- `tests/unit/test_regression.py`: Validates statistical significance checks.

### Integration Tests
- `tests/integration/test_pipeline.py`: Validates the full end-to-end pipeline execution.

## Configuration

Hyperparameters and simulation settings are defined in `code/config.py`. Key parameters include:

- **Numerical Tolerances**: `rtol=1e-9`, `atol=1e-12` (DOP853 solver).
- **Attractor Bounds**: Max state magnitude threshold `100`.
- **Noise Thresholds**: `sigma > 0.1` triggers `HighNoiseWarning`; `sigma > 1.0` triggers `UnphysicalTrajectoryError`.

## License

[Project License]