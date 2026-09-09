# Quickstart Guide: Quantifying the Influence of Initial Conditions on Chaotic Systems

This guide provides instructions for running the full pipeline to analyze how initial conditions and noise influence chaotic dynamics in coupled Lorenz systems.

## Prerequisites

- Python 3.11 or higher
- Required dependencies listed in `requirements.txt`

## Installation

1. Clone the repository and navigate to the project root.
2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Pipeline

The main entry point is `code/main.py`. It supports several subcommands to control different stages of the analysis.

### Full Pipeline Execution

To run the complete pipeline (generation, validation, and analysis) with default settings:

```bash
python code/main.py run-all
```

### Custom Configuration

You can customize the simulation parameters using CLI arguments.

#### Generating Trajectories with Specific Noise Levels and System Dimensions

The `generate` command allows you to specify the number of coupled oscillators (`--N`) and the noise levels (`--noise-level`) to inject into the system.

**Arguments:**

- `--N`: Number of coupled Lorenz oscillators. Default is 5.
 - Example: `--N 3` or `--N 10`
- `--noise-level`: Comma-separated list of noise standard deviation values ($\sigma$).
 - Example: `--noise-level 0.0,0.01,0.1,0.5,1.5`

**Example Command:**

```bash
python code/main.py generate --N 5 --noise-level 0.0,0.01,0.1,1.5
```

This will generate trajectories for a system of 5 coupled oscillators with noise levels ranging from deterministic (0.0) to highly noisy (1.5). The output files will be saved to `data/raw/`.

**Note:** The system automatically determines the number of trials ($k$) based on the noise level:
- $k = 50$ trials if $\sigma < 0.01$
- $k = 30$ trials if $\sigma \ge 0.01$

### Running Analysis Stages

After generating data, you can run the analysis stages independently:

1. **Compute Baselines:**

```bash
python code/main.py compute-baseline --N 5
```

2. **Run FTLE Sweep:**

```bash
python code/main.py run-ftle --N 5
```

3. **Run Regression Analysis and Generate Plots:**

```bash
python code/main.py run-regression --N 5
```

### Output Artifacts

All processed data and visualizations are saved in the `data/processed/` directory:

- `baseline_{N}.json`: Asymptotic Lyapunov exponent baselines
- `ftle_sweep.json`: Finite-Time Lyapunov Exponent results across windows and trials
- `regression_model.json`: Selected regression model parameters
- `results.json`: Statistical summary including p-values and effect sizes
- `plot_deviation_vs_noise.png`: Visualization of bias scaling with noise
- `plot_convergence.png`: FTLE convergence plot across noise levels

## Verification

To verify the installation and run a quick sanity check:

```bash
python code/main.py verify
```

## Troubleshooting

- **Non-Chaotic Regime Error:** If the system parameters result in a non-chaotic regime (max Lyapunov exponent $\le 0$), the pipeline will halt with a `NonChaoticSystemError`. Adjust the `rho` parameter in `code/config.py` if necessary.
- **Unphysical Trajectory:** If noise levels are too high ($\sigma > 1.0$) or trajectories diverge beyond attractor bounds ($|state| > 100$), the specific trial will be flagged as unphysical and skipped.

For more details, refer to the full documentation in `README.md`.