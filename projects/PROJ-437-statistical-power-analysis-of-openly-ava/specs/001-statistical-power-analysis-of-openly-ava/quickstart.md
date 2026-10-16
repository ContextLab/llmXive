# Quickstart: Statistical Power Analysis of Openly Available fMRI Datasets

## Prerequisites
- Python 3.11+  
- Internet access (to download OpenNeuro parquet shards)  
- ≤ 7 GB RAM, ≤ 14 GB disk (GitHub Actions free‑tier compatible)

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
  sample_sizes: [10, 20, 40, 60]
  smoothing_kernels: [2.0, 4.0]   # temporal smoothing in time points
  num_iterations: 50
  random_seed: 42
  effect_sizes: [0.0, 0.2, 0.5, 0.8, 1.0]
  alpha_thresholds: [0.01, 0.05, 0.10]
  snr_levels: [0.5, 1.0, 2.0]

preprocessing:
  roi_extraction: "standard"   # uses MNI152 atlas
  temporal_smoothing: true
```

## Running the Pipeline

### 1. Download Data
```bash
python code/main.py --action download --config config.yaml
```
*Downloads the verified OpenNeuro parquet shards, validates checksums, and stores them under `data/raw/`.*

### 2. Estimate Noise
```bash
python code/main.py --action estimate_noise --config config.yaml
```
*Produces noise profiles used for synthetic data generation.*

### 3. Generate Synthetic Data
```bash
python code/main.py --action generate_synthetic --config config.yaml
```
*Creates synthetic BOLD time‑series with known ground‑truth effect sizes.*

### 4. Run Power Analysis
```bash
python code/main.py --action analyze --config config.yaml
```
*Executes split‑half validation (bootstrapped), builds power curves, and fits the logistic regression model.*

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

- **ROI extraction fails** – check `data/logs/roi_extractor.log`. Verify that the anatomical mask matches the dataset’s voxel dimensions.  
- **Memory overflow** – `memory_monitor.py` will automatically downsample; see `data/logs/memory_monitor.log` for actions taken.  
- **GLM non‑convergence** – failed iterations are logged in `data/aggregated/convergence_log.json`; if > 20 % fail, the final report flags the result as “Unreliable”.  

## Output Interpretation

- **Power Curve** – X: sample size; Y: empirical replication rate (True Positive Rate).  
- **Logistic Regression** – Coefficients quantify the influence of sample size, smoothing kernel, and SNR on replication probability; VIF < 5 indicates acceptable collinearity.  
- **FDR‑corrected p‑values** – Adjusted across paradigms; reported in `results/paper/model_summary.csv`.  
- **Alpha Sensitivity** – Separate curves for each α value are plotted side‑by‑side.

---
