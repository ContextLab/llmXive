# Quickstart: Statistical Power Analysis of Openly Available fMRI Datasets

## Prerequisites
- Python 3.11+  
- Internet access (to download OpenNeuro BIDS datasets)  
- ≤ 7 GB RAM, ≤ 14 GB disk (GitHub Actions free‑tier compatible)

## Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## Configuration
Create a `config.yaml` at the project root:

```yaml
datasets:
  - id: "ds000030"
    paradigm: "motor"
  - id: "ds000206"
    paradigm: "working_memory"
  - id: "ds000117"
    paradigm: "emotional_face"
  - id: "ds000247"
    paradigm: "auditory_oddball"
  - id: "ds001141"
    paradigm: "visual_motion"

simulation:
  sample_sizes: [10, 20, 40, 60]               # primary coarse grid
  sample_sizes_fine: [10, 15, 20, 30, 40, 50, 60]  # optional fine grid for 2 paradigms
  smoothing_kernels: [2.0, 4.0]   # temporal smoothing in time points
  num_iterations: 50
  random_seed: 42
  effect_sizes: [0.0, 0.2, 0.5, 0.8, 1.0]
  alpha_thresholds: [0.01, 0.05, 0.10]
  snr_levels: [0.5, 1.0, 2.0]
  magnitude_tolerances: [10.0, 20.0, 30.0]    # ±10%, ±20%, ±30% for sensitivity

preprocessing:
  roi_extraction: "standard"   # uses MNI152 atlas
  temporal_smoothing: true
```

## Running the Pipeline

### 1. Download Data
```bash
python code/main.py --action download --config config.yaml
```
*Downloads raw BIDS data from OpenNeuro (https://openneuro.org/datasets/...) using `openneuro_py`, validates checksums (T082), and stores under `data/raw/`.*

### 2. Estimate Noise
```bash
python code/main.py --action estimate_noise --config config.yaml
```
*Computes noise profiles from real BOLD time‑series.*

### 3. Inject Synthetic Signals
```bash
python code/main.py --action inject_signals --config config.yaml
```
*Creates signal-injected BOLD time‑series (synthetic signal added to real data).*

### 4. Run Power Analysis
```bash
python code/main.py --action analyze --config config.yaml
```
*Executes split‑half validation (bootstrapped), builds power curves, checks collinearity (T090), fits the logistic regression model, and writes `results/paper/convergence_report.md` (T049) and `results/paper/predictor_correlation.csv` (T090).*

### 5. Generate Report
```bash
python code/main.py --action report --config config.yaml
```
*Produces figures and tables under `results/paper/` ready for manuscript inclusion.*

## Testing

### Unit Tests
```bash
pytest tests/unit/ -v
```

### Integration Test (end‑to‑end on a tiny subset)
```bash
pytest tests/integration/test_end_to_end_pipeline.py -v
```

### Contract Tests
```bash
pytest tests/contract/ -v
```

## Troubleshooting

- **OpenNeuro download fails** – check `data/logs/download.log`. Verify internet connectivity; `openneuro_py` supports resumable downloads.  
- **ROI extraction fails** – check `data/logs/roi_extractor.log`. Verify that the anatomical mask matches the dataset's voxel dimensions.  
- **Memory overflow** – `memory_monitor.py` will automatically downsample; see `data/logs/memory_monitor.log` for actions taken.  
- **GLM non‑convergence** – failed iterations are logged in `data/aggregated/convergence_log.json`; if > 20 % fail, the final report flags the result as "Unreliable".  
- **Checksum mismatch** – `tests/contract/test_data_integrity.py` (T082) will abort the run and emit a clear error message.  
- **Collinearity detected** – if any VIF ≥ 5, `collinearity_checker.py` (T090) logs a warning and the logistic regression is refit without the offending term; see `results/paper/predictor_correlation.csv`.

## Output Interpretation

- **Power Curve** – X: sample size; Y: empirical replication rate (True Positive Rate).  
- **Predictor Correlation** – `results/paper/predictor_correlation.csv` shows correlation matrix and VIF for predictors; VIF < 5 indicates acceptable collinearity.  
- **Logistic Regression** – Coefficients quantify the influence of sample size, smoothing kernel, and SNR on replication probability.  
- **FDR‑corrected p‑values** – Adjusted across paradigms; reported in `results/paper/model_summary.csv`.  
- **Alpha Sensitivity** – Separate curves for each α value (0.01, 0.05, 0.10) are plotted side‑by‑side.  
- **Magnitude Tolerance Sensitivity** – Power curves are shown for ±10%, ±20%, ±30% tolerances to demonstrate robustness.  
- **Fine Grid Results** – For Motor and Working Memory paradigms, power curves are shown on both coarse (10, 20, 40, 60) and fine (10, 15, 20, 30, 40, 50, 60) grids to better capture the non‑linear relationship.  
