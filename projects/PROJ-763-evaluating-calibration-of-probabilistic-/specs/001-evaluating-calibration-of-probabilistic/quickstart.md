# Quickstart: Evaluating Calibration of Probabilistic Weather Forecasts

## Prerequisites
- Python 3.11+
- GitHub Actions runner (multi-core CPU, sufficient RAM, and adequate disk storage)
- Internet access for dataset download

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-763-evaluating-calibration-of-probabilistic-/code/
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

### Step 1: Download and Verify Dataset
```bash
bash data/download.sh
bash data/verify.sh
```
- Downloads SubseasonalRodeo (or NOAA GFS substitute) from verified source.
- Verifies checksum; halts if missing `probability_value` field (exit code 1).

### Step 2: Baseline Calibration Assessment
```bash
python analysis/baseline/align.py
python analysis/baseline/metrics.py
python analysis/baseline/plots.py
```
- Aligns forecasts with observations.
- Computes Brier scores, CRPS.
- Generates reliability diagrams and PIT histograms.
- Outputs: `results_baseline.csv`, `reliability_diagram_raw.png`.

### Step 3: Isotonic Recalibration
```bash
python analysis/isotonic/train.py
python analysis/isotonic/evaluate.py
python analysis/isotonic/sensitivity.py
```
- Fits isotonic regression per lead time and variable.
- Computes recalibrated metrics.
- Runs sensitivity analysis with varying split ratios.
- Outputs: `results_isotonic.csv`, `reliability_diagram_isotonic.png`.

### Step 4: Bayesian Hierarchical Recalibration
```bash
python analysis/bayesian/model.py
python analysis/bayesian/prior_sensitivity.py
python analysis/bayesian/diagnostics.py
```
- Runs MCMC sampling (multiple chains, sufficient draws).
- Checks convergence (R-hat, ESS).
- If fails, generates `results_fallback.csv`.
- Outputs: `results_bayesian.csv` (if converged) or `results_fallback.csv`.

### Step 5: Statistical Comparison
```bash
python analysis/comparison/diebold_mariano.py
python analysis/comparison/summary.py
```
- Runs DM-HAC or Block Bootstrap tests.
- Generates final comparison table.
- Outputs: `results/` directory with all files.

## Expected Outputs

- `results/results_baseline.csv`: Baseline metrics.
- `results/results_isotonic.csv`: Isotonic recalibration metrics.
- `results/results_bayesian.csv`: Bayesian recalibration metrics (if converged).
- `results/results_fallback.csv`: Fallback isotonic results (if Bayesian failed).
- `results/reliability_diagram_*.png`: Reliability diagrams.
- `results/pit_histogram_*.png`: PIT histograms.
- `results/convergence_diagnostics.json`: Bayesian convergence diagnostics.
- `results/pipeline.log`: Full pipeline log.

## Troubleshooting

- **Dataset download failed**: Check internet connection; verify URL; ensure checksum matches.
- **Data Availability Gate Failed**: Dataset lacks `probability_value`; halt execution.
- **Bayesian convergence failed**: Check R-hat, ESS; if > thresholds, fallback to isotonic.
- **Memory overflow**: Use streaming or sample; log power limitation.
- **Autocorrelation in errors**: Shapiro-Wilk test fails; use Block Bootstrap.

## Verification

- **Unit Tests**: `pytest tests/unit/`
- **Integration Tests**: `pytest tests/integration/`
- **Contract Tests**: `pytest tests/contract/`
- **Pipeline Test**: `bash run_pipeline.sh` (entire pipeline within 6 hours).
