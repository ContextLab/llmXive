# Quickstart: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Git

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repo-url>
   cd projects/PROJ-101-quantifying-the-influence-of-initial-con
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` includes `scipy`, `numpy`, `matplotlib`, `pandas`.*

## Running the Pipeline

### 1. Validate Baseline (Constitution Check VI)
Run the baseline validation script to ensure the numerical solver is accurate for the clean system.
```bash
python code/main.py --mode baseline --n_oscillators 1 --coupling 0.0
```
*Expected Output*: A plot showing FTLE convergence and a JSON report confirming $\lambda_{max}$ reaches a significant positive magnitude.

### 2. Generate Noisy Trajectories
Generate the synthetic dataset.
```bash
python code/main.py --mode generate --n_oscillators 5 --coupling 0.2 --noise_levels 0.001 0.01 0.1 --trials 30
```
*Expected Output*: Trajectory files in `data/raw/`.

### 3. Compute FTLE and Analyze
Run the full analysis pipeline (FTLE calculation + Regression).
```bash
python code/main.py --mode analyze --window_sizes 100 500 1000 5000
```
*Expected Output*:
- `data/processed/ftle_results.csv`
- `data/processed/regression_summary.json`
- Figures in `data/processed/figures/`

### 4. Verify Results
Check that the regression model shows a significant positive relationship between noise level and deviation.
```bash
python code/main.py --mode report
```

## Configuration

Edit `code/config.py` to change:
- `SEED`: Global random seed.
- `DEFAULT_N`: Default number of oscillators.
- `DEFAULT_D`: Default coupling strength.
- `TIME_STEP`: Integration step size.
- `TOTAL_TIME`: Total simulation duration.

## Troubleshooting

- **"Trajectory leaves attractor"**: Increase `noise_levels` threshold or reduce `coupling_strength`. The script will flag these as unphysical.
- **"Convergence failed"**: Check `rtol` and `atol` in `config.py`. Default is `1e-9`/`1e-12`.
- **"Runtime error"**: Ensure you are using Python 3.11+ and that `scipy` is installed correctly.
