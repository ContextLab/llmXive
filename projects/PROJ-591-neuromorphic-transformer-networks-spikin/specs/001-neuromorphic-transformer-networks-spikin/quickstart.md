# Quickstart: Neuromorphic Transformer Networks

## Prerequisites

- Python 3.10+
- Git
- Sufficient RAM (for CI compatibility)

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-591-neuromorphic-transformer-networks-spikin
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins `torch` to a CPU-only version and `snnTorch` to a compatible release.*

3. **Verify Environment**:
   ```bash
   python code/tests/neuromorphic_fidelity_test.py
   ```
   This test verifies that LIF neurons fire correctly and gradients are non-NaN.

## Running the Experiments

### 1. Data Download
The script automatically downloads WikiText-2. To force a re-download:
```bash
python code/data/dataset_loader.py --force-download
```

### 2. Training Baseline and Spiking Models
Run the main training script with a specific seed:
```bash
# Baseline
python code/main.py --model baseline --seed 1

# Spiking
python code/main.py --model spiking --seed 1
```
*To run all seeds (multiple baseline + multiple spiking):*
```bash
bash code/run_all_seeds.sh
```

### 3. Analysis
After training completes, run the statistical analysis:
```bash
python code/analysis/statistical_tests.py
```
This generates `data/energy_logs/statistical_results.csv` and `data/energy_logs/sensitivity_analysis.json`.

### 4. Generating Figures
```bash
python code/analysis/plots.py
```
Outputs figures to `data/figures/`.

## Troubleshooting

- **CodeCarbon Fails**: If `codecarbon` cannot access hardware sensors (common on CI), the script will automatically fall back to wall-clock time and flag the metric as "estimated". Check `is_estimated_energy` in the CSV.
- **Zero Spikes**: If the spiking model produces no spikes, the training loop will halt and log a diagnostic report. Check `data/logs/diagnostics.log`.
- **Out of Memory**: The model is designed for moderate RAM requirements. If OOM occurs, reduce `batch_size` in `code/main.py` (default: 32).
