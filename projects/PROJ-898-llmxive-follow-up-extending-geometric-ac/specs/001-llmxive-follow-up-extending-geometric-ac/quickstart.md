# Quickstart: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Prerequisites

- Python 3.11+
- pip
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-898-llmxive-follow-up-extending-geometric-ac
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` includes `pybullet`, `torch`, `scipy`, `numpy`, `pandas`, `scipy`, `statsmodels`.*

4. **Verify PyBullet installation**:
   ```bash
   python -c "import pybullet; print(pybullet.__version__)"
   ```

## Running the Pipeline

### Step 1: Generate Synthetic Test Set
```bash
python code/generate_topology.py --seed 42 --output data/generated/topology_set_v1 --count 60
```
*Output*: `data/generated/topology_set_v1/metadata.json`, `data/generated/topology_set_v1/states_*.npy`
*Note*: If <50 unique topologies are generated, the script will log a CRITICAL error and exit.

### Step 2: Compute Reference Statistics (One-time)
```bash
python code/utils/drift_detector.py --compute-stats --input data/raw/gfm_weights.pt --output data/raw/gam_reference_stats.json
```
*Output*: `data/raw/gam_reference_stats.json` (Mean/Covariance from GFM prior or standard normal if weights missing).
*Note*: If `data/raw/gfm_weights.pt` is missing, the script falls back to standard normal distribution and logs a warning.

### Step 3: Run Inference (Symbolic & Baseline)
```bash
python code/inference_loop.py --config code/config.yaml --mode all
```
*Output*: `data/results/trial_log.csv`, `data/results/gradient_flow_log.json`

### Step 4: Statistical Analysis
```bash
python code/analysis.py --input data/results/trial_log.csv --output data/results/statistical_report.json
```
*Output*: `data/results/statistical_report.json` (contains p-values, CIs, effect sizes, survival analysis)

## Verification

- **Check Uniqueness**: Ensure `metadata.json` contains 50+ unique topologies.
- **Check Gradients**: Verify `gradient_flow_log.json` has `valid_path: true`.
- **Check Statistics**: Ensure `statistical_report.json` reports p-values and 95% CIs.

## Troubleshooting

- **PyBullet Errors**: Ensure `pybullet` is installed and compatible with your OS.
- **Memory Issues**: Reduce `--count` in Step 1 or `--trials` in Step 3.
- **Timeouts**: Increase solver timeout in `code/config.yaml` (not recommended for CI).
- **Missing Weights**: If `data/raw/gfm_weights.pt` is missing, the pipeline will fall back to standard normal distribution for drift detection but log a warning.