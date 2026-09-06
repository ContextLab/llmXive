# Quickstart: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Git

## Installation

1. **Clone and Navigate**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-101-quantifying-the-influence-of-initial-con
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or: venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

### 1. Generate Baseline (Validation)
```bash
python code/main.py --phase baseline --config code/config.yaml
```
*Outputs*: `data/processed/baseline.json` (validates asymptotic limit via Richardson extrapolation).

### 2. Generate Noisy Trajectories & Compute FTLE
```bash
python code/main.py --phase full --config code/config.yaml
```
*Outputs*:
- `data/raw/trajectories_*.npz` (raw data)
- `data/processed/ftle_results.json` (FTLE estimates)
- `data/processed/regression_results.json` (statistical analysis with non-linear model selection)
- `data/processed/plots/deviation_vs_noise.png`

### 3. Run Tests
```bash
pytest tests/ -v
```
*Includes*: Unit tests for numerical stability, integration tests for pipeline.

## Reproducibility

- **Seeds**: Fixed in `code/config.yaml` (default `seed=42`).
- **Dependencies**: Pinned in `requirements.txt`.
- **Data**: All raw data is generated deterministically from seeds.

## Troubleshooting

- **"Escape Time Detected"**: If `escape_time` is recorded, the trajectory exited the basin. This is expected for high noise; the analysis includes this as a covariate.
- **"Convergence Failed"**: If baseline validation fails, increase `T_baseline` in `config.yaml`.
- **Memory Error**: Reduce $N$ or $T_{total}$ in `config.yaml`.