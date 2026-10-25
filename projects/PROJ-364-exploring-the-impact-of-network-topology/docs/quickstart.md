# Quickstart: Exploring the Impact of Network Topology on Heat Dissipation in 2D Materials

This guide walks you through setting up the environment and running the minimal end‑to‑end pipeline on the smallest valid dataset.

## Prerequisites

- Python 3.11 or newer
- Git
- A machine with ≤ 7 GB RAM (the pipeline is designed to run on the free‑tier GitHub Actions runner)

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-364-exploring-the-impact-of-network-topology

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r code/requirements.txt
```

## Data Setup

The pipeline expects a CSV file with defect coordinates (`x`, `y`) and a `sample_id` column [UNRESOLVED-CLAIM: c_2cac7dd5 — status=not_enough_info].

- **Option 1 – Use a real dataset**
 If a paired defect‑coordinate + thermal‑conductivity dataset is available, place the CSV under `data/raw/` and optionally compute its checksum:
 ```bash
 wget -O data/raw/paired_defects.csv <verified-url>
 python code/utils/checksum.py data/raw/paired_defects.csv
 ```

- **Option 2 – Validation‑only synthetic data**
 When no real data is present, generate a deterministic synthetic dataset (validation mode only):
 ```bash
 python code/src/data_ingestion/generate_synthetic.py \
 --output-dir data/raw \
 --n-samples 1 \
 --grid-size 100 \
 --n-defects 50 \
 --seed 42
 ```
 This creates `data/raw/synthetic_defects.csv` and a matching checksum manifest.

## Configuration

Create (or edit) `code/config.yaml` with the minimal settings required for the run:
```yaml
# Proximity threshold handling
proximity_threshold: 2.5 # nm (baseline)
statistical_override: false # set true to use lattice‑constant scaling

# Statistical settings
bootstrap_iterations: 1000
random_seed: 42
```

## Running the Pipeline

```bash
python code/main.py --config code/config.yaml
```

- With **real data**, the script will:
 1. Load the CSV, drop rows with missing coordinates (logged as warnings)
 2. Compute the proximity threshold
 3. Build a graph using `networkx` and `cKDTree`
 4. Extract topological metrics
 5. Perform correlation analysis, bootstrap confidence intervals, Bonferroni correction, and sensitivity analysis
 6. Write results to `results/analysis_results.json` and plots to `results/plots/` [UNRESOLVED-CLAIM: c_c9119177 — status=not_enough_info]

- With **synthetic data**, the script runs up to metric extraction, logs a *validation‑only* warning, and exits without hypothesis testing.

## Expected Outputs

- `results/analysis_results.json` – JSON report conforming to `contracts/analysis.schema.yaml`
- `results/plots/` – PNG scatter plots of each metric vs. thermal conductivity
- `logs/pipeline.log` – Full pipeline log

## Testing

```bash
# Unit tests
pytest tests/unit/

# Integration test (runs the full pipeline on the synthetic dataset)
pytest tests/integration/
```

## Troubleshooting

- **Memory errors** – Ensure the CSV is streamed (`chunksize` in `pandas.read_csv`) or use a smaller synthetic grid.
- **No real data** – Verify that `data/raw/` contains a CSV and that the checksum manifest is present.
- **Disconnected graph warnings** – Appear when the defect network is sparse; metrics are still computed on the largest connected component and flagged in the output.